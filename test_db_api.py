import os
import sqlite3
import json

# Mimic the app's DB connection logic
def get_db_connection():
    db_path = 'backend/stocks.db'
    if not os.path.exists(db_path):
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def test_api():
    print("Testing Strategy API...")
    conn = get_db_connection()
    if not conn:
        print("ERROR: backend/stocks.db not found!")
        return
    
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM strategies')
        strategies = cur.fetchall()
        print(f"Success: Found {len(strategies)} strategies.")
        for s in strategies:
            print(dict(s))
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

    print("\nTesting Market Regime API...")
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        cur.execute('SELECT * FROM market_snapshots ORDER BY date DESC LIMIT 1')
        regime = cur.fetchone()
        if regime:
            print(f"Success: Found regime - {dict(regime)}")
        else:
            print("No regime snapshots found.")
    except Exception as e:
        print(f"ERROR: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_api()
