# Route-Visualisierung: Straßen-Verbindungen anzeigen

## Übersicht

**Ziel:** Wenn der Benutzer auf eine Sub-Route klickt, soll die tatsächliche **Straßen-Route** (nicht Luftlinie) zwischen den Stopps angezeigt werden.

**Beispiel:**
```
Kunde 1 ──┐
          │ (Straßen-Route über Hauptstraße)
          └── Kunde 2
```

Statt:
```
Kunde 1 ──────── Kunde 2  (Luftlinie - nicht realistisch)
```

---

## Aktueller Stand

**Frontend:** `frontend/index.html`
- Sub-Routen werden in der Liste angezeigt
- Beim Klick: Noch keine Route-Visualisierung

**Backend:** `services/llm_optimizer.py`
- OSRM-Integration bereits vorbereitet
- `_get_osrm_distances()` existiert, aber wird noch nicht für Visualisierung verwendet

---

## Implementierung

### Schritt 1: Route-Details-Endpoint

**Datei:** `routes/workflow_api.py` (neu)

```python
@router.post("/api/tour/route-details")
async def get_route_details(request: Request):
    """
    Liefert detaillierte Route zwischen Stopps (OSRM)
    
    Request Body:
    {
        "stops": [
            {"lat": 51.05, "lon": 13.74},
            {"lat": 51.06, "lon": 13.75},
            ...
        ]
    }
    
    Response:
    {
        "routes": [
            {
                "from": {"lat": 51.05, "lon": 13.74},
                "to": {"lat": 51.06, "lon": 13.75},
                "distance_km": 3.5,
                "duration_minutes": 5,
                "geometry": "..."  # Polyline für Karte
            },
            ...
        ]
    }
    """
    body = await request.json()
    stops = body.get("stops", [])
    
    routes = []
    for i in range(len(stops) - 1):
        from_stop = stops[i]
        to_stop = stops[i + 1]
        
        # OSRM Route API aufrufen
        route_data = await get_osrm_route(
            from_stop["lat"], from_stop["lon"],
            to_stop["lat"], to_stop["lon"]
        )
        
        routes.append({
            "from": from_stop,
            "to": to_stop,
            "distance_km": route_data["distance"] / 1000,
            "duration_minutes": route_data["duration"] / 60,
            "geometry": route_data["geometry"]  # Encoded Polyline
        })
    
    return JSONResponse({"routes": routes})
```

---

### Schritt 2: Frontend: Route-Details anzeigen

**Datei:** `frontend/index.html` (erweitern)

```javascript
// Wenn Sub-Route in Liste geklickt wird
async function showRouteDetails(subRoute) {
    const stops = subRoute.stops;
    
    // 1. Route-Details vom Backend abrufen
    const response = await fetch('/api/tour/route-details', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ stops: stops })
    });
    
    const routeDetails = await response.json();
    
    // 2. Modal/Dialog öffnen
    const modal = document.getElementById('routeDetailsModal');
    const modalBody = modal.querySelector('.modal-body');
    
    // 3. Karte initialisieren (z.B. Leaflet)
    const map = L.map('routeMap').setView([51.05, 13.74], 12);
    
    // 4. Für jede Route: Auf Karte zeichnen
    routeDetails.routes.forEach((route, index) => {
        // Decode Polyline
        const path = L.Polyline.fromEncoded(route.geometry);
        
        // Route auf Karte zeichnen
        path.addTo(map);
        
        // Info-Popup anzeigen
        const popup = `${route.from.name} → ${route.to.name}<br>
                      Distanz: ${route.distance_km.toFixed(1)} km<br>
                      Dauer: ${route.duration_minutes.toFixed(1)} Min`;
        path.bindPopup(popup);
    });
    
    // 5. Stopps als Marker anzeigen
    stops.forEach((stop, index) => {
        L.marker([stop.lat, stop.lon])
            .addTo(map)
            .bindPopup(`${index + 1}. ${stop.name}<br>${stop.address}`);
    });
    
    // 6. Modal anzeigen
    bootstrap.Modal.getInstance(modal).show();
}
```

---

### Schritt 3: UI-Integration

**In Tour-Liste:**
```html
<!-- Sub-Route Card -->
<div class="tour-card" onclick="showRouteDetails(subRoute)">
    <h5>W-07.00 Uhr Tour A</h5>
    <p>10 Stopps, 58 Min</p>
    <button class="btn btn-sm btn-primary">
        <i class="fas fa-map"></i> Route anzeigen
    </button>
</div>
```

**Modal:**
```html
<div class="modal fade" id="routeDetailsModal">
    <div class="modal-dialog modal-xl">
        <div class="modal-content">
            <div class="modal-header">
                <h5>Route-Details: W-07.00 Uhr Tour A</h5>
            </div>
            <div class="modal-body">
                <div id="routeMap" style="height: 500px;"></div>
                <div class="route-summary mt-3">
                    <strong>Gesamt:</strong>
                    <span id="totalDistance">0 km</span>,
                    <span id="totalDuration">0 Min</span>
                </div>
            </div>
        </div>
    </div>
</div>
```

---

## OSRM-Integration Details

### OSRM Route API

```javascript
async function getOSRMRoute(fromLat, fromLon, toLat, toLon) {
    const coords = `${fromLon},${fromLat};${toLon},${toLat}`;
    const url = `http://router.project-osrm.org/route/v1/driving/${coords}`;
    
    const response = await fetch(url);
    const data = await response.json();
    
    return {
        distance: data.routes[0].distance,  // Meter
        duration: data.routes[0].duration,  // Sekunden
        geometry: data.routes[0].geometry   // Encoded Polyline
    };
}
```

### Polyline decodieren (für Leaflet)

```javascript
// Leaflet-Polyline Plugin verwenden
const path = L.Polyline.fromEncoded(geometry);
path.addTo(map);
```

---

## Beispiel: W-07.00 Sub-Route A

**Klick auf "W-07.00 Uhr Tour A":**

1. **Modal öffnet sich** mit Karte
2. **10 Marker** zeigen alle Stopps
3. **9 Routen-Linien** zeigen Verbindungen zwischen Stopps (über Straßen)
4. **Info-Popup** bei Klick auf Route:
   ```
   Kunde 1 → Kunde 2
   Distanz: 3.5 km
   Dauer: 5 Min
   ```

5. **Zusammenfassung:**
   ```
   Gesamt: 28.5 km, 42 Min Fahrzeit
   ```

---

## Vorteile

✅ **Realistische Visualisierung:** Straßen-Routen statt Luftlinie  
✅ **Distanz & Zeit:** Echte Werte pro Segment  
✅ **Interaktiv:** Benutzer kann Route erkunden  
✅ **Professionell:** Wie Navigation-Apps  

---

## Nächste Schritte

### Morgen:
- [ ] Backend-Endpoint `/api/tour/route-details` implementieren
- [ ] OSRM-Integration testen
- [ ] Frontend: Route-Details-Modal erstellen

### Später:
- [ ] Karten-Library integrieren (Leaflet/OpenLayers)
- [ ] Route-Optimierung basierend auf Verkehrszeiten
- [ ] Export: Route als GPX-Datei

---

**Status:** 🚧 In Planung - OSRM-Code vorhanden, Frontend-Integration fehlt noch.

