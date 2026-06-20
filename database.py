import sqlite3

DB_NAME = "kasir.db"

def get_connection():
    conn = sqlite3.connect(
        DB_NAME,
        check_same_thread=False,
        timeout=30
    )
    conn.row_factory = sqlite3.Row
    return conn
