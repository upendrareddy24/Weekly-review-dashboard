-- Database Schema for Stock Strategy Tracker

CREATE TABLE IF NOT EXISTS tickers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT UNIQUE NOT NULL,
    sector TEXT,
    industry TEXT,
    horizon TEXT
);

CREATE TABLE IF NOT EXISTS strategies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS setups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ticker_id INTEGER NOT NULL,
    strategy_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    status TEXT DEFAULT 'Wait', -- 'Buy', 'Wait', 'Hold', 'Exit'
    rating TEXT,
    score REAL,
    entry TEXT,
    target TEXT,
    sl TEXT,
    rr TEXT,
    comments TEXT,
    meta_json TEXT, -- Store extra fields as JSON
    FOREIGN KEY (ticker_id) REFERENCES tickers(id),
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);

-- Indexing for fast history lookups
CREATE INDEX IF NOT EXISTS idx_setups_ticker ON setups(ticker_id);
CREATE INDEX IF NOT EXISTS idx_setups_date ON setups(date);
