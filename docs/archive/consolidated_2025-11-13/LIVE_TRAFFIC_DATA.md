# Live-Traffic-Daten Integration

## Übersicht

Die TrafficApp integriert Live-Daten für:
- **Baustellen** (Verkehrshindernisse)
- **Unfälle** (Verkehrshindernisse)
- **Sperrungen** (Verkehrshindernisse)
- **Blitzer/Radar** (Warnungen, keine Hindernisse)

Diese Daten werden in die Routen-Optimierung einbezogen, um:
- Verzögerungen durch Hindernisse zu berücksichtigen
- Alternative Routen vorzuschlagen
- Fahrer über Blitzer zu informieren

## Architektur

### Backend-Service

**Datei:** `backend/services/live_traffic_data.py`

- `LiveTrafficDataService`: Hauptservice für Live-Daten
- `TrafficIncident`: Datenmodell für Hindernisse (Baustellen, Unfälle, Sperrungen)
- `SpeedCamera`: Datenmodell für Blitzer/Radar

### Datenquellen

1. **Autobahn API** (mautinfo.de) - Baustellen
   - Status: TODO (Beispiel-Implementierung vorhanden)
   - Rechtlich: Öffentliche Daten

2. **OpenStreetMap Overpass API** - Sperrungen
   - Status: Implementiert
   - Rechtlich: Open Data (ODbL)

3. **Eigene Datenbank** - Gespeicherte Hindernisse & Blitzer
   - Tabellen: `traffic_incidents`, `speed_cameras`
   - Status: Implementiert
   - Rechtlich: Eigene Daten

4. **Blitzer.de** - Blitzer-Standorte
   - Status: **NICHT implementiert** (keine öffentliche API)
   - Rechtlich: **WICHTIG - siehe unten**

## Blitzer.de Integration

### Rechtlicher Hinweis

**WICHTIG:** Blitzer.de bietet keine öffentliche API. Die Nutzungsbedingungen von Blitzer.de verbieten die kommerzielle Nutzung ihrer Daten ohne ausdrückliche schriftliche Zustimmung.

**Empfehlung:**
1. Kontaktieren Sie Blitzer.de direkt für eine offizielle Genehmigung
2. Alternativ: Nutzen Sie andere Datenquellen mit offenen APIs
3. Oder: Pflegen Sie eigene Blitzer-Daten manuell

### Implementierung

Die TrafficApp unterstützt Blitzer-Daten über:

1. **Datenbank-Tabelle:** `speed_cameras`
   - Manuell eingetragene Daten
   - Import via API-Endpunkte
   - GPX-Import (TODO)

2. **API-Endpunkte:**
   - `GET /api/traffic/cameras` - Blitzer in einem Gebiet abrufen
   - `POST /api/traffic/cameras` - Blitzer-Eintrag erstellen
   - `DELETE /api/traffic/cameras/{camera_id}` - Blitzer-Eintrag löschen

3. **Integration in Routen:**
   - Blitzer werden als **Warnungen** behandelt (nicht als Hindernisse)
   - Sie ändern die Route nicht, informieren aber den Fahrer
   - Optional in Route-Details-Response enthalten

### Datenmodell

```python
@dataclass
class SpeedCamera:
    camera_id: str
    lat: float
    lon: float
    type: str  # "fixed", "mobile", "section_control"
    direction: Optional[str]  # "north", "south", "east", "west", "both"
    speed_limit: Optional[int]  # Geschwindigkeitsbegrenzung in km/h
    description: Optional[str]
    verified: bool  # Ob Standort verifiziert ist
    last_seen: Optional[datetime]
```

## Integration in Routen-Optimierung

### Hindernisse (Baustellen, Unfälle, Sperrungen)

1. **Matrix-Anpassung:**
   - Hindernisse werden in der Distanz-Matrix berücksichtigt
   - Verzögerungen werden basierend auf Severity hinzugefügt:
     - `low`: 0.5× Verzögerung
     - `medium`: 1.0× Verzögerung
     - `high`: 1.5× Verzögerung
     - `critical`: 2.0× Verzögerung

2. **Alternative Routen:**
   - OSRM wird um alternative Routen gebeten, wenn kritische Hindernisse vorhanden sind
   - Parameter: `alternatives=true`, `number=3`

### Blitzer (Warnungen)

1. **Keine Route-Änderung:**
   - Blitzer ändern die Route nicht
   - Sie werden nur als Warnungen angezeigt

2. **Route-Details-Response:**
   - Optional: `speed_cameras` Array in Route-Details
   - Enthält alle Blitzer innerhalb 1 km der Route

## API-Endpunkte

### Hindernisse

- `GET /api/traffic/incidents` - Hindernisse in einem Gebiet
- `POST /api/traffic/incidents` - Hindernis erstellen
- `DELETE /api/traffic/incidents/{incident_id}` - Hindernis löschen

### Blitzer

- `GET /api/traffic/cameras` - Blitzer in einem Gebiet
- `POST /api/traffic/cameras` - Blitzer-Eintrag erstellen
- `DELETE /api/traffic/cameras/{camera_id}` - Blitzer-Eintrag löschen

## Frontend-Integration

### Karten-Marker

Blitzer können auf der Karte angezeigt werden:

```javascript
// Beispiel: Blitzer-Marker hinzufügen
const cameraIcon = L.divIcon({
    className: 'camera-marker',
    html: '<i class="fas fa-camera" style="font-size: 20px; color: #ff9800;"></i>',
    iconSize: [25, 25],
    iconAnchor: [12, 25]
});

L.marker([lat, lon], { icon: cameraIcon })
    .addTo(map)
    .bindPopup(`Blitzer: ${description}`);
```

### Route-Details

Blitzer-Warnungen werden automatisch in Route-Details-Responses eingefügt (falls vorhanden):

```json
{
    "routes": [...],
    "total_distance_km": 28.5,
    "total_duration_minutes": 42.0,
    "speed_cameras": [
        {
            "camera_id": "cam_001",
            "lat": 51.05,
            "lon": 13.73,
            "type": "fixed",
            "speed_limit": 50,
            "description": "Blitzer A4 Richtung Chemnitz"
        }
    ],
    "speed_camera_count": 1
}
```

## Datenbank-Schema

### `traffic_incidents`

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
    delay_minutes INTEGER DEFAULT 0,
    radius_km REAL DEFAULT 0.5,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

### `speed_cameras`

```sql
CREATE TABLE speed_cameras (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    camera_id TEXT UNIQUE NOT NULL,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    type TEXT NOT NULL,  -- "fixed", "mobile", "section_control"
    direction TEXT,  -- "north", "south", "east", "west", "both"
    speed_limit INTEGER,
    description TEXT,
    verified INTEGER DEFAULT 0,
    last_seen TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
```

## Nächste Schritte

1. **Autobahn API Integration:**
   - Implementiere echte Autobahn API (mautinfo.de)
   - Oder: Alternative Datenquelle finden

2. **Blitzer-Daten:**
   - Rechtliche Klärung mit Blitzer.de
   - Oder: Alternative Datenquelle finden
   - Oder: Manuelle Datenerfassung

3. **GPX-Import:**
   - Import-Funktion für GPX-Dateien (Blitzer-Standorte)
   - Validierung und Duplikatsprüfung

4. **Frontend-Visualisierung:**
   - Blitzer-Marker auf Karte
   - Toggle für Anzeige ein/aus
   - Popup mit Details

5. **Caching:**
   - Optimierung des Caching-Mechanismus
   - Separate Cache-Dauer für verschiedene Datentypen

## Rechtliche Hinweise

- **Blitzer.de:** Keine öffentliche API, Nutzungsbedingungen prüfen
- **OpenStreetMap:** ODbL-Lizenz beachten
- **Autobahn API:** Öffentliche Daten, keine Einschränkungen
- **Eigene Daten:** Vollständige Kontrolle, keine rechtlichen Probleme

## Testen

```bash
# Blitzer-Eintrag erstellen
curl -X POST http://localhost:8111/api/traffic/cameras \
  -H "Content-Type: application/json" \
  -d '{
    "camera_id": "test_001",
    "type": "fixed",
    "lat": 51.05,
    "lon": 13.73,
    "speed_limit": 50,
    "description": "Test-Blitzer",
    "verified": true
  }'

# Blitzer in Gebiet abrufen
curl "http://localhost:8111/api/traffic/cameras?min_lat=51.0&min_lon=13.7&max_lat=51.1&max_lon=13.8"
```

