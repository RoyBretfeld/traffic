# OSRM-Integration: Straßen-Routen statt Luftlinie

## Übersicht

Aktuell wird die **Haversine-Distanz** (Luftlinie) verwendet. Für bessere Routenoptimierung sollten wir **OSRM** (Open Source Routing Machine) verwenden, um echte Straßen-Distanzen und -Routen zu berechnen.

---

## Aktueller Stand

**Problem:** Luftlinie ≠ Straßen-Distanz

**Beispiel:**
- Luftlinie: 2 km (geradeaus)
- Straßen-Route: 3.5 km (über Straßen, mit Kurven)
- Zeit: 2.5 Min (Luftlinie) vs. 5 Min (Straßen)

**Impact:** Zeitberechnung ist ungenau → Splitting kann fehlerhaft sein

---

## Lösung: OSRM-Integration

### Was ist OSRM?

**Open Source Routing Machine** - Berechnet Routen über echte Straßen basierend auf OpenStreetMap-Daten.

**Vorteile:**
- ✅ Echte Straßen-Distanzen
- ✅ Echte Fahrzeiten (berücksichtigt Geschwindigkeitslimits)
- ✅ Richtungsinformationen (nicht nur Distanz)
- ✅ Kostenlos & Open Source

---

## Integration-Plan

### Schritt 1: OSRM-Setup

**Option A: Lokaler OSRM-Server**
```bash
# Docker-Container starten
docker run -t -i -p 5000:5000 osrm/osrm-backend \
  osrm-routed --algorithm mld /data/germany-latest.osrm
```

**Option B: Öffentlicher OSRM-Server**
```python
OSRM_BASE_URL = "http://router.project-osrm.org"
# Kostenlos, aber Rate-Limits
```

**Option C: Eigener Server (Produktion)**
- Deutschland-Karte herunterladen
- OSRM-Server auf eigenem Server hosten

---

### Schritt 2: API-Integration

**Datei:** `services/llm_optimizer.py` (bereits vorbereitet!)

**Aktueller Code:**
```python
self.osrm_base = os.environ.get("OSRM_BASE_URL")
self.osrm_profile = os.environ.get("OSRM_PROFILE", "driving")
self.osrm_timeout = float(os.environ.get("OSRM_TIMEOUT", "10"))
```

**Was fehlt noch:**
```python
def _get_osrm_distances(self, stops: List[Dict]) -> Dict[Tuple[int, int], float]:
    """Berechnet Straßen-Distanzen zwischen allen Stopp-Paaren"""
    if not self.osrm_base:
        return None
    
    # OSRM Route API aufrufen
    coordinates = ";".join([f"{s['lon']},{s['lat']}" for s in stops])
    url = f"{self.osrm_base}/route/v1/{self.osrm_profile}/{coordinates}"
    
    response = requests.get(url, timeout=self.osrm_timeout)
    # Parse Response → Distanzen extrahieren
    
    return distance_matrix  # {(0,1): 3.5, (0,2): 7.2, ...}
```

---

### Schritt 3: In LLM-Prompt einbauen

**Aktuell:**
```
Stopps:
0: Kunde 1 - (51.0492, 13.6984)
1: Kunde 2 - (51.0504, 13.7373)
...
```

**Mit OSRM:**
```
Stopps:
0: Kunde 1 - (51.0492, 13.6984)
1: Kunde 2 - (51.0504, 13.7373)
...

Straßen-Distanzen (basierend auf OSRM):
Von 0 nach 1: 3.5 km (5 Min)
Von 0 nach 2: 7.2 km (9 Min)
Von 1 nach 2: 4.1 km (6 Min)
...
```

**Vorteil:** KI bekommt echte Straßen-Distanzen → Bessere Optimierung!

---

### Schritt 4: Visualisierung (Frontend)

**Was der Benutzer sieht:**

**Aktuell (Luftlinie):**
```
Kunde 1 ──────── Kunde 2  (gerade Linie)
```

**Mit OSRM (Straßen-Route):**
```
Kunde 1 ──┐
          │ (Straßen-Route)
          └── Kunde 2  (über Straßen)
```

**Implementierung:**
```javascript
// Wenn Sub-Route geklickt wird:
async function showRouteDetails(subRoute) {
    const stops = subRoute.stops;
    
    // Für jedes Stopp-Paar: OSRM-Route abrufen
    for (let i = 0; i < stops.length - 1; i++) {
        const route = await fetchOSRMRoute(
            stops[i].lat, stops[i].lon,
            stops[i+1].lat, stops[i+1].lon
        );
        
        // Route auf Karte zeichnen (Polyline)
        drawRouteOnMap(route);
    }
}
```

---

## Beispiel: W-07.00 Sub-Route A

**Mit OSRM-Visualisierung:**

```
FAMO-Depot (Start)
    ↓ (2.5 km, 4 Min)
Kunde 1 (Fröbelstraße)
    ↓ (3.2 km, 5 Min über Straßen)
Kunde 2 (Hauptstraße)
    ↓ (1.8 km, 3 Min)
Kunde 3 (Teststraße)
    ...
    ↓
FAMO-Depot (Ende)

Gesamt: 58 Min (Fahrt) + 20 Min (Service) = 78 Min
```

**Auf Karte:** Jede Verbindung zeigt die tatsächliche Straßen-Route, nicht Luftlinie.

---

## API-Endpoints

### OSRM Route API

```bash
# Route zwischen zwei Punkten
GET http://router.project-osrm.org/route/v1/driving/13.6984,51.0492;13.7373,51.0504

# Response:
{
  "routes": [{
    "distance": 3500,  # Meter
    "duration": 300,   # Sekunden
    "geometry": "..."  # Encoded Polyline
  }]
}
```

### OSRM Table API (für Matrix)

```bash
# Distanz-Matrix für mehrere Punkte
GET http://router.project-osrm.org/table/v1/driving/13.6984,51.0492;13.7373,51.0504;...

# Response:
{
  "durations": [[0, 300, 540], [300, 0, 360], ...],
  "distances": [[0, 3500, 7200], [3500, 0, 4100], ...]
}
```

---

## Implementierungs-Reihenfolge

### Phase 1: Backend (Morgen)
- [ ] OSRM-Distanz-Berechnung implementieren
- [ ] In LLM-Prompt einbauen
- [ ] Test mit W-07.00 (30 Stopps)

### Phase 2: Frontend-Visualisierung (Nächste Woche)
- [ ] Route-Details anzeigen wenn Sub-Route geklickt wird
- [ ] OSRM-Route abrufen für jedes Stopp-Paar
- [ ] Route auf Karte zeichnen (Leaflet/OpenLayers)

### Phase 3: Verkehrszeiten (Später)
- [ ] Verkehrszeiten-basierte Routenplanung
- [ ] Unterschiedliche Routen je nach Uhrzeit

---

## Konfiguration

**Umgebungsvariablen:**
```bash
# .env
OSRM_BASE_URL=http://router.project-osrm.org  # Oder lokaler Server
OSRM_PROFILE=driving  # driving, walking, cycling
OSRM_TIMEOUT=10  # Sekunden
```

---

## Vorteile

✅ **Genauere Zeitberechnung:** Straßen-Distanzen statt Luftlinie  
✅ **Bessere Optimierung:** KI bekommt echte Routen-Daten  
✅ **Visualisierung:** Benutzer sieht tatsächliche Straßen-Routen  
✅ **Professioneller:** Wie echte Navigation-Apps  

---

**Status:** 🚧 In Planung - OSRM-Code bereits vorbereitet, muss noch implementiert werden.

