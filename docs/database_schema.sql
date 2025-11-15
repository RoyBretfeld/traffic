-- =====================================================
-- FAMO TrafficApp - Datenbank Schema
-- =====================================================
-- Erstellt: 19. August 2025
-- Aktualisiert: 03. November 2025
-- Version: 2.0.0
-- Beschreibung: SQLite-Schema für Tourenplanung und -optimierung
-- 
-- WICHTIG: Dieses Schema ist synchronisiert mit db/schema.py
-- Alle Änderungen müssen in BEIDEN Dateien gemacht werden!
-- =====================================================

-- =====================================================
-- 1. KUNDENSTAMMDATEN
-- =====================================================

CREATE TABLE IF NOT EXISTS kunden (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    adresse TEXT NOT NULL,
    lat REAL,
    lon REAL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Eindeutigkeit: gleicher Kunde (Name+Adresse) nur einmal
CREATE UNIQUE INDEX IF NOT EXISTS kunden_unique_name_addr
ON kunden(name COLLATE NOCASE, adresse COLLATE NOCASE);

-- Performance-Indizes
CREATE INDEX IF NOT EXISTS idx_kunden_name ON kunden(name);
CREATE INDEX IF NOT EXISTS idx_kunden_adresse ON kunden(adresse);
CREATE INDEX IF NOT EXISTS idx_kunden_koordinaten ON kunden(lat, lon);

-- =====================================================
-- 2. TOURENVERWALTUNG
-- =====================================================

CREATE TABLE IF NOT EXISTS touren (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id TEXT NOT NULL,
    datum TEXT NOT NULL,
    kunden_ids TEXT, -- JSON-Liste von kunden.id
    dauer_min INTEGER,
    distanz_km REAL,
    fahrer TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);

-- Eindeutigkeit: gleiche Tour-ID am selben Datum nur einmal
CREATE UNIQUE INDEX IF NOT EXISTS touren_unique_by_date
ON touren(tour_id, datum);

-- Performance-Indizes
CREATE INDEX IF NOT EXISTS idx_touren_datum ON touren(datum);
CREATE INDEX IF NOT EXISTS idx_touren_tour_id ON touren(tour_id);
CREATE INDEX IF NOT EXISTS idx_touren_fahrer ON touren(fahrer);

-- =====================================================
-- 3. FAHRERFEEDBACK
-- =====================================================

CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tour_id TEXT NOT NULL,
    datum TEXT NOT NULL,
    kommentar TEXT,
    bewertung INTEGER CHECK (bewertung >= 1 AND bewertung <= 5),
    created_at TEXT DEFAULT (datetime('now'))
);

-- Performance-Indizes
CREATE INDEX IF NOT EXISTS idx_feedback_tour_id ON feedback(tour_id);
CREATE INDEX IF NOT EXISTS idx_feedback_datum ON feedback(datum);
CREATE INDEX IF NOT EXISTS idx_feedback_bewertung ON feedback(bewertung);

-- =====================================================
-- 4. GEOCODING CACHE (AKTUELLES SCHEMA)
-- =====================================================

CREATE TABLE IF NOT EXISTS geo_cache (
    address_norm TEXT PRIMARY KEY,
    lat DOUBLE PRECISION NOT NULL,
    lon DOUBLE PRECISION NOT NULL,
    source TEXT DEFAULT 'geocoded',
    precision TEXT,
    region_ok INTEGER,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    by_user TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance-Indizes
CREATE INDEX IF NOT EXISTS idx_geo_cache_updated ON geo_cache(updated_at);
CREATE INDEX IF NOT EXISTS idx_geo_cache_source ON geo_cache(source);
CREATE INDEX IF NOT EXISTS idx_geo_cache_region_ok ON geo_cache(region_ok);

-- =====================================================
-- 4.1. MANUAL QUEUE (für fehlgeschlagene Geocodes)
-- =====================================================

CREATE TABLE IF NOT EXISTS manual_queue (
    id INTEGER PRIMARY KEY,
    address_norm TEXT NOT NULL,
    raw_address TEXT,
    reason TEXT,
    note TEXT,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance-Indizes
CREATE INDEX IF NOT EXISTS ix_manual_queue_created ON manual_queue(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_manual_queue_address ON manual_queue(address_norm);
CREATE INDEX IF NOT EXISTS ix_manual_queue_status ON manual_queue(status);

-- =====================================================
-- 4.2. GEO FAIL (für fehlgeschlagene Geocoding-Versuche)
-- =====================================================

CREATE TABLE IF NOT EXISTS geo_fail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address_norm TEXT NOT NULL,
    raw_address TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Performance-Indizes
CREATE INDEX IF NOT EXISTS idx_geo_fail_address ON geo_fail(address_norm);
CREATE INDEX IF NOT EXISTS idx_geo_fail_created ON geo_fail(created_at DESC);

-- =====================================================
-- 5. POSTLEITZAHL CACHE
-- =====================================================

CREATE TABLE IF NOT EXISTS postal_code_cache (
    postal_code TEXT PRIMARY KEY,
    city TEXT NOT NULL,
    updated_at TEXT DEFAULT (datetime('now'))
);

-- Performance-Index
CREATE INDEX IF NOT EXISTS idx_postal_cache_updated ON postal_code_cache(updated_at);

-- =====================================================
-- 6. TRIGGER FÜR AUTOMATISCHE UPDATES
-- =====================================================

-- Trigger für automatische updated_at Updates
CREATE TRIGGER IF NOT EXISTS update_geocache_timestamp
    AFTER UPDATE ON geocache
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE geocache SET updated_at = datetime('now') WHERE adresse = NEW.adresse;
END;

CREATE TRIGGER IF NOT EXISTS update_postal_cache_timestamp
    AFTER UPDATE ON postal_code_cache
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE postal_code_cache SET updated_at = datetime('now') WHERE postal_code = NEW.postal_code;
END;

-- =====================================================
-- 7. VIEWS FÜR HÄUFIGE ABFRAGEN
-- =====================================================

-- View: Kunden mit Koordinaten
CREATE VIEW IF NOT EXISTS kunden_mit_koordinaten AS
SELECT 
    id,
    name,
    adresse,
    lat,
    lon,
    created_at
FROM kunden 
WHERE lat IS NOT NULL AND lon IS NOT NULL;

-- View: Touren-Statistiken
CREATE VIEW IF NOT EXISTS touren_statistiken AS
SELECT 
    datum,
    COUNT(*) as anzahl_touren,
    SUM(CASE WHEN kunden_ids IS NOT NULL THEN JSON_ARRAY_LENGTH(kunden_ids) ELSE 0 END) as total_kunden,
    AVG(dauer_min) as avg_dauer_min,
    AVG(distanz_km) as avg_distanz_km,
    SUM(distanz_km) as total_distanz_km
FROM touren 
GROUP BY datum 
ORDER BY datum DESC;

-- View: W-Touren (Wochentouren)
CREATE VIEW IF NOT EXISTS w_touren AS
SELECT 
    id,
    tour_id,
    datum,
    kunden_ids,
    dauer_min,
    distanz_km,
    fahrer,
    created_at
FROM touren 
WHERE tour_id LIKE 'W-%';

-- View: PIR-Touren (Pirna-Touren)
CREATE VIEW IF NOT EXISTS pir_touren AS
SELECT 
    id,
    tour_id,
    datum,
    kunden_ids,
    dauer_min,
    distanz_km,
    fahrer,
    created_at
FROM touren 
WHERE tour_id LIKE 'PIR-%';

-- =====================================================
-- 8. BEISPIEL-DATEN
-- =====================================================

-- FAMO Dresden (Hauptstandort)
INSERT OR IGNORE INTO kunden (name, adresse, lat, lon) VALUES
('FAMO Dresden', 'Stuttgarter Str. 33, 01189 Dresden', 51.0504, 13.7373);

-- Beispiel-Kunden
INSERT OR IGNORE INTO kunden (name, adresse, lat, lon) VALUES
('Kunde A', 'Hauptstr. 1, 01067 Dresden', 51.0521, 13.7372),
('Kunde B', 'Marktplatz 5, 01067 Dresden', 51.0519, 13.7375),
('Kunde C', 'Bahnhofstr. 10, 01069 Dresden', 51.0515, 13.7378),
('Kunde D', 'Altmarkt 15, 01067 Dresden', 51.0525, 13.7370),
('Kunde E', 'Neumarkt 8, 01067 Dresden', 51.0520, 13.7375);

-- Beispiel-Touren
INSERT OR IGNORE INTO touren (tour_id, datum, kunden_ids, dauer_min, distanz_km, fahrer) VALUES
('W-07:00', '2025-08-19', '[2,3,4]', 120, 45.5, 'Max Mustermann'),
('W-09:00', '2025-08-19', '[5,6]', 90, 32.1, 'Anna Schmidt'),
('PIR-14:00', '2025-08-19', '[7,8]', 60, 25.3, 'Peter Weber');

-- Beispiel-Geocache (AKTUELLES SCHEMA: geo_cache)
INSERT OR IGNORE INTO geo_cache (address_norm, lat, lon, source, first_seen, last_seen) VALUES
('Stuttgarter Str. 33, 01189 Dresden', 51.0504, 13.7373, 'geocoded', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('Hauptstr. 1, 01067 Dresden', 51.0521, 13.7372, 'geocoded', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('Marktplatz 5, 01067 Dresden', 51.0519, 13.7375, 'geocoded', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Beispiel-PLZ-Cache
INSERT OR IGNORE INTO postal_code_cache (postal_code, city) VALUES
('01189', 'Dresden'),
('01067', 'Dresden'),
('01069', 'Dresden'),
('01097', 'Dresden');

-- =====================================================
-- 9. NÜTZLICHE FUNKTIONEN
-- =====================================================

-- Funktion: JSON-Array-Länge (falls nicht verfügbar)
-- Diese Funktion ist in neueren SQLite-Versionen bereits verfügbar
-- Für ältere Versionen kann sie hier definiert werden

-- =====================================================
-- 10. CLEANUP-OPERATIONEN
-- =====================================================

-- Alte Geocache-Einträge löschen (älter als 30 Tage)
-- DELETE FROM geocache WHERE updated_at < datetime('now', '-30 days');

-- Alte Feedback-Einträge löschen (älter als 1 Jahr)
-- DELETE FROM feedback WHERE created_at < datetime('now', '-1 year');

-- VACUUM für Speicher-Optimierung
-- VACUUM;

-- =====================================================
-- 11. SCHEMA-VALIDIERUNG
-- =====================================================

-- Prüfe Tabellen-Existenz
-- SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;

-- Prüfe Indizes
-- SELECT name FROM sqlite_master WHERE type='index' ORDER BY name;

-- Prüfe Views
-- SELECT name FROM sqlite_master WHERE type='view' ORDER BY name;

-- =====================================================
-- ENDE DES SCHEMAS
-- =====================================================
