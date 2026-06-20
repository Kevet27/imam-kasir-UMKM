import sqlite3

DB_NAME = "kasir.db"

def get_connection():
    conn = sqlite3.connect(
        DB_NAME,
        timeout=30,
        check_same_thread=False
    )
    conn.row_factory
