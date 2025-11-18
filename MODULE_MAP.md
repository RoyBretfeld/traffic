# Modul-Index – FAMO TrafficApp 3.0

**Version:** 1.0  
**Stand:** 2025-11-16  
**Zweck:** Übersicht aller Module, ihrer Verantwortlichkeiten und Kommunikationswege

> **Regel:** Bei jedem neuen Modul oder größeren Umbau: Eintrag in dieser Tabelle aktualisieren.  
> Cursor darf diese Tabelle anpassen, aber **nur Zeilen ändern, die vom aktuellen Change betroffen sind**.

---

## Legende

- **Typ:** `route` (API-Endpoint), `service` (Business-Logik), `repo` (Datenbank-Zugriff), `frontend` (UI-Komponente), `job` (Background-Task), `infra` (Infrastruktur), `parser` (Daten-Parsing), `middleware` (Request-Processing)
- **Status:** `stabil` (produktionsreif), `experimentell` (in Entwicklung), `deprecated` (veraltet, wird entfernt)

---

## Module

| Modul-ID | Dateipfad | Typ | Verantwortlich für | Nutzt | Wird genutzt von | Status |
|----------|-----------|-----|-------------------|-------|------------------|--------|
| **Infrastruktur & Core** |
| backend.app | `backend/app.py` | infra | App-Factory, Router-Registrierung | `db.schema`, `backend.app_setup` | alle Routen | stabil |
| backend.app_setup | `backend/app_setup.py` | infra | Modulare App-Initialisierung | `db.schema`, `backend.config`, Middlewares | `backend.app` | stabil |
| db.core | `db/core.py` | infra | SQLite-Datenbankverbindung | SQLite | alle Services/Repos | stabil |
| db.schema | `db/schema.py` | infra | Schema-Definition & Migration | `db.core` | `backend.app_setup`, alle Services | stabil |
| **API-Routen (Backend)** |
| workflow_api | `backend/routes/workflow_api.py` | route | CSV-Upload, Workflow-Orchestrierung | `tour_plan_parser`, `geo_repo`, `geocode`, `llm_optimizer`, `osrm_client`, `sector_planner`, `real_routing` | Frontend (`index.html`) | stabil |
| engine_api | `backend/routes/engine_api.py` | route | Betriebsordnung-konforme Touren-Engine (UID-basiert) | `uid_service`, `osrm_client`, `sector_planner`, `pirna_clusterer` | Frontend, `workflow_api` | stabil |
| tourplan_match | `backend/routes/tourplan_match.py` | route | Tourplan gegen Geo-Cache matchen | `geo_repo` | Frontend | stabil |
| tourplan_geofill | `backend/routes/tourplan_geofill.py` | route | Fehlende Koordinaten geokodieren | `geocode`, `geo_repo` | Frontend | stabil |
| health_check | `backend/routes/health_check.py` | route | System-Health-Checks (DB, OSRM, System) | `db.core`, `osrm_client` | Frontend, Monitoring | stabil |
| backup_api | `backend/routes/backup_api.py` | route | Datenbank-Backup-Management | `db.core` | Frontend (Admin) | stabil |
| cost_tracker_api | `backend/routes/cost_tracker_api.py` | route | KI-Kosten-Tracking & Statistiken | `cost_tracker` | Frontend (`ki-kosten.html`) | stabil |
| db_schema_api | `backend/routes/db_schema_api.py` | route | Datenbank-Schema-Informationen | `db.core` | Frontend (Admin) | stabil |
| tour_filter_api | `backend/routes/tour_filter_api.py` | route | Tour-Filter-Verwaltung (ignore/allow) | `config/tour_ignore_list.json` | Frontend (`tour-filter.html`) | stabil |
| ki_activity_api | `backend/routes/ki_activity_api.py` | route | KI-Aktivitäts-Log | `cost_tracker` | Frontend (`ki-verhalten.html`) | stabil |
| ki_effectiveness_api | `backend/routes/ki_effectiveness_api.py` | route | KI-Effektivitäts-Metriken | `cost_tracker`, `error_learning_service`, `ki_learning_coordinator` | Frontend (`ki-verhalten.html`) | stabil |
| **Services (Business-Logik)** |
| osrm_client | `services/osrm_client.py` | service | OSRM-Routing-Integration (Route API, Table API) | `requests`, OSRM-Endpoint (Docker/Proxmox) | `workflow_api`, `engine_api`, `real_routing`, `sector_planner` | stabil |
| geocode | `backend/services/geocode.py` | service | Geocoding (DB-First: Cache → Geoapify → Speichern) | `geo_repo`, externe Geocoder-API (Geoapify/Nominatim) | `workflow_api`, `tourplan_geofill` | stabil |
| llm_optimizer | `services/llm_optimizer.py` | service | LLM-basierte Route-Optimierung (OpenAI GPT-4o-mini) | OpenAI API, `osrm_client` | `workflow_api` | stabil |
| sector_planner | `services/sector_planner.py` | service | Dresden-Quadranten-basierte Routenplanung (N/O/S/W) | `osrm_client`, `uid_service` | `workflow_api`, `engine_api` | stabil |
| pirna_clusterer | `services/pirna_clusterer.py` | service | K-Means-Clustering für PIRNA-Touren | `osrm_client` | `engine_api` | stabil |
| real_routing | `backend/services/real_routing.py` | service | Route-Details mit OSRM-Geometrie (Polyline6) | `osrm_client` | `workflow_api` | stabil |
| tour_consolidator | `backend/services/tour_consolidator.py` | service | T10-Touren-Konsolidierung | - | `workflow_api` | stabil |
| uid_service | `services/uid_service.py` | service | UID-Generierung für Touren/Stops | - | `engine_api`, `sector_planner` | stabil |
| cost_tracker | `backend/services/cost_tracker.py` | service | KI-Kosten-Tracking (API-Calls, Token, Kosten) | SQLite (`code_fixes_cost.db`) | `cost_tracker_api`, `ki_activity_api` | stabil |
| error_learning_service | `backend/services/error_learning_service.py` | service | Fehler-Lernsystem (Pattern-Erkennung, Aggregation) | SQLite (`error_learning.db`) | `ki_effectiveness_api` | stabil |
| ki_learning_coordinator | `backend/services/ki_learning_coordinator.py` | service | KI-Lern-Koordinator (Code Audit + Runtime Error + Lessons) | `error_learning_service`, `lessons_updater` | `ki_effectiveness_api` | stabil |
| **Repositories (Datenbank-Zugriff)** |
| geo_repo | `repositories/geo_repo.py` | repo | Geo-Cache-Zugriff (get, upsert) | `db.core`, `geo_cache` Tabelle | `geocode`, `workflow_api`, `tourplan_match` | stabil |
| geo_fail_repo | `repositories/geo_fail_repo.py` | repo | Geo-Fail-Cache (fehlgeschlagene Geocodes) | `db.core`, `geo_fail` Tabelle | `geocode` | stabil |
| geo_alias_repo | `repositories/geo_alias_repo.py` | repo | Geo-Alias-Verwaltung | `db.core`, `geo_alias` Tabelle | `geocode` | stabil |
| **Parser** |
| tour_plan_parser | `backend/parsers/tour_plan_parser.py` | parser | Tourplan-CSV-Parsing (TEHA-Format, Synonym-Auflösung) | `synonyms`, `geo_repo` | `workflow_api` | stabil |
| **Frontend-Komponenten** |
| index.html | `frontend/index.html` | frontend | Haupt-UI (Karte, Tourübersicht, Workflow, Sub-Routen) | `/api/workflow/upload`, `/api/tour/optimize`, `/api/tour/route-details` | Benutzer | stabil |
| ki-kosten.html | `frontend/admin/ki-kosten.html` | frontend | KI-Kosten-Übersicht (Charts, Statistiken) | `/api/cost-tracker/stats`, `/api/cost-tracker/current-model` | Admin | stabil |
| ki-verhalten.html | `frontend/admin/ki-verhalten.html` | frontend | KI-Verhalten-Dashboard (Performance, Effektivität) | `/api/ki/activity-log`, `/api/ki/effectiveness` | Admin | stabil |
| tour-filter.html | `frontend/admin/tour-filter.html` | frontend | Tour-Filter-Verwaltung (ignore/allow) | `/api/tour-filter` | Admin | stabil |
| admin.html | `frontend/admin.html` | frontend | Admin-Hauptseite (Tabs: System, DB, KI) | `/health/db`, `/api/db/list`, `/api/db/schemas` | Admin | stabil |
| panel-ipc.js | `frontend/js/panel-ipc.js` | frontend | Panel-IPC (Inter-Process-Communication für abdockbare Panels) | `postMessage` API | `index.html`, Panel-HTMLs | stabil |
| **Background-Jobs** |
| code_improvement_job | `backend/services/code_improvement_job.py` | job | KI-Code-Verbesserungs-Job (kontinuierlich) | `ai_code_checker`, `cost_tracker` | `code_improvement_job_api` | experimentell (temporär deaktiviert) |
| **Middleware** |
| trace_id_middleware | `backend/middlewares/trace_id.py` | middleware | Trace-ID-Generierung für Request-Tracking | - | alle Routen | stabil |
| error_tally | `backend/middlewares/error_tally.py` | middleware | Error-Tally (Fehler-Zählung) | - | alle Routen | stabil |
| request_id_middleware | `backend/core/error_handlers.py` | middleware | Request-ID-Middleware | - | alle Routen | stabil |

---

## Kommunikations-Flows

### 1. Touren-Workflow (CSV-Upload → Optimierung)

```
Frontend (index.html)
  → POST /api/workflow/upload (workflow_api)
    → tour_plan_parser (CSV-Parsing, Synonym-Auflösung)
    → geo_repo (DB-Cache-Check)
    → geocode (Geocoding: Cache → Geoapify → Speichern)
    → llm_optimizer (Route-Optimierung)
      → osrm_client (Distanzen)
      → OpenAI API (Optimierung)
    → real_routing (Route-Details mit Polyline6)
      → osrm_client (Route API)
  → Frontend (Touren anzeigen)
```

### 2. Sub-Routen-Generator

```
Frontend (index.html)
  → POST /api/tour/optimize (workflow_api)
    → sector_planner (für W-Touren: N/O/S/W)
      → osrm_client (Table API für Distanzen)
    → llm_optimizer (Optimierung)
    → real_routing (Route-Details)
  → Frontend (Sub-Routen anzeigen)
```

### 3. Engine API (Betriebsordnung-konform)

```
Frontend / workflow_api
  → POST /engine/tours/ingest (engine_api)
    → uid_service (UID-Generierung)
  → POST /engine/tours/sectorize (engine_api)
    → sector_planner (Sektorisierung)
      → osrm_client (Distanzen)
  → POST /engine/tours/plan_by_sector (engine_api)
    → sector_planner (Planung mit Zeitbox)
```

### 4. KI-Kosten-Tracking

```
cost_tracker (Service)
  → SQLite (code_fixes_cost.db)
    → cost_tracker_api (REST-Endpoint)
      → Frontend (ki-kosten.html)
```

### 5. Health-Checks

```
Frontend / Monitoring
  → GET /health (health_check)
    → db.core (DB-Verbindung)
    → osrm_client (OSRM-Erreichbarkeit)
  → Response (Status: OK/ERROR)
```

---

## Externe Abhängigkeiten

| Service | Typ | Verwendung | Konfiguration |
|---------|-----|------------|---------------|
| OSRM | Routing | Straßenbasierte Distanzen, Route-Geometrie | `OSRM_BASE_URL` (Docker: `http://127.0.0.1:5000` oder Proxmox-LXC) |
| OpenAI API | LLM | Route-Optimierung, Code-Checker | `OPENAI_API_KEY` (config.env) |
| Geoapify | Geocoding | Adress-zu-Koordinaten (Primär) | API-Key in `geocode.py` |
| Nominatim | Geocoding | Fallback-Geocoding | OpenStreetMap, kostenlos |

---

## Infrastruktur

| Komponente | Typ | Beschreibung | Port/URL |
|-----------|-----|--------------|----------|
| FastAPI Backend | App | Haupt-Backend (Uvicorn) | `http://127.0.0.1:8111` |
| OSRM Container | Docker/LXC | Routing-Service | `http://127.0.0.1:5000` (Docker) oder Proxmox-LXC |
| SQLite DBs | Datenbank | `traffic.db`, `code_fixes_cost.db`, `error_learning.db`, etc. | Lokale Dateien (`data/`) |

---

## Wartung

**Aktualisierung bei:**
- ✅ Neues Modul hinzugefügt
- ✅ Neue Abhängigkeit zwischen Modulen
- ✅ Modul entfernt oder deprecated
- ✅ Status-Änderung (stabil → experimentell oder umgekehrt)

**Cursor-Anweisung:**
- Nur betroffene Zeilen ändern
- Datum im Header aktualisieren
- Kommunikations-Flows erweitern, wenn neue Flows entstehen

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-16  
**Projekt:** FAMO TrafficApp 3.0

📋 **Modul-Index für nachvollziehbare Architektur**

