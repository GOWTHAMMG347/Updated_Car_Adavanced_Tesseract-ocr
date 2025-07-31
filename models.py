from database import get_connection
from datetime import datetime
import json

def login_user(username, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, role FROM users WHERE username=? AND password=?", (username, password))
    user = cur.fetchone()
    conn.close()
    return user

def register_user(username, password):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO users(username, password, role) VALUES(?, ?, ?)", (username, password, 'user'))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def save_processed_file(username, type, input_path, output_path, plates):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO history VALUES(?,?,?,?,?,?)", (
        username, type, input_path, output_path, json.dumps(plates), datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))
    conn.commit()
    conn.close()

def get_user_history(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT type, input_path, output_path, time, plates FROM history WHERE username=?", (username,))
    rows = cur.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], json.loads(row[4])) for row in rows]

def get_all_users():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, role FROM users")
    rows = cur.fetchall()
    conn.close()
    return rows

def get_all_history():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT type, input_path, output_path, time, plates FROM history")
    rows = cur.fetchall()
    conn.close()
    return [(row[0], row[1], row[2], row[3], json.loads(row[4])) for row in rows]

def get_user(username):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT username, role FROM users WHERE username=?", (username,))
    user = cur.fetchone()
    conn.close()
    return user
