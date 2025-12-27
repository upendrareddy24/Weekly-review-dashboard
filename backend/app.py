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
    try:
        conn = get_db_connection()
        cur = get_db_cursor(conn)
        cur.execute('SELECT * FROM strategies')
        strategies = cur.fetchall()
        conn.close()
        return jsonify([dict(s) for s in strategies])
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"!!! STRATEGIES ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/tickers', methods=['GET'])
def get_tickers():
    try:
        conn = get_db_connection()
        cur = get_db_cursor(conn)
        cur.execute('SELECT * FROM tickers')
        tickers = cur.fetchall()
        conn.close()
        return jsonify([dict(t) for t in tickers])
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"!!! TICKERS ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/setups', methods=['GET'])
def get_setups():
    strategy_id = request.args.get('strategy_id')
    bucket = request.args.get('bucket')
    attention_only = request.args.get('attention', 'false').lower() == 'true'
    
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    
    query = """
        SELECT s.*, t.symbol, t.sector, t.thesis, t.bias, st.name as strategy_name
        FROM setups s
        JOIN tickers t ON s.ticker_id = t.id
        JOIN strategies st ON s.strategy_id = st.id
    """
    params = []
    where_clauses = []
    
    if strategy_id:
        where_clauses.append("s.strategy_id = %s" if DATABASE_URL else "s.strategy_id = ?")
        params.append(strategy_id)
    
    if bucket:
        where_clauses.append("s.bucket = %s" if DATABASE_URL else "s.bucket = ?")
        params.append(bucket)
        
    if where_clauses:
        query += " WHERE " + " AND ".join(where_clauses)
    
    cur.execute(query, params)
    setups = cur.fetchall()
    conn.close()
    
    # Process attention logic (mocking price triggers for now as we don't have a real-time stream here yet)
    # In a real app, we'd compare price to trigger_price/invalid_price
    results = [dict(s) for s in setups]
    if attention_only:
        # Filter for 'MONITORING' with specific conditions or just 'STALE'
        # For demo, let's say anything older than 7 days needs attention
        from datetime import timedelta
        cutoff = datetime.now() - timedelta(days=7)
        results = [s for s in results if s['state'] != 'ACTIVE' or datetime.strptime(s['date'], '%Y-%m-%d') < cutoff]
        
    return jsonify(results)

@app.route('/api/tickers/<symbol>', methods=['POST'])
def update_ticker(symbol):
    data = request.json
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    p = "%s" if DATABASE_URL else "?"
    try:
        cur.execute(f"UPDATE tickers SET thesis = {p}, bias = {p} WHERE symbol = {p}",
                   (data.get('thesis'), data.get('bias'), symbol))
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

@app.route('/api/market/regime', methods=['GET', 'POST'])
def market_regime():
    try:
        conn = get_db_connection()
        cur = get_db_cursor(conn)
        if request.method == 'POST':
            data = request.json
            p = "%s" if DATABASE_URL else "?"
            cur.execute(f"INSERT INTO market_snapshots (date, regime, notes) VALUES ({p}, {p}, {p})",
                       (datetime.now().strftime('%Y-%m-%d'), data['regime'], data.get('notes', '')))
            conn.commit()
        
        cur.execute('SELECT * FROM market_snapshots ORDER BY date DESC LIMIT 1')
        regime = cur.fetchone()
        conn.close()
        return jsonify(dict(regime) if regime else {"regime": "Neutral", "notes": "No snapshot taken."})
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"!!! REGIME ERROR: {e}")
        return jsonify({"error": str(e)}), 500

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
        print(f"ERROR: {e}")
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
    try:
        week = request.args.get('week_number')
        conn = get_db_connection()
        cur = get_db_cursor(conn)
        p = "%s" if DATABASE_URL else "?"
        if week and week.isdigit():
            cur.execute(f'SELECT * FROM catalysts WHERE week_number = {p}', (int(week),))
        else:
            cur.execute('SELECT * FROM catalysts')
        items = cur.fetchall()
        conn.close()
        return jsonify([dict(i) for i in items])
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"!!! CATALYSTS ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/macro_reviews', methods=['GET'])
def get_macro_reviews():
    try:
        week = request.args.get('week_number')
        conn = get_db_connection()
        cur = get_db_cursor(conn)
        p = "%s" if DATABASE_URL else "?"
        if week and week.isdigit():
            cur.execute(f'SELECT * FROM macro_reviews WHERE week_number = {p}', (int(week),))
        else:
            cur.execute('SELECT * FROM macro_reviews')
        items = cur.fetchall()
        conn.close()
        return jsonify([dict(i) for i in items])
    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/focus_reviews', methods=['GET'])
def get_focus_reviews():
    try:
        week = request.args.get('week_number')
        conn = get_db_connection()
        cur = get_db_cursor(conn)
        p = "%s" if DATABASE_URL else "?"
        if week and week.isdigit():
            cur.execute(f'SELECT * FROM focus_reviews WHERE week_number = {p}', (int(week),))
        else:
            cur.execute('SELECT * FROM focus_reviews')
        items = cur.fetchall()
        conn.close()
        return jsonify([dict(i) for i in items])
    except Exception as e:
        print(f"ERROR: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/api/wizard/save', methods=['POST'])
def save_wizard_step():
    data = request.json
    step_type = data.get('type') # catalyst, macro, focus
    week = data.get('week_number')
    rows = data.get('rows', [])
    
    conn = get_db_connection()
    cur = get_db_cursor(conn)
    p = "%s" if DATABASE_URL else "?"
    
    try:
        if step_type == 'catalyst':
            cur.execute(f"DELETE FROM catalysts WHERE week_number = {p}", (week,))
            for r in rows:
                slot = r.get('slot', '')
                days = {'Monday': 'm', 'Tuesday': 't', 'Wednesday': 'w', 'Thursday': 'th', 'Friday': 'f'}
                for day_name, key in days.items():
                    event = r.get(key, '')
                    if event: # Only save if there's an event
                        cur.execute(f"""
                            INSERT INTO catalysts (week_number, week_start, day, time_slot, event)
                            VALUES ({p}, {p}, {p}, {p}, {p})
                        """, (week, 'CW'+str(week), day_name, slot, event))
        
        elif step_type == 'macro':
            cur.execute(f"DELETE FROM macro_reviews WHERE week_number = {p}", (week,))
            for r in rows:
                cur.execute(f"""
                    INSERT INTO macro_reviews (week_number, ticker, trend_labels, trade_notes, entry, exit_val, sl, tickers)
                    VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p}, {p})
                """, (week, r['ticker'], r.get('trend', 'Neutral'), r.get('notes', ''), r.get('entry', ''), r.get('exit', ''), r.get('sl', ''), r.get('tickers', '')))
        
        elif step_type == 'focus':
            cur.execute(f"DELETE FROM focus_reviews WHERE week_number = {p}", (week,))
            for r in rows:
                cur.execute(f"""
                    INSERT INTO focus_reviews (week_number, ticker, trend, entry, target, sl, comments)
                    VALUES ({p}, {p}, {p}, {p}, {p}, {p}, {p})
                """, (week, r['stock'], r['trend'], r['entry'], r['target'], r['sl'], r['comments']))
        
        conn.commit()
        return jsonify({"success": True})
    except Exception as e:
        print(f"ERROR: {e}")
        print(f"Save Wizard Error: {e}")
        return jsonify({"error": str(e)}), 400
    finally:
        conn.close()

if __name__ == '__main__':
    # Initialize DB if not exists
    if not os.path.exists(SQLITE_DB_PATH):
        print(f"Database not found at {SQLITE_DB_PATH}. Please run backend/import_data.py first.")
    
    app.run(debug=True, port=int(os.getenv("PORT", 5012)))
