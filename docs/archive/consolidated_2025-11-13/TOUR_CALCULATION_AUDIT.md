# Tour-Berechnung - Audit-Dokumentation

**Version:** 1.0  
**Datum:** 2025-01-09  
**Status:** Verbindlich für externe Audits

---

## 📋 Inhaltsverzeichnis

1. [Übersicht: Tour-Berechnungsprozess](#übersicht)
2. [Schritt 1: CSV-Upload und Parsing](#schritt-1)
3. [Schritt 2: Geocoding und Koordinaten-Resolvierung](#schritt-2)
4. [Schritt 3: Tour-Klassifizierung (W/PIR/CB/BZ/etc.)](#schritt-3)
5. [Schritt 4: Sektor-Planung (W-Touren)](#schritt-4)
6. [Schritt 5: PIRNA-Clustering (PIR-Touren)](#schritt-5)
7. [Schritt 6: Route-Optimierung](#schritt-6)
8. [Schritt 7: Zeitberechnung und Validierung](#schritt-7)
9. [Schritt 8: Finale Route-Generierung](#schritt-8)
10. [Mathematische Formeln](#formeln)

---

## 🔄 Übersicht: Tour-Berechnungsprozess {#übersicht}

### Haupt-Pipeline (Ablaufdiagramm)

```
CSV-Upload
    ↓
[Schritt 1] CSV-Parsing → Tour-Extraktion
    ↓
[Schritt 2] Geocoding → Koordinaten-Resolvierung
    ↓
[Schritt 3] Tour-Klassifizierung
    ↓
    ├─→ W-Tour? → [Schritt 4] Sektor-Planung (N/O/S/W)
    ├─→ PIR-Tour? → [Schritt 5] PIRNA-Clustering
    └─→ Andere? → [Schritt 6] Direkte Route-Optimierung
    ↓
[Schritt 6] Route-Optimierung (LLM oder Heuristik)
    ↓
[Schritt 7] Zeitberechnung & Validierung
    ↓
[Schritt 8] Finale Route-Generierung (OSRM)
    ↓
Tour-Output (JSON)
```

---

## 📥 Schritt 1: CSV-Upload und Parsing {#schritt-1}

### Input
- CSV-Datei mit Format: `KdNr;Name;Straße;PLZ;Ort;Gedruckt`
- Encoding: CP850 (Windows ANSI) → konvertiert zu UTF-8

### Prozess
1. **Datei-Encoding-Detection**
   - Prüfe auf CP850 (Windows ANSI)
   - Konvertiere zu UTF-8 (NFC Normalisierung)
   - Mojibake-Guard: Prüfe auf Encoding-Fehler

2. **CSV-Parsing**
   - Verwende `pandas.read_csv()` mit Semikolon-Separator
   - Erkenne Spalten automatisch:
     - `KdNr` → `customer_number`
     - `Name` → `name`
     - `Straße` → `street`
     - `PLZ` → `postal_code`
     - `Ort` → `city`
     - `Gedruckt` → `tour_name`

3. **Tour-Extraktion**
   - Gruppiere Zeilen nach `tour_name`
   - Leere Zeilen trennen Touren
   - Erstelle `Tour`-Objekte mit `customers`-Liste

### Output
```python
{
    "tours": [
        {
            "name": "W-07.00 Uhr Tour",
            "customers": [
                {
                    "customer_number": "6000",
                    "name": "Büttner",
                    "street": "Steigerstraße 1",
                    "postal_code": "01705",
                    "city": "Freital",
                    "tour_name": "W-07.00 Uhr Tour"
                },
                ...
            ]
        },
        ...
    ]
}
```

### Code-Referenz
- Datei: `backend/parsers/tour_plan_parser.py`
- Funktion: `parse_tour_plan_to_dict()`

---

## 🗺️ Schritt 2: Geocoding und Koordinaten-Resolvierung {#schritt-2}

### Input
- Tour-Objekte mit Adressen (ohne Koordinaten)

### Prozess

#### 2.1 Synonym-Resolvierung
1. **Prüfe Customer-Synonyms** (`CUSTOMER_SYNONYMS.md`)
   - Suche nach `customer_number` → gefunden → verwende Synonym-Koordinaten
   - Suche nach `name` → gefunden → verwende Synonym-Koordinaten
   - **Priorität:** Name-Synonym korrigiert falsche Adressen aus CSV

2. **Adress-Normalisierung**
   - Normalisiere Adresse: `{street}, {postal_code} {city}`
   - Unicode NFC Normalisierung
   - Whitespace-Bereinigung

#### 2.2 Geocoding (falls keine Koordinaten vorhanden)
1. **DB-Lookup** (`geo_cache` Tabelle)
   - Query: `SELECT lat, lon FROM geo_cache WHERE address_norm = ?`
   - Falls gefunden → verwende DB-Koordinaten

2. **Externes Geocoding** (falls nicht in DB)
   - **OpenStreetMap Nominatim** (Primär)
   - **Google Geocoding API** (Fallback)
   - Cache in DB: `INSERT INTO geo_cache (address_norm, lat, lon) VALUES (...)`

### Output
- Tour-Objekte mit `lat` und `lon` für jeden Kunden

### Code-Referenz
- Datei: `backend/parsers/tour_plan_parser.py`
- Funktion: `_extract_tours()`, `_resolve_customer_synonyms()`
- Datei: `repositories/geo_repo.py`
- Funktion: `get()`, `bulk_get()`

---

## 🏷️ Schritt 3: Tour-Klassifizierung {#schritt-3}

### Entscheidungsbaum

```
Tour-Name beginnt mit:
    ├─ "W-" oder "W-XX.XX" → W-Tour → [Schritt 4] Sektor-Planung
    ├─ "PIR" oder "PIR-" → PIR-Tour → [Schritt 5] PIRNA-Clustering
    ├─ "CB" → CB-Tour → [Schritt 6] Direkte Optimierung
    ├─ "BZ" → BZ-Tour → [Schritt 6] Direkte Optimierung
    └─ Sonst → [Schritt 6] Direkte Optimierung
```

### Code-Referenz
- Datei: `routes/workflow_api.py`
- Funktion: `_apply_sector_planning_to_w_tour()`, `_apply_pirna_clustering_to_tour()`
- Datei: `services/sector_planner.py`
- Funktion: `should_use_sector_planning()`

---

## 🧭 Schritt 4: Sektor-Planung (W-Touren) {#schritt-4}

### Input
- W-Tour mit allen Kunden (mit Koordinaten)

### Prozess

#### 4.1 Sektorisierung (N/O/S/W)
1. **Bearing-Berechnung** vom Depot zu jedem Kunden
   - Formel: `bearing = atan2(sin(Δlon) * cos(lat2), cos(lat1) * sin(lat2) - sin(lat1) * cos(lat2) * cos(Δlon))`
   - Wandle zu Grad: `bearing_deg = (bearing * 180 / π + 360) % 360`

2. **Sektor-Zuordnung**
   ```
   Bearing 0°-90°   → O (Ost)
   Bearing 90°-180° → S (Süd)
   Bearing 180°-270°→ W (West)
   Bearing 270°-360°→ N (Nord)
   ```

#### 4.2 Greedy-Route-Planung pro Sektor

**Für jeden Sektor (N, O, S, W):**

1. **Initialisierung**
   - Start: Depot (51.0111988, 13.7016485)
   - `driving_time = 0.0`
   - `service_time = 0.0`
   - `route_uids = [depot_uid]`

2. **Greedy-Loop** (solange Stopps verfügbar)
   
   a) **OSRM Table API** für alle verbleibenden Kandidaten
      - Request: `GET /table/v1/driving/{coords}`
      - Response: Matrix mit Distanzen/Zeiten
   
   b) **Finde besten Kandidaten**
      - Sortiere nach kürzester Fahrzeit (OSRM oder Haversine-Fallback)
      - Optional: LLM-Entscheidung bei ähnlichen Kandidaten (≤2 Min Unterschied)
   
   c) **Zeit-Constraint-Prüfung**
      ```python
      time_without_return = driving_time + segment_minutes + service_time + customer_service_time
      
      if time_without_return > 65.0:  # KRITISCH: 65 Min OHNE Rückfahrt
          break  # Cut: Neue Route starten
      
      return_minutes = calculate_return_to_depot(candidate)
      total_with_return = time_without_return + return_minutes
      
      if total_with_return > 90.0:  # Zeitbox: 90 Min INKL. Rückfahrt
          break  # Cut: Neue Route starten
      ```
   
   d) **Akzeptiere Kandidaten**
      - `route_uids.append(candidate.stop_uid)`
      - `driving_time += segment_minutes`
      - `service_time += customer_service_time` (Standard: 2 Min)
      - Aktualisiere `current_lat`, `current_lon`

3. **Rückfahrt zum Depot**
   - Berechne Distanz vom letzten Stop zum Depot
   - Addiere zu `driving_time`
   - Füge Depot als `route_uids[-1]` hinzu

4. **Route-Erstellung**
   ```python
   # Trenne Rückfahrt von Fahrzeit
   driving_time_without_return = driving_time - return_time
   
   route = SectorRoute(
       driving_time_minutes=driving_time_without_return,  # OHNE Rückfahrt
       service_time_minutes=service_time,
       total_time_minutes=driving_time_without_return + service_time,  # OHNE Rückfahrt
       meta={
           "return_time_minutes": return_time,
           "total_time_with_return": driving_time_without_return + service_time + return_time
       }
   )
   ```

#### 4.3 Tour-Namen
- Format: `{Original-Name} {Sektor} {Route-Letter}`
- Beispiel: `W-07.00 Uhr Tour Nord A`, `W-07.00 Uhr Tour Nord B`

### Output
- Liste von `SectorRoute`-Objekten pro Sektor

### Code-Referenz
- Datei: `services/sector_planner.py`
- Funktion: `sectorize_stops()`, `plan_by_sector()`, `_plan_sector_greedy()`

---

## 🎯 Schritt 5: PIRNA-Clustering (PIR-Touren) {#schritt-5}

### Input
- PIR-Tour mit allen Kunden (mit Koordinaten)

### Prozess

#### 5.1 Clustering-Algorithmus

1. **Sortiere Stopps nach Entfernung vom Depot**
   - Verwende Haversine-Distanz (vereinfacht)
   - Nähere Stopps zuerst

2. **Greedy-Clustering**
   ```
   Cluster = []
   Für jeden Stopp:
       Wenn Cluster leer:
           Starte neuen Cluster
       
       Prüfe: Würde Stopp + Cluster ≤ max_stops_per_cluster (15)?
       UND: Würde Stopp + Cluster ≤ max_time_per_cluster_minutes (120 Min)?
       
       Wenn JA:
           Füge Stopp zu Cluster hinzu
       Wenn NEIN:
           Speichere Cluster
           Starte neuen Cluster mit Stopp
   ```

3. **Zeit-Schätzung pro Cluster**
   ```python
   def _estimate_time_for_stops(stops, depot_lat, depot_lon):
       # Depot → Erster Stop
       dist_to_first = haversine(depot, stops[0]) * 1.3
       
       # Stop → Stop
       total_dist = dist_to_first
       for i in range(1, len(stops)):
           dist = haversine(stops[i-1], stops[i]) * 1.3
           total_dist += dist
       
       # Letzter Stop → Depot
       dist_from_last = haversine(stops[-1], depot) * 1.3
       total_dist += dist_from_last
       
       # Fahrzeit (50 km/h)
       driving_time = (total_dist / 50.0) * 60
       
       # Service-Zeit (2 Min pro Stop)
       service_time = len(stops) * 2.0
       
       return driving_time + service_time
   ```

### Output
- Liste von `PirnaCluster`-Objekten

### Code-Referenz
- Datei: `services/pirna_clusterer.py`
- Funktion: `cluster_stops()`, `_estimate_time_for_stops()`

---

## ⚙️ Schritt 6: Route-Optimierung {#schritt-6}

### Input
- Liste von Stopps (mit Koordinaten)

### Prozess

#### 6.1 Entscheidung: LLM oder Heuristik?

```
Wenn LLM verfügbar UND Tour nicht zu groß:
    → LLM-Optimierung
Sonst:
    → Nearest-Neighbor Heuristik
```

#### 6.2 LLM-Optimierung

1. **System-Prompt** (aus `LLM_ROUTE_RULES.md`)
   - Verbindliche Regeln laden
   - Zeit-Constraints: ≤ 65 Min OHNE Rückfahrt
   - Service-Zeit: 2 Min pro Kunde

2. **User-Prompt**
   - Kunden-Daten als JSON
   - Aktuelle Reihenfolge
   - Depot-Koordinaten

3. **LLM-Response** (GPT-4o-mini)
   - Format: JSON mit `optimized_sequence` (Liste von Indices)
   - **Validierung:** Nur Indices aus erlaubter Liste akzeptieren

4. **Index-Mapping**
   ```python
   optimized_stops = []
   for i in optimized_indices:
       optimized_stops.append(valid_stops[i])
   ```

#### 6.3 Nearest-Neighbor Heuristik

1. **Start:** Depot
2. **Greedy-Loop:**
   ```
   current = depot
   remaining = alle_stopps
   
   Während remaining nicht leer:
       next = nearest_neighbor(current, remaining)  # Kürzeste Distanz
       route.append(next)
       remaining.remove(next)
       current = next
   ```

3. **Distanz-Berechnung:**
   - **Priorität 1:** OSRM Route API
   - **Priorität 2:** Haversine × 1.3 (Fallback)

### Output
- Optimierte Reihenfolge der Stopps (Liste von Indices oder Stopp-Objekten)

### Code-Referenz
- Datei: `backend/services/ai_optimizer.py`
- Funktion: `optimize_route()`, `cluster_stops_into_tours()`
- Datei: `services/osrm_client.py`
- Funktion: `get_route()`, `get_table()`

---

## ⏱️ Schritt 7: Zeitberechnung und Validierung {#schritt-7}

### Input
- Route mit optimierter Reihenfolge

### Prozess

#### 7.1 Fahrzeit-Berechnung

**Methode 1: OSRM Route API (Priorität)**
```python
GET /route/v1/driving/{coords}?overview=full&geometries=geojson

Response:
{
    "routes": [{
        "distance": 5000.0,  # Meter
        "duration": 600.0    # Sekunden
    }]
}

driving_time_minutes = duration / 60.0
```

**Methode 2: Haversine × 1.3 (Fallback)**
```python
# Siehe Formeln-Sektion für Haversine-Formel
haversine_distance = calculate_haversine(lat1, lon1, lat2, lon2)
adjusted_distance = haversine_distance * 1.3  # Stadtverkehr-Faktor
driving_time_minutes = (adjusted_distance / 50.0) * 60  # 50 km/h Durchschnitt
```

#### 7.2 Service-Zeit-Berechnung
```python
service_time_minutes = len(stops) * 2.0  # 2 Minuten pro Kunde
```

#### 7.3 Rückfahrt-Berechnung
```python
last_stop = stops[-1]
return_distance = haversine(last_stop, depot) * 1.3  # Oder OSRM
return_time_minutes = (return_distance / 50.0) * 60
```

#### 7.4 Gesamtzeit-Berechnung

**Zeit OHNE Rückfahrt:**
```python
time_without_return = driving_time_minutes + service_time_minutes
```

**Zeit INKL. Rückfahrt:**
```python
total_time_with_return = time_without_return + return_time_minutes
```

#### 7.5 Validierung

**Constraint 1: Hauptregel (KRITISCH)**
```python
if time_without_return > 65.0:
    # WARNUNG: Tour überschreitet 65 Minuten (OHNE Rückfahrt)
    status = "WARNING"
```

**Constraint 2: Zeitbox**
```python
if total_time_with_return > 90.0:
    # WARNUNG: Tour überschreitet 90 Minuten (INKL. Rückfahrt)
    status = "WARNING"
```

**Constraint 3: Stopp-Validierung**
```python
# Alle Original-Stopps müssen in Route enthalten sein
original_stop_ids = set([s.customer_number for s in original_stops])
route_stop_ids = set([s.customer_number for s in optimized_stops])

if original_stop_ids != route_stop_ids:
    # FEHLER: Stopps fehlen oder wurden hinzugefügt
    status = "ERROR"
```

### Output
- Route mit Zeit-Attributen:
  - `estimated_driving_time_minutes` (OHNE Rückfahrt)
  - `estimated_service_time_minutes`
  - `estimated_total_time_minutes` (OHNE Rückfahrt)
  - `estimated_return_time_minutes`
  - `estimated_total_with_return_minutes` (INKL. Rückfahrt)
- Validierungs-Status: `OK`, `WARNING`, `ERROR`

### Code-Referenz
- Datei: `routes/workflow_api.py`
- Funktion: `_estimate_tour_time_without_return()`, `_calculate_tour_time()`
- Datei: `services/osrm_client.py`
- Funktion: `get_route()`

---

## 🗺️ Schritt 8: Finale Route-Generierung {#schritt-8}

### Input
- Optimierte Route mit validierten Zeiten

### Prozess

#### 8.1 Route-Geometrie (für Karten-Visualisierung)

**OSRM Route API**
```python
GET /route/v1/driving/{coords}?overview=full&geometries=geojson&steps=false

Response:
{
    "routes": [{
        "geometry": {
            "coordinates": [[lon1, lat1], [lon2, lat2], ...],
            "type": "LineString"
        },
        "distance": 5000.0,
        "duration": 600.0
    }]
}
```

**Konvertierung für Leaflet**
```javascript
// GeoJSON → Leaflet Polyline
const polyline = L.polyline(geometry.coordinates.map(c => [c[1], c[0]]), {
    color: routeColor,
    weight: 4
});
map.addLayer(polyline);
```

#### 8.2 Segment-Distanzen (für Kunden-Tabelle)

**Pro Segment:**
```python
segments = []
for i in range(len(stops) - 1):
    from_stop = stops[i]
    to_stop = stops[i+1]
    
    # OSRM Table API oder Haversine
    distance_km, duration_min = get_distance(from_stop, to_stop)
    
    segments.append({
        "from": i,
        "to": i + 1,
        "distance_km": distance_km,
        "duration_minutes": duration_min
    })
```

### Output
- **Route-Geometrie:** GeoJSON für Karten-Visualisierung
- **Segment-Distanzen:** Für Kunden-Tabelle
- **Finale Tour-Struktur:**
```json
{
    "tour_id": "W-07.00 Uhr Tour Nord A",
    "stops": [...],
    "estimated_driving_time_minutes": 52.3,
    "estimated_service_time_minutes": 14.0,
    "estimated_total_time_minutes": 66.3,
    "estimated_return_time_minutes": 8.7,
    "estimated_total_with_return_minutes": 75.0,
    "route_geometry": {...},
    "segments": [...]
}
```

### Code-Referenz
- Datei: `routes/workflow_api.py`
- Endpoint: `/api/tour/route-details`
- Datei: `services/osrm_client.py`
- Funktion: `get_route()`

---

## 📐 Mathematische Formeln {#formeln}

### 1. Haversine-Distanz (Luftlinie)

```python
import math

def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Berechnet Luftlinie-Distanz zwischen zwei GPS-Koordinaten.
    
    Formel:
    a = sin²(Δlat/2) + cos(lat1) × cos(lat2) × sin²(Δlon/2)
    c = 2 × atan2(√a, √(1-a))
    distance = R × c
    
    R = Erdradius = 6371.0 km
    """
    R = 6371.0  # Erdradius in km
    
    # Grad zu Bogenmaß
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    # Differenzen
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    # Haversine-Formel
    a = (math.sin(dlat/2) ** 2 + 
         math.cos(lat1_rad) * math.cos(lat2_rad) * 
         math.sin(dlon/2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c
```

**Anpassung für Stadtverkehr:**
```python
adjusted_distance = haversine_distance * 1.3  # Faktor 1.3
```

### 2. Fahrzeit-Berechnung

```python
# Von Distanz zu Zeit (bei konstanter Geschwindigkeit)
driving_time_minutes = (distance_km / speed_kmh) * 60

# Standard-Geschwindigkeit in Stadtverkehr: 50 km/h
speed_kmh = 50.0
```

### 3. Service-Zeit

```python
service_time_minutes = number_of_stops * service_time_per_stop

# Standard: 2 Minuten pro Kunde
service_time_per_stop = 2.0
```

### 4. Gesamtzeit OHNE Rückfahrt

```python
time_without_return = driving_time_minutes + service_time_minutes
```

### 5. Gesamtzeit INKL. Rückfahrt

```python
total_time_with_return = time_without_return + return_time_minutes
```

### 6. Bearing-Berechnung (für Sektor-Planung)

```python
def calculate_bearing(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Berechnet Richtung (Bearing) von Punkt 1 zu Punkt 2.
    
    Formel:
    bearing = atan2(sin(Δlon) × cos(lat2),
                    cos(lat1) × sin(lat2) - sin(lat1) × cos(lat2) × cos(Δlon))
    
    Ergebnis: 0° = Nord, 90° = Ost, 180° = Süd, 270° = West
    """
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlon = lon2_rad - lon1_rad
    
    y = math.sin(dlon) * math.cos(lat2_rad)
    x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
         math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon))
    
    bearing_rad = math.atan2(y, x)
    bearing_deg = math.degrees(bearing_rad)
    
    # Normalisiere zu 0°-360°
    return (bearing_deg + 360) % 360
```

---

## ✅ Validierungs-Regeln (Checkliste)

### Vor Tour-Output muss geprüft werden:

1. ✅ **Zeit-Constraint 1:** `time_without_return ≤ 65.0` Minuten
2. ✅ **Zeit-Constraint 2:** `total_time_with_return ≤ 90.0` Minuten
3. ✅ **Stopp-Validierung:** Alle Original-Stopps in Route enthalten
4. ✅ **Keine Duplikate:** Jeder Stopp nur einmal in Route
5. ✅ **Depot-Integration:** Route startet/endet am Depot (visuell, nicht als Stop)
6. ✅ **Koordinaten vorhanden:** Alle Stopps haben `lat` und `lon`
7. ✅ **Route-Geometrie:** OSRM-Route erfolgreich generiert oder Haversine-Fallback

---

## 📊 Beispiel-Berechnung

### Beispiel: Tour mit 7 Kunden

**Input:**
- 7 Kunden mit Koordinaten
- Depot: 51.0111988, 13.7016485

**Berechnung:**
```
1. OSRM Route API:
   Depot → Kunde 1: 3.2 km, 4.8 Min
   Kunde 1 → Kunde 2: 1.5 km, 2.3 Min
   Kunde 2 → Kunde 3: 2.1 km, 3.2 Min
   ...
   Kunde 7 → Depot: 5.1 km, 7.8 Min
   
   driving_time_without_return = 4.8 + 2.3 + 3.2 + ... = 52.3 Min
   return_time = 7.8 Min

2. Service-Zeit:
   service_time = 7 × 2.0 = 14.0 Min

3. Gesamtzeit OHNE Rückfahrt:
   time_without_return = 52.3 + 14.0 = 66.3 Min

4. Gesamtzeit INKL. Rückfahrt:
   total_time_with_return = 66.3 + 7.8 = 74.1 Min

5. Validierung:
   time_without_return = 66.3 > 65.0 → ⚠️ WARNUNG
   total_time_with_return = 74.1 < 90.0 → ✅ OK
```

---

## 🔗 Code-Referenzen

| Schritt | Datei | Funktion |
|---------|-------|----------|
| CSV-Parsing | `backend/parsers/tour_plan_parser.py` | `parse_tour_plan_to_dict()` |
| Geocoding | `repositories/geo_repo.py` | `get()`, `bulk_get()` |
| Sektor-Planung | `services/sector_planner.py` | `plan_by_sector()`, `_plan_sector_greedy()` |
| PIRNA-Clustering | `services/pirna_clusterer.py` | `cluster_stops()` |
| LLM-Optimierung | `backend/services/ai_optimizer.py` | `optimize_route()` |
| OSRM-Client | `services/osrm_client.py` | `get_route()`, `get_table()` |
| Workflow | `routes/workflow_api.py` | `workflow_upload()`, `_apply_sector_planning_to_w_tour()` |

---

**Letzte Aktualisierung:** 2025-01-09  
**Version:** 1.0  
**Status:** ✅ Audit-ready

