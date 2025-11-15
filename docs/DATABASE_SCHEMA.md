# 🗄️ FAMO TrafficApp - Datenbank Schema

## 📋 Übersicht

Die FAMO TrafficApp verwendet eine **SQLite-Datenbank** für die Speicherung aller Touren-, Kunden- und Geocoding-Daten. Das Schema ist optimiert für die spezifischen Anforderungen der Tourenplanung und -optimierung.

**WICHTIG:** Dieses Schema ist synchronisiert mit `db/schema.py` und `docs/database_schema.sql`. Alle Änderungen müssen in BEIDEN Dateien gemacht werden!

**Letzte Aktualisierung:** 03. November 2025  
**Version:** 2.0.0

## 🏗️ Datenbankstruktur

### 📊 Tabellen-Übersicht

| Tabelle | Zweck | Hauptfunktion |
|---------|-------|---------------|
| `geo_cache` | Geocoding-Cache | Zwischenspeicher für normalisierte Adressen und Koordinaten |
| `manual_queue` | Manual Queue | Warteschlange für fehlgeschlagene Geocodes die manuell bearbeitet werden müssen |
| `geo_fail` | Geocoding-Fehler | Speichert fehlgeschlagene Geocoding-Versuche für Analyse |
| `kunden` | Kundenstammdaten | Speichert alle Kunden mit Adressen und Koordinaten (optional) |
| `touren` | Tourenverwaltung | Haupttabelle für alle geplanten Touren (optional) |
| `feedback` | Fahrerfeedback | Bewertungen und Kommentare zu Touren (optional) |
| `postal_code_cache` | PLZ-Cache | Zwischenspeicher für Postleitzahlen (optional) |

---

## 👥 Tabelle: `kunden`

**Zweck:** Speichert alle Kundenstammdaten mit Adressen und geografischen Koordinaten.

### 📋 Spalten

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | `INTEGER` | Primärschlüssel | `PRIMARY KEY AUTOINCREMENT` |
| `name` | `TEXT` | Kundenname | `NOT NULL` |
| `adresse` | `TEXT` | Vollständige Adresse | `NOT NULL` |
| `lat` | `REAL` | Breitengrad | `NULL` erlaubt |
| `lon` | `REAL` | Längengrad | `NULL` erlaubt |
| `created_at` | `TEXT` | Erstellungsdatum | `DEFAULT (datetime('now'))` |

### 🔑 Indizes

```sql
-- Eindeutigkeit: gleicher Kunde (Name+Adresse) nur einmal
CREATE UNIQUE INDEX kunden_unique_name_addr
ON kunden(name COLLATE NOCASE, adresse COLLATE NOCASE);
```

### 📝 Beispiel-Daten

```sql
INSERT INTO kunden (name, adresse, lat, lon) VALUES
('FAMO Dresden', 'Stuttgarter Str. 33, 01189 Dresden', 51.0504, 13.7373),
('Kunde A', 'Hauptstr. 1, 01067 Dresden', 51.0521, 13.7372),
('Kunde B', 'Marktplatz 5, 01067 Dresden', 51.0519, 13.7375);
```

---

## 🚚 Tabelle: `touren`

**Zweck:** Haupttabelle für alle geplanten Touren mit Kunden-IDs und Metadaten.

### 📋 Spalten

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | `INTEGER` | Primärschlüssel | `PRIMARY KEY AUTOINCREMENT` |
| `tour_id` | `TEXT` | Tour-Identifikator (z.B. "W-07:00") | `NOT NULL` |
| `datum` | `TEXT` | Tour-Datum (YYYY-MM-DD) | `NOT NULL` |
| `kunden_ids` | `TEXT` | JSON-Liste der Kunden-IDs | `NULL` erlaubt |
| `dauer_min` | `INTEGER` | Geschätzte Dauer in Minuten | `NULL` erlaubt |
| `distanz_km` | `REAL` | Geschätzte Distanz in km | `NULL` erlaubt |
| `fahrer` | `TEXT` | Zugewiesener Fahrer | `NULL` erlaubt |
| `created_at` | `TEXT` | Erstellungsdatum | `DEFAULT (datetime('now'))` |

### 🔑 Indizes

```sql
-- Eindeutigkeit: gleiche Tour-ID am selben Datum nur einmal
CREATE UNIQUE INDEX touren_unique_by_date
ON touren(tour_id, datum);
```

### 📝 Beispiel-Daten

```sql
INSERT INTO touren (tour_id, datum, kunden_ids, dauer_min, distanz_km, fahrer) VALUES
('W-07:00', '2025-08-19', '[1,2,3,4,5]', 120, 45.5, 'Max Mustermann'),
('W-09:00', '2025-08-19', '[6,7,8,9,10]', 90, 32.1, 'Anna Schmidt'),
('PIR-14:00', '2025-08-19', '[11,12,13]', 60, 25.3, 'Peter Weber');
```

---

## 💬 Tabelle: `feedback`

**Zweck:** Speichert Fahrerfeedback und Bewertungen zu abgeschlossenen Touren.

### 📋 Spalten

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | `INTEGER` | Primärschlüssel | `PRIMARY KEY AUTOINCREMENT` |
| `tour_id` | `TEXT` | Tour-Identifikator | `NOT NULL` |
| `datum` | `TEXT` | Tour-Datum | `NOT NULL` |
| `kommentar` | `TEXT` | Fahrerkommentar | `NULL` erlaubt |
| `bewertung` | `INTEGER` | Bewertung (1-5 Sterne) | `NULL` erlaubt |
| `created_at` | `TEXT` | Erstellungsdatum | `DEFAULT (datetime('now'))` |

### 📝 Beispiel-Daten

```sql
INSERT INTO feedback (tour_id, datum, kommentar, bewertung) VALUES
('W-07:00', '2025-08-19', 'Alles gut gelaufen, keine Probleme', 5),
('W-09:00', '2025-08-19', 'Stau auf A4, 15 Min Verspätung', 3),
('PIR-14:00', '2025-08-19', 'Kunde nicht angetroffen', 2);
```

---

## 🗺️ Tabelle: `geo_cache` (AKTUELLES SCHEMA)

**Zweck:** Zwischenspeicher für Geocoding-Ergebnisse zur Performance-Optimierung. Speichert normalisierte Adressen mit Koordinaten.

### 📋 Spalten

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `address_norm` | `TEXT` | Normalisierte Adresse (normalisiert) | `PRIMARY KEY` |
| `lat` | `DOUBLE PRECISION` | Breitengrad | `NOT NULL` |
| `lon` | `DOUBLE PRECISION` | Längengrad | `NOT NULL` |
| `source` | `TEXT` | Quelle des Geocodings | `DEFAULT 'geocoded'` |
| `precision` | `TEXT` | Präzision des Geocodings | `NULL` erlaubt |
| `region_ok` | `INTEGER` | Ob Region korrekt ist (Sachsen) | `NULL` erlaubt |
| `first_seen` | `TIMESTAMP` | Erste Sichtung dieser Adresse | `DEFAULT CURRENT_TIMESTAMP` |
| `last_seen` | `TIMESTAMP` | Letzte Sichtung dieser Adresse | `DEFAULT CURRENT_TIMESTAMP` |
| `by_user` | `TEXT` | Benutzer der das Geocoding erstellt hat | `NULL` erlaubt |
| `updated_at` | `TIMESTAMP` | Letzte Aktualisierung | `DEFAULT CURRENT_TIMESTAMP` |

### 🔑 Indizes

```sql
CREATE INDEX IF NOT EXISTS idx_geo_cache_updated ON geo_cache(updated_at);
CREATE INDEX IF NOT EXISTS idx_geo_cache_source ON geo_cache(source);
CREATE INDEX IF NOT EXISTS idx_geo_cache_region_ok ON geo_cache(region_ok);
```

### 📝 Beispiel-Daten

```sql
INSERT INTO geo_cache (address_norm, lat, lon, source, first_seen, last_seen) VALUES
('stuttgarter str 33 01189 dresden', 51.0504, 13.7373, 'geocoded', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('hauptstr 1 01067 dresden', 51.0521, 13.7372, 'geoapify', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
('marktplatz 5 01067 dresden', 51.0519, 13.7375, 'synonym', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
```

---

## 📋 Tabelle: `manual_queue`

**Zweck:** Warteschlange für fehlgeschlagene Geocodes die manuell bearbeitet werden müssen.

### 📋 Spalten

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | `INTEGER` | Primärschlüssel | `PRIMARY KEY` |
| `address_norm` | `TEXT` | Normalisierte Adresse | `NOT NULL` |
| `raw_address` | `TEXT` | Original-Adresse aus CSV | `NULL` erlaubt |
| `reason` | `TEXT` | Grund für Fehlschlag | `NULL` erlaubt |
| `note` | `TEXT` | Manuelle Notizen | `NULL` erlaubt |
| `status` | `TEXT` | Status (`open`, `closed`, `resolved`) | `DEFAULT 'open'` |
| `created_at` | `TIMESTAMP` | Erstellungsdatum | `DEFAULT CURRENT_TIMESTAMP` |

### 🔑 Indizes

```sql
CREATE INDEX IF NOT EXISTS ix_manual_queue_created ON manual_queue(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_manual_queue_address ON manual_queue(address_norm);
CREATE INDEX IF NOT EXISTS ix_manual_queue_status ON manual_queue(status);
```

### 📝 Beispiel-Daten

```sql
INSERT INTO manual_queue (address_norm, raw_address, reason, status) VALUES
('unbekannte adresse 123', 'Unbekannte Adresse 123', 'Adresse nicht gefunden', 'open'),
('fehlende plz', 'Hauptstraße Dresden', 'PLZ fehlt', 'open');
```

---

## ❌ Tabelle: `geo_fail`

**Zweck:** Speichert fehlgeschlagene Geocoding-Versuche für Analyse und Debugging.

### 📋 Spalten

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `id` | `INTEGER` | Primärschlüssel | `PRIMARY KEY AUTOINCREMENT` |
| `address_norm` | `TEXT` | Normalisierte Adresse | `NOT NULL` |
| `raw_address` | `TEXT` | Original-Adresse | `NULL` erlaubt |
| `reason` | `TEXT` | Grund für Fehlschlag | `NULL` erlaubt |
| `created_at` | `TIMESTAMP` | Erstellungsdatum | `DEFAULT CURRENT_TIMESTAMP` |
| `updated_at` | `TIMESTAMP` | Letzte Aktualisierung | `DEFAULT CURRENT_TIMESTAMP` |

### 🔑 Indizes

```sql
CREATE INDEX IF NOT EXISTS idx_geo_fail_address ON geo_fail(address_norm);
CREATE INDEX IF NOT EXISTS idx_geo_fail_created ON geo_fail(created_at DESC);
```

### 📝 Beispiel-Daten

```sql
INSERT INTO geo_fail (address_norm, raw_address, reason) VALUES
('invalid address', 'Invalid Address 999', 'Keine Ergebnisse von Geoapify'),
('outside region', 'Berlin, Hauptstraße 1', 'Außerhalb Sachsens');
```

---

## 📮 Tabelle: `postal_code_cache`

**Zweck:** Zwischenspeicher für Postleitzahl-zu-Stadt-Zuordnungen.

### 📋 Spalten

| Spalte | Typ | Beschreibung | Constraints |
|--------|-----|--------------|-------------|
| `postal_code` | `TEXT` | Postleitzahl | `PRIMARY KEY` |
| `city` | `TEXT` | Stadtname | `NOT NULL` |
| `updated_at` | `TEXT` | Letzte Aktualisierung | `DEFAULT (datetime('now'))` |

### 📝 Beispiel-Daten

```sql
INSERT INTO postal_code_cache (postal_code, city) VALUES
('01189', 'Dresden'),
('01067', 'Dresden'),
('01069', 'Dresden'),
('01097', 'Dresden');
```

---

## 🔗 Beziehungen zwischen Tabellen

```mermaid
erDiagram
    geo_cache ||--o{ manual_queue : "address_norm"
    geo_cache ||--o{ geo_fail : "address_norm"
    kunden ||--o{ touren : "kunden_ids (JSON)"
    touren ||--o{ feedback : "tour_id"
    postal_code_cache ||--o{ kunden : "PLZ"
```

### 📋 Beziehungsdetails

1. **geo_cache → manual_queue**: Fehlgeschlagene Geocodes landen in der Manual Queue
2. **geo_cache → geo_fail**: Fehlgeschlagene Versuche werden in geo_fail gespeichert
3. **kunden → touren**: Eine Tour kann mehrere Kunden enthalten (über JSON-Array in `kunden_ids`)
4. **touren → feedback**: Eine Tour kann mehrere Feedback-Einträge haben
5. **postal_code_cache → kunden**: PLZ werden für Validierung gecacht

---

## 🚀 Performance-Optimierungen

### 🔍 Wichtige Indizes

```sql
-- Kunden-Suche nach Name/Adresse
CREATE INDEX idx_kunden_name ON kunden(name);
CREATE INDEX idx_kunden_adresse ON kunden(adresse);

-- Touren-Suche nach Datum und Tour-ID
CREATE INDEX idx_touren_datum ON touren(datum);
CREATE INDEX idx_touren_tour_id ON touren(tour_id);

-- Feedback-Suche nach Tour
CREATE INDEX idx_feedback_tour_id ON feedback(tour_id);
CREATE INDEX idx_feedback_datum ON feedback(datum);
```

### ⚡ Query-Optimierungen

```sql
-- Häufige Abfragen
SELECT * FROM kunden WHERE name LIKE '%Mustermann%';
SELECT * FROM touren WHERE datum = '2025-08-19';
SELECT * FROM touren WHERE tour_id LIKE 'W-%';
SELECT COUNT(*) FROM kunden WHERE lat IS NOT NULL;
```

---

## 🔧 Wartung und Backup

### 📦 Backup-Strategie

```bash
# Vollständiges Backup
sqlite3 traffic.db ".backup backup_$(date +%Y%m%d_%H%M%S).db"

# Nur Schema
sqlite3 traffic.db ".schema" > schema_backup.sql

# Nur Daten
sqlite3 traffic.db ".dump" > data_backup.sql
```

### 🧹 Cleanup-Operationen

```sql
-- Alte Geo-Cache-Einträge löschen (älter als 30 Tage)
DELETE FROM geo_cache WHERE updated_at < datetime('now', '-30 days');

-- Alte Geo-Fail-Einträge löschen (älter als 90 Tage)
DELETE FROM geo_fail WHERE created_at < datetime('now', '-90 days');

-- Geschlossene Manual-Queue-Einträge löschen (älter als 30 Tage)
DELETE FROM manual_queue WHERE status = 'closed' AND created_at < datetime('now', '-30 days');

-- Alte Feedback-Einträge löschen (älter als 1 Jahr)
DELETE FROM feedback WHERE created_at < datetime('now', '-1 year');

-- VACUUM für Speicher-Optimierung
VACUUM;
```

---

## 📊 Statistiken und Monitoring

### 📈 Wichtige Metriken

```sql
-- Anzahl Kunden mit/ohne Koordinaten
SELECT 
    COUNT(*) as total_kunden,
    COUNT(lat) as mit_koordinaten,
    COUNT(*) - COUNT(lat) as ohne_koordinaten
FROM kunden;

-- Touren pro Tag
SELECT 
    datum,
    COUNT(*) as anzahl_touren,
    SUM(JSON_ARRAY_LENGTH(kunden_ids)) as total_kunden
FROM touren 
GROUP BY datum 
ORDER BY datum DESC;

-- Durchschnittliche Tour-Dauer
SELECT 
    tour_id,
    AVG(dauer_min) as avg_dauer_min,
    AVG(distanz_km) as avg_distanz_km
FROM touren 
WHERE dauer_min IS NOT NULL 
GROUP BY tour_id;
```

---

## 🛠️ Entwicklung und Testing

### 🧪 Test-Daten generieren

```sql
-- Test-Kunden einfügen
INSERT INTO kunden (name, adresse, lat, lon) 
SELECT 
    'Test-Kunde ' || row_number() OVER (ORDER BY random()),
    'Teststr. ' || (row_number() OVER (ORDER BY random()) % 100) || ', 01067 Dresden',
    51.05 + (random() - 0.5) * 0.1,
    13.73 + (random() - 0.5) * 0.1
FROM (SELECT 1 UNION SELECT 2 UNION SELECT 3 UNION SELECT 4 UNION SELECT 5);
```

### 🔍 Schema-Validierung

```sql
-- Tabellen-Existenz prüfen
SELECT name FROM sqlite_master WHERE type='table';

-- Spalten-Informationen
PRAGMA table_info(geo_cache);
PRAGMA table_info(manual_queue);
PRAGMA table_info(geo_fail);
PRAGMA table_info(kunden);
PRAGMA table_info(touren);
PRAGMA table_info(feedback);
PRAGMA table_info(postal_code_cache);
```

---

## 📚 Weitere Dokumentation

- [API-Dokumentation](API_DOKUMENTATION.md)
- [Installationsanleitung](INSTALLATION_GUIDE.md)
- [Multi-Tour Generator](MULTI_TOUR_GENERATOR_README.md)
- [Technische Dokumentation](TECHNISCHE_DOKUMENTATION.md)

---

## 🔄 Changelog

| Version | Datum | Änderungen |
|---------|-------|------------|
| 1.0.0 | 2025-08-19 | Initiale Schema-Definition |
| 1.1.0 | 2025-08-19 | Geocache-Tabelle hinzugefügt |
| 1.2.0 | 2025-08-19 | PLZ-Cache-Tabelle hinzugefügt |
| 2.0.0 | 2025-11-03 | Schema aktualisiert: `geo_cache` mit allen Spalten, `manual_queue` und `geo_fail` hinzugefügt |

---

*Letzte Aktualisierung: 03. November 2025*
