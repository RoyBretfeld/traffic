# FAMO TrafficApp – API Dokumentation

**Version:** 1.0  
**Base URL:** `http://127.0.0.1:8111`  
**Format:** JSON UTF-8  
**Letzte Aktualisierung:** 2025-11-13

---

## Inhaltsverzeichnis

1. [Allgemeines](#allgemeines)
2. [Workflow & CSV-Verarbeitung](#workflow--csv-verarbeitung)
3. [Tourplan-Management](#tourplan-management)
4. [Geocoding](#geocoding)
5. [Tour-Optimierung](#tour-optimierung)
6. [Engine API](#engine-api)
7. [LLM & KI](#llm--ki)
8. [Backup & Verwaltung](#backup--verwaltung)
9. [Health & Monitoring](#health--monitoring)
10. [Tests](#tests)

---

## Allgemeines

### Format
- **Content-Type**: `application/json`
- **Encoding**: UTF-8
- **Authentifizierung**: Noch nicht aktiv (künftige Version: API-Key / Rollen)

### Fehlerformat
```json
{
  "detail": "Beschreibung",
  "error_code": "OPTIONAL",
  "timestamp": "ISO-8601"
}
```

### HTTP-Status-Codes
- **200**: Erfolg
- **400**: Client-Fehler (Validierung)
- **404**: Nicht gefunden
- **422**: Unprocessable Entity (Validierungsfehler)
- **500**: Server-Fehler

---

## Workflow & CSV-Verarbeitung

### POST `/api/workflow/upload`
CSV-Datei hochladen und vollständigen Workflow ausführen.

**Request:**
```
Content-Type: multipart/form-data
file=<Tourenplan.csv>
```

**Response 200:**
```json
{
  "message": "CSV-Tourenplan erfolgreich verarbeitet",
  "filename": "Tourenplan 21.08.2025.csv",
  "session_id": "uuid-here",
  "workflow_results": {
    "parse_csv": "success",
    "geocode": "success",
    "optimize": "success"
  }
}
```

### POST `/api/workflow/complete`
Kompletter Workflow mit Tourplaene-Dateien.

**Request:**
```json
{
  "files": ["Tourenplan 21.08.2025.csv"],
  "options": {
    "geocode": true,
    "optimize": true
  }
}
```

### GET `/api/workflow/geocoding-progress/{session_id}`
Live-Geocoding-Status abrufen.

**Response 200:**
```json
{
  "session_id": "uuid-here",
  "status": "processing",
  "progress": {
    "total": 100,
    "processed": 45,
    "cached": 30,
    "geocoded": 15
  }
}
```

### GET `/api/workflow/status`
System-Status mit LLM-Metriken.

**Response 200:**
```json
{
  "system": "ok",
  "llm": {
    "available": true,
    "calls_today": 42,
    "avg_latency_ms": 850
  }
}
```

### POST `/api/parse-csv-tourplan`
Parst einen hochgeladenen Tourplan (CSV/TXT) mit der neuen Parser-Logik.

**Request:**
```
Content-Type: multipart/form-data
file=<Tourenplan.csv>
```

**Response 200:**
```json
{
  "message": "CSV-Tourenplan erfolgreich geparst",
  "filename": "Tourenplan 21.08.2025.csv",
  "parsed_data": {
    "metadata": {
      "source_file": "Tourenplan 21.08.2025.csv",
      "delivery_date": "2025-08-21"
    },
    "tours": [...],
    "customers": [...],
    "stats": {
      "total_tours": 26,
      "total_customers": 183,
      "total_bar_customers": 4
    }
  }
}
```

### POST `/api/process-csv-modular`
Startet den kompletten Workflow: Parsing → Geokodierung → Clustering → Optimierung → KI-Kommentare.

**Request:**
```
Content-Type: multipart/form-data
file=<Tourenplan.csv>
```

**Response 200:**
```json
{
  "success": true,
  "filename": "Tourenplan 21.08.2025.csv",
  "workflow_results": {
    "final_results": {
      "routes": {
        "total_routes": 6,
        "tours": [...]
      },
      "ai_commentary": [...]
    },
    "workflow_steps": {
      "parse_csv": "success",
      "geocode": "success",
      "cluster": "success",
      "optimize": "success",
      "ai_comment": "success"
    }
  }
}
```

---

## Tourplan-Management

### GET `/api/tourplan/match`
Matcht Adressen aus einem Tourplan gegen die `geo_cache` Datenbank.

**Query Parameters:**
- `file` (string, required): Pfad zur Original-CSV unter `./Tourplaene`

**Response 200:**
```json
{
  "file": "./Tourplaene/Tourenplan 01.09.2025.csv",
  "rows": 150,
  "ok": 142,
  "warn": 8,
  "bad": 0,
  "items": [
    {
      "row": 1,
      "address": "Löbtauer Straße 1, 01809 Heidenau",
      "has_geo": true,
      "geo": {
        "lat": 50.9836,
        "lon": 13.8663
      },
      "status": "ok"
    }
  ]
}
```

**Status-Codes:**
- **`ok`**: Adresse hat Geo-Daten UND keine Mojibake-Marker
- **`warn`**: Adresse hat keine Geo-Daten ABER keine Mojibake-Marker
- **`bad`**: Adresse enthält Mojibake-Marker (Encoding-Probleme)

### GET `/api/tourplan/geocode-missing`
Geokodiert fehlende Adressen aus einem Tourplan über Nominatim.

**Query Parameters:**
- `file` (string, required): Pfad zur Original-CSV
- `limit` (int, optional): Maximale Anzahl (1-100, default: 20)
- `dry_run` (boolean, optional): Wenn `true`, keine DB-Updates (default: false)

**Response 200:**
```json
{
  "file": "./Tourplaene/Tourenplan 01.09.2025.csv",
  "requested": 15,
  "processed": 10,
  "dry_run": false,
  "items": [
    {
      "address": "Löbtauer Straße 1, 01809 Heidenau",
      "result": {
        "lat": 50.9836,
        "lon": 13.8663
      }
    }
  ]
}
```

### GET `/api/tourplan/list`
Liste verfügbarer Tourplan-CSV-Dateien.

**Response 200:**
```json
{
  "files": [
    {
      "filename": "Tourenplan 21.08.2025.csv",
      "size": 45678,
      "modified": "2025-08-21T10:30:00Z"
    }
  ]
}
```

### POST `/api/tourplan/bulk-process-all`
Verarbeitet alle CSV-Dateien im Verzeichnis `tourplaene/`.

**Response 200:**
```json
{
  "message": "CSV Import erfolgreich!",
  "total_customers": 245,
  "unique_customers": 230,
  "saved_customers": 230,
  "geocoding_success": 228,
  "geocoding_failed": 2,
  "geocoding_rate": "99.1%",
  "files_processed": 21
}
```

### GET `/api/tourplan/bulk-progress/{session_id}`
Live-Progress für Bulk-Processing.

---

## Geocoding

### POST `/api/tourplan/manual-geo`
Speichert manuelle Koordinaten für Adressen ohne Geocoding-Ergebnis.

**Request Body:**
```json
{
  "address": "Teststraße 123, Dresden",
  "latitude": 51.0504,
  "longitude": 13.7373,
  "by_user": "admin"
}
```

**Response 200:**
```json
{
  "ok": true,
  "message": "Koordinaten für 'Teststraße 123, Dresden' gespeichert",
  "coordinates": {
    "lat": 51.0504,
    "lon": 13.7373
  }
}
```

**Validierung:**
- `latitude`: -90 bis 90
- `longitude`: -180 bis 180
- `address`: min. 3 Zeichen

---

## Tour-Optimierung

### POST `/api/tour/optimize`
Tour-Optimierung mit LLM oder Nearest-Neighbor.

**Request Body:**
```json
{
  "tour_id": "W-07.00 Uhr Tour",
  "stops": [
    {
      "customer_number": "1055",
      "address": "Am Trachauer Bahnhof 11, 01139 Dresden",
      "lat": 51.0504,
      "lon": 13.7373
    }
  ],
  "options": {
    "algorithm": "llm",
    "time_window": {
      "start": "08:00",
      "end": "12:00"
    }
  }
}
```

**Response 200:**
```json
{
  "tour_id": "W-07.00 Uhr Tour",
  "optimized_route": [
    {
      "customer_number": "1055",
      "sequence": 1,
      "estimated_arrival": "08:15"
    }
  ],
  "meta": {
    "algorithm": "llm",
    "total_distance_km": 42.3,
    "total_duration_minutes": 58
  }
}
```

### POST `/api/tour/route-details`
Route-Details mit OSRM-Geometrie.

**Request Body:**
```json
{
  "stops": [
    {"lat": 51.0504, "lon": 13.7373},
    {"lat": 51.0600, "lon": 13.7300}
  ],
  "options": {
    "geometries": "polyline6",
    "overview": "full"
  }
}
```

**Response 200:**
```json
{
  "route": {
    "distance": 4230,
    "duration": 3480,
    "geometry": "encoded_polyline6_string",
    "waypoints": [...]
  }
}
```

---

## Engine API

### POST `/engine/tours/ingest`
Akzeptiert Erkennungsformat, erzeugt UIDs, normalisiert, plant Geo.

**Request Body:**
```json
{
  "tours": [
    {
      "tour_id": "ext-2025-11-01-A",
      "label": "W-07.00 Uhr Tour",
      "stops": [
        {
          "source_id": "ROW-12345",
          "label": "Kunde ...",
          "address": "Fröbelstraße 10, Dresden",
          "lat": 51.0,
          "lon": 13.7,
          "time_window": {
            "start": "08:00",
            "end": "12:00"
          }
        }
      ]
    }
  ]
}
```

**Response 200:**
```json
{
  "tours": [
    {
      "tour_uid": "sha256-hash",
      "status": "pending_geo",
      "stops": [
        {
          "stop_uid": "sha256-hash",
          "status": "pending_geo"
        }
      ]
    }
  ]
}
```

### GET `/engine/tours/{tour_uid}/status`
Status abfragen.

**Response 200:**
```json
{
  "tour_uid": "sha256-hash",
  "status": "ready",
  "counters": {
    "total_stops": 28,
    "pending_geo": 0,
    "ready": 28
  }
}
```

### POST `/engine/tours/optimize`
Optimiert nur vollständige Touren (alle Stops mit `lat/lon`).

**Request Body:**
```json
{
  "tour_uid": "sha256-hash",
  "options": {
    "objective": "time"
  }
}
```

**Response 200:**
```json
{
  "tour_uid": "sha256-hash",
  "route": ["stop_uid_1", "stop_uid_2", ...],
  "meta": {
    "objective": "time"
  }
}
```

### POST `/engine/tours/split`
Subtourenbildung mit OSRM Table.

### POST `/engine/tours/sectorize`
Sektorisierung (N/O/S/W) für W-Touren.

### POST `/engine/tours/plan_by_sector`
Planung mit Zeitbox (07:00-09:00).

---

## LLM & KI

### POST `/api/llm/optimize`
Direkte LLM-Routenoptimierung.

**Request Body:**
```json
{
  "stops": [
    {
      "stop_uid": "sha256-hash",
      "label": "Kunde ..."
    }
  ],
  "constraints": {
    "max_duration_minutes": 60
  }
}
```

**Response 200:**
```json
{
  "route": ["stop_uid_1", "stop_uid_2", ...],
  "reasoning": "Optimiert nach geografischer Nähe...",
  "meta": {
    "model": "gpt-4o-mini",
    "tokens_used": 450
  }
}
```

### GET `/api/llm/monitoring`
LLM-Monitoring und Performance-Metriken.

**Response 200:**
```json
{
  "calls_today": 42,
  "calls_total": 1234,
  "avg_latency_ms": 850,
  "total_tokens": 45678,
  "cost_estimate_usd": 12.34
}
```

### GET `/api/llm/templates`
Prompt-Templates und Konfiguration.

---

## Backup & Verwaltung

### POST `/api/backup/create`
Manuelles Backup erstellen.

**Response 200:**
```json
{
  "ok": true,
  "backup_file": "backup_20251113_143000.db",
  "size_bytes": 12345678
}
```

### GET `/api/backup/list`
Backup-Liste abrufen.

**Response 200:**
```json
{
  "backups": [
    {
      "filename": "backup_20251113_143000.db",
      "size_bytes": 12345678,
      "created": "2025-11-13T14:30:00Z"
    }
  ]
}
```

### POST `/api/backup/restore`
Backup wiederherstellen.

**Request Body:**
```json
{
  "backup_file": "backup_20251113_143000.db"
}
```

### POST `/api/backup/cleanup`
Alte Backups bereinigen.

---

## Health & Monitoring

### GET `/healthz`
System-Health-Check.

**Response 200:**
```json
{
  "status": "ok",
  "timestamp": "2025-11-13T14:30:00Z"
}
```

### GET `/health/db`
Datenbank-Health-Check.

**Response 200:**
```json
{
  "ok": true,
  "database": "traffic.db",
  "tables": {
    "geo_cache": 1234,
    "geo_fail": 5
  }
}
```

### GET `/health/osrm`
OSRM-Health-Check.

**Response 200:**
```json
{
  "ok": true,
  "osrm_url": "http://172.16.1.191:5011",
  "response_time_ms": 45
}
```

### GET `/_debug/routes`
Listet alle registrierten API-Routen auf.

**Response 200:**
```json
{
  "routes": [
    {
      "path": "/api/workflow/upload",
      "methods": ["POST"],
      "name": "workflow_upload"
    }
  ]
}
```

---

## Tests

### GET `/api/tests/status`
Gesamtstatus aller Tests.

**Response 200:**
```json
{
  "total": 50,
  "passed": 48,
  "failed": 2,
  "modules": {
    "parser": "ok",
    "geocoding": "ok",
    "routing": "warning"
  }
}
```

### GET `/api/tests/modules`
Modul-Übersicht mit Status.

### GET `/api/tests/list`
Alle verfügbaren Tests.

### POST `/api/tests/run`
Spezifische Tests ausführen.

**Request Body:**
```json
{
  "module": "parser",
  "test_name": "test_csv_parsing"
}
```

---

## Weiterführende Dokumentation

- **[Architecture.md](Architecture.md)** - System-Architektur
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Entwickler-Guide
- **[STANDARDS.md](STANDARDS.md)** - API-Standards

---

**Diese API-Dokumentation konsolidiert alle API-Endpunkte in einem Dokument.**

