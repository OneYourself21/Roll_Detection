import duckdb
import pytz



def select_db(path : str):
    df = duckdb.sql('SELECT * FROM "' + path + '";').pl()
    return df