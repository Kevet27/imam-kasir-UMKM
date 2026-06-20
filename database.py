import sqlite3

DB_NAME = "kasir.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


conn = get_connection()
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users(
id INTEGER PRIMARY KEY AUTOINCREMENT,
username TEXT UNIQUE,
password TEXT,
role TEXT DEFAULT 'user'
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS products(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
nama_barang TEXT,
harga INTEGER,
stok INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS transactions(
id INTEGER PRIMARY KEY AUTOINCREMENT,
user_id INTEGER,
tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
total INTEGER
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS transaction_detail(
id INTEGER PRIMARY KEY AUTOINCREMENT,
transaction_id INTEGER,
product_id INTEGER,
qty INTEGER,
subtotal INTEGER
)
""")

conn.commit()

try:
    cur.execute(
        "INSERT INTO users(username,password,role) VALUES(?,?,?)",
        ("admin","admin123","admin")
    )
    conn.commit()
except:
    pass
