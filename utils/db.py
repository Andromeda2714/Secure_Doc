"""Database connection and helper utilities"""
import mysql.connector
from mysql.connector import pooling
from flask import g

DATABASE_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'secure_document_db'
}

# Connection pool - reuses connections instead of creating new ones each request
_pool = pooling.MySQLConnectionPool(
    pool_name='securedoc_pool',
    pool_size=5,
    pool_reset_session=True,
    **DATABASE_CONFIG
)

def get_db_connection():
    """Get a pooled connection for the current request"""
    if 'db' not in g:
        g.db = _pool.get_connection()
    return g.db

def close_db_connection(e=None):
    """Return connection back to pool at end of request"""
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()  # returns to pool, not actually closed
        except Exception:
            pass
