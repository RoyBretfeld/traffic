# Route-Details 422-Fehler - Fix-Dokumentation

## Problem

### Symptome
- Backend gab 422 (Unprocessable Entity) zurück
- Console-Log: `Failed to load resource: /api/tour/route-details: 422`
- Routen wurden nur als gerade Linien gezeichnet (keine OSRM-Geometrie)
- Warnung: "Route-Details nicht verfügbar, zeichne gerade Linien"

### Ursache
1. **Falsches Request-Format**: Frontend sendete zusätzliche Felder (`name`, `customer_number`, `include_depot`)
2. **Falsche Response-Verarbeitung**: Frontend erwartete Array von Routen, Backend gibt einzelnes Objekt zurück
3. **Koordinaten-Format**: Frontend sendete manchmal `latitude`/`longitude` statt `lat`/`lon`

## Lösung

### 1. Request-Format korrigiert

**Vorher (falsch):**
```javascript
{
    stops: [
        { lat: 51.01127, lon: 13.70161, name: "FAMO Depot", customer_number: "DEPOT" },
        { lat: 51.0504, lon: 13.7373, name: "Kunde 1", customer_number: "12345" }
    ],
    include_depot: true
}
```

**Nachher (korrekt):**
```javascript
{
    stops: [
        { lat: 51.01127, lon: 13.70161 },
        { lat: 51.0504, lon: 13.7373 }
    ]
}
```

### 2. Koordinaten-Konvertierung

```javascript
let stops = customersWithCoords.map(c => {
    // Konvertiere latitude/longitude zu lat/lon falls nötig
    const lat = parseFloat(c.lat || c.latitude);
    const lon = parseFloat(c.lon || c.longitude);
    if (isNaN(lat) || isNaN(lon)) {
        console.warn('[ROUTE-DETAILS] Ungültige Koordinaten:', c);
        return null;
    }
    return { lat: lat, lon: lon };
}).filter(s => s !== null); // Filtere ungültige Koordinaten
```

### 3. Response-Verarbeitung korrigiert

**Backend-Response:**
```javascript
{
    geometry_polyline6: "encoded-polyline-string",
    total_distance_m: 1234.5,
    total_duration_s: 456.7,
    source: "osrm" | "osrm_cached" | "fallback_haversine",
    warnings: [],
    degraded: false
}
```

**Frontend-Verarbeitung:**
```javascript
const routeData = await response.json();
const geometry = routeData.geometry_polyline6;

if (!geometry || typeof geometry !== 'string' || geometry.trim().length === 0) {
    console.warn('[ROUTE-VIS] Keine Geometrie erhalten, verwende Fallback');
    drawStraightLines(customersWithCoords, routeColor, includeDepot);
    return;
}

// Dekodiere Polyline6
const decodedCoordinates = decodePolyline6Inline(geometry);

// Zeichne Route
const polyline = L.polyline(decodedCoordinates, {
    color: routeColor || '#2196F3',
    weight: 4,
    opacity: 0.7
});
```

## Technische Details

### Backend-Endpoint

**Route:** `POST /api/tour/route-details`

**Request-Model:**
```python
class RouteDetailsReq(BaseModel):
    stops: List[Dict[str, float]]  # [{"lat": float, "lon": float}, ...]
    overview: str = "full"
    geometries: str = "polyline6"
    profile: str = "driving"
```

**Response:**
```python
{
    "geometry_polyline6": str,      # Encodierte Polyline6-Geometrie
    "total_distance_m": float,      # Gesamtdistanz in Metern
    "total_duration_s": float,       # Gesamtdauer in Sekunden
    "source": str,                   # "osrm", "osrm_cached", "fallback_haversine"
    "warnings": List[str],           # Warnungen (z.B. OSRM nicht verfügbar)
    "degraded": bool                 # True wenn Fallback verwendet wurde
}
```

### Polyline6-Dekodierung

**Funktion:** `decodePolyline6Inline(encoded)`

**Algorithmus:**
1. Liest encodierte Polyline6-Zeichen
2. Dekodiert zu Koordinaten-Paaren (lat, lon)
3. Gibt Array von Koordinaten zurück: `[[lat, lon], ...]`

**Implementierung:**
```javascript
function decodePolyline6Inline(encoded) {
    if (!encoded || typeof encoded !== 'string') return [];
    let index = 0, lat = 0, lon = 0, coords = [];
    const shift = 5;
    
    const next = () => {
        let result = 0, b, i = 0;
        do {
            if (index >= encoded.length) return null;
            b = encoded.charCodeAt(index++) - 63;
            result |= (b & 0x1f) << (i * shift);
            i++;
        } while (b >= 0x20);
        return (result & 1) ? ~(result >> 1) : (result >> 1);
    };
    
    while (index < encoded.length) {
        const dLat = next();
        const dLon = next();
        if (dLat === null || dLon === null) break;
        lat += dLat;
        lon += dLon;
        coords.push([lat / 1e6, lon / 1e6]); // Polyline6 verwendet 1e6 Präzision
    }
    return coords;
}
```

## Fehlerbehandlung

### Validierung

1. **Koordinaten-Validierung:**
   - Prüft auf `NaN`
   - Filtert ungültige Koordinaten
   - Mindestens 2 Stopps erforderlich

2. **Response-Validierung:**
   - Prüft auf `geometry_polyline6`
   - Prüft auf String-Typ
   - Prüft auf nicht-leeren String

### Fallback-Mechanismus

1. **OSRM nicht verfügbar:**
   - Backend verwendet Haversine-Fallback
   - `degraded: true` in Response
   - Frontend zeichnet Route trotzdem

2. **Keine Geometrie:**
   - Frontend verwendet `drawStraightLines()`
   - Zeichnet gerade Linien zwischen Stopps
   - Warnung in Console

3. **Dekodierungs-Fehler:**
   - Try-Catch um Dekodierung
   - Fallback auf gerade Linien
   - Fehler-Log in Console

## Testing

### Manuelle Tests

1. **Normale Route:**
   - Tour mit mehreren Stopps auswählen
   - Route sollte mit OSRM-Geometrie gezeichnet werden
   - Console: `[ROUTE-VIS] ✅ Dekodierung erfolgreich`

2. **Fallback-Route:**
   - OSRM deaktivieren (Backend)
   - Route sollte trotzdem gezeichnet werden (gerade Linien)
   - Console: `[ROUTE-VIS] Keine Geometrie erhalten, verwende Fallback`

3. **Ungültige Koordinaten:**
   - Tour mit fehlenden Koordinaten
   - Sollte nicht crashen
   - Warnung in Console

### Automatisierte Tests

```javascript
// TODO: Unit-Tests für Route-Details
describe('Route Details API', () => {
    it('should send correct request format', () => {
        // Test implementation
    });
    
    it('should handle response correctly', () => {
        // Test implementation
    });
    
    it('should fallback on error', () => {
        // Test implementation
    });
});
```

## Performance

### Optimierungen
- Polyline6-Dekodierung ist O(n) - linear zur String-Länge
- Route wird nur einmal gezeichnet pro Tour-Auswahl
- Caching im Backend (OSRM-Cache)

### Verbesserungspotenzial
- Route-Geometrie könnte gecacht werden (Frontend)
- Batch-Requests für mehrere Routen
- Lazy-Loading von Route-Details

## Bekannte Probleme

1. **Blitzer/Hindernisse**: Werden aktuell nicht in Response zurückgegeben
   - Lösung: Separater Endpoint oder Backend erweitern

2. **Route-Segmentierung**: Aktuell wird nur eine Route zurückgegeben
   - Lösung: Backend könnte mehrere Segmente zurückgeben

3. **Performance bei vielen Stopps**: Kann bei 100+ Stopps langsam werden
   - Lösung: Route-Optimierung oder Segmentierung

## Wartung

### Regelmäßige Checks
- OSRM-Verfügbarkeit prüfen
- Polyline6-Dekodierung testen
- Fallback-Mechanismus testen

### Code-Review-Punkte
- Request-Format korrekt?
- Response-Verarbeitung korrekt?
- Fehlerbehandlung vorhanden?
- Fallback-Mechanismus funktioniert?

