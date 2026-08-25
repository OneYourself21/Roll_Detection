import duckdb_queries
import polars_queries
import polars as pl
import PATH

DB_PATH = PATH.return_path()

if __name__ == '__main__':
    print("Are the daily candles the same? ")
    print(polars_queries.daily_candles(DB_PATH, "NQZ5", 2025).equals(
        duckdb_queries.daily_candles(DB_PATH, "NQZ5", 2025))
    )

    print("---")
    print("Are the daily returns the same?")
    print(polars_queries.daily_returns(DB_PATH, "NQZ5", 2025).equals(
        duckdb_queries.daily_returns(DB_PATH, "NQZ5", 2025))
    )

    print("---")
    print("Are the rolling stats the same?")
    print(polars_queries.rolling_stats(DB_PATH, "NQZ5", 2025, days=7).equals(
        duckdb_queries.rolling_stats(DB_PATH, "NQZ5", 2025, days=7))
    )

    print("---")
    print("Are the rounded rolling stats the same?")

    df1 = polars_queries.rolling_stats(DB_PATH, "NQZ5", 2025, days=7)
    df2 = duckdb_queries.rolling_stats(DB_PATH, "NQZ5", 2025, days=7)

    df1 = df1.select(
        pl.col("ts_event"),
        pl.col("instrument_id"),
        pl.col("symbol"),
        pl.col("volume"),
        pl.col("rolling_volume"),
        pl.col("rolling_volatility").round(2),
        pl.col("ATR").round(2),
    )

    df2 = df2.select(
        pl.col("ts_event"),
        pl.col("instrument_id"),
        pl.col("symbol"),
        pl.col("volume"),
        pl.col("rolling_volume"),
        pl.col("rolling_volatility").round(2),
        pl.col("ATR").round(2),
    )

    print(df1.equals(df2))
