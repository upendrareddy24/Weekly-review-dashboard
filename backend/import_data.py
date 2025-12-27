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

def import_sheet(conn, sheet_name, strategy_name, bucket_name):
    print(f"Importing {sheet_name} as {strategy_name} into {bucket_name}...")
    try:
        df = pd.read_excel(EXCEL_PATH, sheet_name=sheet_name)
        
        # Cleanup column names (remove leading/trailing spaces)
        df.columns = [str(c).strip() for c in df.columns]
        
        strategy_id = get_or_create_strategy(conn, strategy_name)
        
        for _, row in df.iterrows():
            # Column D: Stock / Ticker
            symbol = str(row.get('Stock', row.get('Ticker', ''))).strip()
            if not symbol or symbol == 'nan' or len(symbol) > 10:
                continue
            
            # Column L & M: Sector & Horizon
            sector = str(row.get('Sector', '')).strip()
            horizon = str(row.get('Horizon', '')).strip()
            
            ticker_id = get_or_create_ticker(conn, symbol, sector, horizon)
            
            # Column A: ChatGPT (Source)
            source = str(row.get('ChatGPT', 'Analyst')).strip()
            
            # Column B: Strategy
            strat_field = str(row.get('Strategy', strategy_name)).strip()
            
            # Column C: BUY Date
            buy_date = row.get('BUY Date', row.get('Date', ''))
            if pd.isna(buy_date): buy_date = ''
            
            # Column E: Category
            category = str(row.get('Category', '')).strip()
            
            # Column F: Pattern Stage
            pattern_stage = str(row.get('Pattern Stage', '')).strip()
            
            # Column G: Score
            score_text = str(row.get('Score', '')).strip()
            
            # Column H: Highlights
            highlights = str(row.get('Highlights', '')).strip()
            
            # Column I, J, K: Price Zones
            breakout_zone = str(row.get('Breakout Zone', '')).strip()
            target_zone = str(row.get('Target Zone', '')).strip()
            invalidation = str(row.get('Invalidation', '')).strip()
            
            # Column N: Confidence
            conf_val = row.get('Confidence', 3)
            try:
                if isinstance(conf_val, str):
                    confidence_stars = conf_val.count('★') if '★' in conf_val else 3
                else:
                    confidence_stars = int(conf_val) if not pd.isna(conf_val) else 3
            except:
                confidence_stars = 3

            # Column O: Buy / Wait
            buy_wait = str(row.get('Buy / Wait', 'Wait')).strip()

            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO setups 
                (ticker_id, strategy_id, date, source, strategy_name, buy_date, category, 
                 pattern_stage, score_text, highlights, breakout_zone, target_zone, 
                 invalidation, horizon, confidence_stars, buy_wait_status, state, bucket)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticker_id, strategy_id, datetime.now().strftime('%Y-%m-%d'), 
                   source, strat_field, str(buy_date), category, pattern_stage, 
                   score_text, highlights, breakout_zone, target_zone, invalidation, 
                   horizon, confidence_stars, buy_wait, 'ACTIVE', bucket_name))
        
        conn.commit()
        print(f"Successfully imported {len(df)} rows from {sheet_name}.")
    except Exception as e:
        print(f"Error importing {sheet_name}: {e}")

if __name__ == "__main__":
    init_db() # This will re-create tables if we want a fresh start, or just run it to ensure schema
    conn = sqlite3.connect(DB_PATH)
    
    # Define which sheets to import and their strategy/bucket names
    sheets_to_import = [
        ('3SWING-PF', 'Swing Portfolio', '3Swing'),
        ('4POS-BO-HK', 'Positional Breakout (HK)', '4POS'),
        ('4Portfolio_10', 'Portfolio 10', 'Holdings'),
        ('5POS-HV-HK', 'HV Positional (HK)', '4POS'),
        ('5HV-PF', 'HV Portfolio', 'Holdings'),
        ('6POS-PAT-HK', 'Pattern Positional (HK)', '4POS'),
        ('6PAT-PF', 'Pattern Portfolio', 'Holdings'),
        ('7INV-HK', 'Invalidation (HK)', '4POS'),
        ('7INV-PF', 'Invalidation Portfolio', 'Holdings'),
        ('3Swing-HK', 'Weekly Breakout (3S)', '3Swing'),
        ('EMA Cons', 'EMA Consolidation', '3Swing'),
        ('BO_Trades', 'Breakout Trades', '3Swing'),
        ('1 week swings', 'Weekly Swings', 'Holdings')
    ]
    
    for sheet, strat, bucket in sheets_to_import:
        import_sheet(conn, sheet, strat, bucket)
        
    conn.close()
    print("Migration complete.")
