from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

# Use absolute path for DB for reliability
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "backend", "stocks.db")

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    conn = get_db_connection()
    strategies = conn.execute('SELECT * FROM strategies').fetchall()
    conn.close()
    return jsonify([dict(s) for s in strategies])

@app.route('/api/tickers', methods=['GET'])
def get_tickers():
    conn = get_db_connection()
    tickers = conn.execute('SELECT * FROM tickers').fetchall()
    conn.close()
    return jsonify([dict(t) for t in tickers])

@app.route('/api/setups', methods=['GET'])
def get_setups():
    strategy_id = request.args.get('strategy_id')
    conn = get_db_connection()
    query = """
        SELECT s.*, t.symbol, t.sector, st.name as strategy_name
        FROM setups s
        JOIN tickers t ON s.ticker_id = t.id
        JOIN strategies st ON s.strategy_id = st.id
    """
    if strategy_id:
        query += " WHERE s.strategy_id = ?"
        setups = conn.execute(query, (strategy_id,)).fetchall()
    else:
        setups = conn.execute(query).fetchall()
    conn.close()
    return jsonify([dict(s) for s in setups])

@app.route('/api/prices', methods=['POST'])
def get_prices():
    data = request.json
    symbols = data.get('symbols', [])
    if not symbols:
        return jsonify({})
    
    prices = {}
    try:
        # Multi-ticker fetch is faster
        tickers = yf.Tickers(' '.join(symbols))
        for symbol in symbols:
            try:
                # Use faster data access if available
                p = tickers.tickers[symbol].fast_info['last_price']
                prices[symbol] = round(p, 2)
            except:
                prices[symbol] = "N/A"
        return jsonify(prices)
    except Exception as e:
        return jsonify({"error": str(e)}), 400

@app.route('/api/ticker/<symbol>/history', methods=['GET'])
def get_ticker_history(symbol):
    conn = get_db_connection()
    ticker = conn.execute('SELECT id FROM tickers WHERE symbol = ?', (symbol,)).fetchone()
    if not ticker:
        return jsonify({"error": "Ticker not found"}), 404
    
    setups = conn.execute("""
        SELECT s.*, st.name as strategy_name
        FROM setups s
        JOIN strategies st ON s.strategy_id = st.id
        WHERE s.ticker_id = ?
        ORDER BY s.date DESC
    """, (ticker['id'],)).fetchall()
    conn.close()
    return jsonify([dict(s) for s in setups])

if __name__ == '__main__':
    # Initialize DB if not exists
    if not os.path.exists(DB_PATH):
        print("Database not found. Please run backend/import_data.py first.")
    
    app.run(debug=False, port=int(os.getenv("PORT", 5012)))
