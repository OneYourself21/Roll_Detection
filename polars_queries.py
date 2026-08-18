import polars as pl

def select_db(path : str) -> pl.DataFrame:
    df = pl.read_parquet(path)
    return df

def daily_candles(path : str, contract : str, year : int) -> pl.DataFrame:
    previous_year = year -1

    df = pl.scan_parquet(path

    ).filter(

        pl.col("symbol") == contract,
        pl.col("ts_event").dt.year().is_in([previous_year, year]),

    ).group_by((pl.col("ts_event").dt.offset_by("-18h")).dt.strftime('%Y/%m/%d').alias("temp"), maintain_order= True).agg(

        pl.col("ts_event").first(),
        pl.col("instrument_id").first(),
        pl.col("symbol").first(),
        pl.col("open").first(),
        pl.col("high").max(),
        pl.col("low").min(),
        pl.col("close").last(),
        pl.col("volume").sum()

    ).drop("temp"

    ).collect()

    return df


def daily_returns(path : str, contract : str, year : int) -> pl.DataFrame:
    df = daily_candles(path, contract, year)

    returns = df.select(
        pl.col("ts_event"),
        pl.col("instrument_id"),
        pl.col("symbol"),
        pl.col("close").diff(1).alias("close_to_close_returns"),
        (pl.col("close") - pl.col("open")).alias("intraday_returns"),
    )

    return returns
