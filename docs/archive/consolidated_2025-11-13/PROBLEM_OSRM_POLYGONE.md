# Problem: OSRM-Polygone werden nicht korrekt visualisiert

## Problembeschreibung

Die OSRM-Routen werden auf der Karte als **gerade Linien** (Haversine-Fallback) angezeigt, statt als **straßenbasierte Routen** mit korrekter Polyline-Geometrie.

## Symptome

1. **Frontend zeigt "haversine_fallback"** statt "osrm" in der Konsole
2. **Gerade Linien** zwischen Stopps statt Straßen-Routen
3. **Endpoint `/api/tour/route-details` gibt 404** zurück (obwohl im Router registriert)
4. **OSRM läuft** (Docker Container aktiv), aber Geometrie wird nicht verwendet

## Technischer Ablauf

### 1. Frontend ruft Route-Details-API auf

**Datei:** `frontend/index.html` (Zeile 2326-2330)
```javascript
const response = await fetch('/api/tour/route-details', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stops: stops, include_depot: includeDepot })
});
```

**Problem:** Endpoint gibt 404 zurück → Fallback zu `drawStraightLines()`

### 2. Backend: Route-Details-Endpoint

**Datei:** `routes/workflow_api.py` (Zeile 2434-2550)

**Endpoint:** `POST /api/tour/route-details`

**Ablauf:**
1. Empfängt Stopps-Liste
2. Ruft `client.get_route([from_coord, to_coord])` auf
3. Prüft ob `segment_route.get("geometry")` vorhanden ist
4. Falls nicht → Fallback zu Haversine (gerade Linie)

**Problem:** Endpoint ist registriert, gibt aber 404 zurück

### 3. OSRM-Client

**Datei:** `services/osrm_client.py` (Zeile 249-299)

**Methode:** `get_route(coords)`

**Ablauf:**
1. Formatiert Koordinaten: `lon,lat;lon,lat;...`
2. Ruft OSRM auf: `/route/v1/driving/{coords}?overview=full&geometries=polyline&steps=false`
3. Extrahiert `geometry` aus Response: `route.get("geometry")`
4. Gibt Dict zurück: `{"geometry": "...", "distance_km": ..., "duration_min": ...}`

**Problem:** OSRM gibt Polyline zurück, aber sie wird nicht korrekt weitergegeben

### 4. Frontend: Polyline-Dekodierung

**Datei:** `frontend/index.html` (Zeile 2209-2288)

**Funktion:** `decodePolyline(encoded)`

**Ablauf:**
1. Prüft ob `@mapbox/polyline` Library verfügbar ist
2. Dekodiert Polyline: `polyline.decode(cleanEncoded)`
3. Konvertiert zu Leaflet-Format: `[lat, lon]`
4. Fallback: Eigene Implementierung (Precision 5)

**Problem:** Wird nicht aufgerufen, da Endpoint 404 gibt

## Root Cause Analysis

### Problem 1: Endpoint gibt 404 zurück

**Ursache:** 
- Router ist registriert (`backend/app.py` Zeile 77)
- Endpoint ist definiert (`routes/workflow_api.py` Zeile 2434)
- Server läuft, aber Endpoint wird nicht gefunden

**Mögliche Ursachen:**
- FastAPI-Reload hat Endpoint nicht erkannt
- Router-Prefix-Problem
- Server muss komplett neu gestartet werden

### Problem 2: OSRM-Geometrie wird nicht verwendet

**Ursache:**
- Endpoint gibt 404 → Frontend verwendet Fallback
- Selbst wenn Endpoint funktioniert, könnte `geometry` fehlen

**Mögliche Ursachen:**
- OSRM gibt keine Geometrie zurück
- `segment_route.get("geometry")` ist `None`
- Koordinaten-Format falsch (lat/lon vs lon/lat)

## Test-Ergebnisse

### OSRM-Direkttest
```bash
curl "http://localhost:5000/route/v1/driving/13.70161,51.01127;13.804567,51.013179?overview=full&geometries=polyline&steps=false"
```
**Ergebnis:** ✅ OSRM gibt Polyline zurück (851 Zeichen)

### Endpoint-Test
```bash
POST http://localhost:8111/api/tour/route-details
```
**Ergebnis:** ❌ 404 Not Found

### Router-Registrierung
```python
from routes.workflow_api import router
routes = [r.path for r in router.routes]
```
**Ergebnis:** ✅ `/api/tour/route-details` ist im Router vorhanden

## Betroffene Dateien

1. **`routes/workflow_api.py`** (Zeile 2434-2550)
   - Route-Details-Endpoint
   - OSRM-Client-Aufruf
   - Fallback-Logik

2. **`services/osrm_client.py`** (Zeile 249-299)
   - `get_route()` Methode
   - OSRM-API-Aufruf
   - Response-Parsing

3. **`frontend/index.html`** (Zeile 2209-2437)
   - `decodePolyline()` Funktion
   - `drawRouteLines()` Funktion
   - Polyline-Dekodierung

4. **`backend/app.py`** (Zeile 31, 77)
   - Router-Import
   - Router-Registrierung

5. **Dokumentation:**
   - `docs/ROUTE_VISUALISIERUNG.md`
   - `docs/OSRM_INTEGRATION_ROAD_ROUTES.md`
   - `docs/BUGS_TO_FIX.md`

## Lösungsansätze

### Lösung 1: Server komplett neu starten
- Alle Python-Prozesse beenden
- Server neu starten
- Endpoint sollte dann verfügbar sein

### Lösung 2: Endpoint-Debugging
- Prüfen ob Router korrekt geladen wird
- Prüfen ob FastAPI-Reload funktioniert
- Manuell Router registrieren falls nötig

### Lösung 3: OSRM-Geometrie-Debugging
- Logging in `get_route()` hinzufügen
- Prüfen ob `geometry` wirklich zurückgegeben wird
- Koordinaten-Format validieren

### Lösung 4: Frontend-Fallback verbessern
- Auch bei 404 OSRM direkt aufrufen
- Polyline-Dekodierung testen
- Koordinaten-Reihenfolge prüfen

## Nächste Schritte

1. ✅ Problem dokumentiert
2. ⏳ Relevante Dateien in ZIP sammeln
3. ⏳ Server komplett neu starten
4. ⏳ Endpoint testen
5. ⏳ OSRM-Geometrie validieren
6. ⏳ Frontend-Dekodierung testen

## Status

- **Problem identifiziert:** ✅
- **Root Cause gefunden:** ⏳ (Endpoint 404 + mögliche Geometrie-Probleme)
- **Lösung implementiert:** ❌
- **Getestet:** ❌

