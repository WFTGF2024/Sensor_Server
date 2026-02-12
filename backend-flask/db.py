import sqlite3
from flask import g, current_app
from config import current_config

def get_db():
    """
    Cache the DB connection in Flask's `g` object to avoid reconnecting.
    """
    if 'db' not in g:
        db_config = current_config.get_db_config()
        g.db = sqlite3.connect(db_config["database"])
        g.db.row_factory = sqlite3.Row
    return g.db

def close_db(error=None):
    """
    Close the DB connection at the end of the request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()
