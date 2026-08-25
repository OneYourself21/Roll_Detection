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