-- db/migrations/019_geo_flags.sql
-- Erweitert geo_cache Tabelle um source, precision, region_ok und Timestamps
-- Fügt manual_queue Tabelle für fehlgeschlagene Geocodes hinzu

-- Geo_cache Tabelle erweitern
ALTER TABLE geo_cache ADD COLUMN IF NOT EXISTS source TEXT;
ALTER TABLE geo_cache ADD COLUMN IF NOT EXISTS precision TEXT;
ALTER TABLE geo_cache ADD COLUMN IF NOT EXISTS region_ok INTEGER;
ALTER TABLE geo_cache ADD COLUMN IF NOT EXISTS first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP;
ALTER TABLE geo_cache ADD COLUMN IF NOT EXISTS last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

-- Eindeutigen Index für address_norm erstellen (falls noch nicht vorhanden)
CREATE UNIQUE INDEX IF NOT EXISTS ux_geo_cache_address_norm ON geo_cache(address_norm);

-- Manual-Queue Tabelle für fehlgeschlagene Geocodes
CREATE TABLE IF NOT EXISTS manual_queue (
  id INTEGER PRIMARY KEY,
  address_norm TEXT NOT NULL,
  raw_address TEXT,
  reason TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index für schnelle Abfragen nach Erstellungsdatum
CREATE INDEX IF NOT EXISTS ix_manual_queue_created ON manual_queue(created_at DESC);

-- Index für Adress-Lookups
CREATE INDEX IF NOT EXISTS ix_manual_queue_address ON manual_queue(address_norm);
