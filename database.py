import sqlite3

DB_NAME = "car_app.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # Users table
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        password TEXT,
        role TEXT DEFAULT 'user'
    )""")

    # History table
    cur.execute("""CREATE TABLE IF NOT EXISTS history(
        username TEXT,
        type TEXT,
        input_path TEXT,
        output_path TEXT,
        plates TEXT,
        time TEXT
    )""")

    conn.commit()
    conn.close()
