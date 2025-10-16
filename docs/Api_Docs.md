# FAMO TrafficApp – API Dokumentation

Diese Dokumentation beschreibt die wichtigsten REST-Endpunkte der TrafficApp. Die API orientiert sich an der 8-Schritte-Architektur aus `docs/Neu/Neue Prompts.md`. Alle Endpunkte geben JSON zurück und laufen standardmäßig unter `http://127.0.0.1:8111` (lokal).

---

## 0. Allgemeines

- Format: JSON UTF-8
- Authentifizierung: Noch nicht aktiv (künftige Version: API-Key / Rollen)
- Fehlerformat: `{ "detail": "Beschreibung", "error_code": "OPTIONAL", "timestamp": "ISO-8601" }`

---

## Manuelle Koordinaten-Eingabe

### POST /api/tourplan/manual-geo
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

**Response (200):**
```json
{
  "ok": true,
  "message": "Koordinaten für 'Teststraße 123, Dresden' gespeichert",
  "coordinates": {"lat": 51.0504, "lon": 13.7373}
}
```

**Validierung:**
- `latitude`: -90 bis 90
- `longitude`: -180 bis 180
- `address`: min. 3 Zeichen

**Verwendung:** Für Adressen die vom automatischen Geocoding nicht gefunden werden, können Koordinaten manuell eingegeben werden. Diese werden in der `geo_cache` Tabelle mit `source="manual"` gespeichert.

---

## Schritt 1 – CSV-Upload & Parsing

### POST `/api/parse-csv-tourplan`
Parst einen hochgeladenen Tourplan (CSV/TXT) mit der neuen Parser-Logik.

**Request**
```
Content-Type: multipart/form-data
file=<Tourenplan.csv>
```

**Response 200**
```
{
  "message": "CSV-Tourenplan erfolgreich geparst",
  "filename": "Tourenplan 21.08.2025.csv",
  "parsed_data": {
    "metadata": {
      "source_file": "Tourenplan 21.08.2025.csv",
      "delivery_date": "2025-08-21"
    },
    "tours": [
      {
        "name": "W-07.00 Uhr Tour",
        "tour_type": "W",
        "time": "07:00",
        "is_bar_tour": false,
        "customer_count": 28,
        "customers": [
          {
            "customer_number": "1055",
            "name": "Motoreninstandsetzung",
            "street": "Am Trachauer Bahnhof 11",
            "postal_code": "01139",
            "city": "Dresden",
            "bar_flag": false
          }
          // ... weitere Kunden
        ]
      }
      // ... weitere Touren
    ],
    "customers": [ ... ],
    "stats": {
      "total_tours": 26,
      "total_customers": 183,
      "total_bar_customers": 4
    }
  },
  "metadata": {
    "delivery_date": "2025-08-21",
    "total_tours": 26,
    "total_customers": 183,
    "total_bar_customers": 4
  }
}
```

**Fehler**
- `400` – Datei fehlt oder ungültig
- `500` – Parsing fehlgeschlagen (Detail im Fehlertext)

---

### POST `/api/parse-csv-pandas`
Alternative für einfache CSV-Dateien (gleiche Logik, aber reduziert auf Tour-/Kundenzählung).

**Response 200**
```
{
  "message": "CSV erfolgreich geparst",
  "filename": "Tourenplan 21.08.2025.csv",
  "tour_count": 26,
  "customer_count": 183,
  "parsed_data": { ... identisch wie oben ... }
}
```

---

### GET `/api/csv-summary/{filename}`
Liefert Metadaten zu bereits hochgeladenen Dateien (`data/uploads`).

**Response 200**
```
{
  "filename": "Tourenplan 21.08.2025.csv",
  "summary": {
    "total_tours": 26,
    "total_customers": 183,
    "total_bar_customers": 4,
    "tour_types": { "W": 12, "PIR": 3, ... }
  }
}
```

**Fehler**
- `404` – Datei nicht gefunden

---

### POST `/api/csv-bulk-process`
Verarbeitet alle CSV-Dateien im Verzeichnis `tourplaene/`. Aktuell noch legacy (pandas-basiert, ersetzt schrittweise durch neuen Parser).

**Response 200**
```
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

---

### POST `/api/csv-tour-process`
Ältere Pipeline zur Tour-Erkennung und Speicherung in SQLite (historisch, ersetzt durch neuen Workflow). Es wird empfohlen, stattdessen `/api/process-csv-modular` zu verwenden.

---

## Schritt 2 – Geokodierung & Validierung

Geokodierung läuft aktuell innerhalb von `/api/process-csv-modular` (Workflow) bzw. temporär noch in Legacy-Routen (`/api/csv-bulk-process`). Ergebnisse werden in SQLite (`data/customers.db`) persistiert; jede Adresse wird nur einmal geokodiert, weitere Anfragen nutzen den Cache.

Geplante Endpunkte (Backlog):
- `POST /api/geocode/batch` – Mehrere Adressen vorab geokodieren
- `GET /api/geocode/cache/{address}` – Cache-Status / Treffer anzeigen


## Schritt 3 – Zeit-/Distanzmatrix

Im derzeitigen Code erfolgt die Matrixberechnung innerhalb der Services (`real_routing.py`). Öffentliche Endpunkte folgen mit der Integration der echten Routing-API. Geplant:

- `POST /api/time-matrix` – Matrix für gegebene Koordinaten erzeugen


## Schritt 4 & 5 – Clustering & Tourenoptimierung

### POST `/api/process-csv-modular`
Startet den kompletten Workflow: Parsing → Geokodierung → Clustering → Optimierung → KI-Kommentare.

**Request**
```
Content-Type: multipart/form-data
file=<Tourenplan.csv>
```

**Response 200**
```
{
  "success": true,
  "filename": "Tourenplan 21.08.2025.csv",
  "workflow_results": {
    "final_results": {
      "routes": {
        "total_routes": 6,
        "tours": [
          {
            "tour_id": "W-07:00-A",
            "stops": 12,
            "estimated_duration_minutes": 58,
            "estimated_distance_km": 42.3,
            "constraints_satisfied": true
          }
        ]
      },
      "ai_commentary": [
        {
          "tour_id": "W-07:00-A",
          "comment": "Tour bleibt unter 60 Minuten, BAR-Kunde am Ende für bessere Kassenführung."
        }
      ]
    },
    "workflow_steps": {
      "parse_csv": "success",
      "geocode": "success",
      "cluster": "success",
      "optimize": "success",
      "ai_comment": "success"
    }
  },
  "message": "Modularer Workflow erfolgreich: 6 Routen verarbeitet"
}
```

**Fehler 200 (Workflow fehlgeschlagen)**
```
{
  "success": false,
  "error": "Zeitlimit überschritten",
  "workflow_state": {
    "parse_csv": "success",
    "geocode": "success",
    "cluster": "failure"
  },
  "message": "Workflow fehlgeschlagen"
}
```

---

### GET `/api/workflow-info`
Liefert eine Zusammenfassung der konfigurierten Workflow-Schritte und Parameter.

**Response 200**
```
{
  "success": true,
  "workflow_info": {
    "steps": ["parse_csv", "geocode", "cluster", "optimize", "ai_comment"],
    "max_driving_time": 60,
    "service_time_per_customer": 2
  },
  "message": "Workflow-Informationen erfolgreich abgerufen"
}
```

---

## Schritt 6 – AI-Kommentare / RAG

AI-Kommentare werden derzeit im Workflow generiert (`ai_optimizer`).

Geplante Erweiterungen:
- RAG/Vectorstore-Anbindung für FAQ, historische Antworten und Dokumentkontext.
- Eigene Endpoints (z. B. `POST /api/tours/{tour_id}/commentary`, `GET /api/tours/{tour_id}/commentary`).


## Schritt 7 – Frontend / Tour-Daten

Die folgenden Tour-Endpunkte sind aktiv, viele basieren noch auf der alten Datenbankstruktur und werden an die neue Pipeline angepasst.

### GET `/api/touren`
Liste alle gespeicherten Touren mit Basisinformationen.

**Response 200 (gekürzt)**
```
[
  {
    "tour_id": 1,
    "tour_name": "W-07.00 Uhr Tour",
    "datum": "2025-08-21",
    "kunde_count": 28,
    "status": "planned"
  }
]
```

### GET `/api/tours/{tour_id}`
Gibt sämtliche Stopps einer Tour zurück (inkl. Geodaten, BAR-Markierung, AI-Kommentare – abhängig vom Datenmodell).

### GET `/api/tours/date/{YYYY-MM-DD}`
Touren eines bestimmten Tages.

### POST `/api/tours/create`
Manuell Touren anlegen (für Testzwecke).

### PUT `/api/tours/{tour_id}/stops/sequence`
Reihenfolge (Drag & Drop) anpassen.

### POST `/api/tours/{tour_id}/split_ai`
Legacy-Endpunkt für KI-basierte Touraufteilung (multitour generator). Wird perspektivisch durch den modularen Workflow ersetzt.


## Schritt 8 – Tests, Logging, Versionierung

Noch keine dedizierten Endpunkte. Logfiles erreichbar via Dateisystem (`logs/`). Geplante API (z. B. `/api/logs/csv-import` für Debugging), sobald Logging standardisiert ist.


## Hilfs-/Legacy-Endpunkte (Auswahl)

- `GET /health` – Systemstatus
- `GET /api/dashboard`, `/api/db-status`, `/api/llm-status` – Admin/Monitoring
- `POST /api/parse-universal-routes` – Historischer CSV-Parser
- `POST /api/parse-csv-modular` – Alternative Schreibweise (alias) für `process-csv-modular`

---

## Roadmap (API)

| Schritt | Status | Nächste Ausbaustufe |
|---------|--------|----------------------|
| 1       | [OK] aktiv | Upload-Validierung, Dateiversionierung |
| 2       | 🔄 teilweise | Batch-Geocoding-Endpunkt, Cache-API |
| 3       | 🔄 in Arbeit | Direkter Matrix-Endpunkt mit Providerwahl |
| 4/5     | [OK] aktiv (Workflow) | Synchronous vs. async Jobs, Job-Status-API |
| 6       | 🔄 teilweise | Dedizierte KI-Kommentar-Endpunkte |
| 7       | 🔄 legacy | Neue Tour-API auf Basis der Workflow-Daten |
| 8       | 🔄 geplant | Log-/Prompt-API, Testresultate |

---

## Hinweise für Entwickler

- Nach jeder Änderung in den Workflow-Schritten API-Doku aktualisieren.
- Endpunkte, die noch Legacy-Logik verwenden, sukzessive auf den neuen Parser/Workflow migrieren.
- Für neue Funktionen stets die 8-Schritte-Architektur als Referenz nutzen.