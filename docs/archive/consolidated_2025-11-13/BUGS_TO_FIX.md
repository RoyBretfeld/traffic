# Bugs die behoben werden müssen

**Datum:** 2025-01-09  
**Status:** 🐛 Bekannte Probleme

---

## 🐛 Problem 1: BAR-Flags werden in Sub-Routen nicht korrekt übernommen

### Symptom
- BAR-Zähler wird in Tour-Übersicht angezeigt
- Aber in Sub-Routen fehlen die BAR-Flags bei einzelnen Kunden
- Kunden die eigentlich BAR sind, werden nicht als BAR markiert

### Analyse
- Code versucht BAR-Flags zu erhalten (siehe `splitTourIntoSubRoutes` in `frontend/index.html`)
- Mapping zwischen Original-Stopps und Sub-Route-Stopps funktioniert möglicherweise nicht zuverlässig
- `updateToursWithSubRoutes` übernimmt BAR-Flags, aber nur wenn `bar_flag` im Stop-Objekt vorhanden ist

### Mögliche Ursachen
1. **Fehlende BAR-Flags beim Erstellen von Sub-Routen:**
   - Wenn Stopps von Backend kommen ohne `bar_flag`
   - Wenn Mapping zwischen `customer_number`/`name` nicht funktioniert

2. **BAR-Flag wird überschrieben:**
   - Bei der Konvertierung zwischen verschiedenen Formaten (stop → customer)
   - Beim Update der Touren-Liste

### Lösungsansatz

#### 1. Backend: BAR-Flag explizit übergeben
```python
# In routes/workflow_api.py - optimize_tour_with_ai()
optimized_stops = []
for i in optimized_indices:
    stop = dict(valid_stops[i])
    # WICHTIG: BAR-Flag explizit setzen (auch wenn nicht im Original vorhanden)
    if 'bar_flag' not in stop:
        # Prüfe Tour-Level BAR-Status
        stop['bar_flag'] = tour.get('is_bar_tour', False)
    optimized_stops.append(stop)
```

#### 2. Frontend: BAR-Flag-Mapping verbessern
```javascript
// In splitTourIntoSubRoutes()
const stopBarFlagMap = new Map();
originalStops.forEach(s => {
    const key1 = s.customer_number || s.order_id;
    const key2 = s.name || s.customer;
    if (key1) stopBarFlagMap.set(key1, s.bar_flag || false);
    if (key2) stopBarFlagMap.set(key2, s.bar_flag || false);
});

// Beim Hinzufügen zu Route:
const newStopWithBarFlag = {
    ...stop,
    bar_flag: stop.bar_flag !== undefined 
        ? stop.bar_flag 
        : (stopBarFlagMap.get(stop.customer_number) || 
           stopBarFlagMap.get(stop.name) || 
           tour.is_bar_tour || 
           false)
};
```

#### 3. Validierung hinzufügen
```javascript
// Nach Erstellen von Sub-Routen prüfen:
subRoutes.forEach(subRoute => {
    const barCount = subRoute.stops.filter(s => s.bar_flag === true).length;
    console.log(`Sub-Route ${subRoute.sub_route}: ${barCount} BAR-Kunden`);
    
    // Warnung wenn BAR-Kunden erwartet wurden aber fehlen
    if (tour.is_bar_tour && barCount === 0) {
        console.warn(`WARNUNG: Sub-Route ${subRoute.sub_route} sollte BAR-Kunden haben, aber keiner gefunden!`);
    }
});
```

### Dateien zu prüfen
- `frontend/index.html` - `splitTourIntoSubRoutes()` (Zeile ~3050-3320)
- `frontend/index.html` - `updateToursWithSubRoutes()` (Zeile ~3380-3450)
- `routes/workflow_api.py` - `optimize_tour_with_ai()` (Zeile ~1625-1640)

---

## 🐛 Problem 2: Routen werden nur als Luftlinien angezeigt (OSRM funktioniert nicht)

### Symptom
- Routen auf der Karte werden als **gestrichelte gerade Linien** angezeigt (Fallback)
- Keine straßenbasierten Routen (OSRM Polyline)
- In Konsole: `Route-Details nicht verfügbar, zeichne gerade Linien`

### Analyse

#### Frontend (`frontend/index.html`, Zeile 2209-2224)
```javascript
if (route.geometry && typeof route.geometry === 'string') {
    // OSRM Polyline (encodiert) - vereinfacht: zeichne gerade Linie zwischen from/to
    // Für jetzt: Gerade Linie (später kann Polyline-Decoder hinzugefügt werden)
    polyline = L.polyline(
        [[fromLat, fromLon], [toLat, toLon]],  // ❌ FALSCH: Gerade Linie statt Polyline!
        {...}
    );
}
```

**Problem:** OSRM gibt eine **encodierte Polyline** zurück, aber der Code zeichnet nur eine gerade Linie zwischen Start und Ziel!

#### Backend (`routes/workflow_api.py`, Zeile 1917-1923)
```python
segment_route = osrm_client.get_route([from_coord, to_coord])

if segment_route and segment_route.get("geometry"):
    geometry = segment_route.get("geometry")  # Encoded Polyline String
    source = "osrm"
```

**Backend gibt korrekt die Geometrie zurück**, aber Frontend dekodiert sie nicht!

### Lösungsansatz

#### 1. OSRM-Geometrie-Format prüfen
OSRM gibt Geometrie als **encoded polyline** (String) zurück:
- Format: `"polyline({encoded_string})"` oder nur `"{encoded_string}"`
- Beispiel: `"polyline(_p~iF~ps|U_ulLnnqC_mqNvxq`@"

#### 2. Polyline-Decoder im Frontend hinzufügen

**Option A: Leaflet Polyline-Decoder Plugin**
```html
<!-- In index.html -->
<script src="https://cdn.jsdelivr.net/npm/@mapbox/polyline@1.0.1/polyline.js"></script>
```

**Option B: Eigene Polyline-Decoder-Funktion**
```javascript
function decodePolyline(encoded) {
    // Entferne "polyline(" und ")" falls vorhanden
    encoded = encoded.replace(/^polyline\(/, '').replace(/\)$/, '');
    
    // Verwende @mapbox/polyline oder eigene Implementierung
    if (typeof polyline !== 'undefined') {
        return polyline.decode(encoded, 5);  // 5 = precision
    }
    
    // Fallback: Eigene Implementierung
    const coordinates = [];
    let index = 0;
    const len = encoded.length;
    let lat = 0;
    let lng = 0;
    
    while (index < len) {
        let b, shift = 0, result = 0;
        do {
            b = encoded.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << shift;
            shift += 5;
        } while (b >= 0x20);
        
        const dlat = ((result & 1) !== 0 ? ~(result >> 1) : (result >> 1));
        lat += dlat;
        
        shift = 0;
        result = 0;
        do {
            b = encoded.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << shift;
            shift += 5;
        } while (b >= 0x20);
        
        const dlng = ((result & 1) !== 0 ? ~(result >> 1) : (result >> 1));
        lng += dlng;
        
        coordinates.push([lat / 1e5, lng / 1e5]);
    }
    
    return coordinates;
}
```

#### 3. Frontend-Code korrigieren
```javascript
// In drawRouteLines() - Zeile ~2209
if (route.geometry && typeof route.geometry === 'string') {
    try {
        // Dekodiere OSRM Polyline
        const decodedCoordinates = decodePolyline(route.geometry);
        
        // Konvertiere zu Leaflet-Format: [lat, lon]
        const leafletCoords = decodedCoordinates.map(coord => [coord[0], coord[1]]);
        
        polyline = L.polyline(leafletCoords, {
            color: routeColor || '#2196F3',
            weight: 4,
            opacity: 0.7
        });
        
        console.log(`[ROUTE-VIS] OSRM-Route gezeichnet: ${decodedCoordinates.length} Punkte`);
    } catch (error) {
        console.error('Fehler beim Dekodieren der Polyline:', error);
        // Fallback: Gerade Linie
        polyline = L.polyline(
            [[route.from.lat, route.from.lon], [route.to.lat, route.to.lon]],
            { color: routeColor, weight: 4, opacity: 0.7 }
        );
    }
} else {
    // Fallback: Gerade Linie
    polyline = L.polyline(
        [[route.from.lat, route.from.lon], [route.to.lat, route.to.lon]],
        { color: routeColor, weight: 3, opacity: 0.6, dashArray: '10, 5' }
    );
}
```

#### 4. OSRM-Client prüfen
Prüfe ob OSRM-Server erreichbar ist:
```python
# In services/osrm_client.py
def get_route(self, coords: List[Tuple[float, float]]):
    # Prüfe OSRM-Verfügbarkeit
    if not self.available:
        return None
    
    # Prüfe ob Geometrie-Format korrekt ist
    response = self._call_osrm_route(coords, geometries="polyline")
    if response and "routes" in response:
        route = response["routes"][0]
        geometry = route.get("geometry")
        
        # OSRM gibt "polyline({encoded})" zurück
        if geometry and isinstance(geometry, str):
            # Entferne "polyline(" und ")" falls vorhanden
            if geometry.startswith("polyline("):
                geometry = geometry[9:-1]  # Entferne "polyline(" und ")"
        
        return {
            "geometry": geometry,  # Encoded polyline string
            "distance_km": route.get("distance", 0) / 1000.0,
            "duration_min": route.get("duration", 0) / 60.0
        }
```

### Dateien zu prüfen
- `frontend/index.html` - `drawRouteLines()` (Zeile ~2148-2254)
- `routes/workflow_api.py` - `get_route_details()` (Zeile ~1847-1960)
- `services/osrm_client.py` - `get_route()` (muss prüfen ob Geometrie korrekt zurückgegeben wird)

### Test
```javascript
// In Browser-Konsole testen:
fetch('/api/tour/route-details', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        stops: [
            { lat: 51.01127, lon: 13.70161, name: 'Depot' },
            { lat: 51.05, lon: 13.74, name: 'Kunde 1' }
        ],
        include_depot: true
    })
})
.then(r => r.json())
.then(data => console.log('Route-Daten:', data));
```

**Erwartetes Ergebnis:**
```json
{
    "routes": [{
        "from": {...},
        "to": {...},
        "geometry": "polyline(_p~iF~ps|U_ulLnnqC_mqNvxq`@",  // Encoded polyline
        "source": "osrm"
    }]
}
```

---

## ✅ Checkliste für Fixes

### BAR-Flags:
- [ ] Backend: BAR-Flag explizit in `optimize_tour_with_ai()` setzen
- [ ] Frontend: Mapping in `splitTourIntoSubRoutes()` verbessern
- [ ] Frontend: Validierung nach Erstellen von Sub-Routen hinzufügen
- [ ] Test: Sub-Route mit BAR-Kunden erstellen und prüfen ob Flags vorhanden sind

### OSRM-Routen:
- [ ] Polyline-Decoder im Frontend hinzufügen (@mapbox/polyline)
- [ ] `drawRouteLines()` anpassen um encodierte Polyline zu dekodieren
- [ ] OSRM-Client prüfen ob Geometrie korrekt zurückgegeben wird
- [ ] Test: Route auf Karte zeichnen und prüfen ob straßenbasiert (nicht gerade Linie)

---

**Status:** 🐛 Bugs dokumentiert, Fixes ausstehend

