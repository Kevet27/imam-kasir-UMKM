import sqlite3

DB_NAME = "kasir.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


conn = get_connection()
cur = conn.cursor()

# tabel user
cur.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE,
    password TEXT,
    role TEXT DEFAULT 'user'
)
""")

# tabel barang
cur.execute("""
CREATE TABLE IF NOT EXISTS products(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    nama_barang TEXT,
    harga INTEGER,
    stok INTEGER
)
""")

# tabel transaksi
cur.execute("""
CREATE TABLE IF NOT EXISTS transactions(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    tanggal TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total INTEGER
)
""")

# detail transaksi
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

# admin default
try:
    cur.execute(
        "INSERT INTO users(username,password,role) VALUES(?,?,?)",
        ("admin","admin123","admin")
    )
    conn.commit()
except:
    pass

import streamlit as st
from database import get_connection

st.set_page_config(
    page_title="Kasir UMKM",
    layout="wide"
)

if "login" not in st.session_state:
    st.session_state.login = False

if "user_id" not in st.session_state:
    st.session_state.user_id = None

if "role" not in st.session_state:
    st.session_state.role = ""


def login():
    st.title("LOGIN KASIR UMKM")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        cur.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )

        user = cur.fetchone()

        if user:
            st.session_state.login = True
            st.session_state.user_id = user["id"]
            st.session_state.role = user["role"]
            st.success("Login berhasil")
            st.rerun()
        else:
            st.error("Username atau password salah")


def register():
    st.subheader("Daftar Akun")

    user = st.text_input("Username Baru")
    pw = st.text_input("Password Baru", type="password")

    if st.button("Daftar"):

        if user.strip() == "" or pw.strip() == "":
            st.error("Username dan password tidak boleh kosong")

        else:
            try:
                cur.execute(
                    "SELECT * FROM users WHERE username=?",
                    (user,)
                )

                cek_user = cur.fetchone()

                if cek_user:
                    st.error("Username sudah digunakan")

                else:
                    cur.execute(
                        """
                        INSERT INTO users(username,password)
                        VALUES(?,?)
                        """,
                        (user, pw)
                    )

                    conn.commit()

                    st.success("Akun berhasil dibuat, silakan login")

            except Exception as e:
                st.error(f"Terjadi kesalahan: {e}")


if st.session_state.login == False:
    tab1, tab2 = st.tabs(["Login","Register"])

    with tab1:
        login()

    with tab2:
        register()

else:
    st.title("Kasir UMKM")
    st.success("Login berhasil")

    st.write("Silakan gunakan menu di sidebar")

    if st.button("Logout"):
        st.session_state.login = False
        st.session_state.user_id = None
        st.session_state.role = ""
        st.rerun()

import streamlit as st
import pandas as pd
from database import get_connection

# ==========================
# CEK LOGIN
# ==========================
if "login" not in st.session_state or st.session_state.login == False:
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

user_id = st.session_state.user_id

st.title("📊 Dashboard")

# ==========================
# TOTAL TRANSAKSI HARI INI
# ==========================
cur.execute("""
SELECT COUNT(*) as jumlah
FROM transactions
WHERE user_id = ?
AND DATE(tanggal)=DATE('now','localtime')
""", (user_id,))

jumlah_transaksi = cur.fetchone()["jumlah"]

# ==========================
# TOTAL OMZET HARI INI
# ==========================
cur.execute("""
SELECT COALESCE(SUM(total),0) as omzet
FROM transactions
WHERE user_id = ?
AND DATE(tanggal)=DATE('now','localtime')
""", (user_id,))

omzet_hari_ini = cur.fetchone()["omzet"]

# ==========================
# TOTAL SELURUH TRANSAKSI
# ==========================
cur.execute("""
SELECT COUNT(*) as total
FROM transactions
WHERE user_id = ?
""", (user_id,))

total_transaksi = cur.fetchone()["total"]

# ==========================
# TOTAL SELURUH OMZET
# ==========================
cur.execute("""
SELECT COALESCE(SUM(total),0) as total_omzet
FROM transactions
WHERE user_id = ?
""", (user_id,))

total_omzet = cur.fetchone()["total_omzet"]

# ==========================
# CARD
# ==========================
col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Jumlah Transaksi Hari Ini",
        jumlah_transaksi
    )

    st.metric(
        "Total Seluruh Transaksi",
        total_transaksi
    )

with col2:
    st.metric(
        "Omzet Hari Ini",
        f"Rp {omzet_hari_ini:,.0f}"
    )

    st.metric(
        "Total Omzet",
        f"Rp {total_omzet:,.0f}"
    )

st.divider()

# ==========================
# PENJUALAN 7 HARI TERAKHIR
# ==========================
st.subheader("Grafik Penjualan 7 Hari Terakhir")

query = """
SELECT
DATE(tanggal) as tanggal,
SUM(total) as omzet
FROM transactions
WHERE user_id=?
AND DATE(tanggal)>=DATE('now','-6 day')
GROUP BY DATE(tanggal)
ORDER BY tanggal
"""

df = pd.read_sql_query(query, conn, params=(user_id,))

if len(df) > 0:
    st.line_chart(
        df.set_index("tanggal")
    )
else:
    st.info("Belum ada transaksi.")

# ==========================
# TRANSAKSI TERBARU
# ==========================
st.divider()

st.subheader("Riwayat Transaksi Terbaru")

query2 = """
SELECT *
FROM transactions
WHERE user_id=?
ORDER BY tanggal DESC
LIMIT 10
"""

df2 = pd.read_sql_query(query2, conn, params=(user_id,))

if len(df2) > 0:
    df2.index = range(1, len(df2)+1)
    st.dataframe(df2, use_container_width=True)
else:
    st.info("Belum ada transaksi.")

import streamlit as st
import pandas as pd
from database import get_connection

# =====================
# CEK LOGIN
# =====================
if "login" not in st.session_state or st.session_state.login == False:
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

user_id = st.session_state.user_id

st.title("📦 Barang Jual")

# =====================
# TAMBAH BARANG
# =====================
with st.expander("➕ Tambah Barang", expanded=True):

    nama_barang = st.text_input("Nama Barang")
    harga = st.number_input(
        "Harga",
        min_value=0,
        step=1000
    )

    stok = st.number_input(
        "Stok",
        min_value=0,
        step=1
    )

    if st.button("Simpan Barang"):

        if nama_barang == "":
            st.error("Nama barang tidak boleh kosong")

        else:
            cur.execute(
                """
                INSERT INTO products
                (user_id,nama_barang,harga,stok)
                VALUES(?,?,?,?)
                """,
                (
                    user_id,
                    nama_barang,
                    int(harga),
                    int(stok)
                )
            )

            conn.commit()
            st.success("Barang berhasil ditambahkan")
            st.rerun()

st.divider()

# =====================
# PENCARIAN
# =====================
cari = st.text_input("🔍 Cari Barang")

query = """
SELECT *
FROM products
WHERE user_id=?
AND nama_barang LIKE ?
ORDER BY nama_barang
"""

df = pd.read_sql_query(
    query,
    conn,
    params=(user_id, f"%{cari}%")
)

if len(df) == 0:
    st.info("Belum ada barang.")
    st.stop()

# =====================
# DAFTAR BARANG
# =====================
st.subheader("Daftar Barang")

for index, row in df.iterrows():

    with st.expander(
        f"{row['nama_barang']} | Harga Rp {row['harga']:,.0f} | Stok {row['stok']}"
    ):

        nama_baru = st.text_input(
            "Nama Barang",
            value=row["nama_barang"],
            key=f"nama{row['id']}"
        )

        harga_baru = st.number_input(
            "Harga",
            value=int(row["harga"]),
            min_value=0,
            key=f"harga{row['id']}"
        )

        stok_baru = st.number_input(
            "Stok",
            value=int(row["stok"]),
            min_value=0,
            key=f"stok{row['id']}"
        )

        col1, col2 = st.columns(2)

        # =====================
        # UPDATE
        # =====================
        with col1:
            if st.button(
                "💾 Update",
                key=f"update{row['id']}"
            ):

                cur.execute(
                    """
                    UPDATE products
                    SET nama_barang=?,
                        harga=?,
                        stok=?
                    WHERE id=?
                    """,
                    (
                        nama_baru,
                        int(harga_baru),
                        int(stok_baru),
                        row["id"]
                    )
                )

                conn.commit()
                st.success("Barang berhasil diperbarui")
                st.rerun()

        # =====================
        # HAPUS
        # =====================
        with col2:
            if st.button(
                "🗑 Hapus",
                key=f"hapus{row['id']}"
            ):

                cur.execute(
                    """
                    DELETE FROM products
                    WHERE id=?
                    """,
                    (row["id"],)
                )

                conn.commit()
                st.success("Barang berhasil dihapus")
                st.rerun()

# =====================
# RINGKASAN
# =====================
st.divider()

cur.execute(
    """
    SELECT COUNT(*) jumlah_barang
    FROM products
    WHERE user_id=?
    """,
    (user_id,)
)

jumlah_barang = cur.fetchone()["jumlah_barang"]

cur.execute(
    """
    SELECT COALESCE(SUM(stok),0) total_stok
    FROM products
    WHERE user_id=?
    """,
    (user_id,)
)

total_stok = cur.fetchone()["total_stok"]

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Jumlah Jenis Barang",
        jumlah_barang
    )

with col2:
    st.metric(
        "Total Stok",
        total_stok
    )

import streamlit as st
import pandas as pd
from database import get_connection

# ======================
# CEK LOGIN
# ======================
if "login" not in st.session_state or st.session_state.login == False:
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

conn = get_connection()
cur = conn.cursor()

user_id = st.session_state.user_id

st.title("🛒 Kasir")

# ======================
# SESSION KERANJANG
# ======================
if "keranjang" not in st.session_state:
    st.session_state.keranjang = []

# ======================
# AMBIL DATA BARANG
# ======================
query = """
SELECT *
FROM products
WHERE user_id=?
AND stok > 0
ORDER BY nama_barang
"""

df_barang = pd.read_sql_query(query, conn, params=(user_id,))

if len(df_barang) == 0:
    st.info("Belum ada barang tersedia.")
    st.stop()

# ======================
# PILIH BARANG
# ======================
st.subheader("Tambah ke Keranjang")

barang = st.selectbox(
    "Pilih Barang",
    df_barang["nama_barang"]
)

row = df_barang[df_barang["nama_barang"] == barang].iloc[0]

st.write("Harga :", f"Rp {row['harga']:,.0f}")
st.write("Stok :", row["stok"])

qty = st.number_input(
    "Jumlah",
    min_value=1,
    max_value=int(row["stok"]),
    value=1
)

if st.button("➕ Tambah"):
    subtotal = int(row["harga"]) * qty

    st.session_state.keranjang.append({
        "id_barang": row["id"],
        "nama_barang": row["nama_barang"],
        "harga": int(row["harga"]),
        "qty": qty,
        "subtotal": subtotal
    })

    st.success("Barang masuk ke keranjang")
    st.rerun()

# ======================
# KERANJANG
# ======================
st.divider()
st.subheader("Keranjang")

if len(st.session_state.keranjang) == 0:
    st.info("Keranjang masih kosong.")

else:

    df_keranjang = pd.DataFrame(
        st.session_state.keranjang
    )

    st.dataframe(
        df_keranjang,
        use_container_width=True
    )

    total = df_keranjang["subtotal"].sum()

    st.subheader(
        f"Total : Rp {total:,.0f}"
    )

    col1, col2 = st.columns(2)

    # ======================
    # SIMPAN TRANSAKSI
    # ======================
    with col1:
        if st.button("💾 Simpan Transaksi"):

            cur.execute(
                """
                INSERT INTO transactions(user_id,total)
                VALUES(?,?)
                """,
                (user_id, int(total))
            )

            conn.commit()

            transaction_id = cur.lastrowid

            # detail transaksi
            for item in st.session_state.keranjang:

                cur.execute(
                    """
                    INSERT INTO transaction_detail
                    (transaction_id,product_id,qty,subtotal)
                    VALUES(?,?,?,?)
                    """,
                    (
                        transaction_id,
                        item["id_barang"],
                        item["qty"],
                        item["subtotal"]
                    )
                )

                # kurangi stok
                cur.execute(
                    """
                    UPDATE products
                    SET stok = stok - ?
                    WHERE id=?
                    """,
                    (
                        item["qty"],
                        item["id_barang"]
                    )
                )

            conn.commit()

            st.session_state.keranjang = []

            st.success("Transaksi berhasil disimpan")
            st.rerun()

    # ======================
    # HAPUS KERANJANG
    # ======================
    with col2:
        if st.button("🗑 Kosongkan Keranjang"):
            st.session_state.keranjang = []
            st.rerun()

# ======================
# TRANSAKSI TERAKHIR
# ======================
st.divider()

st.subheader("10 Transaksi Terakhir")

query = """
SELECT *
FROM transactions
WHERE user_id=?
ORDER BY tanggal DESC
LIMIT 10
"""

df_transaksi = pd.read_sql_query(
    query,
    conn,
    params=(user_id,)
)

if len(df_transaksi) > 0:
    df_transaksi.index = range(1, len(df_transaksi)+1)
    st.dataframe(
        df_transaksi,
        use_container_width=True
    )
else:
    st.info("Belum ada transaksi.")
import streamlit as st
import pandas as pd
from database import get_connection
from io import BytesIO

# ==========================
# CEK LOGIN
# ==========================
if "login" not in st.session_state or st.session_state.login == False:
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

conn = get_connection()
user_id = st.session_state.user_id

st.title("📊 Laporan Penjualan")

# ==========================
# PILIH PERIODE
# ==========================
periode = st.selectbox(
    "Pilih Periode",
    [
        "Hari Ini",
        "7 Hari",
        "1 Bulan",
        "1 Tahun"
    ]
)

# ==========================
# QUERY BERDASARKAN PERIODE
# ==========================
if periode == "Hari Ini":

    query = """
    SELECT *
    FROM transactions
    WHERE user_id=?
    AND DATE(tanggal)=DATE('now','localtime')
    ORDER BY tanggal DESC
    """

elif periode == "7 Hari":

    query = """
    SELECT *
    FROM transactions
    WHERE user_id=?
    AND DATE(tanggal)>=DATE('now','-6 day')
    ORDER BY tanggal DESC
    """

elif periode == "1 Bulan":

    query = """
    SELECT *
    FROM transactions
    WHERE user_id=?
    AND DATE(tanggal)>=DATE('now','-1 month')
    ORDER BY tanggal DESC
    """

else:

    query = """
    SELECT *
    FROM transactions
    WHERE user_id=?
    AND DATE(tanggal)>=DATE('now','-1 year')
    ORDER BY tanggal DESC
    """

df = pd.read_sql_query(query, conn, params=(user_id,))

# ==========================
# RINGKASAN
# ==========================
jumlah_transaksi = len(df)

if len(df) > 0:
    total_omzet = int(df["total"].sum())
else:
    total_omzet = 0

col1, col2 = st.columns(2)

with col1:
    st.metric(
        "Jumlah Transaksi",
        jumlah_transaksi
    )

with col2:
    st.metric(
        "Total Omzet",
        f"Rp {total_omzet:,.0f}"
    )

st.divider()

# ==========================
# TABEL LAPORAN
# ==========================
st.subheader("Daftar Transaksi")

if len(df) > 0:

    df_show = df.copy()
    df_show.index = range(1, len(df_show)+1)

    st.dataframe(
        df_show,
        use_container_width=True
    )

else:
    st.info("Belum ada transaksi.")

# ==========================
# GRAFIK PENJUALAN
# ==========================
st.divider()
st.subheader("Grafik Penjualan")

if len(df) > 0:

    grafik = (
        df.groupby(df["tanggal"].str[:10])["total"]
        .sum()
        .reset_index()
    )

    grafik.columns = ["Tanggal", "Omzet"]

    st.line_chart(
        grafik.set_index("Tanggal")
    )

# ==========================
# EXPORT EXCEL
# ==========================
st.divider()

st.subheader("Export Laporan Excel")

if len(df) > 0:

    output = BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(
            writer,
            index=False,
            sheet_name="Laporan"
        )

    excel_data = output.getvalue()

    st.download_button(
        label="📥 Download Excel",
        data=excel_data,
        file_name="laporan_penjualan.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
import streamlit as st
import pandas as pd
from database import get_connection

# ==========================
# CEK LOGIN
# ==========================
if "login" not in st.session_state or st.session_state.login == False:
    st.warning("Silakan login terlebih dahulu.")
    st.stop()

# ==========================
# CEK ROLE ADMIN
# ==========================
if st.session_state.role != "admin":
    st.error("Halaman ini hanya dapat diakses admin.")
    st.stop()

conn = get_connection()
cur = conn.cursor()

st.title("🔐 Panel Admin")

# ==========================
# STATISTIK SISTEM
# ==========================
st.subheader("📈 Statistik Sistem")

# Jumlah user
cur.execute("""
SELECT COUNT(*) jumlah_user
FROM users
WHERE role='user'
""")
jumlah_user = cur.fetchone()["jumlah_user"]

# Total transaksi
cur.execute("""
SELECT COUNT(*) total_transaksi
FROM transactions
""")
total_transaksi = cur.fetchone()["total_transaksi"]

# Total omzet
cur.execute("""
SELECT COALESCE(SUM(total),0) total_omzet
FROM transactions
""")
total_omzet = cur.fetchone()["total_omzet"]

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Jumlah UMKM",
        jumlah_user
    )

with col2:
    st.metric(
        "Total Transaksi",
        total_transaksi
    )

with col3:
    st.metric(
        "Total Omzet",
        f"Rp {total_omzet:,.0f}"
    )

st.divider()

# ==========================
# DAFTAR USER
# ==========================
st.subheader("👥 Daftar Pengguna")

query_user = """
SELECT
u.id,
u.username,
u.role,
COUNT(t.id) jumlah_transaksi,
COALESCE(SUM(t.total),0) total_penjualan
FROM users u
LEFT JOIN transactions t
ON u.id=t.user_id
GROUP BY u.id
ORDER BY u.username
"""

df_user = pd.read_sql_query(query_user, conn)

if len(df_user) > 0:

    for index, row in df_user.iterrows():

        with st.expander(
            f"{row['username']} ({row['role']})"
        ):

            st.write(
                "Jumlah Transaksi:",
                row["jumlah_transaksi"]
            )

            st.write(
                "Total Penjualan:",
                f"Rp {row['total_penjualan']:,.0f}"
            )

            # admin utama tidak dapat dihapus
            if row["username"] != "admin":

                if st.button(
                    f"🗑 Hapus User {row['username']}",
                    key=row["id"]
                ):

                    # hapus detail transaksi
                    cur.execute("""
                    DELETE FROM transaction_detail
                    WHERE transaction_id IN (
                        SELECT id
                        FROM transactions
                        WHERE user_id=?
                    )
                    """, (row["id"],))

                    # hapus transaksi
                    cur.execute("""
                    DELETE FROM transactions
                    WHERE user_id=?
                    """, (row["id"],))

                    # hapus produk
                    cur.execute("""
                    DELETE FROM products
                    WHERE user_id=?
                    """, (row["id"],))

                    # hapus user
                    cur.execute("""
                    DELETE FROM users
                    WHERE id=?
                    """, (row["id"],))

                    conn.commit()

                    st.success("User berhasil dihapus")
                    st.rerun()

else:
    st.info("Belum ada pengguna.")

st.divider()

# ==========================
# RIWAYAT TRANSAKSI SEMUA USER
# ==========================
st.subheader("🧾 Riwayat Transaksi Seluruh Pengguna")

query_transaksi = """
SELECT
t.id,
u.username,
t.tanggal,
t.total
FROM transactions t
JOIN users u
ON t.user_id=u.id
ORDER BY t.tanggal DESC
LIMIT 100
"""

df_transaksi = pd.read_sql_query(
    query_transaksi,
    conn
)

if len(df_transaksi) > 0:

    df_transaksi.index = range(
        1,
        len(df_transaksi)+1
    )

    st.dataframe(
        df_transaksi,
        use_container_width=True
    )

else:
    st.info("Belum ada transaksi.")
