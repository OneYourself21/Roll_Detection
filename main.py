import duckdb_queries
import Polars_queries

DB_PATH = "YOUR_DB_PATH"

if __name__ == '__main__':
    print(duckdb_queries.select_db(DB_PATH))
    print(Polars_queries.select_db(DB_PATH))

