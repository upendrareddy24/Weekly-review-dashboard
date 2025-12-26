import sqlite3
import pandas as pd
import json
import os
from datetime import datetime

DB_PATH = "d:/AntiGravity/stock_tracker/backend/stocks.db"
EXCEL_PATH = r"C:\Users\nbhav\Downloads\Weekly Market review _HK.xlsx"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    with open("d:/AntiGravity/stock_tracker/backend/schema.sql") as f:
        conn.executescript(f.read())
    conn.commit()
    conn.close()
    print("Database initialized.")

def get_or_create_ticker(conn, symbol, sector="", horizon=""):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM tickers WHERE symbol = ?", (symbol,))
    row = cursor.fetchone()
    if row:
        return row[0]
    
    cursor.execute("INSERT INTO tickers (symbol, sector, horizon) VALUES (?, ?, ?)", 
                   (symbol, sector, horizon))
    conn.commit()
    return cursor.lastrowid

def get_or_create_strategy(conn, name):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM strategies WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row[0]
    
    cursor.execute("INSERT INTO strategies (name) VALUES (?)", (name,))
    conn.commit()
    return cursor.lastrowid

def import_sheet(conn, sheet_name, strategy_name):
    print(f"Importing {sheet_name} as {strategy_name}...")
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
        # Identify common columns
        # Each sheet has different columns, so we map them
        
        strategy_id = get_or_create_strategy(conn, strategy_name)
        
        for _, row in df.iterrows():
            # Basic ticker extraction - looking for 'Ticker' or 'Stock'
            symbol = str(row.get('Ticker', row.get('Stock', ''))).strip()
            if not symbol or symbol == 'nan' or len(symbol) > 10:
                continue
            
            ticker_id = get_or_create_ticker(conn, symbol)
            
            # Extract common fields
            date_val = row.get('Date', datetime.now().strftime('%Y-%m-%d'))
            if pd.isna(date_val): date_val = datetime.now().strftime('%Y-%m-%d')
            
            status = str(row.get('decision', row.get('Signal', 'Wait'))).strip()
            rating = str(row.get('Rating', row.get('Setup Rating', '')))
            score = row.get('Score (5)', row.get('Total score for 5', None))
            entry = str(row.get('Entry', ''))
            target = str(row.get('Target', ''))
            sl = str(row.get('SL', ''))
            rr = str(row.get('RR', ''))
            comments = str(row.get('Comments', row.get('Notes', row.get('Commetns/ Key Takeaways', ''))))
            
            # Store all other info in meta
            meta = {k: str(v) for k, v in row.items() if k not in ['Ticker', 'Stock', 'Date']}
            
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO setups 
                (ticker_id, strategy_id, date, status, rating, score, entry, target, sl, rr, comments, meta_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticker_id, strategy_id, str(date_val), status, rating, score, entry, target, sl, rr, comments, json.dumps(meta)))
        
        conn.commit()
    except Exception as e:
        print(f"Error importing {sheet_name}: {e}")

if __name__ == "__main__":
    init_db()
    conn = sqlite3.connect(DB_PATH)
    
    # Define which sheets to import and their strategy names
    sheets_to_import = {
        '3Swing-HK': 'Weekly Breakout (3S)',
        '4POS-BO-HK': 'Positional Breakout (4P)',
        '1 week swings': 'Weekly Swings',
        'EMA Cons': 'EMA Consolidation',
        'BO_Trades': 'Breakout Trades'
    }
    
    for sheet, strat in sheets_to_import.items():
        import_sheet(conn, sheet, strat)
        
    conn.close()
    print("Migration complete.")
