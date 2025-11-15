# Splitting-Prozess: Informationsfluss-Diagramm

## Übersicht

Dieses Diagramm zeigt, wie eine große Tour (z.B. W-07.00 mit 30 Stopps) in mehrere Sub-Routen aufgeteilt wird, **unter Verwendung von variablen Distanzen** zwischen jedem Stopp-Paar.

---

## Informationsfluss: Schritt-für-Schritt

```
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: generateSubRoutes()                                    │
│ - Erkennt W-Touren oder Touren mit > 4 Kunden                   │
│ - Bereitet Stopps vor (mit Koordinaten)                         │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ API CALL: POST /api/tour/optimize                               │
│ Request Body:                                                    │
│ {                                                                │
│   "tour_id": "W-07.00",                                          │
│   "stops": [                                                     │
│     {"lat": 51.0492, "lon": 13.6984, ...},                      │
│     {"lat": 51.0504, "lon": 13.7372, ...},                      │
│     ... (30 Stopps)                                             │
│   ]                                                              │
│ }                                                                │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ BACKEND: routes/workflow_api.py                                  │
│ optimize_tour_with_ai()                                          │
│                                                                   │
│ 1. Filtert Stopps mit Koordinaten                                │
│ 2. Optimiert Reihenfolge (LLM oder Nearest-Neighbor)           │
│ 3. Berechnet INDIVIDUELLE Distanzen pro Segment:                │
│                                                                   │
│    segment_distances = [                                         │
│      {                                                           │
│        "from": "depot",                                          │
│        "to": 0,                                                  │
│        "distance_km": 5.2,        ← VARIABEL!                   │
│        "driving_time_minutes": 6.24 ← VARIABEL!                 │
│      },                                                          │
│      {                                                           │
│        "from": 0,                                                │
│        "to": 1,                                                  │
│        "distance_km": 3.1,        ← VARIABEL!                   │
│        "adjusted_distance_km": 4.03,                            │
│        "driving_time_minutes": 4.84 ← VARIABEL!                 │
│      },                                                          │
│      {                                                           │
│        "from": 1,                                                │
│        "to": 2,                                                  │
│        "distance_km": 10.5,       ← VARIABEL!                   │
│        "adjusted_distance_km": 13.65,                           │
│        "driving_time_minutes": 16.38 ← VARIABEL!                 │
│      },                                                          │
│      ... (29 weitere Segmente)                                  │
│    ]                                                             │
│                                                                   │
│ 4. Berechnet Gesamtzeiten                                       │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ RESPONSE: JSON mit segment_distances                            │
│ {                                                                │
│   "optimized_stops": [...],                                      │
│   "estimated_driving_time_minutes": 185.3,                      │
│   "estimated_service_time_minutes": 60,                         │
│   "estimated_total_time_minutes": 245.3,                        │
│   "segment_distances": [                                         │
│     {"from": "depot", "to": 0, "driving_time_minutes": 6.24},  │
│     {"from": 0, "to": 1, "driving_time_minutes": 4.84},         │
│     {"from": 1, "to": 2, "driving_time_minutes": 16.38},        │
│     ...                                                          │
│   ],                                                             │
│   "depot_coordinates": {"lat": 51.0111988, "lon": 13.7016485}  │
│ }                                                                │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: splitTourIntoSubRoutes()                              │
│                                                                   │
│ INPUT:                                                           │
│   - tour: {tour_id: "W-07.00", stops: [...]}                    │
│   - optimizationResult: {segment_distances: [...], ...}        │
│                                                                   │
│ LOGIK:                                                           │
│                                                                   │
│ maxTimePerRoute = 60 Minuten                                     │
│ serviceTimePerStop = 2 Minuten                                  │
│                                                                   │
│ ┌─────────────────────────────────────────────────────────┐   │
│ │ Für jeden Stop in optimierter Reihenfolge:              │   │
│ │                                                           │   │
│ │ Stop 0:                                                  │   │
│ │   - driveTime = segment_distances[0].driving_time       │   │
│ │     (= 6.24 Min vom Depot) ← VARIABEL!                   │   │
│ │   - serviceTime = 2 Min                                  │   │
│ │   - total = 8.24 Min                                     │   │
│ │   - ✅ Passt in Route A                                  │   │
│ │                                                           │   │
│ │ Stop 1:                                                  │   │
│ │   - driveTime = segment_distances[1].driving_time       │   │
│ │     (= 4.84 Min von Stop 0) ← VARIABEL!                 │   │
│ │   - serviceTime = 2 Min                                  │   │
│ │   - total = 6.84 Min                                     │   │
│ │   - Route A: 8.24 + 6.84 = 15.08 Min ✅                 │   │
│ │                                                           │   │
│ │ Stop 2:                                                  │   │
│ │   - driveTime = segment_distances[2].driving_time       │   │
│ │     (= 16.38 Min von Stop 1) ← VARIABEL! (lange Distanz)│   │
│ │   - serviceTime = 2 Min                                  │   │
│ │   - total = 18.38 Min                                    │   │
│ │   - Route A: 15.08 + 18.38 = 33.46 Min ✅               │   │
│ │                                                           │   │
│ │ Stop 3:                                                  │   │
│ │   - driveTime = segment_distances[3].driving_time       │   │
│ │     (= 9.6 Min von Stop 2) ← VARIABEL!                  │   │
│ │   - serviceTime = 2 Min                                  │   │
│ │   - total = 11.6 Min                                     │   │
│ │   - Route A: 33.46 + 11.6 = 45.06 Min ✅                │   │
│ │                                                           │   │
│ │ ...                                                       │   │
│ │                                                           │   │
│ │ Stop 8:                                                  │   │
│ │   - driveTime = 12.5 Min (variable!)                     │   │
│ │   - serviceTime = 2 Min                                  │   │
│ │   - total = 14.5 Min                                     │   │
│ │   - Route A: 58.2 + 14.5 = 72.7 Min ❌ ÜBERSCHREITET!   │   │
│ │   - ➡️ Route A abschließen (8 Stopps)                   │   │
│ │   - ➡️ Route B starten mit Stop 8                       │   │
│ │                                                           │   │
│ │ Stop 9 (neue Route B):                                   │   │
│ │   - driveTime = segment_distances[9].driving_time       │   │
│ │     (= 8.5 Min von Stop 8) ← VARIABEL!                   │   │
│ │   - serviceTime = 2 Min                                  │   │
│ │   - Route B: 0 + 10.5 = 10.5 Min ✅                     │   │
│ │                                                           │   │
│ │ ... (weiter mit variablen Distanzen)                    │   │
│ └─────────────────────────────────────────────────────────┘   │
│                                                                   │
│ OUTPUT:                                                          │
│   [                                                              │
│     {                                                            │
│       tour_id: "W-07.00",                                        │
│       sub_route: "A",                                           │
│       stops: [stop0, stop1, ..., stop7],                        │
│       driving_time: 58.2,                                       │
│       service_time: 16,                                         │
│       total_time: 74.2                                          │
│     },                                                           │
│     {                                                            │
│       tour_id: "W-07.00",                                        │
│       sub_route: "B",                                           │
│       stops: [stop8, stop9, ..., stop15],                       │
│       driving_time: 52.3,                                       │
│       service_time: 16,                                         │
│       total_time: 68.3                                          │
│     },                                                           │
│     ... (weitere Sub-Routen)                                    │
│   ]                                                              │
└───────────────────────┬─────────────────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│ FRONTEND: updateToursWithSubRoutes()                            │
│ - Ersetzt ursprüngliche Tour durch Sub-Routen                  │
│ - Zeigt in UI: "W-07.00 A", "W-07.00 B", "W-07.00 C", ...      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Beispiel: W-07.00 mit 30 Stopps

### Variable Distanzen (Beispiel)

| Segment | Von → Zu | Distanz (km) | Fahrzeit (Min) | Service (Min) | Total (Min) |
|---------|----------|--------------|----------------|---------------|-------------|
| Depot → Stop 0 | Depot → 1. Kunde | 5.2 | 6.24 | 2.0 | 8.24 |
| Stop 0 → Stop 1 | 1. → 2. Kunde | 3.1 | 4.84 | 2.0 | 6.84 |
| Stop 1 → Stop 2 | 2. → 3. Kunde | 10.5 | 16.38 | 2.0 | 18.38 |
| Stop 2 → Stop 3 | 3. → 4. Kunde | 8.0 | 9.60 | 2.0 | 11.60 |
| Stop 3 → Stop 4 | 4. → 5. Kunde | 4.5 | 5.40 | 2.0 | 7.40 |
| Stop 4 → Stop 5 | 5. → 6. Kunde | 6.8 | 8.16 | 2.0 | 10.16 |
| Stop 5 → Stop 6 | 6. → 7. Kunde | 7.2 | 8.64 | 2.0 | 10.64 |
| Stop 6 → Stop 7 | 7. → 8. Kunde | 5.5 | 6.60 | 2.0 | 8.60 |
| Stop 7 → Stop 8 | 8. → 9. Kunde | 10.4 | 12.48 | 2.0 | 14.48 |
| **Stop 7 → Stop 8** | | | | | **Summe Route A: 74.32** ❌ |
| Stop 8 → Stop 9 | 9. → 10. Kunde (Route B) | 8.5 | 10.20 | 2.0 | 12.20 |
| ... | ... | ... | ... | ... | ... |

### Splitting-Ergebnis

```
Route A (0-7): 8 Stopps, 74.2 Min (wegen 8. → 9. überschreitet 60 Min)
Route B (8-15): 8 Stopps, 68.3 Min
Route C (16-23): 8 Stopps, 71.5 Min
Route D (24-30): 7 Stopps, 58.2 Min
```

**Ergebnis: 4 Sub-Routen** (variabel je nach tatsächlichen Distanzen!)

---

## Wichtige Unterschiede zu vorher

### ❌ VORHER (feste Werte):
```javascript
// Alle Stopps: 5 Min Fahrt + 2 Min Service = 7 Min
const estimatedDriveTime = 5;  // FEST!
```

**Problem:** 
- 30 Stopps × 7 Min = 210 Min → 3-4 Routen
- Ignoriert: Depot → Kunde 1 kann 5 km (6 Min) oder 8 km (9.6 Min) sein
- Ignoriert: Kunde 1 → Kunde 2 kann 3 km (3.6 Min) oder 10 km (12 Min) sein

### ✅ JETZT (variable Distanzen):
```javascript
// Jeder Stopp: Individuelle Distanz vom Backend
const driveTime = segment_distances[i].driving_time_minutes;  // VARIABEL!
// Depot → Stop 0: 6.24 Min (5.2 km)
// Stop 0 → Stop 1: 4.84 Min (3.1 km)
// Stop 1 → Stop 2: 16.38 Min (10.5 km) ← lange Distanz!
// Stop 2 → Stop 3: 9.60 Min (8.0 km)
```

**Vorteil:**
- Berücksichtigt jede einzelne Distanz
- Depot → Kunde: 5 km = 6 Min, 8 km = 9.6 Min
- Kunde → Kunde: 3 km = 3.6 Min, 10 km = 12 Min
- **Resultat:** Genauere Aufteilung, oft 5-6 Routen statt 3-4

---

## Datenstruktur: segment_distances

```json
{
  "segment_distances": [
    {
      "from": "depot",
      "to": 0,
      "distance_km": 5.2,
      "driving_time_minutes": 6.24
    },
    {
      "from": 0,
      "to": 1,
      "distance_km": 3.1,
      "adjusted_distance_km": 4.03,
      "driving_time_minutes": 4.84
    },
    {
      "from": 1,
      "to": 2,
      "distance_km": 10.5,
      "adjusted_distance_km": 13.65,
      "driving_time_minutes": 16.38
    }
    // ... weitere Segmente
  ]
}
```

**Berechnung:**
- `distance_km`: Haversine-Distanz (Luftlinie)
- `adjusted_distance_km`: `distance_km × 1.3` (Faktor für Stadtverkehr)
- `driving_time_minutes`: `(adjusted_distance_km / 50 km/h) × 60`

---

## Fallback-Logik

Falls `segment_distances` nicht verfügbar:

1. **Frontend berechnet selbst** aus Koordinaten:
   ```javascript
   distanceKm = haversineDistance(stop1.lat, stop1.lon, stop2.lat, stop2.lon);
   adjustedDistance = distanceKm * 1.3;  // Faktor für Stadtverkehr
   drivingTime = (adjustedDistance / 50) * 60;  // 50 km/h
   ```

2. **Letzter Fallback**: 5 Minuten (selten nötig)

---

## Zusammenfassung

✅ **Variable Distanzen**: Jedes Segment hat individuelle Fahrzeit  
✅ **Depot → Kunde**: 5 km = 6 Min, 8 km = 9.6 Min (variabel!)  
✅ **Kunde → Kunde**: 3 km = 3.6 Min, 10 km = 12 Min (variabel!)  
✅ **Genauere Aufteilung**: 5-6 Sub-Routen statt 3-4  
✅ **Realistische Zeitschätzung**: Basierend auf tatsächlichen Distanzen

