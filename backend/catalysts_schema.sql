-- Add Catalysts table for weekly review
CREATE TABLE IF NOT EXISTS catalysts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    week_start TEXT NOT NULL,
    day TEXT NOT NULL, -- 'M', 'T', 'W', 'TH', 'F'
    time_slot TEXT NOT NULL, -- 'BM', 'MH', 'AM'
    event TEXT NOT NULL
);

-- Add Index for faster lookup
CREATE INDEX IF NOT EXISTS idx_catalysts_week ON catalysts(week_start);
