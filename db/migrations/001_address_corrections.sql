-- Migration 001: SQLite Robustheit & Performance-Optimierungen
-- 
-- Setzt WAL-Mode für bessere Concurrency und NORMAL synchronous
-- für Balance zwischen Performance und Datenintegrität.
-- Fügt zusätzliche Indizes für häufig genutzte Abfragen hinzu.

-- PRAGMA-Einstellungen (nur SQLite, idempotent)
-- WAL-Mode erlaubt gleichzeitige Lese- und Schreibzugriffe
PRAGMA journal_mode=WAL;

-- NORMAL synchronous: Balance zwischen Performance und Datenintegrität
-- (FULL wäre sicherer, aber langsamer)
PRAGMA synchronous=NORMAL;

-- Timeout für Busy-Retrys erhöhen (default 5s, hier 30s)
PRAGMA busy_timeout=30000;

-- Foreign Keys aktivieren (falls später benötigt)
PRAGMA foreign_keys=ON;

-- Indizes für geo_cache Tabelle (Performance-Optimierung)
-- Index für source-Lookups (z.B. "manual" vs "geocoded")
CREATE INDEX IF NOT EXISTS ix_geo_cache_source ON geo_cache(source);

-- Index für region_ok Filter (regionale Validierung)
CREATE INDEX IF NOT EXISTS ix_geo_cache_region_ok ON geo_cache(region_ok) WHERE region_ok IS NOT NULL;

-- Index für last_seen (älteste Einträge zuerst bei Cleanup)
CREATE INDEX IF NOT EXISTS ix_geo_cache_last_seen ON geo_cache(last_seen ASC);

-- Composite Index für häufige Queries: source + region_ok
CREATE INDEX IF NOT EXISTS ix_geo_cache_source_region ON geo_cache(source, region_ok);

-- Index für manual_queue Status-Lookups
CREATE INDEX IF NOT EXISTS ix_manual_queue_status ON manual_queue(status) WHERE status IS NOT NULL;

-- Composite Index für manuelle Queue: status + created_at (neueste offene Fälle zuerst)
CREATE INDEX IF NOT EXISTS ix_manual_queue_status_created ON manual_queue(status, created_at DESC) WHERE status = 'open';

