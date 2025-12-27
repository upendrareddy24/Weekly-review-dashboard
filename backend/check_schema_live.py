import sqlite3
import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    if DATABASE_URL:
        conn = psycopg2.connect(DATABASE_URL)
    else:
        conn = sqlite3.connect('stocks.db')
        conn.row_factory = sqlite3.Row
    return conn

try:
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Check setups table
    if DATABASE_URL:
        cur.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'setups'")
        columns = cur.fetchall()
        print("SETUPS COLUMNS (Postgres):")
        for col in columns:
            print(f"- {col[0]} ({col[1]})")
            
        cur.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'macro_reviews'")
        columns = cur.fetchall()
        print("\nMACRO_REVIEWS COLUMNS (Postgres):")
        for col in columns:
            print(f"- {col[0]}")
            
    else:
        cur.execute("PRAGMA table_info(setups)")
        columns = cur.fetchall()
        print("SETUPS COLUMNS (SQLite):")
        for col in columns:
            print(f"- {col['name']} ({col['type']})")

        cur.execute("PRAGMA table_info(macro_reviews)")
        columns = cur.fetchall()
        print("\nMACRO_REVIEWS COLUMNS (SQLite):")
        for col in columns:
            print(f"- {col['name']}")
            
    conn.close()

except Exception as e:
    print(f"Error: {e}")
