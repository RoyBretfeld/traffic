# Blitzer & Hindernisse Integration – Vollständige Dokumentation

**Datum:** 2025-11-20  
**Version:** 1.0  
**Status:** ✅ Implementiert und produktionsreif

---

## 📋 Übersicht

Die Blitzer & Hindernisse-Integration zeigt relevante Verkehrsinformationen entlang einer Route an:
- **Blitzer/Radar** (Speed Cameras) – Warnungen, ändern Route nicht
- **Hindernisse** (Traffic Incidents) – Baustellen, Unfälle, Sperrungen – können Route beeinflussen

### Funktionsweise

1. **Route-Berechnung:** Frontend sendet Stopps an `/api/tour/route-details`
2. **Blitzer/Hindernisse-Suche:** Backend dekodiert Route-Geometrie und sucht relevante Einträge
3. **Filterung:** Nur Einträge innerhalb des definierten Radius werden zurückgegeben
4. **Anzeige:** Frontend zeigt Marker auf der Karte und Info-Banner

---

## 🎯 Filterung & Kriterien

### Blitzer (Speed Cameras)

- **Radius:** 1 km um die Route
- **Filterung:** Alle Blitzer innerhalb des Radius
- **Typen:** `fixed`, `mobile`, `section_control`

### Hindernisse (Traffic Incidents)

- **Radius:** 300 m (0.3 km) um die Route
- **Severity-Filter:** Nur `medium`, `high`, `critical` (keine `low`)
- **Radius-Berücksichtigung:** Wenn Hindernis einen größeren `radius_km` hat, wird dieser berücksichtigt
- **Typen:** `construction`, `accident`, `closure`

**Beispiel:**
- Hindernis 1: 500 m entfernt, Severity "low" → **nicht angezeigt**
- Hindernis 2: 250 m entfernt, Severity "medium" → **angezeigt**
- Hindernis 3: 400 m entfernt, Severity "high", radius_km=0.5 → **angezeigt** (weil radius_km > 300 m)

---

## 🔧 Backend-Implementierung

### Datei: `backend/services/real_routing.py`

**Funktion:** `build_route_details()`

```python
# Dekodiere Polyline6-Geometrie zu Route-Koordinaten
route_coords = _decode_polyline6_to_coords(result["geometry_polyline6"])

# Hole Blitzer entlang der Route (innerhalb 1 km)
cameras = traffic_service.get_cameras_near_route(route_coords, max_distance_km=1.0)

# Hole Hindernisse entlang der Route (innerhalb 300m)
incidents = traffic_service.get_incidents_near_route(route_coords, max_distance_km=0.3)

# Füge zur Response hinzu
result["speed_cameras"] = [...]
result["traffic_incidents"] = [...]
```

### Datei: `backend/services/live_traffic_data.py`

**Funktionen:**
- `get_cameras_near_route()` – Findet Blitzer entlang Route
- `get_incidents_near_route()` – Findet Hindernisse entlang Route
- `_distance_to_route()` – Berechnet minimale Distanz zur Route
- `_point_to_line_distance()` – Präzise Distanzberechnung mit Projektion

**Filterung in `get_incidents_near_route()`:**
```python
# Nur Hindernisse mit mindestens "medium" Severity
if incident.severity in ["medium", "high", "critical"]:
    relevant_incidents.append(incident)
```

---

## 🖥️ Frontend-Implementierung

### Datei: `frontend/index.html`

**Funktionen:**
- `addSpeedCameraMarker()` – Zeigt Blitzer-Marker auf Karte
- `addTrafficIncidentMarker()` – Zeigt Hindernisse-Marker auf Karte
- `showSpeedCameraInfo()` – Info-Banner mit Anzahl
- `showTrafficIncidentInfo()` – Info-Banner mit Anzahl
- `clearSpeedCameraMarkers()` – Entfernt alle Blitzer-Marker
- `clearTrafficIncidentMarkers()` – Entfernt alle Hindernisse-Marker

**Integration in `visualizeRoute()` (Zeilen 4542-4565):**
```javascript
// Zeige Blitzer entlang der Route
if (routeData.speed_cameras && Array.isArray(routeData.speed_cameras) && routeData.speed_cameras.length > 0) {
    clearSpeedCameraMarkers();
    routeData.speed_cameras.forEach(camera => {
        addSpeedCameraMarker(camera);
    });
    showSpeedCameraInfo(routeData.speed_camera_count || routeData.speed_cameras.length);
}

// Zeige Hindernisse entlang der Route
if (routeData.traffic_incidents && Array.isArray(routeData.traffic_incidents) && routeData.traffic_incidents.length > 0) {
    clearTrafficIncidentMarkers();
    routeData.traffic_incidents.forEach(incident => {
        addTrafficIncidentMarker(incident);
    });
    showTrafficIncidentInfo(routeData.traffic_incident_count || routeData.traffic_incidents.length);
}
```

---

## 📡 API-Endpunkte

### Route-Details (mit Blitzer/Hindernisse)

**Endpoint:** `POST /api/tour/route-details`

**Request:**
```json
{
  "stops": [
    {"lat": 51.0504, "lon": 13.7373},
    {"lat": 51.0522, "lon": 13.7380}
  ],
  "geometries": "polyline6"
}
```

**Response:**
```json
{
  "geometry_polyline6": "...",
  "total_distance_m": 12345,
  "total_duration_s": 1800,
  "source": "osrm",
  "speed_cameras": [
    {
      "camera_id": "cam_001",
      "type": "fixed",
      "lat": 51.0510,
      "lon": 13.7375,
      "direction": "both",
      "speed_limit": 50,
      "description": "Blitzer Hauptbahnhof",
      "verified": true
    }
  ],
  "speed_camera_count": 1,
  "traffic_incidents": [
    {
      "incident_id": "inc_001",
      "type": "construction",
      "lat": 51.0504,
      "lon": 13.7373,
      "severity": "medium",
      "description": "Baustelle - rechte Spur gesperrt",
      "delay_minutes": 5,
      "radius_km": 0.3,
      "affected_roads": []
    }
  ],
  "traffic_incident_count": 1
}
```

### Blitzer-Verwaltung

**GET** `/api/traffic/cameras?min_lat=51.0&min_lon=13.7&max_lat=51.1&max_lon=13.8`
- Holt Blitzer in einem Gebiet

**POST** `/api/traffic/cameras`
- Erstellt neuen Blitzer-Eintrag

**DELETE** `/api/traffic/cameras/{camera_id}`
- Löscht Blitzer-Eintrag

### Hindernisse-Verwaltung

**GET** `/api/traffic/incidents?min_lat=51.0&min_lon=13.7&max_lat=51.1&max_lon=13.8`
- Holt Hindernisse in einem Gebiet

**POST** `/api/traffic/incidents`
- Erstellt neues Hindernis

**DELETE** `/api/traffic/incidents/{incident_id}`
- Löscht Hindernis

---

## 🗄️ Datenbank-Schema

### Tabelle: `speed_cameras`

```sql
CREATE TABLE speed_cameras (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  camera_id TEXT UNIQUE NOT NULL,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  type TEXT NOT NULL,  -- "fixed", "mobile", "section_control"
  direction TEXT,  -- "north", "south", "east", "west", "both"
  speed_limit INTEGER,  -- Geschwindigkeitsbegrenzung in km/h
  description TEXT,
  verified INTEGER DEFAULT 0,  -- 0 = false, 1 = true
  last_seen TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

### Tabelle: `traffic_incidents`

```sql
CREATE TABLE traffic_incidents (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  incident_id TEXT UNIQUE NOT NULL,
  type TEXT NOT NULL,  -- "construction", "accident", "closure"
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  severity TEXT NOT NULL,  -- "low", "medium", "high", "critical"
  description TEXT,
  start_time TEXT,
  end_time TEXT,
  delay_minutes INTEGER DEFAULT 0,  -- Geschätzte Verzögerung in Minuten
  radius_km REAL DEFAULT 0.5,  -- Radius in km, in dem das Hindernis relevant ist
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

---

## 🧪 Test & Debugging

### Scripts

**1. Prüfe Datenbank-Inhalt:**
```bash
python scripts/check_traffic_incidents.py
```

**2. Erstelle Test-Hindernisse:**
```bash
python scripts/create_test_incidents.py
```

### Browser-Konsole

**Erfolgreiche Integration zeigt:**
```
[ROUTE-VIS] 2 Blitzer entlang der Route gefunden
[ROUTE-VIS] 1 Hindernisse entlang der Route gefunden
Route-Details: 2 Blitzer, 1 Hindernisse gefunden
```

**Wenn keine gefunden:**
```
Route-Details: Keine Blitzer/Hindernisse gefunden (Route-Länge: 150 Punkte)
```

### Logging

Backend-Logs zeigen:
- Anzahl gefundener Blitzer/Hindernisse
- Route-Koordinaten-Anzahl
- Fehler beim Laden (falls vorhanden)

---

## ⚙️ Konfiguration

### Filter-Parameter anpassen

**Datei:** `backend/services/real_routing.py` (Zeile 424, 441)

```python
# Blitzer-Radius (aktuell: 1.0 km)
cameras = traffic_service.get_cameras_near_route(route_coords, max_distance_km=1.0)

# Hindernisse-Radius (aktuell: 0.3 km = 300 m)
incidents = traffic_service.get_incidents_near_route(route_coords, max_distance_km=0.3)
```

**Datei:** `backend/services/live_traffic_data.py` (Zeile 481-488)

```python
# Severity-Filter anpassen
if incident.severity in ["medium", "high", "critical"]:  # Hier anpassen
    relevant_incidents.append(incident)
```

---

## 🔍 Troubleshooting

### Problem: Keine Blitzer/Hindernisse werden angezeigt

**Lösung:**
1. Prüfe ob Daten in DB vorhanden: `python scripts/check_traffic_incidents.py`
2. Prüfe Browser-Konsole auf Fehler
3. Prüfe Backend-Logs auf Fehler
4. Stelle sicher, dass Route durch Gebiet mit Hindernissen führt

### Problem: Zu viele Hindernisse werden angezeigt

**Lösung:**
1. Reduziere `max_distance_km` in `real_routing.py` (Zeile 441)
2. Verschärfe Severity-Filter in `live_traffic_data.py` (Zeile 481)
3. Reduziere `radius_km` bei Hindernissen in DB

### Problem: Server-Fehler beim Laden

**Lösung:**
1. Prüfe ob Tabellen existieren (werden automatisch erstellt)
2. Prüfe Backend-Logs auf detaillierte Fehlermeldungen
3. Stelle sicher, dass `LiveTrafficDataService` korrekt initialisiert wird

---

## 📝 Rechtlicher Hinweis

**WICHTIG:** Blitzer.de bietet keine öffentliche API. Die Nutzungsbedingungen von Blitzer.de verbieten die kommerzielle Nutzung ihrer Daten ohne ausdrückliche schriftliche Zustimmung.

**Empfehlung:**
1. Kontaktieren Sie Blitzer.de direkt für eine offizielle Genehmigung
2. Alternativ: Nutzen Sie andere Datenquellen mit offenen APIs
3. Oder: Pflegen Sie eigene Blitzer-Daten manuell in der Datenbank

**Aktuelle Implementierung:**
- Verwendet eigene Datenbank (`speed_cameras` Tabelle)
- Manuell eingetragene Daten
- Optional: GPX-Import (TODO)

---

## 🚀 Nächste Schritte / Erweiterungen

### Geplant

1. **GPX-Import für Blitzer:**
   - Import von GPX-Dateien mit Blitzer-Standorten
   - Automatische Erkennung von Typ und Richtung

2. **Live-Daten-Integration:**
   - OpenStreetMap Overpass API für Baustellen (bereits teilweise implementiert)
   - Externe Traffic-APIs (falls verfügbar)

3. **Route-Optimierung mit Hindernissen:**
   - Alternative Routen bei kritischen Hindernissen
   - Verzögerungs-Berechnung in Route-Zeit

4. **Benachrichtigungen:**
   - Push-Benachrichtigungen bei neuen Hindernissen
   - E-Mail-Benachrichtigungen für kritische Hindernisse

---

## 📚 Verwandte Dokumentation

- **Synonym-Erkennung & Blitzer:** `docs/SYNONYM_ERKENNUNG_UND_BLITZER.md`
- **Live-Traffic-Daten:** `docs/archive/consolidated_2025-11-13/LIVE_TRAFFIC_DATA.md`
- **API-Dokumentation:** `docs/API_DOKUMENTATION.md` (falls vorhanden)

---

**Ende der Dokumentation**  
**Letzte Aktualisierung:** 2025-11-20

