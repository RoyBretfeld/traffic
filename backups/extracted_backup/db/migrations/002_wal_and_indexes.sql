-- Migration 002: WAL-Mode und zusätzliche Indizes für address_corrections DB
-- Diese Migration wird automatisch von address_admin_app_fixed.py ausgeführt

-- PRAGMA-Einstellungen für bessere Performance
PRAGMA journal_mode = WAL;
PRAGMA synchronous = NORMAL;

-- Indizes für address_exception_queue
CREATE INDEX IF NOT EXISTS idx_queue_status ON address_exception_queue(status);
CREATE INDEX IF NOT EXISTS idx_queue_seen ON address_exception_queue(times_seen, last_seen);

-- Indizes für address_corrections
CREATE INDEX IF NOT EXISTS idx_corr_key ON address_corrections(key);
CREATE INDEX IF NOT EXISTS idx_corr_city_zip ON address_corrections(city, postal_code);

