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

@app.route('/api/setups', methods=['POST'])
def save_setup():
    data = request.json
    conn = get_db_connection()
    try:
        # If ID exists, update; otherwise, insert
        if data.get('id'):
            conn.execute("""
                UPDATE setups SET 
                status = ?, rating = ?, score = ?, entry = ?, 
                target = ?, sl = ?, rr = ?, comments = ?, date = ?
                WHERE id = ?
            """, (data['status'], data['rating'], data['score'], data['entry'], 
                  data['target'], data['sl'], data['rr'], data['comments'], 
                  data.get('date', datetime.now().strftime('%Y-%m-%d')), data['id']))
        else:
            # Need to get ticker_id first
            ticker = conn.execute('SELECT id FROM tickers WHERE symbol = ?', (data['symbol'],)).fetchone()
            if not ticker:
                # Create ticker on the fly if needed
                cur = conn.execute('INSERT INTO tickers (symbol) VALUES (?)', (data['symbol'],))
                ticker_id = cur.lastrowid
            else:
                ticker_id = ticker['id']
            
            conn.execute("""
                INSERT INTO setups 
                (ticker_id, strategy_id, date, status, rating, score, entry, target, sl, rr, comments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (ticker_id, data['strategy_id'], data.get('date', datetime.now().strftime('%Y-%m-%d')),
                  data['status'], data['rating'], data['score'], data['entry'], 
                  data['target'], data['sl'], data['rr'], data['comments']))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/filters', methods=['GET'])
def get_filters():
    conn = get_db_connection()
    sectors = conn.execute('SELECT DISTINCT sector FROM tickers WHERE sector IS NOT NULL').fetchall()
    statuses = conn.execute('SELECT DISTINCT status FROM setups').fetchall()
    conn.close()
    return jsonify({
        "sectors": [s[0] for s in sectors] + ["General"],
        "statuses": [s[0] for s in statuses]
    })

@app.route('/api/catalysts', methods=['GET'])
def get_catalysts():
    week = request.args.get('week', datetime.now().strftime('%Y-%W'))
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM catalysts WHERE week_start = ?', (week,)).fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])

@app.route('/api/catalysts', methods=['POST'])
def save_catalyst():
    data = request.json
    conn = get_db_connection()
    try:
        conn.execute("""
            INSERT INTO catalysts (week_start, day, time_slot, event)
            VALUES (?, ?, ?, ?)
        """, (data['week'], data['day'], data['time_slot'], data['event']))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize DB if not exists
    if not os.path.exists(DB_PATH):
        print("Database not found. Please run backend/import_data.py first.")
    
    app.run(debug=False, port=int(os.getenv("PORT", 5012)))
