# FAMO TrafficApp - Komplette Architektur-Übersicht

**Version:** 2.0  
**Erstellt:** 2025-01-10  
**Letzte Aktualisierung:** 2025-11-16  
**Status:** Aktuell  
**Zweck:** Umfassende Übersicht aller Module, Komponenten und Statistiken für KI-Assistenten

> **⚠️ WICHTIG:** Diese Dokumentation muss bei Änderungen an Routing/OSRM, Touren-Workflow, Infrastruktur oder Hauptmodulen aktualisiert werden.  
> Siehe auch: [`MODULE_MAP.md`](../MODULE_MAP.md) für detaillierte Modul-Kommunikation.

---

## 1️⃣ Systemübersicht

### High-Level-Architektur

```
┌─────────────────────────────────────────────────────────────┐
│                    Client (Browser)                          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Frontend (Vanilla JS/HTML)                          │   │
│  │  - index.html (Haupt-UI)                             │   │
│  │  - admin.html (Admin-Bereich)                        │   │
│  │  - Leaflet.js (Karten)                               │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │ HTTP/REST (Port 8111)
┌────────────────────────────▼────────────────────────────────┐
│              Backend (FastAPI, Python 3.10)                  │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  API-Routen (backend/routes/)                       │   │
│  │  - workflow_api.py                                  │   │
│  │  - engine_api.py                                     │   │
│  │  - health_check.py                                   │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Services (services/, backend/services/)             │   │
│  │  - osrm_client.py                                    │   │
│  │  - llm_optimizer.py                                  │   │
│  │  - sector_planner.py                                 │   │
│  └──────────────────────────────────────────────────────┘   │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  Repositories (repositories/)                         │   │
│  │  - geo_repo.py                                        │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────────┬────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
┌───────▼────────┐  ┌────────▼────────┐  ┌───────▼────────┐
│ OSRM Container │  │ SQLite DBs      │  │ OpenAI API     │
│ (Docker/LXC)   │  │ (data/)         │  │ (GPT-4o-mini)  │
│ Port 5000/5011 │  │ traffic.db      │  │                │
└────────────────┘  └─────────────────┘  └────────────────┘
```

### Datenfluss (High-Level)

1. **Frontend** sendet Request → **Backend API-Route**
2. **API-Route** nutzt **Services** für Business-Logik
3. **Services** nutzen **Repositories** für DB-Zugriff
4. **Services** kommunizieren mit **externen Services** (OSRM, OpenAI)
5. **Response** zurück an **Frontend**

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

## 2️⃣ Touren-Workflow (Detailliert)

### Kompletter Datenfluss: Import → Geocoding → Matching → Routing → Sub-Routen → Export

```
1. CSV-Upload (Frontend)
   ↓
2. POST /api/workflow/upload (workflow_api)
   ↓
3. Parser (tour_plan_parser.py)
   - Format-Erkennung (TEHA vs. Standard)
   - Encoding-Erkennung (CP850, UTF-8)
   - Mojibake-Reparatur
   - Synonym-Auflösung (SynonymStore)
   ↓
4. Geocoding (DB-First-Strategie)
   - geo_repo.get() → Cache-Check
   - Falls nicht gefunden: geocode_address() → Geoapify API
   - geo_repo.upsert() → Speichern in DB
   - Fehlgeschlagene → geo_fail_repo (Retry-Logic)
   ↓
5. Tour-Konsolidierung (tour_consolidator.py)
   - T10-Touren zusammenführen
   - Duplikat-Erkennung
   ↓
6. Tour-Filterung (tour_ignore_list.json)
   - ignore_tours vs. allow_tours
   - W-Touren, CB, BZ, PIR automatisch erkannt
   ↓
7. Sektor-Planung / Clustering
   - W-Touren: sector_planner.py (N/O/S/W)
   - PIRNA-Touren: pirna_clusterer.py (K-Means)
   ↓
8. Route-Optimierung
   - llm_optimizer.py (OpenAI GPT-4o-mini)
   - ODER Nearest-Neighbor (Fallback)
   - osrm_client.py (Distanzen via Table API)
   ↓
9. OSRM-Route-Berechnung (real_routing.py)
   - Route API für Geometrie (Polyline6)
   - osrm_client.py (Route API)
   ↓
10. Zeitbox-Validierung
    - 65 Min ohne Rückfahrt
    - 90 Min mit Rückfahrt
    - Proaktive Aufteilung bei Überschreitung
    ↓
11. Sub-Routen-Generierung (bei Bedarf)
    - Automatische Aufteilung großer Touren
    - Sub-Route-Suffix (-A, -B, -C, ...)
    ↓
12. Response an Frontend
    - Touren mit Koordinaten
    - Route-Geometrie (Polyline6)
    - Sub-Routen-Liste
    - Statistiken
```

### Wichtige Entscheidungspunkte

- **Tour-Filter:** `config/tour_ignore_list.json` bestimmt, welche Touren verarbeitet werden
- **Sektor-Planung:** Nur für W-Touren, CB, BZ, PIR (automatisch erkannt)
- **OSRM-First:** Distanzen immer über OSRM, Fallback: Haversine
- **DB-First Geocoding:** Cache → Geoapify → Speichern (minimiert API-Calls)

---

## 3️⃣ Routing-Stack

### OSRM-Container (Proxmox vs. Docker)

**Proxmox-LXC (Produktion):**
- **Container-ID:** 101
- **Hostname:** `OSRM`
- **IP:** `172.16.1.191` (DHCP, Bridge: `vmbr0`)
- **Port:** `5011`
- **Konfiguration:** `OSRM_BASE_URL=http://172.16.1.191:5011`

**Docker (Entwicklung/Heim):**
- **Container:** `osrm-backend` (Docker Desktop)
- **Port:** `5000` (Standard) oder `5011`
- **Konfiguration:** `OSRM_BASE_URL=http://127.0.0.1:5000`

### OSRM-Client (`services/osrm_client.py`)

**Features:**
- **Route API:** Punkt-zu-Punkt-Routen mit Polyline6-Geometrie
- **Table API:** Distanz-Matrizen (1×N, N×N)
- **Circuit Breaker:** Automatische Fehlerbehandlung bei OSRM-Ausfall
- **Timeout-Handling:** Max. 30s pro Request
- **Lazy-Initialisierung:** Wird erst beim ersten Zugriff erstellt (nach `config.env` Laden)

**Fallback-Strategie:**
- OSRM nicht verfügbar → Haversine-Distanz (Luftlinie)
- Timeout → Haversine-Distanz
- Circuit Breaker aktiv → Haversine-Distanz

### Routing-Optimierung

**Strategie:** OSRM-First
1. OSRM Table API für Distanzen
2. LLM-Optimierung (OpenAI) mit OSRM-Distanzen
3. OSRM Route API für Geometrie (Polyline6)
4. Fallback: Haversine bei OSRM-Ausfall

---

## 4️⃣ Module & Verantwortung

### Backend-Services (Kurz-Zusammenfassung)

| Service | Verantwortung | Wird genutzt von |
|---------|--------------|------------------|
| `osrm_client` | OSRM-Routing (Route API, Table API) | `workflow_api`, `engine_api`, `real_routing`, `sector_planner` |
| `geocode` | Geocoding (DB-First: Cache → Geoapify) | `workflow_api`, `tourplan_geofill` |
| `llm_optimizer` | LLM-Route-Optimierung (OpenAI) | `workflow_api` |
| `sector_planner` | Dresden-Quadranten-Planung (N/O/S/W) | `workflow_api`, `engine_api` |
| `pirna_clusterer` | K-Means-Clustering für PIRNA-Touren | `engine_api` |
| `real_routing` | Route-Details mit OSRM-Geometrie | `workflow_api` |
| `tour_consolidator` | T10-Touren-Konsolidierung | `workflow_api` |
| `uid_service` | UID-Generierung für Touren/Stops | `engine_api`, `sector_planner` |
| `cost_tracker` | KI-Kosten-Tracking | `cost_tracker_api`, `ki_activity_api` |
| `error_learning_service` | Fehler-Lernsystem | `ki_effectiveness_api` |

### Frontend-Komponenten

| Komponente | Verantwortung | Nutzt API |
|-----------|--------------|-----------|
| `index.html` | Haupt-UI (Karte, Tourübersicht, Workflow) | `/api/workflow/upload`, `/api/tour/optimize`, `/api/tour/route-details` |
| `admin.html` | Admin-Hauptseite (Tabs: System, DB, KI) | `/health/db`, `/api/db/list`, `/api/db/schemas` |
| `ki-kosten.html` | KI-Kosten-Übersicht | `/api/cost-tracker/stats`, `/api/cost-tracker/current-model` |
| `ki-verhalten.html` | KI-Verhalten-Dashboard | `/api/ki/activity-log`, `/api/ki/effectiveness` |
| `tour-filter.html` | Tour-Filter-Verwaltung | `/api/tour-filter` |

**Detaillierte Modul-Kommunikation:** Siehe [`MODULE_MAP.md`](../MODULE_MAP.md)

---

## 5️⃣ Infra & Ports

### Proxmox-Host

**Container-Übersicht:**
- **OSRM-Container (LXC 101):**
  - Hostname: `OSRM`
  - IP: `172.16.1.191` (DHCP, Bridge: `vmbr0`)
  - Port: `5011` (OSRM)
  - Status: Produktiv

**Netzwerk:**
- Bridge: `vmbr0`
- DHCP: Aktiv
- Firewall: Konfiguriert

### Lokale Entwicklung (Docker)

**OSRM-Container:**
- Container: `osrm-backend`
- Port: `5000` (Standard) oder `5011`
- URL: `http://127.0.0.1:5000` oder `http://localhost:5011`

**Backend (FastAPI):**
- Port: `8111` (Standard)
- URL: `http://127.0.0.1:8111`
- Start: `python start_server.py` oder `uvicorn backend.app:app --reload --port 8111`

### Weitere Services (geplant/optional)

- **Frigate:** Port `5000` (falls konfiguriert)
- **Weitere Container:** Siehe Proxmox-Übersicht

### Konfiguration

**Backend (`config.env`):**
```bash
OSRM_BASE_URL=http://172.16.1.191:5011  # Proxmox
# ODER:
OSRM_BASE_URL=http://127.0.0.1:5000     # Docker (lokal)
```

**Frontend:**
- Backend-URL: `http://127.0.0.1:8111` (fest codiert in `index.html`)

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

**Letzte Aktualisierung:** 2025-11-16  
**Nächste Schritte:** Implementierung gemäß `docs/STATISTIK_NAV_ADMIN_PLAN.md` und `docs/licensing-plan.md`

---

## 📋 Wartung & Aktualisierung

**Pflicht-Update bei:**
- ✅ Änderung an **Routing / OSRM-Anbindung**
- ✅ Änderungen im **Touren-Workflow** (neuer Schritt, neue Queue)
- ✅ Änderungen an **Infra** (Container-IP, Ports, Docker vs. LXC)
- ✅ Einführung/Entfernung von **Hauptmodulen** (neue Services, neue Routen)

**Regel:** Kein größerer Merge/Commit ohne zu prüfen:
> "Hat sich durch diese Änderung die Architektur sichtbar verändert?"  
> Wenn ja → Abschnitt in `ARCHITEKTUR_KOMPLETT.md` + `MODULE_MAP.md` anpassen.

**Siehe auch:**
- [`MODULE_MAP.md`](../MODULE_MAP.md) - Detaillierte Modul-Kommunikation
- [`docs/Architecture.md`](Architecture.md) - Basis-Architektur
- [`PROJECT_PROFILE.md`](../PROJECT_PROFILE.md) - Projektkontext

