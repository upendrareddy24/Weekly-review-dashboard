import sqlite3
import json

DB_PATH = "d:/AntiGravity/stock_tracker/backend/stocks.db"

def verify():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Check ticker count
    cursor.execute("SELECT COUNT(*) FROM tickers")
    ticker_count = cursor.fetchone()[0]
    print(f"Total Tickers: {ticker_count}")
    
    # Check strategy count
    cursor.execute("SELECT name, id FROM strategies")
    strats = cursor.fetchall()
    print(f"Strategies: {strats}")
    
    # Check setup count
    cursor.execute("SELECT COUNT(*) FROM setups")
    setup_count = cursor.fetchone()[0]
    print(f"Total Setups: {setup_count}")
    
    # Show history for a common ticker (e.g., AAPL or TSLA if they exist)
    cursor.execute("SELECT symbol, id FROM tickers LIMIT 10")
    sample_tickers = cursor.fetchall()
    print(f"Sample Tickers: {sample_tickers}")
    
    if sample_tickers:
        tid = sample_tickers[0][1]
        symbol = sample_tickers[0][0]
        cursor.execute("""
            SELECT s.date, st.name, s.status, s.comments 
            FROM setups s
            JOIN strategies st ON s.strategy_id = st.id
            WHERE s.ticker_id = ?
            ORDER BY s.date DESC
        """, (tid,))
        history = cursor.fetchall()
        print(f"\nHistory for {symbol}:")
        for h in history:
            print(h)
            
    conn.close()

if __name__ == "__main__":
    verify()
