"""Database connection and helper utilities"""
import mysql.connector
from flask import g

DATABASE_CONFIG = {
    'host': '127.0.0.1',
    'user': 'root',
    'password': '',
    'database': 'secure_document_db'
}

def get_db_connection():
    """Get or create database connection"""
    if 'db' not in g:
        g.db = mysql.connector.connect(**DATABASE_CONFIG)
    return g.db

def close_db_connection(e=None):
    """Close database connection"""
    db = g.pop('db', None)
    if db is not None:
        db.close()
