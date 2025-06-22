-- SQLite schema for the Forex Bot

-- Users table to store information about bot users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,          -- Telegram User ID
    telegram_id INTEGER UNIQUE NOT NULL,
    first_name TEXT,
    last_name TEXT,
    username TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Trades table to log user trades
CREATE TABLE IF NOT EXISTS trades (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pair TEXT NOT NULL,
    lots REAL NOT NULL,
    open_price REAL NOT NULL,
    close_price REAL,
    status TEXT NOT NULL CHECK(status IN ('open', 'closed')), -- 'open' or 'closed'
    opened_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    closed_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Price alerts set by users
CREATE TABLE IF NOT EXISTS alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    pair TEXT NOT NULL,
    target_price REAL NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('active', 'triggered')), -- 'active' or 'triggered'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Performance tracking for different strategies or the bot overall
CREATE TABLE IF NOT EXISTS performance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    strategy_name TEXT NOT NULL,
    wins INTEGER DEFAULT 0,
    losses INTEGER DEFAULT 0,
    total_pips REAL DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User-specific settings
CREATE TABLE IF NOT EXISTS settings (
    user_id INTEGER PRIMARY KEY,
    notifications_enabled BOOLEAN DEFAULT 1,
    timezone TEXT DEFAULT 'UTC',
    risk_profile TEXT DEFAULT 'moderate', -- e.g., 'conservative', 'moderate', 'aggressive'
    FOREIGN KEY (user_id) REFERENCES users (id)
);

-- Indexes to improve query performance
CREATE INDEX IF NOT EXISTS idx_trades_user_status ON trades (user_id, status);
CREATE INDEX IF NOT EXISTS idx_alerts_user_status ON alerts (user_id, status); 