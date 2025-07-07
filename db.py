import pymysql
from flask import g, current_app

DB_CONFIG = {
    "host": "localhost",
    "user": "zjh",
    "password": "20040624ZJH",
    "database": "modality",
    "charset": "utf8mb4",
    "use_unicode": True,
    "cursorclass": pymysql.cursors.DictCursor
}

def get_db():
    """
    Cache the DB connection in Flask's `g` object to avoid reconnecting.
    """
    if 'db' not in g:
        g.db = pymysql.connect(**DB_CONFIG)
    return g.db

def close_db(error=None):
    """
    Close the DB connection at the end of the request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()
