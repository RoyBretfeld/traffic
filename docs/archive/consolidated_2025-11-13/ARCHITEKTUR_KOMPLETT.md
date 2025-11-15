# FAMO TrafficApp - Komplette Architektur-Übersicht

**Erstellt:** 2025-01-10  
**Status:** Aktuell  
**Zweck:** Umfassende Übersicht aller Module, Komponenten und Statistiken für KI-Assistenten

---

## 📊 Projekt-Statistiken

### Dateien-Übersicht
- **Gesamt:** 1.346 Dateien
- **Python-Dateien:** 423
- **Markdown-Dateien:** 143
- **JSON-Dateien:** 309
- **CSV-Dateien:** 207
- **HTML-Dateien:** 12
- **JavaScript-Dateien:** 2 (in frontend/)
- **INI-Dateien:** 87
- **PowerShell-Scripts:** 14
- **Datenbank-Dateien:** 11

### API-Endpoints
- **Route-Dateien:** 32
- **Geschätzte Endpoints:** ~147 (basierend auf Funktionszählung)
- **Registrierte Router:** 29 (in `backend/app.py`)

### Module & Services
- **Backend-Services:** 22 (in `backend/services/`)
- **Services (Root):** 19 (in `services/`)
- **Repositories:** 6 (in `repositories/`)
- **Parsers:** 4 (in `backend/parsers/`)

---

## 🏗️ System-Architektur

```
┌─────────────────────────────────────────────────────────────────┐
│                    Frontend (Vanilla JS/HTML)                    │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  index.html (Hauptseite)                                │   │
│  │  - Karte (Leaflet.js)                                    │   │
│  │  - Tourübersicht                                         │   │
│  │  - Workflow-Box                                          │   │
│  │  - Statistik-Box (geplant)                              │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Weitere HTML-Seiten                                     │   │
│  │  - tourplan-management.html                              │   │
│  │  - test-dashboard.html                                   │   │
│  │  - multi-tour-generator.html                             │   │
│  │  - coordinate-verify.html                                │   │
│  │  - ai-test.html                                          │   │
│  │  - tourplan-visual-test.html                             │   │
│  │  - tourplan-test.html                                    │   │
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
│              FastAPI Backend (Python 3.x)                         │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  API-Routen (routes/)                                    │   │
│  │  - workflow_api.py (Haupt-Workflow)                     │   │
│  │  - tourplan_match.py (Adress-Matching)                   │   │
│  │  - upload_csv.py (CSV-Upload)                            │   │
│  │  - engine_api.py (Route-Engine)                           │   │
│  │  - health_check.py (Health-Checks)                       │   │
│  │  - backup_api.py (Backup-Management)                     │   │
│  │  - ai_test_api.py (AI-Tests)                             │   │
│  │  - audit_*.py (Audit-Endpoints)                          │   │
│  │  - tourplan_*.py (Tourplan-Management)                    │   │
│  │  - failcache_*.py (Fail-Cache-Management)               │   │
│  │  - manual_api.py (Manuelle Korrekturen)                  │   │
│  │  - coordinate_verify_api.py (Koordinaten-Verifizierung)  │   │
│  │  - address_recognition_api.py (Adress-Erkennung)         │   │
│  │  - summary_api.py (Zusammenfassungen)                    │   │
│  │  - test_dashboard_api.py (Test-Dashboard)                │   │
│  │  - endpoint_flow_api.py (Endpoint-Flow)                  │   │
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
│  │  - coordinate_verifier.py (Koordinaten-Verifizierung)    │   │
│  │  - csv_ai_parser.py (AI-CSV-Parser)                      │   │
│  │  - csv_bulk_processor.py (Bulk-Verarbeitung)             │   │
│  │  - file_parser.py (Datei-Parsing)                        │   │
│  │  - geo_validator.py (Geo-Validierung)                    │   │
│  │  - geocode.py (Geocoding)                                 │   │
│  │  - multi_tour_generator.py (Multi-Tour-Generierung)      │   │
│  │  - optimization_rules.py (Optimierungs-Regeln)           │   │
│  │  - real_routing.py (Echtes Routing)                      │   │
│  │  - synonyms.py (Synonym-Verwaltung)                      │   │
│  │  - text_normalize.py (Text-Normalisierung)               │   │
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
│  │  - prompt_manager.py (Prompt-Management)                │   │
│  │  - workflow_engine.py (Workflow-Engine)                   │   │
│  │  - geocode_fill.py (Async Geocoding)                     │   │
│  │  - fuzzy_suggest.py (Fuzzy-Suggestions)                  │   │
│  │  - private_customer_filter.py (Private-Kunden-Filter)    │   │
│  │  - tour_plan_grouper.py (Tour-Gruppierung)              │   │
│  │  - tour_plan_raw_reader.py (Raw-Reader)                   │   │
│  │  - uid_service.py (UID-Generierung)                      │   │
│  │  - w_route_optimizer.py (W-Route-Optimierung)           │   │
│  │  - code_quality_monitor.py (Code-Qualität)               │   │
│  │  - geocode_persist.py (Geocoding-Persistierung)          │   │
│  │  - llm_address_helper.py (LLM-Adress-Helper)              │   │
│  │  - secure_key_manager.py (Key-Management)                │   │
│  │  - stop_dto.py (Stop-DTO)                                │   │
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
│  │  - dao.py (Data Access Object)                            │   │
│  │  - config.py (DB-Konfiguration)                           │   │
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

## 🔌 API-Endpoints (Übersicht)

### Workflow & Tour-Management
- `POST /api/workflow/upload` - CSV-Upload + kompletter Workflow
- `POST /api/workflow/complete` - Workflow für Tourplaene-Datei
- `GET /api/workflow/status` - System-Status
- `GET /api/workflow/geocoding-progress/{session_id}` - Live-Geocoding-Status
- `POST /api/tour/optimize` - Tour-Optimierung
- `POST /api/tour/route-details` - Route-Details mit OSRM-Geometrie

### Geocoding & Adress-Management
- `GET /api/tourplan/match` - Tourplan gegen DB matchen
- `POST /api/tourplan/geofill` - Fehlende Koordinaten geokodieren
- `POST /api/tourplan/geofill-bulk` - Bulk-Geocoding
- `GET /api/address-recognition/status` - Erkennungsrate
- `POST /api/tourplan/manual-geo` - Manuelle Geo-Korrektur
- `GET /api/coordinate/verify` - Koordinaten-Verifizierung

### Tourplan-Management
- `GET /api/tourplaene/list` - Liste aller Tourplaene
- `GET /api/tourplan/status` - Tourplan-Status
- `POST /api/tourplan/suggest` - Vorschläge für Adressen
- `POST /api/tourplan/accept` - Vorschlag akzeptieren
- `POST /api/tourplan/triage` - Triage für Adressen
- `POST /api/tourplan/bulk-analysis` - Bulk-Analyse
- `POST /api/tourplan/bulk-process` - Bulk-Verarbeitung

### LLM & AI
- `POST /api/llm/optimize` - LLM-Routenoptimierung
- `GET /api/llm/monitoring` - LLM-Monitoring
- `GET /api/llm/templates` - Prompt-Templates
- `POST /api/ai-test/analyze` - AI-Adress-Analyse

### Audit & Debugging
- `GET /api/audit/geo` - Geo-Audit
- `GET /api/audit/geocoding` - Geocoding-Audit
- `GET /api/audit/status` - Status-Audit
- `GET /api/audit/integrity` - Integritäts-Prüfung
- `GET /api/debug/geo` - Geo-Debug

### Fail-Cache & Manual Queue
- `GET /api/failcache/list` - Fail-Cache-Liste
- `POST /api/failcache/clear` - Fail-Cache leeren
- `GET /api/failcache/improved` - Verbesserte Fail-Cache-Ansicht
- `GET /api/manual/list` - Manual-Queue-Liste
- `POST /api/manual/resolve` - Manual-Eintrag auflösen

### System & Health
- `GET /health` - Server-Health
- `GET /health/db` - Datenbank-Status
- `GET /summary` - System-Zusammenfassung
- `GET /api/tests/status` - Test-Status
- `GET /api/endpoint-flow/modules` - Endpoint-Flow-Module
- `GET /api/endpoint-flow/flow` - Datenfluss-Visualisierung

### Backup & Maintenance
- `POST /api/backup/create` - Backup erstellen
- `GET /api/backup/list` - Backup-Liste
- `POST /api/backup/restore` - Backup wiederherstellen
- `POST /api/backup/cleanup` - Backups bereinigen

### Engine & Routing
- `POST /api/engine/optimize` - Route-Engine-Optimierung
- `POST /api/engine/generate` - Route-Generierung

### Upload & CSV
- `POST /api/upload/csv` - CSV-Upload
- `POST /api/parse-csv-tourplan` - CSV-Tourplan parsen
- `POST /api/process-csv-modular` - CSV modular verarbeiten

---

## 📦 Module-Details

### 1. Workflow-Engine (`routes/workflow_api.py`)
**Größe:** ~2.500 Zeilen  
**Verantwortlich:** Kompletter Workflow von CSV-Upload bis Route-Optimierung

**Hauptfunktionen:**
- CSV-Upload und Parsing
- Geocoding (DB-First-Strategie)
- Tour-Konsolidierung
- Sektor-Planung (Dresden-Quadranten)
- PIRNA-Clustering
- LLM-basierte Route-Optimierung
- OSRM-Route-Visualisierung
- Zeitbox-Validierung (90-Minuten-Problem)

**Dependencies:**
- `backend.parsers.tour_plan_parser`
- `repositories.geo_repo`
- `services.sector_planner`
- `services.pirna_clusterer`
- `services.osrm_client`
- `services.llm_optimizer`
- `backend.services.tour_consolidator`

### 2. Sektor-Planer (`services/sector_planner.py`)
**Verantwortlich:** Dresden-Quadranten-Planung für W-Touren

**Features:**
- 4-Sektor-Planung (N/O/S/W)
- 8-Sektor-Planung (N, NO, O, SO, S, SW, W, NW) - geplant
- Zeitbox-Validierung (65 Min ohne Rückfahrt, 90 Min mit Rückfahrt)
- Proaktive Route-Aufteilung bei Überschreitung

### 3. PIRNA-Clusterer (`services/pirna_clusterer.py`)
**Verantwortlich:** Geografisches Clustering für PIRNA-Touren

**Features:**
- K-Means-ähnliches Clustering
- Distanz-basierte Gruppierung
- Zeitbox-Validierung

### 4. OSRM-Client (`services/osrm_client.py`)
**Verantwortlich:** Kommunikation mit OSRM-Docker-Container

**Features:**
- Route-Berechnung (Straßen-Distanzen)
- Distance-Matrix
- Polyline-Geometrie
- Circuit-Breaker bei Fehlern
- Timeout-Handling

### 5. LLM-Optimizer (`services/llm_optimizer.py`)
**Verantwortlich:** AI-basierte Route-Optimierung

**Features:**
- OpenAI GPT-4o-mini Integration
- Prompt-Management
- Response-Parsing
- Kosten-Tracking
- Monitoring

### 6. Geocoding-System
**Komponenten:**
- `repositories/geo_repo.py` - DB-Repository
- `services/geocode_fill.py` - Async Geocoding
- `backend/services/geocode.py` - Geocoding-Logik
- `repositories/geo_fail_repo.py` - Fail-Cache

**Strategie:** DB-First (Cache → Geoapify → Speichern)

### 7. Synonym-System
**Komponenten:**
- `backend/services/synonyms.py` - SynonymStore
- `repositories/geo_alias_repo.py` - Alias-Repository
- `scripts/import_customer_synonyms.py` - Import-Script

**Features:**
- Automatische Auflösung beim CSV-Parsen
- Alias → Real Customer ID Mapping
- Adress-Ersetzung

### 8. Tour-Konsolidierung (`backend/services/tour_consolidator.py`)
**Verantwortlich:** Konsolidierung von T10-Touren

**Features:**
- Automatische Gruppierung
- Duplikat-Erkennung
- Tour-Merging

---

## 🗄️ Datenbank-Schema

### Haupt-Tabellen (traffic.db)

**`geo_cache`**
- `id` (PK)
- `address` (normalisiert, unique)
- `latitude`
- `longitude`
- `source` (geoapify, manual, etc.)
- `first_seen`
- `last_seen`
- `confidence`
- `metadata` (JSON)

**`address_synonyms`**
- `id` (PK)
- `tourplan_kdnr`
- `alias`
- `real_customer_id`
- `address`
- `lat`
- `lon`
- `note`

**`manual_queue`**
- `id` (PK)
- `address`
- `reason`
- `status`
- `created_at`
- `resolved_at`

**`geo_fail`**
- `id` (PK)
- `address`
- `error`
- `attempts`
- `last_attempt`
- `expires_at`

---

## 🔄 Datenfluss

### Typischer Workflow

```
1. CSV-Upload
   ↓
2. Parser (tour_plan_parser.py)
   - Format-Erkennung (TEHA vs. Standard)
   - Encoding-Erkennung (CP850, UTF-8)
   - Mojibake-Reparatur
   ↓
3. Synonym-Auflösung (SynonymStore)
   - Alias → Real Customer ID
   - Adress-Ersetzung
   ↓
4. Geocoding (geo_repo.py)
   - DB-Cache-Check
   - Falls nicht gefunden: Geoapify
   - Speichern in DB
   ↓
5. Tour-Konsolidierung (tour_consolidator.py)
   - T10-Touren zusammenführen
   ↓
6. Sektor-Planung / Clustering
   - W-Touren: Sektor-Planung (sector_planner.py)
   - PIRNA-Touren: Clustering (pirna_clusterer.py)
   ↓
7. Route-Optimierung
   - LLM-Optimierung (llm_optimizer.py)
   - ODER Nearest-Neighbor
   ↓
8. OSRM-Route-Berechnung (osrm_client.py)
   - Distance-Matrix
   - Route-Geometrie
   ↓
9. Zeitbox-Validierung
   - 90-Minuten-Check
   - Route-Aufteilung bei Überschreitung
   ↓
10. Response an Frontend
    - Touren mit Koordinaten
    - Route-Geometrie
    - Statistiken
```

---

## 🎯 Geplante Features (aus Plänen)

### Statistik-Box & Navigations-Admin
**Plan:** `docs/STATISTIK_NAV_ADMIN_PLAN.md`  
**Status:** Geplant

**Features:**
- Statistik-Box auf Hauptseite (Read-only)
- Reduzierte Navigation (Hauptseite, ABI-Talks, Admin)
- Admin-Bereich (Testboard, AI-Test, Statistik & Archiv, Fenster & Docking)
- Zeitbox-Visualisierung (rote Unterlegung)
- Abdockbare Panels (Karte, Tourübersicht)

### Lizenzierungssystem
**Plan:** `docs/licensing-plan.md`  
**Status:** Geplant

**Features:**
- Ed25519-basierte JWT-Lizenzen
- Online/Offline-Aktivierung
- Device-Fingerprinting
- Grace-Period (10 Tage)
- Revocation
- Admin-UI für Lizenzverwaltung

### Multi-Monitor & Routen-Export
**Plan:** `docs/PLAN_MULTI_MONITOR_ROUTEN_EXPORT.md`  
**Status:** Geplant

**Features:**
- Multi-Monitor-Support
- Manuelle Routen-Bearbeitung (Drag & Drop)
- Export zu Maps (Google Maps, GPX, QR-Code)

---

## 🔧 Technologie-Stack

### Backend
- **Framework:** FastAPI (Python 3.x)
- **Server:** Uvicorn
- **Datenbank:** SQLite (traffic.db, customers.db, etc.)
- **ORM:** SQLAlchemy (teilweise)
- **HTTP-Client:** httpx
- **Geocoding:** Geoapify API
- **Routing:** OSRM (Docker-Container)
- **AI:** OpenAI GPT-4o-mini

### Frontend
- **Technologie:** Vanilla JavaScript/HTML/CSS
- **Karten:** Leaflet.js
- **Polyline:** @mapbox/polyline
- **UI-Framework:** Bootstrap 5
- **Icons:** Font Awesome 6

### DevOps
- **Container:** Docker (OSRM)
- **Build:** PyInstaller (geplant)
- **Signierung:** Authenticode (geplant)
- **Sync:** PowerShell-Scripts

---

## 📁 Verzeichnisstruktur

```
FAMO TrafficApp 3.0/
├── backend/              # Backend-Code
│   ├── app.py           # FastAPI-App (Haupt-Einstiegspunkt)
│   ├── services/        # Backend-Services (22 Dateien)
│   ├── parsers/         # Parser (4 Dateien)
│   ├── db/              # Datenbank-Layer (4 Dateien)
│   └── utils/           # Utilities
├── routes/               # API-Routen (32 Dateien)
├── services/             # Services (19 Dateien)
├── repositories/         # Datenbank-Repositories (6 Dateien)
├── frontend/             # Frontend (12 HTML, 2 JS)
├── data/                # Datenbanken & Daten
│   ├── traffic.db       # Haupt-Datenbank
│   ├── customers.db     # Kunden-Datenbank
│   ├── backups/         # Datenbank-Backups
│   ├── staging/         # Staging-Bereich
│   └── uploads/         # Upload-Bereich
├── config/              # Konfigurationsdateien
│   ├── tour_ignore_list.json
│   ├── dynamic/         # Dynamische Configs
│   └── static/          # Statische Configs
├── docs/                # Dokumentation (143 Markdown-Dateien)
├── scripts/             # Utility-Scripts (156 Dateien)
├── tests/               # Tests (117 Dateien)
├── db/                  # Datenbank-Schema & Migrationen
├── ingest/              # CSV-Ingestion
├── tools/               # Tools & Utilities (59 Dateien)
└── ZIP/                 # ZIP-Archive
```

---

## 🔐 Sicherheit & Best Practices

### Encoding
- UTF-8 durchgängig
- Mojibake-Reparatur
- Encoding-Guards (`backend/utils/encoding_guards.py`)

### Datenbank
- WAL-Mode aktiviert
- Automatische Backups (täglich 16:00 Uhr)
- Fail-Cache für fehlgeschlagene Geocodes

### API
- CORS aktiviert (alle Origins)
- JSON-Responses mit UTF-8
- Error-Handling mit strukturierten Fehlermeldungen

### Geocoding
- Rate-Limiting (Geoapify)
- Fail-Cache mit Expiration
- DB-First-Strategie (minimiert API-Calls)

---

## 📈 Metriken & Monitoring

### LLM-Monitoring
- Request-Count
- Token-Usage
- Kosten-Tracking
- Response-Zeiten

### Geocoding-Statistiken
- Cache-Hit-Rate
- API-Call-Count
- Fail-Rate
- Erkennungsrate

### System-Status
- Datenbank-Health
- OSRM-Status
- Disk-Space
- Backup-Status

---

## 🚀 Deployment

### Lokale Entwicklung
- Server: `python start_server.py` oder `uvicorn backend.app:app --reload --port 8111`
- OSRM: Docker-Container (Port 5000)

### Produktion (geplant)
- PyInstaller-Build
- Authenticode-Signierung
- USB-Distribution
- Lizenzierungssystem

---

## 📚 Wichtige Dokumentation

### Architektur & Design
- `docs/Architecture.md` - Basis-Architektur
- `docs/ARCHITEKTUR_KOMPLETT.md` - Diese Datei
- `docs/ENDPOINT_FLOW.md` - Endpoint-Flow

### Pläne
- `docs/STATISTIK_NAV_ADMIN_PLAN.md` - Statistik & Navigation
- `docs/licensing-plan.md` - Lizenzierungssystem
- `docs/PLAN_MULTI_MONITOR_ROUTEN_EXPORT.md` - Multi-Monitor
- `docs/PLAENE_UEBERSICHT.md` - Übersicht aller Pläne

### Features
- `docs/CUSTOMER_SYNONYMS.md` - Synonym-System
- `docs/TOUR_NAMING_SCHEMA.md` - Tour-Namensschema
- `docs/DRESDEN_QUADRANTEN_ZEITBOX.md` - Sektor-Planung

### Fixes & Probleme
- `docs/FIX_ROUTE_DETAILS_404.md` - Route-Details-Fix
- `docs/FIX_APPLIED_OSRM_TIMEOUT.md` - OSRM-Timeout-Fix
- `docs/PROBLEM_OSRM_POLYGONE.md` - OSRM-Polygon-Problem

---

## 🎓 Für KI-Assistenten

### Wichtige Dateien zum Lesen
1. **`backend/app.py`** - Haupt-Einstiegspunkt, alle Router-Registrierungen
2. **`routes/workflow_api.py`** - Haupt-Workflow-Logik
3. **`frontend/index.html`** - Haupt-Frontend
4. **`docs/ARCHITEKTUR_KOMPLETT.md`** - Diese Datei (Übersicht)

### Häufige Aufgaben
- **Neue API-Endpoints:** Erstelle Datei in `routes/`, registriere in `backend/app.py`
- **Neue Services:** Erstelle Datei in `backend/services/` oder `services/`
- **Frontend-Änderungen:** Bearbeite `frontend/index.html` oder erstelle neue HTML-Datei
- **Datenbank-Änderungen:** Schema in `db/schema.py`, Migrationen in `db/migrations/`

### Code-Standards
- UTF-8 Encoding überall
- JSON-Responses mit `create_utf8_json_response()`
- Error-Handling mit strukturierten Fehlermeldungen
- Logging mit `print()` (später durch Logging-Modul ersetzen)

---

## 📊 Zusammenfassung für KI

**Projekt-Größe:**
- 1.346 Dateien insgesamt
- 423 Python-Dateien
- 143 Markdown-Dateien
- 32 Route-Dateien
- ~147 API-Endpoints
- 22 Backend-Services
- 19 Services (Root)
- 6 Repositories
- 4 Parser

**Haupt-Module:**
1. Workflow-Engine (CSV → Geocoding → Optimierung)
2. Sektor-Planer (Dresden-Quadranten)
3. PIRNA-Clusterer (Geografisches Clustering)
4. OSRM-Client (Straßen-Routing)
5. LLM-Optimizer (AI-Routenoptimierung)
6. Geocoding-System (DB-First-Strategie)
7. Synonym-System (Alias-Auflösung)
8. Tour-Konsolidierung (T10-Merging)

**Technologie:**
- Backend: FastAPI (Python)
- Frontend: Vanilla JS/HTML/CSS
- Datenbank: SQLite
- Routing: OSRM (Docker)
- AI: OpenAI GPT-4o-mini
- Geocoding: Geoapify

**Geplante Features:**
- Statistik-Box & Navigation (geplant)
- Lizenzierungssystem (geplant)
- Multi-Monitor & Export (geplant)

---

**Letzte Aktualisierung:** 2025-01-10  
**Nächste Schritte:** Implementierung gemäß `docs/STATISTIK_NAV_ADMIN_PLAN.md` und `docs/licensing-plan.md`

