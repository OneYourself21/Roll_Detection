# Roll Detection 

Goal is to use window functions in parquet and duckdb to find when to switch contracts.
Comparison between the speed of the two is also planned.
The motive was due to SQLite slow 3second speed to SELECT the entire database.

---

## Database

Used Parquet_Builder from https://github.com/OneYourself21/Databento_CSV_to_Parquet as the database.
It used Polars set in EST however duckdb pulls with local session timezone by default so set timezone to EST on polars.

---

## Functions:

### select_db(path : str) -> pl.dataframe.frame.DataFrame:

Selects the entire database

#### Inputs:

- path (A string path to the database)

#### Outputs:

- All candles (Every single OHLCV candle in the database as a polars dataframe)

### daily_candles(path : str, contract : str, year : int) -> pl.dataframe.frame.DataFrame:

Computes Daily OHLCV data for a specific contract.

#### Inputs:

- path (A string path to the database)
- contract (A string in a format like NQZ5 as databento stores NQZ15 and NQZ25 as NQZ5)
- year (An interger where the contract is active e.g. for NQZ5 2015 or 2025)

#### Outputs:

- Daily OHLCV candles (As a polar's dataframe)