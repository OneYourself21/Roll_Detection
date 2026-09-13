import duckdb
import polars as pl


def select_db(path : str) -> pl.DataFrame:
    duckdb.sql('SET TIMEZONE = "America/New_York";')
    df = duckdb.sql('SELECT * FROM "' + path + '";').pl()
    return df


def daily_candles(path : str, contract : str, year : int) -> pl.DataFrame:
    previous_year = year - 1

    duckdb.sql('SET TIMEZONE = "America/New_York";')

    query = """
               SELECT FIRST(ts_event ORDER BY ts_event) AS ts_event,
                      ANY_VALUE(instrument_id) AS instrument_id,
                      ANY_VALUE(symbol) AS symbol,
                      FIRST(open ORDER BY ts_event) AS open,
                      MAX(high) AS high,
                      MIN(low) AS low,
                      LAST(close ORDER BY ts_event) AS close,
                      SUM(volume) AS volume
               FROM read_parquet($path)
               WHERE symbol = $contract 
                 AND (date_part('year', ts_event) = $previous_year OR date_part('year', ts_event) = $current_year) 
               GROUP BY strftime(ts_event - INTERVAL 18 HOUR, '%Y/%m/%d') ORDER BY 1;
            """

    df = duckdb.sql(query, params =
                    {
                        "path" : path,
                        "contract" : contract,
                        "previous_year" : previous_year,
                        "current_year" : year,
                    }
                    ).pl()

    return df


def daily_returns(path : str, contract : str, year : int) -> pl.DataFrame:
    previous_year = year - 1

    duckdb.sql('SET TIMEZONE = "America/New_York";')

    query = """ SELECT ts_event,
                       instrument_id,
                       symbol,
                       close - LAG(close) OVER (ORDER BY ts_event) AS close_to_close_returns,
                       close - open AS intraday_returns,           
                FROM (
                      SELECT FIRST(ts_event ORDER BY ts_event) AS ts_event,
                             ANY_VALUE(instrument_id) AS instrument_id,
                             ANY_VALUE(symbol) AS symbol,
                             FIRST(open ORDER BY ts_event) AS open,
                             LAST(close ORDER BY ts_event) AS close,
                      FROM read_parquet($path)
                      WHERE symbol = $contract 
                        AND (date_part('year', ts_event) = $previous_year OR date_part('year', ts_event) = $current_year) 
                      GROUP BY strftime(ts_event - INTERVAL 18 HOUR, '%Y/%m/%d') ORDER BY 1
                     ) daily_candles
            """

    returns = duckdb.sql(query, params =
                    {
                        "path" : path,
                        "contract" : contract,
                        "previous_year" : previous_year,
                        "current_year" : year,
                    }
                    ).pl()

    return returns


def rolling_stats(path : str, contract : str, year : int, days : int) -> pl.DataFrame:
    previous_year = year - 1

    normalising_factor = 1-(1/days)

    duckdb.sql('SET TIMEZONE = "America/New_York";')

    duckdb.sql("""CREATE TABLE daily_candles AS 
                      SELECT ts_event,
                             instrument_id,
                             symbol,
                             CAST(volume AS BIGINT) AS volume,
                          
                             CAST(SUM(volume) OVER (ORDER BY (DATE_TRUNC('day', ts_event))
                                        RANGE BETWEEN INTERVAL ($days - 1) DAYS PRECEDING
                                                  AND INTERVAL 0 DAYS FOLLOWING) AS BIGINT) AS rolling_volume,
                             
                             stddev(returns) OVER (ORDER BY (DATE_TRUNC('day', ts_event))
                                         RANGE BETWEEN INTERVAL ($days - 1) DAYS PRECEDING
                                                   AND INTERVAL 0 DAYS FOLLOWING) AS rolling_volatility,

                             GREATEST(high - low, 
                                      ABS(high - LAG(close) OVER (ORDER BY ts_event)),
                                      ABS(low -  LAG(close) OVER (ORDER BY ts_event))) AS true_range,

                    
                      FROM (SELECT FIRST(ts_event ORDER BY ts_event) AS ts_event,
                                   ANY_VALUE(instrument_id) AS instrument_id,
                                   ANY_VALUE(symbol) AS symbol,
                                   FIRST(open ORDER BY ts_event) AS open,
                                   MAX(high) AS high,
                                   MIN(low) AS low,
                                   LAST(close ORDER BY ts_event) AS close,
                                   SUM(volume) AS volume,
                                   LAST(close ORDER BY ts_event) - FIRST(open ORDER BY ts_event) AS returns,
                            FROM read_parquet($path)
                            WHERE symbol = $contract 
                              AND (date_part('year', ts_event) = $previous_year OR date_part('year', ts_event) = $current_year) 
                            GROUP BY strftime(ts_event - INTERVAL 18 HOUR, '%Y/%m/%d') ORDER BY 1)
               """, params ={
                             "path": path,
                             "contract": contract,
                             "previous_year": previous_year,
                             "current_year": year,
                             "days": days
                             })

    query_2 = """WITH RECURSIVE ATR (ts_event, true_range, average_true_range) AS (
                                     -- Base case: seed with the first row
                                     SELECT
                                         ts_event,
                                         true_range,
                                         true_range AS average_true_range
                                     FROM daily_candles
                                     WHERE ts_event = (SELECT MIN(ts_event) FROM daily_candles)

                                     UNION ALL

                                     -- Recursive step: advance one row at a time
                                     SELECT
                                         next.ts_event,
                                         next.true_range,
                                         atr.average_true_range * $normalising_factor + next.true_range / $days AS average_true_range
                                     FROM ATR atr
                                     JOIN daily_candles next
                                         ON next.ts_event = (
                                             SELECT MIN(ts_event)
                                             FROM daily_candles
                                             WHERE ts_event > atr.ts_event
                                                            )
                                                                                   )
                 SELECT
                     dc.ts_event,
                     dc.instrument_id,
                     dc.symbol,
                     dc.volume,
                     dc.rolling_volume,
                     dc.rolling_volatility,
                     atr.average_true_range AS ATR
                 FROM ATR atr
                 JOIN daily_candles dc ON atr.ts_event = dc.ts_event
                 """

    df = duckdb.sql(query_2, params={"normalising_factor" : normalising_factor, "days" : days}).pl()
    duckdb.sql("""DROP TABLE daily_candles;""")

    return df


def rollover_dates(path : str, min_overlap : int) -> pl.DataFrame:
    with duckdb.connect() as con:
        con.sql('SET TIMEZONE = "America/New_York";')



        filter_volume_query = """
            CREATE TEMP TABLE filtered_daily_candles AS
            SELECT LAST(ts_event ORDER BY volume) AS ts_event,
                   LAST(instrument_id ORDER BY volume) AS instrument_id,
                   LAST(symbol ORDER BY volume) AS symbol,
                   LAST(open ORDER BY volume) AS open,
                   LAST(high ORDER BY volume) AS high,
                   LAST(low ORDER BY volume) AS low,
                   LAST(close ORDER BY volume) AS close,
                   LAST(volume ORDER BY volume) AS volume
            FROM (
                SELECT date_trunc('day', FIRST(ts_event - INTERVAL 18 HOUR ORDER BY ts_event)) AS ts_event,
                   ANY_VALUE(instrument_id)          AS instrument_id,
                   ANY_VALUE(symbol)                 AS symbol,
                   FIRST(open ORDER BY ts_event) AS open,
                   MAX(high) AS high,
                   MIN(low) AS low,
                   LAST(close ORDER BY ts_event) AS close,
                   CAST(SUM(volume) AS BIGINT) AS volume
                FROM read_parquet($path)
                WHERE NOT symbol LIKE '%-%'
                GROUP BY date_trunc('day', ts_event - INTERVAL 18 HOUR),
                     instrument_id
                ORDER BY 1, volume, instrument_id
            ) daily_candles
            GROUP BY ts_event
            ORDER BY 1;       
            """

        con.sql(filter_volume_query, params={'path': path})

        instrument_query = """
            CREATE TEMP TABLE instrument_history AS
            SELECT ts_event,
                   instrument_id,
                   symbol,
                   
                   IF(MIN(instrument_id) OVER rolling_symbols ==
                      MAX(instrument_id) OVER rolling_symbols 
                      AND COUNT(instrument_id) OVER rolling_symbols == $min_overlap,
                       symbol,
                       'temp') AS current_symbol,
                       
            FROM filtered_daily_candles
            WINDOW rolling_symbols AS (ORDER BY ts_event
                   ROWS BETWEEN $min_overlap - 1 PRECEDING
                            AND 0 FOLLOWING)
            """

        con.sql(instrument_query, params={"min_overlap" : min_overlap})

        drop_nulls = ("""DELETE
                     FROM instrument_history 
                     WHERE current_symbol == 'temp'""")

        con.sql(drop_nulls)

        times_query = """
             SELECT *
             FROM (
                   SELECT ts_event,
                          LAG(instrument_id) OVER (ORDER BY ts_event) AS previous_instrument_id,
                          instrument_id AS new_instrument_id,
                          LAG(current_symbol) OVER (ORDER BY ts_event) AS previous_symbol,
                          current_symbol,
                   FROM instrument_history
                   ) sub
             WHERE sub.previous_instrument_id != sub.new_instrument_id
                  """

        df = con.sql(times_query).pl()

    return df