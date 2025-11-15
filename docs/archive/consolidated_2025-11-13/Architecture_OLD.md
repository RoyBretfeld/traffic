# FAMO TrafficApp - Architektur-Dokumentation

**Letzte Aktualisierung:** 2025-01-10 (Spät)

## Übersicht

Die FAMO TrafficApp ist eine KI-basierte Route-Optimierungsanwendung für Tourenplanung und Geocoding. Das System nutzt eine modulare Architektur mit FastAPI-Backend, SQLite-Datenbank und modernem Frontend.

**Wichtige Änderungen (2025-01-10):**
- ✅ Pydantic V2 Kompatibilität hergestellt
- ✅ Error Envelope & Trace-ID Middlewares implementiert
- ✅ Deterministischer Routing-Optimizer integriert
- ✅ API-Kompatibilität verbessert (`fill_missing`, `StopModel`)

## System-Architektur

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (HTML/CSS/JS)                │
│  - index.html (Hauptseite)                              │
│  - tourplan-management.html (Tour-Management)            │
│  - test-dashboard.html (Test-Übersicht)                  │
│  - multi-tour-generator.html (Route-Optimierung)         │
└────────────────┬────────────────────────────────────────┘
                 │ HTTP/REST
┌────────────────▼────────────────────────────────────────┐
│              FastAPI Backend (Python)                    │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │ workflow_api │  │  backup_api  │  │ test_dash_   │ │
│  │              │  │              │  │ api          │ │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘ │
│         │                 │                 │          │
│  ┌──────▼─────────────────▼─────────────────▼──────┐  │
│  │          Services & Repositories                │  │
│  │  - sector_planner.py (Dresden-Quadranten)       │  │
│  │  - pirna_clusterer.py (PIRNA-Clustering)        │  │
│  │  - osrm_client.py (OSRM-Routing)                │  │
│  │  - llm_optimizer.py (OpenAI GPT-4o-mini)        │  │
│  │  - geocode_fill.py (Async Geocoding)            │  │
│  │  - workflow_engine.py (Workflow-Orchestrierung) │  │
│  │  - geo_repo.py (DB-Operations)                  │  │
│  └──────┬──────────────────────────────────────────┘  │
│         │                                              │
┌─────────▼──────────────────────────────────────────────┐
│           SQLite Database (traffic.db)                 │
│  - geo_cache (Geocoding-Cache mit normalisierten      │
│              Adressen und Metadaten)                  │
│  - manual_queue (Fehlgeschlagene Geocodes)            │
│  - geo_fail (Geocoding-Fehler für Analyse)           │
│  - kunden (Kundenstammdaten, optional)                │
│  - touren (Touren-Daten, optional)                     │
└────────────────────────────────────────────────────────┘
```

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
- `POST /api/llm/optimize` - Direkte LLM-Routenoptimierung
- `GET /api/llm/monitoring` - LLM-Monitoring und Performance-Metriken
- `GET /api/llm/templates` - Prompt-Templates und Konfiguration

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

### 2. Backup-System (`scripts/db_backup.py` + `routes/backup_api.py`)

**Verantwortlich:** Automatische und manuelle Datenbank-Backups

**Endpoints:**
- `POST /api/backup/create` - Manuelles Backup erstellen
- `GET /api/backup/list` - Backup-Liste abrufen
- `POST /api/backup/restore` - Backup wiederherstellen
- `POST /api/backup/cleanup` - Alte Backups bereinigen

**Features:**
- Tägliche automatische Backups (16:00 Uhr)
- SQLite-native Backup-Methode (sicher auch bei WAL-Mode)
- 30-Tage Retention
- Windows Task Scheduler Integration

### 3. Bulk-Processing (`routes/tourplan_bulk_process.py`)

**Verantwortlich:** Massenverarbeitung aller CSV-Dateien

**Endpoints:**
- `POST /api/tourplan/bulk-process-all` - Alle CSVs verarbeiten
- `GET /api/tourplan/bulk-progress/{session_id}` - Live-Progress

**Workflow:**
1. Iteriere über alle CSV-Dateien in `tourplaene/`
2. Parse jede Datei mit `parse_tour_plan_to_dict`
3. DB-First Geocoding für jeden Kunden
4. Live-Progress-Tracking (Datei, Kunde, DB-Hits, Geoapify-Calls)

### 4. Multi-Tour Generator (`backend/services/multi_tour_generator.py`)

**Verantwortlich:** KI-basierte Aufteilung großer Touren in optimale Untertouren

**Features:**
- Geografisches Clustering mit KI
- Zeit-Constraints (60min + 2min/Kunde + 5min Puffer)
- Depot-Integration (FAMO Dresden)
- Automatische Validierung

**API-Endpoint:** (Noch in audit/csv_parsing/backend_app.py)
- `POST /tour/{tour_id}/generate_multi_ai`

**Frontend-Integration:**
- Button auf Hauptseite (`index.html`) - erscheint nur bei W-Touren
- Erweiterte Ansicht: `/ui/multi-tour-generator.html`

### 5. Engine API (`routes/engine_api.py`)

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

### 6. Sektor-Planer (`services/sector_planner.py`)

**Verantwortlich:** Dresden-Quadranten-basierte Routenplanung für W-Touren

**Features:**
- Bearing-Berechnung (Azimut 0-360°)
- Sektorzuordnung (N/O/S/W, deterministisch)
- Greedy-Planung pro Sektor
- Zeitbox-Validierung (07:00 Start, 09:00 Rückkehr)
- OSRM-First Strategie mit Fallback

**Verwendung:**
- Automatisch für W-Touren (erkannt durch `should_use_sector_planning()`)
- Optional für CB, BZ, PIR-Touren (aber nicht empfohlen)

### 7. PIRNA-Clusterer (`services/pirna_clusterer.py`)

**Verantwortlich:** Clustering-basierte Routenplanung für PIRNA-Touren

**Features:**
- K-Means-Clustering basierend auf Koordinaten
- Automatische Cluster-Größen-Anpassung
- Zeitbasierte Validierung

### 8. OSRM-Client (`services/osrm_client.py`)

**Verantwortlich:** OSRM-Routing-Integration für straßenbasierte Distanzen

**Features:**
- Route API für Punkt-zu-Punkt-Routen
- Table API für Distanz-Matrizen
- Circuit Breaker für Fehlerbehandlung
- Lazy-Initialisierung (nach config.env Laden)

### 9. Test-Dashboard (`routes/test_dashboard_api.py` + `frontend/test-dashboard.html`)

**Verantwortlich:** Modul-Tests und Status-Übersicht

**Endpoints:**
- `GET /api/tests/status` - Gesamtstatus aller Tests
- `GET /api/tests/modules` - Modul-Übersicht mit Status
- `GET /api/tests/list` - Alle verfügbaren Tests
- `POST /api/tests/run` - Spezifische Tests ausführen

**Features:**
- Visuelles Feedback während Test-Ausführung
- Live-Output-Anzeige
- Modul-Status (grün/rot/unbekannt)
- Einzelne Tests pro Modul ausführen

## Datenbank-Schema

**WICHTIG:** Vollständiges Schema siehe `docs/DATABASE_SCHEMA.md` und `docs/database_schema.sql`

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
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## Geocoding-Provider

### Priorität
1. **Geoapify** (Primär) - API-Key: `32abbda2bed24f58846db0c5685e8b49`
   - Rate Limit: 200ms zwischen Calls
   - Filter: `countrycode:de`
   - Format: GeoJSON
2. **Mapbox** (Fallback) - Falls Geoapify-Key nicht gesetzt
3. **Nominatim** (Fallback) - OpenStreetMap, kostenlos

## Endpoint-Übersicht

### Workflow (`/api/workflow/*`)
- `POST /api/workflow/upload` - CSV-Upload und vollständiger Workflow
- `POST /api/workflow/complete` - Kompletter Workflow mit Tourplaene-Dateien
- `GET /api/workflow/geocoding-progress/{session_id}` - Live-Geocoding-Status
- `GET /api/workflow/status` - System-Status mit LLM-Metriken

### Tour-Optimierung (`/api/tour/*`)
- `POST /api/tour/optimize` - Tour-Optimierung mit LLM oder Nearest-Neighbor
- `POST /api/tour/route-details` - Route-Details mit OSRM-Geometrie

### Engine API (`/engine/tours/*`) - Betriebsordnung-konform
- `POST /engine/tours/ingest` - Akzeptiert Erkennungsformat, erzeugt UIDs
- `GET /engine/tours/{tour_uid}/status` - Status abfragen
- `POST /engine/tours/optimize` - Optimiert nur vollständige Touren
- `POST /engine/tours/split` - Subtourenbildung mit OSRM Table
- `POST /engine/tours/sectorize` - Sektorisierung (N/O/S/W) für W-Touren
- `POST /engine/tours/plan_by_sector` - Planung mit Zeitbox (07:00-09:00)

### LLM (`/api/llm/*`)
- `POST /api/llm/optimize` - Direkte LLM-Routenoptimierung
- `GET /api/llm/monitoring` - LLM-Monitoring und Performance-Metriken
- `GET /api/llm/templates` - Prompt-Templates und Konfiguration

### Tourplan-Management (`/api/tourplan/*`)
- `GET /api/tourplan/match` - Tourplan gegen DB matchen
- `POST /api/tourplan/bulk-process-all` - Alle CSVs verarbeiten
- `GET /api/tourplan/bulk-progress/{session_id}` - Bulk-Progress

### Backup (`/api/backup/*`)
- `POST /api/backup/create` - Backup erstellen
- `GET /api/backup/list` - Backup-Liste
- `POST /api/backup/restore` - Backup wiederherstellen
- `POST /api/backup/cleanup` - Bereinigung

### Tests (`/api/tests/*`)
- `GET /api/tests/status` - Test-Status
- `GET /api/tests/modules` - Modul-Übersicht
- `POST /api/tests/run` - Tests ausführen

## Frontend-Komponenten

### Hauptseite (`index.html`)
- CSV-Upload mit Live-Geocoding-Progress
- Tour-Übersicht mit W-Tour/BAR-Highlighting
- Multi-Tour Generator Button (erscheint bei W-Touren)
- Karte mit Leaflet.js

### Tour-Management (`tourplan-management.html`)
- CSV-Liste mit Status
- Bulk-Processing mit Live-Progress
- Optimierte Touren anzeigen/bearbeiten

### Test-Dashboard (`test-dashboard.html`)
- Modul-Status mit visueller Anzeige
- Einzelne Tests ausführen
- Live-Output und Ergebnisse

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
- **Konfiguriert in:** `app_config.json`

## Weiterentwicklung

### Geplant
1. Multi-Tour Generator API vollständig integrieren
2. Tour-Splitting im Frontend
3. Manuelle Tour-Bearbeitung
4. Export-Funktionen (PDF, Excel)

### Aktueller Stand (10. Januar 2025 - Spät)
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
- ⚠️ Phase 2.1 Schema noch nicht aktiviert (Feature-Flag)
- ⚠️ Phase 2.3 Statistik-Detailseite noch ausstehend

## Dokumentation-Links

- [Multi-Tour Generator API](./MULTI_TOUR_GENERATOR_API.md)
- [Database Backup](./DATABASE_BACKUP.md)
- [W-Route Optimierung](./W_ROUTE_OPTIMIERUNG.md)
- [Adaptive Pattern Engine](./ADAPTIVE_PATTERN_ENGINE.md)
