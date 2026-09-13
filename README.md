# Roll Detection 

Goal is to use window functions in parquet and duckdb to find when to switch contracts.
Comparison between the speed of the two is also planned.
The motive to switch to parquet was due to SQLite slow 3second speed to SELECT the entire database.

---

## Database

Used Parquet_Builder from https://github.com/OneYourself21/Databento_CSV_to_Parquet as the database.
It used Polars set in EST however duckdb pulls with local session timezone by default so set timezone to EST on duckdb to not be stuck on BST.

---

## Functions:

### select_db(path : str) -> pl.DataFrame:

Selects the entire database

#### Inputs:

- path (A string path to the database)

#### Outputs:

A polar dataframe with all OHLCV 1 min candles with the following schema:
- ts_event : datetime
- instrument_id : interger
- symbol : string
- open : float
- high : float
- low : float
- close : float
- volume : interger

### daily_candles(path : str, contract : str, year : int) -> pl.DataFrame:

Computes Daily OHLCV data for a specific contract.

#### Inputs:

- path (A string path to the database)
- contract (A string in a format like NQZ5 as databento stores NQZ15 and NQZ25 as NQZ5)
- year (An interger where the contract is active e.g. for NQZ5 2015 or 2025)

#### Outputs:

A polar dataframe with all OHLCV daily candles with the following schema:
- ts_event : datetime (Note: ts_event may not be consistent during low activity days)
- instrument_id : interger
- symbol : string
- open : float
- high : float
- low : float
- close : float
- volume : interger

### daily_returns(path : str, contract : str, year : int) -> pl.DataFrame:

Computes the close to close returns and open to close difference (intraday returns)

#### Inputs:

- path (A string path to the database)
- contract (A string in a format like NQZ5 as databento stores NQZ15 and NQZ25 as NQZ5)
- year (An interger where the contract is active e.g. for NQZ5 2015 or 2025)

#### Outputs:

A polar dataframe with the following schema:
- ts_event : datetime
- instrument_id : interger
- symbol : string
- close_to_close_returns : float
- intraday_returns : float 

### rolling_stats(path : str, contract : str, year : int, days : int) -> pl.DataFrame:

#### Inputs:

- path (A string path to the database)
- contract (A string in a format like NQZ5 as databento stores NQZ15 and NQZ25 as NQZ5)
- year (An interger where the contract is active e.g. for NQZ5 2015 or 2025)

#### Outputs:

A polar dataframe with the following schema:
- ts_event : datetime
- instrument_id : interger
- symbol : string
- volume : interger
- rolling_volume : interger
- rolling_volatility : float (note floating point precision between engines may cause differences between the two engines)
- ATR : float (note floating point precision between engines may cause differences between the two engines)

### def rollover_dates(path : str, min_overlap : int) -> pl.DataFrame:

#### Inputs:

- path (A string path to the database)
- min_overlap (denote number of days of volume leading another contract between switching)

#### Outputs:

A polars dataframe with the following schema:

- ts_event : datetime (note the aggregated daily candles were truncated)
- previous_instrument_id : interger
- new_instrument_id : interger
- previous_symbol : str
- current_symbol : str

The output gives each date the traded contract should switch and only has rows for each switch.
In my testing min_overlap of 1 day is sufficient and does not create any flip-flopping between contracts.
If you test it you will see that min_overlap set to 1 day leads to a greater length.
This is because NQM0 has only 5 trading days of data at the start of the dataset where it has the most volume so is omitted by checks via polars (and duckdb mimics this behavior for parity).

#### Logic Chain and Intentional Decisions

- Aggregates every daily candle and picks the one with the most volume for that day and contract (done by instrument_id to remove inconsistencies)
- Marks each day, where one contract has min_overlap days of consistently having the most volume and marks them.
- Drops every other day (Theoretically if a contract leads for less than min_overlap it is also deleted but is intentionally removed by thinking of it as an uncertain period)
- Find each contract change

---
## Contract Rollover Dates
#### When min overlap is set to 1.
| ts_event                         | previous_instrument_id   | new_instrument_id   | previous_symbol   | current_symbol   |
|----------------------------------|--------------------------|---------------------|-------------------|------------------|
| 2010-06-10 00:00:00 EDT          | 6641                     | 26715               | NQM0              | NQU0             |
| 2010-09-09 00:00:00 EDT          | 26715                    | 3088                | NQU0              | NQZ0             |
| 2010-12-09 00:00:00 EST          | 3088                     | 93735               | NQZ0              | NQH1             |
| 2011-03-10 00:00:00 EST          | 93735                    | 30668               | NQH1              | NQM1             |
| 2011-06-09 00:00:00 EDT          | 30668                    | 56972               | NQM1              | NQU1             |
| 2011-09-08 00:00:00 EDT          | 56972                    | 12038               | NQU1              | NQZ1             |
| 2011-12-08 00:00:00 EST          | 12038                    | 8870                | NQZ1              | NQH2             |
| 2012-03-08 00:00:00 EST          | 8870                     | 20924               | NQH2              | NQM2             |
| 2012-06-07 00:00:00 EDT          | 20924                    | 57494               | NQM2              | NQU2             |
| 2012-09-13 00:00:00 EDT          | 57494                    | 10016               | NQU2              | NQZ2             |
| 2012-12-13 00:00:00 EST          | 10016                    | 36931               | NQZ2              | NQH3             |
| 2013-03-07 00:00:00 EST          | 36931                    | 11518               | NQH3              | NQM3             |
| 2013-06-13 00:00:00 EDT          | 11518                    | 17591               | NQM3              | NQU3             |
| 2013-09-12 00:00:00 EDT          | 17591                    | 28499               | NQU3              | NQZ3             |
| 2013-12-12 00:00:00 EST          | 28499                    | 382251              | NQZ3              | NQH4             |
| 2014-03-13 00:00:00 EDT          | 382251                   | 8223                | NQH4              | NQM4             |
| 2014-06-15 00:00:00 EDT          | 8223                     | 83745               | NQM4              | NQU4             |
| 2014-09-11 00:00:00 EDT          | 83745                    | 28097               | NQU4              | NQZ4             |
| 2014-12-11 00:00:00 EST          | 28097                    | 50207               | NQZ4              | NQH5             |
| 2015-03-12 00:00:00 EDT          | 50207                    | 58385               | NQH5              | NQM5             |
| 2015-06-11 00:00:00 EDT          | 58385                    | 2913                | NQM5              | NQU5             |
| 2015-09-10 00:00:00 EDT          | 2913                     | 12809               | NQU5              | NQZ5             |
| 2015-12-10 00:00:00 EST          | 12809                    | 49734               | NQZ5              | NQH6             |
| 2016-03-10 00:00:00 EST          | 49734                    | 765                 | NQH6              | NQM6             |
| 2016-06-09 00:00:00 EDT          | 765                      | 2563                | NQM6              | NQU6             |
| 2016-09-08 00:00:00 EDT          | 2563                     | 2887                | NQU6              | NQZ6             |
| 2016-12-08 00:00:00 EST          | 2887                     | 35888               | NQZ6              | NQH7             |
| 2017-03-09 00:00:00 EST          | 35888                    | 6398                | NQH7              | NQM7             |
| 2017-06-08 00:00:00 EDT          | 6398                     | 26054               | NQM7              | NQU7             |
| 2017-09-07 00:00:00 EDT          | 26054                    | 15466               | NQU7              | NQZ7             |
| 2017-12-07 00:00:00 EST          | 15466                    | 16210               | NQZ7              | NQH8             |
| 2018-03-08 00:00:00 EST          | 16210                    | 23520               | NQH8              | NQM8             |
| 2018-06-07 00:00:00 EDT          | 23520                    | 47511               | NQM8              | NQU8             |
| 2018-09-13 00:00:00 EDT          | 47511                    | 16041               | NQU8              | NQZ8             |
| 2018-12-13 00:00:00 EST          | 16041                    | 15657               | NQZ8              | NQH9             |
| 2019-03-07 00:00:00 EST          | 15657                    | 9166                | NQH9              | NQM9             |
| 2019-06-13 00:00:00 EDT          | 9166                     | 36742               | NQM9              | NQU9             |
| 2019-09-12 00:00:00 EDT          | 36742                    | 15907               | NQU9              | NQZ9             |
| 2019-12-12 00:00:00 EST          | 15907                    | 10204               | NQZ9              | NQH0             |
| 2020-03-15 00:00:00 EDT          | 10204                    | 16908               | NQH0              | NQM0             |
| 2020-06-14 00:00:00 EDT          | 16908                    | 14028               | NQM0              | NQU0             |
| 2020-09-13 00:00:00 EDT          | 14028                    | 16337               | NQU0              | NQZ0             |
| 2020-12-13 00:00:00 EST          | 16337                    | 4378                | NQZ0              | NQH1             |
| 2021-03-13 00:00:00 EST          | 4378                     | 2786                | NQH1              | NQM1             |
| 2021-06-13 00:00:00 EDT          | 2786                     | 828                 | NQM1              | NQU1             |
| 2021-09-12 00:00:00 EDT          | 828                      | 2770                | NQU1              | NQZ1             |
| 2021-12-09 00:00:00 EST          | 2770                     | 3541                | NQZ1              | NQH2             |
| 2022-03-12 00:00:00 EST          | 3541                     | 2895                | NQH2              | NQM2             |
| 2022-06-12 00:00:00 EDT          | 2895                     | 10391               | NQM2              | NQU2             |
| 2022-09-11 00:00:00 EDT          | 10391                    | 13613               | NQU2              | NQZ2             |
| 2022-12-11 00:00:00 EST          | 13613                    | 20631               | NQZ2              | NQH3             |
| 2023-03-12 00:00:00 EST          | 20631                    | 3522                | NQH3              | NQM3             |
| 2023-06-11 00:00:00 EDT          | 3522                     | 2130                | NQM3              | NQU3             |
| 2023-09-10 00:00:00 EDT          | 2130                     | 260937              | NQU3              | NQZ3             |
| 2023-12-10 00:00:00 EST          | 260937                   | 750                 | NQZ3              | NQH4             |
| 2024-03-10 00:00:00 EST          | 750                      | 13743               | NQH4              | NQM4             |
| 2024-06-16 00:00:00 EDT          | 13743                    | 4358                | NQM4              | NQU4             |
| 2024-09-15 00:00:00 EDT          | 4358                     | 106364              | NQU4              | NQZ4             |
| 2024-12-16 00:00:00 EST          | 106364                   | 42288528            | NQZ4              | NQH5             |
| 2025-03-17 00:00:00 EDT          | 42288528                 | 42005804            | NQH5              | NQM5             |
| 2025-06-15 00:00:00 EDT          | 42005804                 | 42008487            | NQM5              | NQU5             |
| 2025-09-15 00:00:00 EDT          | 42008487                 | 158704              | NQU5              | NQZ5             |
| 2025-12-14 00:00:00 EST          | 158704                   | 42002475            | NQZ5              | NQH6             |
| 2026-03-15 00:00:00 EDT          | 42002475                 | 42004058            | NQH6              | NQM6             |
| 2026-06-14 00:00:00 EDT          | 42004058                 | 42004177            | NQM6              | NQU6             |