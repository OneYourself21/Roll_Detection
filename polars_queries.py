import polars as pl
from polars import max_horizontal


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


def rolling_stats(path : str, contract : str, year : int, days : int) -> pl.DataFrame:
    com = days - 1
    days = str(days) + "d"

    df = daily_candles(path, contract, year)

    df = df.with_columns(
        returns = pl.col("close") - pl.col("open"),
        range = max_horizontal(
                         pl.col("high") - pl.col("low"),
                         abs(pl.col("high") - pl.col("close").shift(1)),
                         abs(pl.col("low") - pl.col("close").shift(1))
                   ),
        trunc_date = pl.col("ts_event").dt.truncate("1d")
    )

    df = df.with_columns(
        rolling_volume=pl.col("volume").rolling_sum_by(by = "trunc_date", window_size = days),
        rolling_volatility = pl.col("returns").rolling_std_by(by = "trunc_date", window_size = days),
        ATR = pl.col("range").ewm_mean(com = com, adjust=False),
    )

    df = df.drop("returns", "open", "high", "low", "close", "range", "trunc_date")
    return df


def rollover_dates(path : str, min_overlap : int) -> pl.DataFrame:
    df = pl.scan_parquet(path

                         ).filter(pl.col("symbol").str.contains("-") != True

    ).group_by(((pl.col("ts_event").dt.offset_by("-18h")).dt.truncate("1d").alias("temp"),
                      pl.col("instrument_id").alias("temp2")),
                      ).agg(

        (pl.col("ts_event").first()).dt.offset_by("-18h").dt.truncate("1d"),
        pl.col("instrument_id").first(),
        pl.col("symbol").first(),
        pl.col("open").first(),
        pl.col("high").max(),
        pl.col("low").min(),
        pl.col("close").last(),
        pl.col("volume").sum()

    ).sort(pl.col("temp"), pl.col("temp2")).drop("temp" , "temp2"

           ).collect()

    return df