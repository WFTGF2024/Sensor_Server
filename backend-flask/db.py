import pymysql
from flask import g, current_app
from config import current_config

def get_db():
    """
    Cache the DB connection in Flask's `g` object to avoid reconnecting.
    """
    if 'db' not in g:
        db_config = current_config.get_db_config()
        db_config["cursorclass"] = pymysql.cursors.DictCursor
        g.db = pymysql.connect(**db_config)
    return g.db

def close_db(error=None):
    """
    Close the DB connection at the end of the request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()
