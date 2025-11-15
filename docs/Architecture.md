# FAMO TrafficApp - Konsolidierte Architektur-Dokumentation

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-13  
**Status:** Konsolidiert aus Architecture.md, ARCHITEKTUR_KOMPLETT.md, TECHNICAL_IMPLEMENTATION.md, TECHNISCHE_DOKUMENTATION.md

---

## Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [System-Architektur](#system-architektur)
3. [Projekt-Statistiken](#projekt-statistiken)
4. [Haupt-Module](#haupt-module)
5. [Datenbank-Schema](#datenbank-schema)
6. [Geocoding-Provider](#geocoding-provider)
7. [KI-Integration](#ki-integration)
8. [Frontend-Komponenten](#frontend-komponenten)
9. [Technologie-Stack](#technologie-stack)
10. [Sicherheit & Best Practices](#sicherheit--best-practices)
11. [Deployment](#deployment)

---

## Übersicht

Die FAMO TrafficApp ist eine KI-basierte Route-Optimierungsanwendung für Tourenplanung und Geocoding. Das System nutzt eine modulare Architektur mit FastAPI-Backend, SQLite-Datenbank und modernem Frontend.

**Wichtige Änderungen (2025-01-10):**
- ✅ Pydantic V2 Kompatibilität hergestellt
- ✅ Error Envelope & Trace-ID Middlewares implementiert
- ✅ Deterministischer Routing-Optimizer integriert
- ✅ API-Kompatibilität verbessert (`fill_missing`, `StopModel`)

---

## System-Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Vanilla JS/HTML)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  index.html (Hauptseite)                                │   │
│  │  - Karte (Leaflet.js)                                    │   │
│  │  - Tourübersicht                                         │   │
│  │  - Workflow-Box                                          │   │
│  │  - Statistik-Box                                         │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Weitere HTML-Seiten                                     │   │
│  │  - tourplan-management.html                              │   │
│  │  - test-dashboard.html                                   │   │
│  │  - multi-tour-generator.html                             │   │
│  │  - coordinate-verify.html                                │   │
│  │  - ai-test.html                                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  JavaScript-Module                                       │   │
│  │  - address-helper.js                                     │   │
│  │  - ai_tour_classifier.js                                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP/REST
┌────────────────────────────▼────────────────────────────────────┐
│              FastAPI Backend (Python 3.11+)                       │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API-Routen (routes/)                                    │   │
│  │  - workflow_api.py (Haupt-Workflow)                     │   │
│  │  - tourplan_match.py (Adress-Matching)                   │   │
│  │  - upload_csv.py (CSV-Upload)                            │   │
│  │  - engine_api.py (Route-Engine)                           │   │
│  │  - health_check.py (Health-Checks)                       │   │
│  │  - backup_api.py (Backup-Management)                     │   │
│  │  - audit_*.py (Audit-Endpoints)                          │   │
│  │  - tourplan_*.py (Tourplan-Management)                    │   │
│  │  - failcache_*.py (Fail-Cache-Management)               │   │
│  │  - manual_api.py (Manuelle Korrekturen)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Backend-Services (backend/services/)                    │   │
│  │  - adaptive_pattern_engine.py (Pattern-Learning)         │   │
│  │  - address_analyzer.py (Adress-Analyse)                   │   │
│  │  - address_corrections.py (Adress-Korrekturen)           │   │
│  │  - address_corrector.py (Korrektur-Logik)                │   │
│  │  - address_mapper.py (Adress-Mapping)                    │   │
│  │  - address_validator.py (Adress-Validierung)             │   │
│  │  - ai_config.py (AI-Konfiguration)                       │   │
│  │  - ai_optimizer.py (AI-Optimierung)                      │   │
│  │  - geocode.py (Geocoding)                                 │   │
│  │  - multi_tour_generator.py (Multi-Tour-Generierung)      │   │
│  │  - optimization_rules.py (Optimierungs-Regeln)           │   │
│  │  - tour_consolidator.py (Tour-Konsolidierung)            │   │
│  │  - tour_manager.py (Tour-Management)                      │   │
│  │  - workflow_orchestrator.py (Workflow-Orchestrierung)   │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Services (services/)                                    │   │
│  │  - sector_planner.py (Dresden-Quadranten-Planung)       │   │
│  │  - pirna_clusterer.py (PIRNA-Clustering)                │   │
│  │  - osrm_client.py (OSRM-Routing-Client)                 │   │
│  │  - llm_optimizer.py (LLM-Routenoptimierung)              │   │
│  │  - llm_monitoring.py (LLM-Monitoring)                   │   │
│  │  - workflow_engine.py (Workflow-Engine)                   │   │
│  │  - geocode_fill.py (Async Geocoding)                     │   │
│  │  - fuzzy_suggest.py (Fuzzy-Suggestions)                  │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Repositories (repositories/)                             │   │
│  │  - geo_repo.py (Geocoding-Repository)                    │   │
│  │  - geo_fail_repo.py (Fail-Cache-Repository)              │   │
│  │  - geo_alias_repo.py (Alias-Repository)                 │   │
│  │  - manual_repo.py (Manual-Queue-Repository)             │   │
│  │  - address_lookup.py (Adress-Lookup)                    │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Parser (backend/parsers/)                                │   │
│  │  - tour_plan_parser.py (Tourplan-Parser)                 │   │
│  │  - excel_parser.py (Excel-Parser)                        │   │
│  │  - pdf_parser.py (PDF-Parser)                            │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Datenbank-Layer (db/)                                   │   │
│  │  - core.py (DB-Connection)                                │   │
│  │  - schema.py (Schema-Definition)                          │   │
│  │  - migrate_schema.py (Schema-Migrationen)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│           SQLite Datenbanken (data/)                            │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  traffic.db (Haupt-Datenbank)                             │   │
│  │  - geo_cache (Geocoding-Cache)                           │   │
│  │  - address_synonyms (Adress-Synonyme)                    │   │
│  │  - manual_queue (Manuelle Korrekturen)                   │   │
│  │  - geo_fail (Geocoding-Fehler)                           │   │
│  │  - kunden (Kundenstammdaten, optional)                   │   │
│  │  - touren (Touren-Daten, optional)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  customers.db (Kunden-Datenbank)                         │   │
│  │  - customers (Kundenstammdaten)                          │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  address_corrections.sqlite3 (Adress-Korrekturen)         │   │
│  │  - address_corrections (Korrektur-Daten)                 │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  llm_monitoring.db (LLM-Monitoring)                       │   │
│  │  - llm_requests (LLM-Request-Logs)                       │   │
│  │  - llm_responses (LLM-Response-Logs)                     │   │
│  └──────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

---

## Projekt-Statistiken

### Dateien-Übersicht
- **Gesamt:** ~1.346 Dateien
- **Python-Dateien:** ~423
- **Markdown-Dateien:** ~143
- **JSON-Dateien:** ~309
- **CSV-Dateien:** ~207
- **HTML-Dateien:** ~12
- **JavaScript-Dateien:** ~2 (in frontend/)
- **PowerShell-Scripts:** ~14

### API-Endpoints
- **Route-Dateien:** ~32
- **Geschätzte Endpoints:** ~147
- **Registrierte Router:** ~29 (in `backend/app.py`)

### Module & Services
- **Backend-Services:** ~22 (in `backend/services/`)
- **Services (Root):** ~19 (in `services/`)
- **Repositories:** ~6 (in `repositories/`)
- **Parsers:** ~4 (in `backend/parsers/`)

---

## Haupt-Module

### 1. Workflow-Engine (`routes/workflow_api.py`)

**Verantwortlich:** CSV-Upload, Parsing, Geocoding, Route-Optimierung

**Endpoints:**
- `POST /api/workflow/upload` - CSV-Datei hochladen und verarbeiten
- `POST /api/workflow/complete` - Kompletter Workflow mit Tourplaene-Dateien
- `GET /api/workflow/geocoding-progress/{session_id}` - Live-Geocoding-Status
- `GET /api/workflow/status` - System-Status mit LLM-Metriken
- `POST /api/tour/optimize` - Tour-Optimierung mit LLM oder Nearest-Neighbor
- `POST /api/tour/route-details` - Route-Details mit OSRM-Geometrie

**Datenfluss:**
1. CSV-Upload → Staging
2. Parser erkennt Format (TEHA vs. Standard)
3. DB-First Geocoding (Cache → Geoapify → Speichern)
4. LLM-basierte Route-Optimierung
5. Response mit optimierten Touren

**DB-First Strategie:**
```python
# 1. Prüfe DB-Cache
cached = geo_get(address)
if cached:
    return cached["lat"], cached["lon"]

# 2. Nicht gefunden → Geocode mit Geoapify
result = geocode_address(address)

# 3. Speichere in DB
geo_upsert(address, lat, lon, source="geoapify")

# 4. Beim nächsten Mal: Direkt aus DB (Schritt 1)
```

### 2. Engine API (`routes/engine_api.py`)

**Verantwortlich:** Betriebsordnung-konforme Touren-Engine (UID-basiert)

**Endpoints:**
- `POST /engine/tours/ingest` - Akzeptiert Erkennungsformat, erzeugt UIDs
- `GET /engine/tours/{tour_uid}/status` - Status abfragen
- `POST /engine/tours/optimize` - Optimiert nur vollständige Touren
- `POST /engine/tours/split` - Subtourenbildung mit OSRM Table
- `POST /engine/tours/sectorize` - Sektorisierung (N/O/S/W) für W-Touren
- `POST /engine/tours/plan_by_sector` - Planung mit Zeitbox (07:00-09:00)

**Features:**
- UID-basierte Touren-Identifikation
- OSRM-First Strategie für Distanzberechnung
- Zeitbox-Validierung (65 Min ohne Rückfahrt, 90 Min mit Rückfahrt)

### 3. Sektor-Planer (`services/sector_planner.py`)

**Verantwortlich:** Dresden-Quadranten-basierte Routenplanung für W-Touren

**Features:**
- Bearing-Berechnung (Azimut 0-360°)
- Sektorzuordnung (N/O/S/W, deterministisch)
- Greedy-Planung pro Sektor
- Zeitbox-Validierung (07:00 Start, 09:00 Rückkehr)
- OSRM-First Strategie mit Fallback

### 4. PIRNA-Clusterer (`services/pirna_clusterer.py`)

**Verantwortlich:** Clustering-basierte Routenplanung für PIRNA-Touren

**Features:**
- K-Means-Clustering basierend auf Koordinaten
- Automatische Cluster-Größen-Anpassung
- Zeitbasierte Validierung

### 5. OSRM-Client (`services/osrm_client.py`)

**Verantwortlich:** OSRM-Routing-Integration für straßenbasierte Distanzen

**Features:**
- Route API für Punkt-zu-Punkt-Routen
- Table API für Distanz-Matrizen
- Circuit Breaker für Fehlerbehandlung
- Lazy-Initialisierung (nach config.env Laden)

### 6. Multi-Tour Generator (`backend/services/multi_tour_generator.py`)

**Verantwortlich:** KI-basierte Aufteilung großer Touren in optimale Untertouren

**Features:**
- Geografisches Clustering mit KI
- Zeit-Constraints (60min + 2min/Kunde + 5min Puffer)
- Depot-Integration (FAMO Dresden)
- Automatische Validierung

### 7. Backup-System (`scripts/db_backup.py` + `routes/backup_api.py`)

**Verantwortlich:** Automatische und manuelle Datenbank-Backups

**Features:**
- Tägliche automatische Backups (16:00 Uhr)
- SQLite-native Backup-Methode (sicher auch bei WAL-Mode)
- 30-Tage Retention
- Windows Task Scheduler Integration

---

## Datenbank-Schema

**Vollständiges Schema:** Siehe `docs/DATABASE_SCHEMA.md`

### geo_cache (AKTUELLES SCHEMA)
```sql
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
```

### manual_queue
```sql
CREATE TABLE IF NOT EXISTS manual_queue (
    id INTEGER PRIMARY KEY,
    address_norm TEXT NOT NULL,
    raw_address TEXT,
    reason TEXT,
    note TEXT,
    status TEXT DEFAULT 'open',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### geo_fail
```sql
CREATE TABLE IF NOT EXISTS geo_fail (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    address_norm TEXT NOT NULL,
    raw_address TEXT,
    reason TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    next_attempt TEXT DEFAULT NULL
);
```

---

## Geocoding-Provider

### Priorität
1. **Geoapify** (Primär) - API-Key: `32abbda2bed24f58846db0c5685e8b49`
   - Rate Limit: 200ms zwischen Calls
   - Filter: `countrycode:de`
   - Format: GeoJSON
2. **Mapbox** (Fallback) - Falls Geoapify-Key nicht gesetzt
3. **Nominatim** (Fallback) - OpenStreetMap, kostenlos

---

## KI-Integration

### LLM-Optimizer (`services/llm_optimizer.py`)
- **Provider:** OpenAI GPT-4o-mini (Primär)
- **Model:** `gpt-4o-mini` (konfiguriert in `config.env`)
- **Anwendung:** Route-Optimierung, geografisches Clustering
- **Monitoring:** Performance-Tracking in `llm_monitoring.db`
- **Fallback:** Nearest-Neighbor wenn LLM nicht verfügbar

### Sektor-Planung (Dresden-Quadranten)
- Bearing-basierte Sektorzuordnung (N/O/S/W)
- Greedy-Algorithmus pro Sektor
- Zeitbox-Validierung (65 Min ohne Rückfahrt, 90 Min mit Rückfahrt)
- OSRM-First für Distanzberechnung

### PIRNA-Clustering
- K-Means-Clustering für PIRNA-Touren
- Automatische Cluster-Größen-Anpassung
- Zeitbasierte Validierung

---

## Frontend-Komponenten

### Hauptseite (`index.html`)
- CSV-Upload mit Live-Geocoding-Progress
- Tour-Übersicht mit W-Tour/BAR-Highlighting
- Multi-Tour Generator Button (erscheint bei W-Touren)
- Karte mit Leaflet.js
- Abdockbare Panels (Map/Tours)

### Tour-Management (`tourplan-management.html`)
- CSV-Liste mit Status
- Bulk-Processing mit Live-Progress
- Optimierte Touren anzeigen/bearbeiten

### Test-Dashboard (`test-dashboard.html`)
- Modul-Status mit visueller Anzeige
- Einzelne Tests ausführen
- Live-Output und Ergebnisse

---

## Technologie-Stack

```
Backend:     FastAPI (Python 3.11+)
Database:    SQLite mit Geocaching
Frontend:    HTML5 + Leaflet.js + Vanilla JavaScript
AI/ML:       OpenAI GPT-4o-mini (Primär), Ollama (optional)
Routing:     OSRM (lokal/Docker) + OpenRouteService (geplant)
Server:      Uvicorn ASGI
Maps:        OpenStreetMap (Leaflet)
```

---

## Sicherheit & Best Practices

### Geocoding
- **DB-First:** Verhindert unnötige API-Calls (Cache → Geoapify → Speichern)
- **Synonym-System:** Automatische Auflösung von Kunden-Namen über `CUSTOMER_SYNONYMS.md`
- **Rate Limiting:** 200ms Delay für Geoapify
- **Fehlerbehandlung:** Retry-Logik für 429-Errors, fehlgeschlagene → `manual_queue`
- **Normalisierung:** Adressen werden normalisiert vor Cache-Lookup (`address_norm`)

### Backups
- **Automatisch:** Täglich um 16:00 Uhr
- **Retention:** 30 Tage
- **Wiederherstellung:** Mit automatischem Pre-Backup

### Datenintegrität
- **Read-Only:** Tourplaene-Verzeichnis schreibgeschützt
- **Deduplizierung:** Kunden pro Tour eindeutig
- **Validierung:** Koordinaten-Checks (nicht 0,0)
- **Zeitbox-Validierung:** Routen werden streng validiert (65 Min ohne Rückfahrt, 90 Min mit Rückfahrt)
- **Proaktive Aufteilung:** Routen werden von Anfang an aufgeteilt (nicht erst nach Überschreitung)

---

## Deployment

### Start-Script
```bash
python start_server.py
```

### Windows Task Scheduler
```powershell
.\scripts\schedule_backup_windows.ps1
```

### Port
- **Standard:** 8111
- **Konfiguriert in:** `app_config.json` oder `.env`

### Docker
```bash
docker-compose up --build
```

---

## Weiterentwicklung

### Aktueller Stand (2025-11-13)
- ✅ 90-Minuten-Routen-Problem gelöst (proaktive Aufteilung)
- ✅ Dresden-Quadranten & Zeitbox implementiert
- ✅ OSRM-Integration aktiv (Route API, Table API, Polyline6)
- ✅ Polyline6-Decoder im Frontend implementiert
- ✅ Deterministischer Routing-Optimizer (OR-Tools, NN+2-Opt)
- ✅ Error Envelope & Trace-ID Middlewares
- ✅ Pydantic V2 Kompatibilität hergestellt
- ✅ Stats-Box mit echten DB-Daten
- ✅ Admin-Bereich mit Health-Checks
- ✅ Abdockbare Panels (Map/Tours)

### Geplant
1. Multi-Tour Generator API vollständig integrieren
2. Tour-Splitting im Frontend
3. Manuelle Tour-Bearbeitung
4. Export-Funktionen (PDF, Excel)

---

## Weiterführende Dokumentation

- **[API.md](API.md)** - Vollständige API-Dokumentation
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Entwicklerhandbuch
- **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - Datenbankschema
- **[STANDARDS.md](STANDARDS.md)** - Entwicklungsstandards

---

**Diese konsolidierte Architektur-Dokumentation fasst alle Architektur-Informationen in einem Dokument zusammen.**

