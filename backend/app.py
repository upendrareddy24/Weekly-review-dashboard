from flask import Flask, jsonify, request, render_template, send_from_directory
from flask_cors import CORS
import sqlite3
import yfinance as yf
import pandas as pd
import json
import os
from datetime import datetime

# Adjust paths for Heroku where app.py is in backend/ and folders are in root
app = Flask(__name__, 
            template_folder='../templates', 
            static_folder='../static')
CORS(app)

import psycopg2
from psycopg2.extras import RealDictCursor
import urllib.parse

# Heroku Postgres or Local SQLite
DATABASE_URL = os.getenv('DATABASE_URL')
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SQLITE_DB_PATH = os.path.join(BASE_DIR, "stocks.db")

def get_db_connection():
    if DATABASE_URL:
        # PostgreSQL logic
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        return conn
    else:
        # SQLite fallback
        conn = sqlite3.connect(SQLITE_DB_PATH)
        conn.row_factory = sqlite3.Row
        return conn

def get_db_cursor(conn):
    if DATABASE_URL:
        return conn.cursor(cursor_factory=RealDictCursor)
    return conn.cursor()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/strategies', methods=['GET'])
def get_strategies():
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    cur.execute('SELECT * FROM strategies')
    strategies = cur.fetchall()
    conn.close()
    return jsonify([dict(s) for s in strategies])

@app.route('/api/tickers', methods=['GET'])
def get_tickers():
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    cur.execute('SELECT * FROM tickers')
    tickers = cur.fetchall()
    conn.close()
    return jsonify([dict(t) for t in tickers])

@app.route('/api/setups', methods=['GET'])
def get_setups():
    strategy_id = request.args.get('strategy_id')
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    query = """
        SELECT s.*, t.symbol, t.sector, st.name as strategy_name
        FROM setups s
        JOIN tickers t ON s.ticker_id = t.id
        JOIN strategies st ON s.strategy_id = st.id
    """
    if strategy_id:
        p = "%s" if DATABASE_URL else "?"
        query += f" WHERE s.strategy_id = {p}"
        cur.execute(query, (strategy_id,))
    else:
        cur.execute(query)
    setups = cur.fetchall()
    conn.close()
    return jsonify([dict(s) for s in setups])

@app.route('/api/setups', methods=['POST'])
def save_setup():
    data = request.json
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    p = "%s" if DATABASE_URL else "?"
    try:
        if data.get('id'):
            cur.execute(f"""
                UPDATE setups SET 
                status = {p}, rating = {p}, score = {p}, entry = {p}, 
                target = {p}, sl = {p}, rr = {p}, comments = {p}, date = {p}
                WHERE id = {p}
            """, (data['status'], data['rating'], data['score'], data['entry'], 
                  data['target'], data['sl'], data['rr'], data['comments'], 
                  data.get('date', datetime.now().strftime('%Y-%m-%d')), data['id']))
        else:
            cur.execute(f'SELECT id FROM tickers WHERE symbol = {p}', (data['symbol'],))
            ticker = cur.fetchone()
            if not ticker:
                cur.execute(f'INSERT INTO tickers (symbol) VALUES ({p}){" RETURNING id" if DATABASE_URL else ""}', (data['symbol'],))
                ticker_id = cur.fetchone()[0] if DATABASE_URL else cur.lastrowid
            else:
                ticker_id = ticker['id']
            
            cur.execute(f"""
                INSERT INTO setups 
                (ticker_id, strategy_id, date, status, rating, score, entry, target, sl, rr, comments)
                VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
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
    cur = get_db_cursor(conn)
    cur.execute('SELECT DISTINCT sector FROM tickers WHERE sector IS NOT NULL')
    sectors = cur.fetchall()
    cur.execute('SELECT DISTINCT status FROM setups')
    statuses = cur.fetchall()
    conn.close()
    return jsonify({
        "sectors": [s['sector'] if DATABASE_URL else s[0] for s in sectors] + ["General"],
        "statuses": [s['status'] if DATABASE_URL else s[0] for s in statuses]
    })

@app.route('/api/catalysts', methods=['GET'])
def get_catalysts():
    week = request.args.get('week', datetime.now().strftime('%Y-%W'))
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    p = "%s" if DATABASE_URL else "?"
    cur.execute(f'SELECT * FROM catalysts WHERE week_start = {p}', (week,))
    items = cur.fetchall()
    conn.close()
    return jsonify([dict(i) for i in items])

@app.route('/api/catalysts', methods=['POST'])
def save_catalyst():
    data = request.json
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    p = "%s" if DATABASE_URL else "?"
    try:
        cur.execute(f"""
            INSERT INTO catalysts (week_start, day, time_slot, event)
            VALUES ({p}, {p}, {p}, {p})
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
