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

def init_db():
    try:
        db = mysql.connector.connect(**DATABASE_CONFIG)
        cursor = db.cursor()
        
        # Create the table if it doesn't exist
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS compliance_rules (
                id INT AUTO_INCREMENT PRIMARY KEY,
                rule_type VARCHAR(50) UNIQUE NOT NULL,
                content TEXT NOT NULL,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
            )
        """)
        
        # Insert default values if the table is empty
        cursor.execute("SELECT COUNT(*) FROM compliance_rules")
        if cursor.fetchone()[0] == 0:
            default_rules = [
                ("id_guidelines", "1. Must be a government-issued ID (Passport, Driver's License).\n2. The name on the ID must match the System Data name.\n3. The image must be clear and legible."),
                ("form_rules", "1. Must be the most recent version of the compliance document.\n2. User signatures must be present and dated.\n3. Any incomplete fields result in immediate rejection.")
            ]
            cursor.executemany("INSERT INTO compliance_rules (rule_type, content) VALUES (%s, %s)", default_rules)
            db.commit()
            print("INFO: 'compliance_rules' table created and seeded with default data.")

        cursor.close()
        db.close()
    except mysql.connector.Error as err:
        print(f"Error during database setup: {err}")

if __name__ == '__main__':
    init_db()
