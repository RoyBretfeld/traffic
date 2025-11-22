-- Migration 020: Tour-Import & Vorladen
-- Erstellt Tabellen für Batch-Import von Touren und Kunden-Vorladen
-- Datum: 2025-11-19

-- Tabelle für Import-Batches (Metadaten zu einem Importlauf)
CREATE TABLE IF NOT EXISTS import_batches (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    name         TEXT NOT NULL,
    source       TEXT,              -- z.B. 'Kunde_X_CSV', 'Manueller Upload'
    created_by   TEXT,
    created_at   DATETIME DEFAULT CURRENT_TIMESTAMP,
    status       TEXT NOT NULL DEFAULT 'pending',     -- pending|running|completed|failed
    total_tours  INTEGER DEFAULT 0,
    total_stops  INTEGER DEFAULT 0,
    geocoded_ok  INTEGER DEFAULT 0,
    geocoded_failed INTEGER DEFAULT 0,
    geocoded_pending INTEGER DEFAULT 0
);

-- Tabelle für Import-Batch-Items (pro Datei im Batch)
CREATE TABLE IF NOT EXISTS import_batch_items (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    batch_id       INTEGER NOT NULL REFERENCES import_batches(id) ON DELETE CASCADE,
    filename       TEXT,
    status         TEXT NOT NULL DEFAULT 'pending',   -- pending|running|completed|failed
    tours_created  INTEGER DEFAULT 0,
    stops_created  INTEGER DEFAULT 0,
    error_message  TEXT,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabelle für Kunden-Adress-Pool (Vorladen von Kunden mit Geocode)
CREATE TABLE IF NOT EXISTS customers (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id    TEXT,           -- Kundeneigene ID, falls vorhanden
    name           TEXT,
    street         TEXT,
    zip            TEXT,
    city           TEXT,
    country        TEXT DEFAULT 'Deutschland',
    lat            REAL,
    lon            REAL,
    geocode_status TEXT DEFAULT 'pending',           -- pending|ok|failed
    last_used_at   DATETIME,
    created_at     DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at     DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_import_batches_status ON import_batches(status);
CREATE INDEX IF NOT EXISTS idx_import_batches_created ON import_batches(created_at);
CREATE INDEX IF NOT EXISTS idx_import_batch_items_batch ON import_batch_items(batch_id);
CREATE INDEX IF NOT EXISTS idx_customers_external_id ON customers(external_id);
CREATE INDEX IF NOT EXISTS idx_customers_geocode_status ON customers(geocode_status);
CREATE INDEX IF NOT EXISTS idx_customers_city_zip ON customers(city, zip);

-- Foreign Key Constraints aktivieren (SQLite unterstützt das ab Version 3.6.19)
PRAGMA foreign_keys = ON;

