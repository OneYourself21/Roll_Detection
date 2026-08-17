import duckdb
import polars as pl


def select_db(path : str) -> pl.dataframe.frame.DataFrame:
    duckdb.sql('SET TIMEZONE = "EST";')
    df = duckdb.sql('SELECT * FROM "' + path + '";').pl()
    return df


def daily_candles(path : str, contract : str, year : int) -> pl.dataframe.frame.DataFrame:
    previous_year = str(year - 1)
    current_year = str(year)
    duckdb.sql('SET TIMEZONE = "EST";')
    select_q = """SELECT
                FIRST(ts_event ORDER BY ts_event) AS ts_event,
                ANY_VALUE(instrument_id) AS instrument_id,
                ANY_VALUE(symbol) AS symbol,
                FIRST(open ORDER BY ts_event) AS open,
                MAX(high) AS high,
                MIN(low) AS low,
                LAST(close ORDER BY ts_event) AS close,
                SUM(volume) AS volume 
                """

    from_q = " FROM '" + path + "' "
    where_q = " WHERE symbol = '" + contract + "' AND (strftime(ts_event, '%Y') = '" + previous_year + "' OR strftime(ts_event, '%Y') = '" + current_year + "')"
    group_q = " GROUP BY strftime(ts_event - INTERVAL 18 HOUR, '%Y/%m/%d') ORDER BY 1;"

    df = duckdb.sql(select_q + from_q + where_q + group_q).pl()
    return df