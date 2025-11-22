# Synonym-Erkennung & Blitzer/Hindernisse – Technische Dokumentation

**Datum:** 2025-11-20  
**Version:** 1.0  
**Zweck:** Vollständige technische Dokumentation der Synonym-Erkennung und Blitzer/Hindernisse-Funktionalität

---

## 📋 Inhaltsverzeichnis

1. [Synonym-Erkennung](#1-synonym-erkennung)
2. [Blitzer & Hindernisse](#2-blitzer--hindernisse)
3. [Integration im Workflow](#3-integration-im-workflow)
4. [API-Endpunkte](#4-api-endpunkte)
5. [Datenbank-Schema](#5-datenbank-schema)

---

## 1. Synonym-Erkennung

### 1.1 Übersicht

Die Synonym-Erkennung löst Kunden-Namen und KdNr aus Tourplänen auf ihre echten Kundennummern und Adressen auf. Dies ist besonders wichtig, wenn:
- Auf Tourplänen keine vollständige Adresse vorhanden ist
- Die KdNr auf dem Tourplan nicht mit der echten Kundennummer übereinstimmt
- Kunden unter verschiedenen Namen/Aliasen auftreten (z.B. "Büttner" → "Peuget Büttner", KdNr 4318)

### 1.2 Architektur

**Kernkomponenten:**

1. **`SynonymStore`** (`backend/services/synonyms.py`)
   - Persistenter Store für Adress-Synonyme
   - Speichert Alias → Customer/Address/Coordinates Mapping
   - Prioritäts-basierte Suche

2. **`tour_plan_parser.py`** (`backend/parsers/tour_plan_parser.py`)
   - Integriert Synonym-Erkennung direkt beim CSV-Parsen
   - Prüft zuerst KdNr, dann Name
   - Setzt `_synonym_lat` und `_synonym_lon` wenn gefunden

3. **`tourplan_match.py`** (`backend/routes/tourplan_match.py`)
   - Verwendet Synonyme beim Matching/Geocoding
   - Überspringt Geocoding wenn Synonym bereits Koordinaten hat

### 1.3 Funktionsweise

#### Schritt 1: CSV-Parsing mit Synonym-Check

**Datei:** `backend/parsers/tour_plan_parser.py` (Zeilen 245-310)

```python
# 1. KdNr-Lookup (höchste Priorität)
if first_cell and synonym_store:
    kdnr_synonym = synonym_store.resolve(f"KdNr:{first_cell}")
    if kdnr_synonym:
        # Übernehme Adresse aus Synonym
        synonym_street = kdnr_synonym.street or street or ""
        synonym_postal_code = kdnr_synonym.postal_code or postal_code or ""
        synonym_city = kdnr_synonym.city or city or ""
        synonym_lat = kdnr_synonym.lat
        synonym_lon = kdnr_synonym.lon
        resolved_customer_id = kdnr_synonym.customer_id

# 2. Name-Lookup (falls KdNr nicht gefunden)
if not kdnr_synonym and customer_name and synonym_store:
    name_synonym = synonym_store.resolve(customer_name)
    if name_synonym:
        # Übernehme Adresse aus Synonym
        synonym_street = name_synonym.street or street or ""
        # ... (gleiche Logik wie bei KdNr)
```

**Priorität:**
1. **KdNr-Lookup** (`KdNr:{kdnr}`) - Priority 2 (höchste)
2. **Name-Lookup** (Kundenname) - Priority 1
3. **Fallback** - Normale Adress-Verarbeitung

#### Schritt 2: Synonym-Auflösung im SynonymStore

**Datei:** `backend/services/synonyms.py` (Zeilen 61-101)

```python
def resolve(self, alias: str) -> Optional[Synonym]:
    """
    Löst einen Alias auf (wird VOR Geocoding verwendet).
    """
    an = self._norm(alias)  # Normalisiert: lowercase, entfernt Sonderzeichen
    row = self.db.execute(
        "SELECT * FROM address_synonyms WHERE alias_norm=? AND active=1 ORDER BY priority DESC LIMIT 1",
        (an,)
    ).fetchone()
    
    if not row:
        return None
    
    # Nutzungsstatistik tracken
    try:
        self.db.execute("INSERT INTO synonym_hits(alias_norm) VALUES (?)", (an,))
        self.db.commit()
    except Exception:
        pass  # Ignorieren wenn Hit-Tabelle noch nicht existiert
    
    return Synonym(...)  # Synonym-Objekt mit allen Daten
```

**Normalisierung:**
- `_norm()` verwendet `normalize_token()` aus `common.normalize`
- Entfernt Sonderzeichen, konvertiert zu lowercase
- Beispiel: "Büttner" → "buettner", "KdNr:6000" → "kdnr:6000"

#### Schritt 3: Verwendung im Workflow

**Datei:** `backend/routes/tourplan_match.py` (Zeilen 295-308)

```python
# KRITISCH: Synonym-Check VOR Normalisierung
customer_name = customer.get('name', '')
synonym_hit = None
if customer_name:
    from common.synonyms import resolve_synonym
    synonym_hit = resolve_synonym(customer_name)

if synonym_hit:
    # Synonym gefunden - verwende die Synonym-Adresse
    addrs.append(synonym_hit.resolved_address)
else:
    # Normale Normalisierung
    addrs.append(normalize_address(full_address, ...))
```

**Vorteil:** Wenn Synonym bereits Koordinaten hat, wird Geocoding übersprungen (schneller, keine API-Kosten).

### 1.4 Datenbank-Schema

**Tabelle:** `address_synonyms`

```sql
CREATE TABLE address_synonyms (
  alias TEXT PRIMARY KEY,              -- Original-Alias (z.B. "Büttner")
  alias_norm TEXT NOT NULL,            -- Normalisierter Alias (z.B. "buettner")
  customer_id TEXT,                    -- Echte KdNr (z.B. "4318")
  customer_name TEXT,                  -- Echter Kundenname (z.B. "Peuget Büttner")
  street TEXT,                         -- Straße
  postal_code TEXT,                    -- PLZ
  city TEXT,                           -- Stadt
  country TEXT DEFAULT 'DE',           -- Land
  lat REAL,                            -- Breitengrad (optional)
  lon REAL,                            -- Längengrad (optional)
  note TEXT,                           -- Zusatzinfo (z.B. "PF")
  active INTEGER DEFAULT 1,            -- Aktiv (1) oder inaktiv (0)
  priority INTEGER DEFAULT 0,          -- Priorität (2=KdNr, 1=Name, 0=Sonst)
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

**Index:**
```sql
CREATE INDEX idx_address_synonyms_alias_norm ON address_synonyms(alias_norm);
CREATE INDEX idx_address_synonyms_priority ON address_synonyms(priority DESC);
```

**Nutzungsstatistik:**
```sql
CREATE TABLE synonym_hits (
  alias_norm TEXT NOT NULL,
  hit_at TEXT DEFAULT (datetime('now'))
);
```

### 1.5 Beispiel-Workflow

**Tourplan-Eintrag:**
```
KdNr: 6000, Name: "Büttner", Adresse: (leer)
```

**Verarbeitung:**
1. **Parser** liest KdNr "6000" und Name "Büttner"
2. **SynonymStore.resolve("KdNr:6000")** → Kein Treffer
3. **SynonymStore.resolve("Büttner")** → Treffer!
   - `customer_id`: "4318"
   - `customer_name`: "Peuget Büttner"
   - `street`: "Steigerstr. 1"
   - `postal_code`: "01705"
   - `city`: "Freital"
   - `lat`: 50.9999, `lon`: 13.6666
4. **Parser** setzt `_synonym_lat` und `_synonym_lon` im Customer-Dict
5. **Geocoding** wird übersprungen (Koordinaten bereits vorhanden)
6. **Ergebnis:** Kunde wird korrekt mit Adresse und Koordinaten verarbeitet

---

## 2. Blitzer & Hindernisse

### 2.1 Übersicht

Die Blitzer & Hindernisse-Funktion zeigt:
- **Blitzer/Radar** (Speed Cameras) - Warnungen, ändern Route nicht
- **Hindernisse** (Traffic Incidents) - Baustellen, Unfälle, Sperrungen - können Route beeinflussen

### 2.2 Architektur

**Kernkomponenten:**

1. **`LiveTrafficDataService`** (`backend/services/live_traffic_data.py`)
   - Service für Live-Traffic-Daten
   - `SpeedCamera` - Datenmodell für Blitzer
   - `TrafficIncident` - Datenmodell für Hindernisse

2. **`live_traffic_api.py`** (`backend/routes/live_traffic_api.py`)
   - API-Endpunkte für Blitzer und Hindernisse
   - `GET /api/traffic/cameras` - Blitzer in einem Gebiet
   - `GET /api/traffic/incidents` - Hindernisse in einem Gebiet

3. **Frontend** (`frontend/index.html`)
   - Toggle-Buttons für Blitzer/Hindernisse
   - Leaflet-Marker für Anzeige auf Karte
   - Integration in Route-Visualisierung

### 2.3 Funktionsweise

#### Backend: Blitzer-Daten abrufen

**Datei:** `backend/services/live_traffic_data.py` (Zeilen 557-595)

```python
def get_speed_cameras_in_area(
    self,
    bounds: Tuple[float, float, float, float],
    camera_types: List[str] = None
) -> List[SpeedCamera]:
    """
    Holt Blitzer/Radar-Standorte in einem bestimmten Gebiet.
    
    WICHTIG: Blitzer.de bietet keine öffentliche API. Diese Funktion verwendet:
    - Eigene Datenbank (manuell gepflegte Daten)
    - Optional: Importierte GPX-Dateien
    """
    min_lat, min_lon, max_lat, max_lon = bounds
    
    # Prüfe Cache
    if self._is_camera_cache_valid():
        cameras = [
            cam for cam in self.cached_cameras
            if min_lat <= cam.lat <= max_lat and min_lon <= cam.lon <= max_lon
        ]
        
        if camera_types:
            cameras = [cam for cam in cameras if cam.type in camera_types]
        
        return cameras
    
    # Hole neue Daten aus Datenbank
    # ...
```

**Datenmodell:**
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
```

#### Frontend: Blitzer anzeigen

**Datei:** `frontend/index.html` (Zeilen 3835-3963)

**Toggle-Funktion:**
```javascript
let showSpeedCameras = true;  // Standardmäßig an
let speedCameraMarkers = [];  // Array aller Blitzer-Marker

function toggleSpeedCameras() {
    showSpeedCameras = !showSpeedCameras;
    if (showSpeedCameras) {
        // Zeige alle Blitzer-Marker wieder an
        speedCameraMarkers.forEach(marker => {
            marker.addTo(map);
        });
        updateSpeedCameraToggleButton();
    } else {
        // Verstecke alle Blitzer-Marker
        speedCameraMarkers.forEach(marker => {
            marker.remove();
        });
        updateSpeedCameraToggleButton();
    }
}
```

**Marker hinzufügen:**
```javascript
function addSpeedCameraMarker(camera) {
    if (!map || !showSpeedCameras) {
        return;  // Karte nicht geladen oder Blitzer ausgeschaltet
    }
    
    // Icon-Farbe basierend auf Typ
    let iconColor = '#ff9800';  // Standard: Orange
    if (camera.type === 'fixed') {
        iconColor = '#ff5722';  // Rot-Orange für feste Blitzer
    } else if (camera.type === 'mobile') {
        iconColor = '#ff9800';  // Orange für mobile Blitzer
    }
    
    // Leaflet-Icon erstellen
    const icon = L.divIcon({
        html: `<i class="fas fa-camera" style="color: ${iconColor}; font-size: 20px;"></i>`,
        className: 'speed-camera-marker',
        iconSize: [20, 20],
        iconAnchor: [10, 10]
    });
    
    // Marker erstellen und zur Karte hinzufügen
    const marker = L.marker([camera.lat, camera.lon], { icon: icon });
    
    // Popup mit Blitzer-Details
    let popupContent = `<strong><i class="fas fa-camera"></i> Blitzer</strong><br>`;
    if (camera.type === 'fixed') {
        popupContent += `<span class="badge badge-danger">Fester Blitzer</span><br>`;
    } else if (camera.type === 'mobile') {
        popupContent += `<span class="badge badge-warning">Mobiler Blitzer</span><br>`;
    }
    if (camera.speed_limit) {
        popupContent += `Geschwindigkeitsbegrenzung: ${camera.speed_limit} km/h<br>`;
    }
    if (camera.description) {
        popupContent += `${camera.description}`;
    }
    marker.bindPopup(popupContent);
    
    marker.addTo(map);
    speedCameraMarkers.push(marker);
}
```

**UI-Button:**
```html
<h5 class="mt-3"><i class="fas fa-camera"></i> Blitzer & Hindernisse</h5>
<div class="d-flex gap-2">
    <button id="toggleSpeedCamerasBtn" class="btn btn-warning" 
            onclick="toggleSpeedCameras()" 
            title="Blitzer auf der Karte ein-/ausblenden">
        <i class="fas fa-eye-slash"></i> Blitzer ausblenden
    </button>
    <button id="toggleTrafficIncidentsBtn" class="btn btn-secondary" 
            onclick="toggleTrafficIncidents()" 
            title="Hindernisse auf der Karte ein-/ausblenden">
        <i class="fas fa-eye"></i> Hindernisse einblenden
    </button>
</div>
```

### 2.4 Datenbank-Schema

**Tabelle:** `speed_cameras`

```sql
CREATE TABLE speed_cameras (
  camera_id TEXT PRIMARY KEY,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  type TEXT NOT NULL,  -- "fixed", "mobile", "section_control"
  direction TEXT,      -- "north", "south", "east", "west", "both"
  speed_limit INTEGER, -- Geschwindigkeitsbegrenzung in km/h
  description TEXT,
  verified INTEGER DEFAULT 0,  -- 0=unverifiziert, 1=verifiziert
  last_seen TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

**Tabelle:** `traffic_incidents`

```sql
CREATE TABLE traffic_incidents (
  incident_id TEXT PRIMARY KEY,
  lat REAL NOT NULL,
  lon REAL NOT NULL,
  type TEXT NOT NULL,  -- "construction", "accident", "closure"
  severity TEXT NOT NULL,  -- "low", "medium", "high", "critical"
  description TEXT,
  delay_minutes REAL,  -- Geschätzte Verzögerung in Minuten
  radius_km REAL DEFAULT 0.5,  -- Radius in km, in dem das Hindernis relevant ist
  start_time TEXT,
  end_time TEXT,
  created_at TEXT DEFAULT (datetime('now')),
  updated_at TEXT DEFAULT (datetime('now'))
);
```

### 2.5 Rechtlicher Hinweis

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

## 3. Integration im Workflow

### 3.1 Synonym-Erkennung im CSV-Parsing

**Workflow:**
1. CSV-Datei wird hochgeladen
2. `tour_plan_parser.py` parst die Datei
3. Für jeden Kunden:
   - Prüft zuerst KdNr-Lookup (`KdNr:{kdnr}`)
   - Falls nicht gefunden: Name-Lookup
   - Wenn Synonym gefunden: Übernimmt Adresse und Koordinaten
   - Wenn keine Adresse vorhanden: Normalisiert Adresse für Geocoding
4. Geocoding wird nur durchgeführt, wenn keine Koordinaten vorhanden sind

**Vorteile:**
- ✅ Schneller (kein Geocoding nötig wenn Synonym Koordinaten hat)
- ✅ Kostengünstiger (weniger API-Calls)
- ✅ Zuverlässiger (bekannte Adressen werden nicht falsch geocodiert)

### 3.2 Blitzer/Hindernisse in Route-Visualisierung

**Aktueller Status:**
- ✅ Frontend-Code vorhanden für Blitzer/Hindernisse-Anzeige
- ✅ Backend liefert `speed_cameras` und `traffic_incidents` in der `route-details` Response
- ✅ Route-spezifische Filterung implementiert (nur relevante Hindernisse)

**Implementierung:**
```javascript
// In visualizeRoute() Funktion (frontend/index.html, Zeile 4542-4565)
if (routeData.speed_cameras && Array.isArray(routeData.speed_cameras) && routeData.speed_cameras.length > 0) {
    console.log(`[ROUTE-VIS] ${routeData.speed_cameras.length} Blitzer entlang der Route gefunden`);
    clearSpeedCameraMarkers();
    routeData.speed_cameras.forEach(camera => {
        addSpeedCameraMarker(camera);
    });
    showSpeedCameraInfo(routeData.speed_camera_count || routeData.speed_cameras.length);
}

if (routeData.traffic_incidents && Array.isArray(routeData.traffic_incidents) && routeData.traffic_incidents.length > 0) {
    console.log(`[ROUTE-VIS] ${routeData.traffic_incidents.length} Hindernisse entlang der Route gefunden`);
    clearTrafficIncidentMarkers();
    routeData.traffic_incidents.forEach(incident => {
        addTrafficIncidentMarker(incident);
    });
    showTrafficIncidentInfo(routeData.traffic_incident_count || routeData.traffic_incidents.length);
}
```

**Backend-Implementierung:**
- `backend/services/real_routing.py` → `build_route_details()` Funktion (Zeilen 406-468)
- Dekodiert Polyline6-Geometrie zu Route-Koordinaten
- Ruft `LiveTrafficDataService.get_cameras_near_route()` auf (max_distance: 1 km)
- Ruft `LiveTrafficDataService.get_incidents_near_route()` auf (max_distance: 0.3 km)
- Fügt `speed_cameras` und `traffic_incidents` zur Response hinzu

---

## 4. API-Endpunkte

### 4.1 Synonym-API

**Aktuell:** Keine explizite API (wird intern verwendet)

**Mögliche Erweiterung:**
- `GET /api/synonyms?alias={alias}` - Synonym auflösen
- `GET /api/synonyms/list` - Alle Synonyme auflisten
- `POST /api/synonyms` - Synonym hinzufügen
- `PUT /api/synonyms/{alias}` - Synonym aktualisieren
- `DELETE /api/synonyms/{alias}` - Synonym löschen

### 4.2 Blitzer-API

**Endpunkt:** `GET /api/traffic/cameras`

**Parameter:**
- `min_lat` (float, required) - Minimale Breitengrad
- `min_lon` (float, required) - Minimale Längengrad
- `max_lat` (float, required) - Maximale Breitengrad
- `max_lon` (float, required) - Maximale Längengrad
- `types` (string, optional) - Komma-getrennte Liste: `fixed,mobile,section_control`

**Response:**
```json
{
  "cameras": [
    {
      "camera_id": "cam_001",
      "type": "fixed",
      "lat": 51.0504,
      "lon": 13.7373,
      "direction": "both",
      "speed_limit": 50,
      "description": "Fester Blitzer auf B170",
      "verified": true
    }
  ],
  "count": 1,
  "legal_notice": "Daten aus eigener Datenbank. Bitte prüfen Sie rechtliche Aspekte bei Nutzung externer Datenquellen."
}
```

**Endpunkt:** `POST /api/traffic/cameras`

**Request Body:**
```json
{
  "camera_id": "cam_001",
  "lat": 51.0504,
  "lon": 13.7373,
  "type": "fixed",
  "direction": "both",
  "speed_limit": 50,
  "description": "Fester Blitzer auf B170",
  "verified": true
}
```

### 4.3 Hindernisse-API

**Endpunkt:** `GET /api/traffic/incidents`

**Parameter:**
- `min_lat`, `min_lon`, `max_lat`, `max_lon` (float, required)
- `types` (string, optional) - `construction,accident,closure`
- `severity` (string, optional) - `low,medium,high,critical`

**Response:**
```json
{
  "incidents": [
    {
      "incident_id": "inc_001",
      "type": "construction",
      "lat": 51.0504,
      "lon": 13.7373,
      "severity": "medium",
      "description": "Baustelle auf B170",
      "delay_minutes": 15.0,
      "radius_km": 0.5
    }
  ],
  "count": 1
}
```

---

## 5. Datenbank-Schema

### 5.1 Synonym-Tabellen

**`address_synonyms`** - Haupttabelle für Synonyme
**`synonym_hits`** - Nutzungsstatistik (optional)

### 5.2 Blitzer/Hindernisse-Tabellen

**`speed_cameras`** - Blitzer-Standorte
**`traffic_incidents`** - Verkehrshindernisse

### 5.3 Indizes

```sql
-- Synonyme
CREATE INDEX idx_address_synonyms_alias_norm ON address_synonyms(alias_norm);
CREATE INDEX idx_address_synonyms_priority ON address_synonyms(priority DESC);
CREATE INDEX idx_address_synonyms_active ON address_synonyms(active);

-- Blitzer
CREATE INDEX idx_speed_cameras_location ON speed_cameras(lat, lon);
CREATE INDEX idx_speed_cameras_type ON speed_cameras(type);

-- Hindernisse
CREATE INDEX idx_traffic_incidents_location ON traffic_incidents(lat, lon);
CREATE INDEX idx_traffic_incidents_severity ON traffic_incidents(severity);
```

---

## 📚 Verwandte Dokumentation

- **Kunden-Synonyme:** `docs/CUSTOMER_SYNONYMS.md`
- **Live-Traffic-Daten:** `docs/archive/consolidated_2025-11-13/LIVE_TRAFFIC_DATA.md`
- **Tourplan-Parser:** `backend/parsers/tour_plan_parser.py` (Code-Kommentare)

---

**Ende der Dokumentation**  
**Letzte Aktualisierung:** 2025-11-20 20:30

