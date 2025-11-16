# 🗺️ Routenbildung - Vollständige Dokumentation

**Version:** 1.0  
**Datum:** 2025-11-05  
**Zweck:** Umfassende Dokumentation der Routenerstellung in der FAMO TrafficApp

---

## 📋 Inhaltsverzeichnis

1. [Übersicht](#übersicht)
2. [Routing-Flow](#routing-flow)
3. [Beteiligte Dateien](#beteiligte-dateien)
4. [Komponenten-Details](#komponenten-details)
5. [Fallback-Mechanismen](#fallback-mechanismen)
6. [Baustellen-Integration](#baustellen-integration)
7. [API-Endpoints](#api-endpoints)
8. [Konfiguration](#konfiguration)

---

## 🎯 Übersicht

Die Routenbildung in der FAMO TrafficApp erfolgt in mehreren Schritten:

1. **Koordinaten sammeln**: Stopps mit (lat, lon) werden vorbereitet
2. **OSRM anfragen**: Primärer Routing-Service (Open Source Routing Machine)
3. **Fallback aktivieren**: Bei OSRM-Ausfall → Haversine-Distanz
4. **Baustellen prüfen**: Route wird auf Baustellen überprüft
5. **Geometrie bereitstellen**: Polyline für Frontend-Visualisierung

### Routing-Architektur

```
Frontend (Route anzeigen)
    ↓
API Endpoint (/api/tour/route-details)
    ↓
OSRM Client (services/osrm_client.py)
    ↓
OSRM Server (http://router.project-osrm.org)
    ↓
Route mit Geometrie (Polyline)
    ↓
Baustellen-Integration (services/construction_service.py)
    ↓
Finale Route mit Verzögerungen
```

---

## 🔄 Routing-Flow

### 1. Route-Anfrage vom Frontend

**Endpoint:** `POST /api/tour/route-details`

**Request Body:**
```json
{
    "stops": [
        {"lat": 51.05, "lon": 13.74, "name": "Kunde 1"},
        {"lat": 51.06, "lon": 13.75, "name": "Kunde 2"}
    ],
    "include_depot": true
}
```

### 2. Koordinaten vorbereiten

**Datei:** `routes/workflow_api.py` (Zeile 2424-2483)

```python
# Depot-Koordinaten (FAMO Dresden)
depot_coords = (51.01127, 13.70161)

coords_list = []
if include_depot:
    coords_list.append(depot_coords)

for stop in stops:
    coords_list.append((lat, lon))
```

### 3. Route pro Segment berechnen

**Datei:** `routes/workflow_api.py` (Zeile 2489-2536)

Für jedes Segment (von → zu):
1. OSRM Client aufrufen
2. Route mit Geometrie abrufen
3. Bei Fehler: Haversine-Fallback

### 4. OSRM-Anfrage

**Datei:** `services/osrm_client.py` (Zeile 69-141)

**API-URL Format:**
```
{base_url}/route/v1/driving/{coords}?overview=full&geometries=polyline
```

**Parameter:**
- `overview=full`: Detaillierte Geometrie (nicht nur vereinfacht)
- `geometries=polyline`: Polyline-Encoding (komprimiert)
- `alternatives=false`: Nur eine Route (nicht mehrere Alternativen)

**Response:**
```json
{
    "code": "Ok",
    "routes": [{
        "distance": 3500,      // Meter
        "duration": 312,       // Sekunden
        "geometry": "encoded_polyline_string"
    }]
}
```

### 5. Fallback bei OSRM-Ausfall

**Datei:** `services/osrm_client.py` (Zeile 118-141)

Wenn OSRM nicht verfügbar:
- **Haversine-Distanz** berechnen (Luftlinie)
- **Faktor 1.3** für reale Straßendistanz
- **Geschwindigkeit 50 km/h** (Durchschnitt Stadtverkehr)
- **Keine Geometrie** (Frontend zeichnet gerade Linie)

### 6. Baustellen-Integration (optional)

**Datei:** `backend/services/real_routing.py` (Zeile 239-317)

**Schritte:**
1. Alle Route-Punkte sammeln
2. Baustellen in der Nähe finden (ConstructionService)
3. Prüfen ob Route durch Baustelle führt
4. Verzögerungen hinzufügen:
   - Komplette Sperrung: +20 Minuten
   - Brücke/Tunnel: +15 Minuten
   - Standard: +10 Minuten

### 7. Response an Frontend

**Datei:** `routes/workflow_api.py` (Zeile 2537-2542)

```json
{
    "routes": [
        {
            "from": {"lat": 51.05, "lon": 13.74},
            "to": {"lat": 51.06, "lon": 13.75},
            "distance_km": 3.5,
            "duration_minutes": 5.2,
            "geometry": "encoded_polyline",
            "source": "osrm"
        }
    ],
    "total_distance_km": 28.5,
    "total_duration_minutes": 42.0
}
```

---

## 📁 Beteiligte Dateien

### Core Routing Services

| Datei | Zweck | Wichtigste Funktionen |
|-------|-------|----------------------|
| `services/osrm_client.py` | OSRM Client | `get_route()`, `get_distance_matrix()` |
| `backend/services/real_routing.py` | Erweiterter Routing-Service | `calculate_route()`, `_integrate_construction_data()` |

### API Endpoints

| Datei | Endpoint | Zweck |
|-------|----------|-------|
| `routes/workflow_api.py` | `POST /api/tour/route-details` | Route-Details für Frontend |
| `routes/workflow_api.py` | `POST /api/llm/optimize` | LLM-Routenoptimierung |
| `routes/ki_routes.py` | `POST /api/ki/calculate-routes` | KI-Routenberechnung |

### Traffic Integration

| Datei | Zweck |
|-------|-------|
| `services/construction_service.py` | Baustellen-Daten aus OpenStreetMap |
| `services/traffic_data_service.py` | Live-Traffic-Daten (Platzhalter) |

### Konfiguration

| Datei | Zweck |
|-------|-------|
| `config.env` | OSRM_BASE_URL, OSRM_PROFILE, OSRM_TIMEOUT |
| `docker-compose.yml` | Lokale OSRM-Instanz (optional) |

### Frontend

| Datei | Zweck |
|-------|-------|
| `frontend/index.html` | Route-Visualisierung mit Leaflet |

---

## 🔧 Komponenten-Details

### 1. OSRM Client (`services/osrm_client.py`)

**Klasse:** `OSRMClient`

**Initialisierung:**
```python
client = OSRMClient(base_url="http://router.project-osrm.org")
# Oder automatisch aus config.env: OSRM_BASE_URL
```

**Verfügbarkeitsprüfung:**
- Automatisch beim Initialisieren
- Test-Route: Berlin-Koordinaten
- Bei Fehler: `available = False`

**Hauptmethoden:**

#### `get_route(coords: List[Tuple[float, float]])`

**Input:**
```python
coords = [(51.05, 13.74), (51.06, 13.75)]  # (lat, lon)
```

**Output:**
```python
{
    "geometry": "encoded_polyline_string",  # Polyline (kann None sein)
    "distance_km": 3.5,
    "duration_min": 5.2,
    "source": "osrm"  # oder "haversine"
}
```

**Interner Ablauf:**
1. Prüfe ob OSRM verfügbar (`self._available`)
2. Baue OSRM-URL: `/route/v1/driving/{lon},{lat};{lon},{lat}?overview=full&geometries=polyline`
3. HTTP GET Request (timeout: 10s)
4. Parse JSON Response
5. Validiere Geometrie (nicht leer)
6. Bei Fehler: Haversine-Fallback

#### `get_distance_matrix(...)`

**Zweck:** Distanzmatrix für mehrere Punkte (für Optimierung)

**OSRM Table API:**
```
/table/v1/driving/{coords}?sources={0,1}&destinations={2,3}
```

### 2. Real Routing Service (`backend/services/real_routing.py`)

**Klasse:** `RealRoutingService`

**Routing-Priorität:**
1. **OSRM** (wenn `OSRM_BASE_URL` gesetzt)
2. **Mapbox** (wenn `MAPBOX_ACCESS_TOKEN` gesetzt)
3. **Fallback** (Haversine)

**Hauptmethode:**

#### `async calculate_route(points: List[RoutePoint]) -> FullRoute`

**Input:**
```python
points = [
    RoutePoint(lat=51.05, lon=13.74, address="Straße 1", name="Kunde 1"),
    RoutePoint(lat=51.06, lon=13.75, address="Straße 2", name="Kunde 2")
]
```

**Output:**
```python
FullRoute(
    total_distance_km=3.5,
    total_duration_minutes=5,
    total_traffic_delay=10,  # Baustellen-Verzögerung
    segments=[RouteSegment(...)],
    avoided_issues=["Baustelle umfahren: road_construction"]
)
```

**Ablauf:**
1. Versuche OSRM (`_calculate_osrm()`)
2. Wenn fehlgeschlagen: Versuche Mapbox (`_calculate_mapbox()`)
3. Wenn beide fehlgeschlagen: Fallback (`_fallback()`)
4. Baustellen-Integration (`_integrate_construction_data()`)

**Baustellen-Integration:**
- Prüft ob Route durch Baustellen führt
- Fügt Verzögerungen hinzu (10-20 Min pro Baustelle)
- Markiert umfahrene Baustellen

### 3. Construction Service (`services/construction_service.py`)

**Klasse:** `ConstructionService`

**Zweck:** Baustellen-Daten aus OpenStreetMap abrufen

**Hauptmethoden:**

#### `get_construction_sites_in_bbox(min_lat, min_lon, max_lat, max_lon)`

**Overpass Query:**
```overpass
[out:json][timeout:25];
(
  way["highway"]["construction"](...);
  way["barrier"="construction"](...);
);
out geom;
```

#### `check_route_through_construction(route_geometry)`

**Prüfung:**
- Baustellen in 100m Buffer um Route
- Minimale Distanz < 50m → Route betroffen
- Gibt betroffene Baustellen zurück

---

## 🛡️ Fallback-Mechanismen

### Fallback-Hierarchie

```
1. OSRM (öffentlicher Server: router.project-osrm.org)
   ↓ (bei Fehler)
2. OSRM (lokaler Server: localhost:5000)
   ↓ (bei Fehler)
3. Haversine-Distanz (Luftlinie × 1.3)
```

### Haversine-Berechnung

**Formel:**
```python
R = 6371.0  # Erdradius in km
a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
c = 2 × atan2(√a, √(1-a))
distance = R × c × 1.3  # Faktor für Stadtverkehr
```

**Geschwindigkeit:**
- Stadtverkehr: 50 km/h
- Autobahn: 100 km/h (nicht implementiert)

**Zeitberechnung:**
```python
duration_minutes = (distance_km / 50.0) * 60
```

---

## 🚧 Baustellen-Integration

### Ablauf

1. **Route-Geometrie sammeln**
   ```python
   all_geometry_points = []
   for segment in route.segments:
       all_geometry_points.extend(segment.route_geometry)
   ```

2. **Baustellen finden**
   ```python
   goes_through, affected_sites = construction_service.check_route_through_construction(
       all_geometry_points
   )
   ```

3. **Verzögerungen berechnen**
   - Komplette Sperrung (`access=no`): +20 Min
   - Brücke/Tunnel: +15 Min
   - Standard: +10 Min

4. **Route aktualisieren**
   - Verzögerung proportional auf Segmente aufteilen
   - `total_traffic_delay` erhöhen
   - `avoided_issues` Liste erweitern

### Konfiguration

**Overpass API URL:**
```python
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
```

**Cache:**
- TTL: 1 Stunde
- Cache-Key: Bounding Box Koordinaten

---

## 🌐 API-Endpoints

### 1. Route-Details für Visualisierung

**Endpoint:** `POST /api/tour/route-details`

**Datei:** `routes/workflow_api.py` (Zeile 2424)

**Verwendung:** Frontend zeigt Route auf Karte

**Request:**
```json
{
    "stops": [
        {"lat": 51.05, "lon": 13.74, "name": "Kunde 1"},
        {"lat": 51.06, "lon": 13.75, "name": "Kunde 2"}
    ],
    "include_depot": true
}
```

**Response:**
```json
{
    "routes": [
        {
            "from": {"lat": 51.05, "lon": 13.74},
            "to": {"lat": 51.06, "lon": 13.75},
            "distance_km": 3.5,
            "duration_minutes": 5.2,
            "geometry": "encoded_polyline",
            "source": "osrm"
        }
    ],
    "total_distance_km": 28.5,
    "total_duration_minutes": 42.0,
    "source": "osrm"
}
```

### 2. LLM-Routenoptimierung

**Endpoint:** `POST /api/llm/optimize`

**Datei:** `routes/workflow_api.py` (Zeile 2373)

**Verwendung:** KI-optimierte Reihenfolge der Stopps

**Intern:** Verwendet OSRM für Distanzberechnung

### 3. Tour-Zeit-Schätzung

**Funktion:** `_estimate_tour_time_without_return()`

**Datei:** `routes/workflow_api.py` (Zeile 210)

**Verwendung:** Schätzt Fahrzeit für Tour (ohne Rückfahrt)

**OSRM-Parameter:**
- Depot → erster Kunde → alle weiteren Kunden
- **OHNE** Rückfahrt zum Depot

---

## ⚙️ Konfiguration

### Environment Variables

**Datei:** `config.env`

```bash
# OSRM Configuration
OSRM_BASE_URL=http://router.project-osrm.org
OSRM_PROFILE=driving
OSRM_TIMEOUT=20

# Alternative: Lokaler OSRM Server
# OSRM_BASE_URL=http://localhost:5000

# Mapbox (optional, Fallback)
MAPBOX_ACCESS_TOKEN=your_token_here

# Overpass API (für Baustellen)
OVERPASS_API_URL=https://overpass-api.de/api/interpreter
```

### Docker-Compose (lokale OSRM-Instanz)

**Datei:** `docker-compose.yml`

```yaml
services:
  osrm:
    image: osrm/osrm-backend:latest
    ports:
      - "5000:5000"
    volumes:
      - ./osrm:/data/osrm-backend
```

**Verwendung:**
1. OSM-Daten herunterladen
2. OSRM-Daten vorbereiten (`osrm-extract`, `osrm-contract`)
3. Docker-Container starten
4. `OSRM_BASE_URL=http://localhost:5000` in `config.env`

---

## 🔗 Abhängigkeiten zwischen Komponenten

```
routes/workflow_api.py
    ├── get_osrm_client() → services/osrm_client.py
    │   └── OSRMClient.get_route() → OSRM Server
    │
    └── get_route_details() → Frontend

backend/services/real_routing.py
    ├── RealRoutingService.calculate_route()
    │   ├── _calculate_osrm() → OSRM Server
    │   ├── _calculate_mapbox() → Mapbox API (optional)
    │   └── _fallback() → Haversine
    │
    └── _integrate_construction_data()
        └── services/construction_service.py
            └── Overpass API → OpenStreetMap
```

---

## 📊 Datenfluss-Diagramm

```
[Frontend]
    │
    ├─→ POST /api/tour/route-details
    │       │
    │       └─→ routes/workflow_api.py::get_route_details()
    │               │
    │               ├─→ Koordinaten vorbereiten
    │               │
    │               └─→ Für jedes Segment:
    │                       │
    │                       ├─→ services/osrm_client.py::get_route()
    │                       │       │
    │                       │       ├─→ OSRM verfügbar? → HTTP GET
    │                       │       │   └─→ /route/v1/driving/{coords}
    │                       │       │
    │                       │       └─→ Fallback: Haversine
    │                       │
    │                       └─→ Route mit Geometrie
    │
    └─→ Response mit Routes
            │
            └─→ Leaflet Visualisierung
```

---

## 🐛 Troubleshooting

### Problem: Route wird als Luftlinie angezeigt

**Ursache:** OSRM liefert keine Geometrie

**Lösung:**
1. Prüfe OSRM-URL: `OSRM_BASE_URL` in `config.env`
2. Prüfe OSRM-Verfügbarkeit: Server erreichbar?
3. Prüfe Parameter: `overview=full&geometries=polyline` gesetzt?

**Code-Änderung:**
```python
# services/osrm_client.py, Zeile 92
route_url = f"{self.base_url}/route/v1/driving/{coords_str}?overview=full&geometries=polyline"
```

### Problem: Baustellen werden nicht erkannt

**Ursache:** Overpass API nicht erreichbar oder keine Baustellen in der Region

**Lösung:**
1. Prüfe Overpass API: `https://overpass-api.de/api/interpreter`
2. Prüfe Cache: Baustellen werden 1 Stunde gecacht
3. Prüfe Logs: `[CONSTRUCTION]` Meldungen

### Problem: Timeout bei OSRM-Anfragen

**Ursache:** OSRM-Server überlastet oder langsam

**Lösung:**
1. Erhöhe Timeout: `OSRM_TIMEOUT=30` in `config.env`
2. Verwende lokalen OSRM-Server
3. Fallback aktivieren (automatisch)

---

## 📝 Zusammenfassung

### Routing-Stack

1. **OSRM Client** (`services/osrm_client.py`)
   - Primärer Routing-Service
   - Polyline-Geometrie für Straßenrouten
   - Haversine-Fallback

2. **Real Routing Service** (`backend/services/real_routing.py`)
   - Erweiterte Routing-Funktionen
   - Baustellen-Integration
   - Mapbox-Fallback (optional)

3. **Construction Service** (`services/construction_service.py`)
   - Baustellen-Daten aus OSM
   - Route-Prüfung auf Baustellen
   - Verzögerungs-Berechnung

4. **API Endpoints** (`routes/workflow_api.py`)
   - `/api/tour/route-details` für Frontend
   - `/api/llm/optimize` für KI-Optimierung

### Wichtige Konstanten

- **Depot:** (51.01127, 13.70161) - FAMO Dresden
- **Geschwindigkeit:** 50 km/h (Stadtverkehr)
- **Haversine-Faktor:** 1.3 (Luftlinie → Straßendistanz)
- **OSRM Timeout:** 20 Sekunden (Standard)

---

**Letzte Aktualisierung:** 2025-11-05  
**Autor:** Code Audit System  
**Version:** 1.0

