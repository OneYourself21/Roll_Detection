import duckdb
import polars as pl


def select_db(path : str) -> pl.DataFrame:
    duckdb.sql('SET TIMEZONE = "EST";')
    df = duckdb.sql('SELECT * FROM "' + path + '";').pl()
    return df


def daily_candles(path : str, contract : str, year : int) -> pl.DataFrame:
    previous_year = year - 1

    duckdb.sql('SET TIMEZONE = "EST";')

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

    duckdb.sql('SET TIMEZONE = "EST";')

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
                     ) sub
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