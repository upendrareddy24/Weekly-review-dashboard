from flask import Flask, jsonify, request
from flask_cors import CORS
import sqlite3
import yfinance as yf
import pandas as pd
import json
import os

app = Flask(__name__)
CORS(app)

DB_PATH = "backend/stocks.db"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

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

@app.route('/api/price/<symbol>', methods=['GET'])
def get_price(symbol):
    try:
        ticker = yf.Ticker(symbol)
        price = ticker.fast_info['last_price']
        return jsonify({"symbol": symbol, "price": round(price, 2)})
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
    app.run(debug=True, port=int(os.getenv("PORT", 5012)))
