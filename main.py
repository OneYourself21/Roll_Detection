import duckdb_queries
import polars_queries
import PATH

DB_PATH = PATH.return_path()

if __name__ == '__main__':
    print("Are the daily candles the same? ")
    print(polars_queries.daily_candles(DB_PATH, "NQZ5", 2025).equals(duckdb_queries.daily_candles(DB_PATH, "NQZ5", 2025)))

    print("---")
    print("Are the daily returns the same?")
    print(polars_queries.daily_returns(DB_PATH, "NQZ5", 2025).equals(duckdb_queries.daily_returns(DB_PATH, "NQZ5", 2025)))