-- Migration: stats_daily Tabelle für AR-04
-- Datum: 2025-11-22
-- Beschreibung: Tagesstatistiken für schnelle Auswertung im Adminbereich

CREATE TABLE IF NOT EXISTS stats_daily (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    date              DATE NOT NULL,
    region            TEXT,            -- NULL = global
    total_tours       INTEGER DEFAULT 0,
    completed_tours    INTEGER DEFAULT 0,
    aborted_tours     INTEGER DEFAULT 0,
    total_stops       INTEGER DEFAULT 0,
    total_km_planned  REAL DEFAULT 0,
    total_km_real     REAL DEFAULT 0,
    total_time_min    REAL DEFAULT 0,
    total_cost        REAL DEFAULT 0,
    avg_delay_minutes REAL DEFAULT 0,
    avg_success_score REAL DEFAULT 0,
    created_at        DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at        DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_stats_daily_date_region ON stats_daily(date, region);
CREATE INDEX IF NOT EXISTS idx_stats_daily_date ON stats_daily(date DESC);

