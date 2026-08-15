import polars as pl

def select_db(path : str):
    df = pl.read_parquet(path)
    return df