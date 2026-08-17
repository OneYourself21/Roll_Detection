import duckdb_queries
import polars_queries
import PATH

DB_PATH = PATH.return_path()

if __name__ == '__main__':
    print("Producing daily candles with both duckdb and polars and comparing them...")
    print("Result: ")
    print(polars_queries.daily_candles(DB_PATH, "NQZ5", 2025).equals(duckdb_queries.daily_candles(DB_PATH, "NQZ5", 2025)))