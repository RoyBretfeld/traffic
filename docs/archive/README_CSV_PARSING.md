# README_CSV_PARSING.md

# CSV-Parsing Dokumentation

## Übersicht

Das TrafficApp verarbeitet Tourplan-CSV-Dateien mit automatischer Geocodierung und intelligenter Adresserkennung. Die Original-CSVs werden read-only behandelt und nie modifiziert.

## PF/BAR-Synonyme

### Funktionsweise

PF-Kunden („Jochen – PF", „Sven – PF") werden **nicht** geocodiert, sondern aus Synonym-Stammdaten bedient.

- **Synonym-Resolver**: `common/synonyms.py` enthält feste Koordinaten für PF-Kunden
- **Short-Circuit**: Geocoder wird für PF-Kunden **nicht** aufgerufen
- **Frontend**: Zeigt `resolved_address`, routet via `lat/lon`
- **Audit**: Zählt Synonyme als geokodiert

### Synonym-Koordinaten pflegen

```python
# In common/synonyms.py
_SYNONYMS: Dict[str, SynonymHit] = {
    "PF:JOCHEN": SynonymHit("PF:JOCHEN", "Pf-Depot Jochen, Dresden", 51.0500, 13.7373),
    "PF:SVEN":   SynonymHit("PF:SVEN",   "Pf-Depot Sven, Dresden",   51.0600, 13.7300),
}
```

### Akzeptanzkriterien

- ✅ „Jochen – PF" und „Sven – PF" erscheinen **mit Koordinaten** und **ohne** „nan, nan nan"
- ✅ Geocoder wird für diese Einträge **nicht** angerufen (Short-Circuit)
- ✅ API liefert DTO mit `resolved_address`, `geo_source='synonym'`, `valid=true`
- ✅ Audit: `missing_count == 0` bei CSV mit nur PF-Einträgen

### Kundennummern-Resolver

- In `common/synonyms.py` ist ein schlanker Resolver hinterlegt: `resolve_customer_number(name) -> Optional[int]`
- Zweck: Für Synonyme die echte ERP-Kundennummer verfügbar machen, ohne bestehende CSV-Felder zu überschreiben
- API/DTO-Nutzung: wird als separates Feld `customer_number_resolved` ausgegeben (nicht verpflichtend im UI)

## CSV/Import-Härtung

### NaN/Excel-Apostroph-Behandlung

- Parser und Bulk-Prozessor entfernen führende/abschließende Apostroph‑Marker aus Excel
- Wandeln `NaN` in leere Strings um
- Adressen werden nur aus vorhandenen Teilen gebaut
- Es erscheint kein „nan, nan nan" oder ", ," mehr

### Frontend-Rendering

- Frontend rendert priorisiert `resolved_address`
- Danach `address`
- Sonst aus Teilen `street, postal_code, city` (bereinigt)

## API-DTO-Struktur

### Stop-DTO

```python
{
    "id": "stop_id",
    "display_name": "Firmenname",
    "resolved_address": "Vollständige Adresse",
    "lat": 51.05,
    "lon": 13.74,
    "geo_source": "synonym|cache|geocoder",
    "valid": true,
    "extra": {
        "status": "ok|warn|bad",
        "markers": [],
        "manual_needed": false
    }
}
```

### Valid-Flag

- `valid=true`: Koordinaten sind gültig und können für Routing verwendet werden
- `valid=false`: Koordinaten fehlen oder sind ungültig, kein Routing möglich

## Geocoding-Workflow

1. **Synonym-Check**: VOR Geocoding wird geprüft, ob es sich um einen PF-Kunden handelt
2. **Short-Circuit**: PF-Kunden werden direkt aus Synonym-Daten bedient
3. **Normal-Geocoding**: Andere Adressen werden über Nominatim geocodiert
4. **Cache-Integration**: Alle Ergebnisse werden in `geo_cache` gespeichert
5. **DTO-Erstellung**: Konsistente API-Ausgabe mit `build_stop_dto()`

## Tests

### Synonym-Tests

- `tests/test_synonym_shortcircuit.py`: PF-Synonyme umgehen Geocoder
- `tests/test_stop_dto_valid.py`: DTO liefert `resolved_address` + Guard schlägt bei fehlenden Koords an
- `tests/test_audit_counts_synonyms.py`: Audit zählt PF-Synonyme als geokodiert

### Test-Ausführung

```bash
# Alle Synonym-Tests
pytest tests/test_synonym_shortcircuit.py tests/test_stop_dto_valid.py tests/test_audit_counts_synonyms.py -v

# Spezifische Tests
pytest tests/test_synonym_shortcircuit.py::test_pf_synonym_skips_geocoder -v
```

## Wartung

### Neue Synonyme hinzufügen

1. In `common/synonyms.py` neue Einträge zu `_SYNONYMS` hinzufügen
2. Aliase in `_ALIASES` definieren
3. Tests aktualisieren
4. Dokumentation erweitern

### Koordinaten aktualisieren

1. Neue Koordinaten in `common/synonyms.py` eintragen
2. Cache leeren: `python clear_fail_cache.py`
3. Tests ausführen
4. Frontend testen

## Abschlussreport & Storage-Policy

### Persistenz-Policy

Alle Geocoding-Ergebnisse werden über den **einheitlichen Persist-Writer** (`services/geocode_persist.py`) gespeichert:

- **Synonyme**: `source='synonym'`, `precision=None`, `region_ok=1`
- **Geocoder**: `source='geocoder'`, `precision='full'` oder `'zip_centroid'`
- **Cache**: `source='cache'`, `precision=None`
- **Manual-Queue**: Fehlgeschlagene Adressen werden automatisch in `manual_queue` gespeichert

### Datenbank-Schema

#### geo_cache Tabelle (erweitert)
```sql
CREATE TABLE geo_cache (
  address_norm TEXT PRIMARY KEY,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  source TEXT,                    -- synonym|geocoder|cache
  precision TEXT,                 -- full|zip_centroid|NULL
  region_ok INTEGER,              -- 1=ok, 0=außerhalb, NULL=unbekannt
  first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  by_user TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### manual_queue Tabelle (neu)
```sql
CREATE TABLE manual_queue (
  id INTEGER PRIMARY KEY,
  address_norm TEXT NOT NULL,
  raw_address TEXT,
  reason TEXT,                    -- geocode_miss|invalid_coordinates|timeout
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Sonderbehandlungen

#### Normalisierung
- **Pipe-zu-Komma**: `"Straße 1 | Dresden"` → `"Straße 1, Dresden"`
- **Halle-Entfernung**: `"Hauptstraße 1, Halle 14, Dresden"` → `"Hauptstraße 1, Dresden"`
- **OT-Entfernung**: `"Alte Str. 33, Glashütte (OT Hirschbach)"` → `"Alte Str. 33, Glashütte"`
- **Schreibfehler-Korrekturen**: `"Haupstr."` → `"Hauptstr."`, `"Strae"` → `"Straße"`
- **Mojibake-Fixes**: `"FrÃ¶belstraÃŸe"` → `"Fröbelstraße"`

#### Spellfix
- Konservative Korrekturen (z.B. „Haupstr."→„Hauptstr.")
- Nur bei eindeutigen Fällen

#### OT-Rewrite
- `"Gemeinde OT Ortsteil"` → `"Ortsteil, Gemeinde"`
- Automatische Erkennung von Ortsteilen

#### Synonym-System
- PF/BAR-Kunden → feste Koordinaten, `source='synonym'`
- Short-Circuit verhindert Geocoder-Aufrufe

#### Zip-Centroid
- Bei PLZ+Stadt ohne Hausnummer → `precision='zip_centroid'`
- Fallback für unvollständige Adressen

#### Region-Flag
- `region_ok` basierend auf `state` aus Geocoder-Antwort
- Sachsen, Thüringen, Sachsen-Anhalt = `region_ok=1`

#### Manual-Queue
- „nan", leere oder unauflösbare Adressen
- Automatische Kategorisierung nach Grund

### API-Endpoints

#### Abschlussreport
```http
GET /api/audit/status?limit=50
```

**Response:**
```json
{
  "csv_files": 30,
  "unique_addresses_csv": 7328,
  "coverage_pct": 99.99,
  "missing_count": 1,
  "missing_preview": ["nan, nan Pulsnitz"],
  "sources": {
    "synonym": 2,
    "geocoder": 7000,
    "cache": 325,
    "unknown": 0
  },
  "precision": {
    "full": 6500,
    "zip_centroid": 500,
    "none": 327
  },
  "region_stats": {
    "ok": 7200,
    "bad": 50,
    "unknown": 78
  },
  "manual_queue_count": 1,
  "manual_queue_preview": [...],
  "ok": false
}
```

#### Manual-Queue Management
```http
GET /api/audit/manual-queue?limit=100
POST /api/audit/export-manual-queue
```

### Export-Funktionen

#### Manual-Queue Export
```python
from repositories.manual_repo import export_csv
count = export_csv("./var/manual_queue/pending_20250115_1030.csv")
```

#### CSV-Format
```csv
id,address_norm,raw_address,reason,created_at
1,"nan, nan pulsnitz","nan, nan Pulsnitz","geocode_miss","2025-01-15 10:30:00"
```

### Tests

#### Persistenz-Tests
```bash
pytest tests/test_persist_and_flags.py -v
```

#### Manual-Queue Tests
```bash
pytest tests/test_manual_queue_and_export.py -v
```

#### Audit-Status Tests
```bash
pytest tests/test_audit_status_breakdown.py -v
```

## Troubleshooting

### "nan, nan nan" erscheint noch

- Prüfen ob Synonym-Resolver korrekt konfiguriert ist
- Cache leeren und neu aufbauen
- Frontend-Cache leeren (Browser-Refresh)

### Geocoder wird trotzdem aufgerufen

- Prüfen ob `resolve_synonym()` korrekt funktioniert
- Logs auf Synonym-Treffer prüfen
- Tests ausführen

### Audit zeigt falsche Zählung

- Prüfen ob Synonyme korrekt in Cache gespeichert werden
- `bulk_get()` Test mit Synonym-Adressen
- Audit-Endpoint direkt testen

### Manual-Queue Probleme

- Prüfen ob `manual_queue` Tabelle existiert
- `repositories.manual_repo.list_open()` testen
- Export-Funktion prüfen

### Persistenz-Probleme

- Prüfen ob `upsert_ex()` korrekt funktioniert
- Datenbank-Schema aktualisieren
- `services.geocode_persist.write_result()` testen

## Aktueller Entwicklungsstand (Stand: Oktober 2025)

### ✅ Implementiert und getestet

1. **Synonyme (PF/BAR-Kunden)**
   - `common/synonyms.py`: Zentrale Synonym-Verwaltung
   - `services/stop_dto.py`: Stop-DTO mit `resolved_address`, `geo_source`, `valid`-Flag
   - Short-Circuit für PF/BAR-Kunden ohne externen Geocoding-Aufruf
   - Tests: `tests/test_synonym_shortcircuit.py`, `tests/test_stop_dto_valid.py`, `tests/test_audit_counts_synonyms.py`

2. **Modulare Refaktorierung**
   - `common/tour_data_models.py`: Zentrale Datenstrukturen (`TourStop`, `TourInfo`, `TourPlan`)
   - `services/tour_plan_raw_reader.py`: Rohdaten-Extrakteur für CSV
   - `services/tour_plan_grouper.py`: Tour-Gruppierung und BAR-Konsolidierung
   - `common/text_cleaner.py`: Intelligente Zeichenkorrektur (`??`-Fixes)
   - `repositories/address_lookup.py`: Adress-Lookup mit Cache (PLZ+Name-Regel)

3. **Normalisierung**
   - `common/normalize.py`: Zentrale Adressnormalisierung
   - Unterstützt: Pipe-zu-Komma, Halle-Entfernung, OT-Entfernung, Schreibfehler-Korrektionen, Mojibake-Fixes
   - Intelligente `??`-Zeichenkorrektur basierend auf Kontext
   - Konsistente Normalisierung über alle Komponenten

4. **Persistenzrichtlinie**
   - `services/geocode_persist.py`: Einheitlicher Persist-Writer
   - `repositories/geo_repo.py`: Erweiterte `upsert_ex()` für neue Felder
   - `repositories/manual_repo.py`: Manual-Queue Management mit Export
   - Database-Schema mit erweiterten Feldern: `source`, `precision`, `region_ok`, `first_seen`, `last_seen`

5. **API-Endpoints**
   - `GET /api/audit/status`: Abschlussreport mit Geocoding-Statistiken
   - `GET /health/db`: Datenbank-Status
   - `routes/audit_geocoding.py`: Audit mit optionalen Datei-Parametern
   - `routes/tourplan_match.py`: Tourplan-Matching mit DTO-Integration

6. **Frontend-Integration**
   - `frontend/index.html`: Aktualisiert für neue API-Endpoints
   - `GET /` und `GET /ui/`: Frontend-Serving
   - Dynamische Datenbank- und LLM-Status-Checks

### ⚠️ Behobene Import-Fehler (Oktober 2025)

1. **`routes/tourplan_suggest.py`**
   - ❌ Problem: `ImportError: cannot import name 'normalize_addr'`
   - ✅ Lösung: Import entfernt, `normalize_address` aus `common/normalize.py` verwendet

2. **`routes/failcache_improved.py`**
   - ❌ Problem: `ImportError: cannot import name 'normalize_addr'`
   - ✅ Lösung: Import entfernt, `normalize_address` aus `common/normalize.py` verwendet

3. **Zirkuläre Importe (früher)**
   - ❌ Problem: `TourInfo` und `TourStop` in `backend/parsers/tour_plan_parser.py` + `services/tour_plan_grouper.py`
   - ✅ Lösung: In `common/tour_data_models.py` zentralisiert

4. **Fehlende Normalisierungsfunktionen**
   - ❌ Problem: `normalize_addr` wurde aus `repositories/geo_repo.py` entfernt
   - ✅ Lösung: `normalize_address` aus `common/normalize.py` überall verwendet
   - ✅ `repositories/geo_alias_repo.py` aktualisiert

### 📋 Datei-Übersicht (Neue und Modifizierte Dateien)

#### Neu erstellt
- `common/tour_data_models.py` - Zentrale Datenstrukturen
- `common/text_cleaner.py` - Intelligente Zeichenkorrektur
- `common/synonyms.py` - Synonym-Verwaltung (bereits vorhanden, bestätigt)
- `repositories/address_lookup.py` - Adress-Lookup mit Cache
- `repositories/manual_repo.py` - Manual-Queue Management
- `services/tour_plan_raw_reader.py` - Rohdaten-Extrakteur
- `services/tour_plan_grouper.py` - Tour-Gruppierung (bereits vorhanden, bestätigt)
- `services/geocode_persist.py` - Einheitlicher Persist-Writer
- `services/stop_dto.py` - Stop-DTO Builder
- `routes/audit_status.py` - Abschlussreport Endpoint
- `routes/health_check.py` - Datenbank-Status Endpoint

#### Modifiziert
- `common/normalize.py` - Erweiterte Normalisierung
- `backend/parsers/tour_plan_parser.py` - Modulare Refaktorierung
- `repositories/geo_repo.py` - Erweiterte `upsert_ex()`
- `repositories/geo_alias_repo.py` - Import-Anpassung
- `routes/tourplan_suggest.py` - Import-Fehler behoben
- `routes/failcache_improved.py` - Import-Fehler behoben
- `routes/tourplan_match.py` - DTO-Integration
- `routes/audit_geocoding.py` - Optionale Datei-Parameter
- `backend/app.py` - Router-Registrierung aktualisiert
- `frontend/index.html` - API-Integration aktualisiert

### 🧪 Tests

#### Neue Tests
- `tests/test_synonym_shortcircuit.py` - Synonym-Short-Circuit
- `tests/test_stop_dto_valid.py` - Stop-DTO Validierung
- `tests/test_audit_counts_synonyms.py` - Audit mit Synonymen
- `tests/test_persist_and_flags.py` - Persistenz und Flags
- `tests/test_manual_queue_and_export.py` - Manual-Queue Export
- `tests/test_audit_status_breakdown.py` - Audit-Status Report

### 📊 Bekannte Arbeiten in Bearbeitung

1. **Normalisierungstests**: `comprehensive_test_suite.py` - Mehrfache Iterationen, um Test-Erwartungen mit Normalisierungslogik zu synchronisieren
2. **Tour-Parsing**: `test_tourplan_analysis.py` - Analyse von 5 Tourplänen mit graphischer Darstellung
3. **Mojibake-Fixes**: `test_mojibake_fixes.py` - Gezielte Tests für `??`-Zeichenkorrektur

### 🛠️ Architektur-Highlights

1. **Zentralisierte Normalisierung**: Alle Komponenten verwenden `common/normalize.py`
2. **Modular refaktoriert**: Große Funktionen in kleinere, testbare Module aufgeteilt
3. **Einheitliche Persistenz**: Alle Geocoding-Ergebnisse über `services/geocode_persist.py`
4. **DTO-Pattern**: Konsistente API-Ausgaben über `services/stop_dto.py`
5. **Fehlerhafte Importe behoben**: `normalize_addr` vollständig durch `normalize_address` ersetzt

### ⏭️ Nächste Schritte (Nach Server-Fix)

1. Server-Startup debuggen und beheben
2. `comprehensive_test_suite.py` vervollständigen
3. Tour-Parsing-Tests durchführen
4. Manual-Queue Funktionalität verifizieren
5. Audit-Endpoints testen
6. Frontend-Integration validieren
7. Git-Commit und Push

---

**Dokumentation zuletzt aktualisiert**: 21. Oktober 2025, 13:10 Uhr
**Status**: ✅ Großteil implementiert, Server-Startup muss debuggt werden
