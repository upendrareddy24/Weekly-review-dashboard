import sqlite3
import psycopg2
from psycopg2.extras import execute_values
import os
from dotenv import load_dotenv

load_dotenv()

SQLITE_PATH = "backend/stocks.db"
POSTGRES_URL = os.getenv("DATABASE_URL")

def migrate():
    if not POSTGRES_URL:
        print("Error: DATABASE_URL not found in environment.")
        return

    print(f"Connecting to SQLite: {SQLITE_PATH}")
    sl_conn = sqlite3.connect(SQLITE_PATH)
    sl_cur = sl_conn.cursor()

    print(f"Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(POSTGRES_URL, sslmode='require')
    pg_cur = pg_conn.cursor()

    # Define tables to migrate in order (dependencies first)
    tables = ["strategies", "tickers", "setups", "catalysts"]

    for table in tables:
        print(f"Migrating table: {table}")
        
        # Get column names from SQLite
        sl_cur.execute(f"PRAGMA table_info({table})")
        columns = [row[1] for row in sl_cur.fetchall()]
        col_list = ", ".join(columns)
        placeholders = ", ".join(["%s"] * len(columns))

        # Fetch data from SQLite
        sl_cur.execute(f"SELECT * FROM {table}")
        rows = sl_cur.fetchall()

        if not rows:
            print(f"  - No data in {table}, skipping.")
            continue

        # Insert into Postgres
        # First, ensure table exists (we trust existing schema.sql or we create it here)
        # For simplicity, we assume the user has run a 'create' script or the app initialized it.
        # But Postgres doesn't auto-create tables via Flask in this setup as easily as SQLite.
        
        # Better: Truncate and Reload
        pg_cur.execute(f"TRUNCATE TABLE {table} RESTART IDENTITY CASCADE")
        
        insert_query = f"INSERT INTO {table} ({col_list}) VALUES %s"
        execute_values(pg_cur, insert_query, rows)
        print(f"  - Migrated {len(rows)} rows.")

    pg_conn.commit()
    sl_conn.close()
    pg_conn.close()
    print("Migration complete!")

if __name__ == "__main__":
    migrate()
