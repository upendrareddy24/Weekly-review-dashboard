-- Database Schema for Stock Strategy Tracker

CREATE TABLE IF NOT EXISTS tickers (
    id SERIAL PRIMARY KEY,
    symbol TEXT UNIQUE NOT NULL,
    sector TEXT,
    industry TEXT,
    horizon TEXT,
    thesis TEXT,           -- Master investment thesis
    bias TEXT DEFAULT 'Neutral' -- Bullish, Bearish, Neutral
);

CREATE TABLE IF NOT EXISTS strategies (
    id SERIAL PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT
);

CREATE TABLE IF NOT EXISTS setups (
    id SERIAL PRIMARY KEY,
    ticker_id INTEGER NOT NULL,
    strategy_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    week_number INTEGER,      -- Step 1: Calendar Week (1-52)
    source TEXT,              -- Column A: ChatGPT / Analyst / AI
    strategy_name TEXT,       -- Column B: Strategy
    buy_date TEXT,            -- Column C: BUY Date
    category TEXT,            -- Column E: Category
    pattern_stage TEXT,       -- Column F: Pattern Stage
    score_text TEXT,          -- Column G: Score (e.g. 8.25 A+)
    highlights TEXT,          -- Column H: Highlights
    breakout_zone TEXT,       -- Column I: Breakout Zone
    target_zone TEXT,         -- Column J: Target Zone
    invalidation TEXT,        -- Column K: Invalidation
    horizon TEXT,             -- Column M: Horizon
    confidence_stars INTEGER, -- Column N: Confidence (1-5)
    buy_wait_status TEXT,     -- Column O: Buy / Wait
    bucket TEXT,              -- Tactical Bucket Mapping
    state TEXT DEFAULT 'MONITORING', -- Tactical application state
    entry REAL,
    target REAL,
    sl REAL,
    comments TEXT,
    meta_json TEXT, 
    FOREIGN KEY (ticker_id) REFERENCES tickers(id),
    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
);

CREATE TABLE IF NOT EXISTS market_snapshots (
    id SERIAL PRIMARY KEY,
    date TEXT NOT NULL,
    regime TEXT,           -- Risk-On, Risk-Off
    notes TEXT
);

CREATE TABLE IF NOT EXISTS catalysts (
    id SERIAL PRIMARY KEY,
    week_number INTEGER,      -- Associated Review Week (1-52)
    week_start TEXT,
    day TEXT NOT NULL,
    time_slot TEXT NOT NULL,
    event TEXT
);

CREATE TABLE IF NOT EXISTS macro_reviews (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    trend_labels TEXT,    -- e.g. "Long: Bullish, Short: Bearish"
    trade_notes TEXT,
    entry TEXT,
    exit_val TEXT,
    sl TEXT,
    tickers TEXT
);

CREATE TABLE IF NOT EXISTS focus_reviews (
    id SERIAL PRIMARY KEY,
    week_number INTEGER NOT NULL,
    ticker TEXT NOT NULL,
    trend TEXT,
    entry TEXT,
    target TEXT,
    sl TEXT,
    comments TEXT
);

-- Indexing for fast state and history lookups
CREATE INDEX IF NOT EXISTS idx_setups_ticker ON setups(ticker_id);
CREATE INDEX IF NOT EXISTS idx_setups_state ON setups(state);
CREATE INDEX IF NOT EXISTS idx_setups_date ON setups(date);
CREATE INDEX IF NOT EXISTS idx_macro_week ON macro_reviews(week_number);
CREATE INDEX IF NOT EXISTS idx_focus_week ON focus_reviews(week_number);
