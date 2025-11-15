# Audit-Dokumentation: Sub-Routen Generator

**Erstellt:** 2025-11-09  
**Version:** 3.0  
**Zweck:** Vollständige Dokumentation der Sub-Routen-Generierung für Audit-Zwecke

---

## 1. Übersicht

Der Sub-Routen Generator ist ein kritischer Bestandteil der FAMO TrafficApp, der große Touren (insbesondere W-Touren) automatisch in mehrere optimierte Sub-Routen aufteilt, die jeweils maximal 60-65 Minuten dauern (ohne Rückfahrt zum Depot).

### 1.1 Hauptfunktion

- **Input:** Große Tour mit vielen Stopps (z.B. W-07.00 mit 30 Adressen)
- **Output:** Mehrere optimierte Sub-Routen (z.B. W-07.00 A, W-07.00 B, W-07.00 C)
- **Constraint:** Jede Sub-Route ≤ 65 Minuten (Fahrzeit + Servicezeit, ohne Rückfahrt)

### 1.2 Technologie-Stack

- **Frontend:** Vanilla JavaScript (ES6+)
- **Backend:** Python 3.10+ mit FastAPI
- **Optimierung:** LLM (GPT-4o-mini) oder Nearest-Neighbor Fallback
- **Routing:** OSRM (Open Source Routing Machine) für präzise Fahrzeiten

---

## 2. Architektur-Übersicht

### 2.1 Komponenten-Diagramm

```
┌─────────────────────────────────────────────────────────────┐
│ FRONTEND (frontend/index.html)                              │
│                                                              │
│  ┌────────────────────────────────────────────────────┐    │
│  │ generateSubRoutes()                                │    │
│  │ - Findet W-Touren & große Touren (>4 Kunden)      │    │
│  │ - Bereitet API-Requests vor                        │    │
│  │ - Verarbeitet Backend-Responses                    │    │
│  └──────────────────┬─────────────────────────────────┘    │
│                     │                                        │
│  ┌──────────────────▼─────────────────────────────────┐    │
│  │ splitTourIntoSubRoutes()                           │    │
│  │ - Splittet Touren > 65 Min (Fallback)             │    │
│  │ - Verwendet variable Distanzen                     │    │
│  └────────────────────────────────────────────────────┘    │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ POST /api/tour/optimize
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ BACKEND (routes/workflow_api.py)                             │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ optimize_tour_with_ai()                            │    │
│  │ - Validiert Stopps                                  │    │
│  │ - Ruft LLM-Optimierung auf                         │    │
│  │ - Fallback: Nearest-Neighbor                       │    │
│  │ - Berechnet Zeiten (OSRM oder Haversine)           │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────────┐    │
│  │ enforce_timebox()                                    │    │
│  │ - Prüft Zeit-Constraint (60-65 Min)                 │    │
│  │ - Ruft _split_large_tour_in_workflow() auf         │    │
│  └──────────────────┬──────────────────────────────────┘    │
│                     │                                        │
│  ┌──────────────────▼──────────────────────────────────────┐│
│  │ _split_large_tour_in_workflow()                        ││
│  │ - Rekursives Splitting                                ││
│  │ - Validierung jeder Route                             ││
│  │ - OSRM für präzise Zeiten                             ││
│  └───────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────────┘
                       │
                       │
┌──────────────────────▼──────────────────────────────────────┐
│ SERVICES                                                      │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ services/llm_optimizer.py                          │    │
│  │ - GPT-4o-mini für Route-Optimierung                 │    │
│  │ - JSON-Response mit optimierter Reihenfolge        │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                               │
│  ┌─────────────────────────────────────────────────────┐    │
│  │ services/osrm_client.py                            │    │
│  │ - OSRM Table API für Fahrzeiten                    │    │
│  │ - Fallback: Haversine-Distanz                      │    │
│  └─────────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────────┘
```

---

## 3. Detaillierter Datenfluss

### 3.1 Phase 1: Frontend - Tour-Erkennung

**Datei:** `frontend/index.html`  
**Funktion:** `generateSubRoutes()`

```javascript
// Schritt 1: Finde alle Touren, die optimiert werden müssen
const toursToOptimize = workflowResult.tours.filter(t => {
    const customerCount = (t.stops || []).length;
    const isWTour = /^W-\d+\.\d+/.test(t.tour_id);
    const isLargeTour = customerCount > 4;
    return isWTour || isLargeTour;
});

// Schritt 2: Filtere Stopps mit Koordinaten
const stopsWithCoords = stops.filter(s => s.lat && s.lon);

// Schritt 3: Bereite API-Request vor
const requestBody = {
    tour_id: tour.tour_id,
    is_bar_tour: tour.is_bar_tour || false,
    stops: stopsWithCoords.map(s => ({
        customer_number: s.order_id || s.customer_number,
        name: s.customer || s.name,
        address: s.address,
        lat: s.lat,
        lon: s.lon,
        bar_flag: s.bar_flag || tour.is_bar_tour || false
    }))
};
```

**Kriterien für Optimierung:**
- W-Touren (Regex: `/^W-\d+\.\d+/`) → **IMMER**
- Andere Touren mit > 4 Kunden → **Auch**

**Validierung:**
- Nur Stopps mit `lat` und `lon` werden verwendet
- Warnung wenn keine Koordinaten vorhanden

---

### 3.2 Phase 2: Backend - API-Endpoint

**Datei:** `routes/workflow_api.py`  
**Endpoint:** `POST /api/tour/optimize`  
**Funktion:** `optimize_tour_with_ai()`

#### 3.2.1 Request-Validierung

```python
# 1. Filtere Stopps mit gültigen Koordinaten
valid_stops = [
    s for s in request.stops
    if isinstance(s.lat, (int, float)) and isinstance(s.lon, (int, float))
    and -90 <= s.lat <= 90 and -180 <= s.lon <= 180
]

# 2. Prüfe ob mindestens 1 gültiger Stopp vorhanden
if len(valid_stops) == 0:
    raise HTTPException(400, "Keine Stopps mit gültigen Koordinaten")
```

#### 3.2.2 Optimierungs-Strategie

**Priorität 1: LLM-Optimierung** (wenn enabled)

```python
try:
    result = await llm_optimizer.optimize_route(
        stops=valid_stops,
        depot_coords=(51.0111988, 13.7016485),  # FAMO-Depot Dresden
        model="gpt-4o-mini",
        temperature=0.3
    )
    optimized_indices = result.optimized_route  # [5, 12, 3, 7, ...]
    optimized_stops = [valid_stops[i] for i in optimized_indices]
except Exception as e:
    # Fallback zu Nearest-Neighbor
    optimized_stops = optimize_tour_stops(valid_stops)
```

**Priorität 2: Nearest-Neighbor Fallback**

```python
def optimize_tour_stops(stops: List[Dict]) -> List[Dict]:
    """
    Nearest-Neighbor Heuristik:
    1. Starte mit erstem Stopp
    2. Finde nächsten unbesuchten Stopp (Haversine-Distanz)
    3. Füge zu Route hinzu
    4. Wiederhole bis alle Stopps besucht
    """
    optimized = [stops[0]]
    remaining = stops[1:]
    
    while remaining:
        last = optimized[-1]
        nearest = min(remaining, key=lambda s: haversine_distance(
            last['lat'], last['lon'],
            s['lat'], s['lon']
        ))
        optimized.append(nearest)
        remaining.remove(nearest)
    
    return optimized
```

---

### 3.3 Phase 3: Zeitberechnung

**Datei:** `routes/workflow_api.py`  
**Funktion:** `_calculate_tour_time()` / `_estimate_tour_time_without_return()`

#### 3.3.1 OSRM-basierte Berechnung (wenn verfügbar)

```python
async def _estimate_tour_time_without_return(stops: List[Dict], use_osrm: bool = True) -> float:
    """
    Berechnet Fahrzeit OHNE Rückfahrt zum Depot.
    
    WICHTIG: Rückfahrt wird separat berechnet und zählt NICHT in die 60-65 Min Regel!
    """
    if use_osrm and osrm_client.available:
        # OSRM Table API für präzise Fahrzeiten
        coords = [(s['lat'], s['lon']) for s in stops]
        table = await osrm_client.table(coords)
        total_time = sum(table.durations[i][i+1] for i in range(len(stops)-1))
        return total_time / 60.0  # Sekunden → Minuten
    else:
        # Fallback: Haversine-Distanz
        total_distance = 0.0
        for i in range(len(stops) - 1):
            dist = haversine_distance(
                stops[i]['lat'], stops[i]['lon'],
                stops[i+1]['lat'], stops[i+1]['lon']
            )
            adjusted_dist = dist * 1.3  # Faktor für Stadtverkehr
            total_distance += adjusted_dist
        return (total_distance / 50.0) * 60  # 50 km/h Durchschnitt
```

#### 3.3.2 Service-Zeit

```python
service_time = len(stops) * 2  # 2 Minuten pro Kunde
```

#### 3.3.3 Gesamtzeit (ohne Rückfahrt)

```python
time_without_return = driving_time + service_time
```

**WICHTIG:** Rückfahrt zum Depot wird separat berechnet und zählt **NICHT** in die 60-65 Minuten Regel!

---

### 3.4 Phase 4: Timebox-Enforcement

**Datei:** `routes/workflow_api.py`  
**Funktion:** `enforce_timebox()`

```python
# Konstanten
TIME_BUDGET_WITHOUT_RETURN = 60.0  # Minuten (ohne Rückfahrt)
TIME_BUDGET_WITH_RETURN = 90.0     # Minuten (mit Rückfahrt)

# Prüfe gegen Limits
if est_no_return > TIME_BUDGET_WITHOUT_RETURN:
    # Tour überschreitet Limit → Splitte
    split_tours = _split_large_tour_in_workflow(
        tour_name, stops, TIME_BUDGET_WITHOUT_RETURN
    )
    return split_tours
else:
    # Tour ist OK → gebe als einzelne Route zurück
    return [materialize_tour(tour_name, stops, est_no_return, back_minutes)]
```

---

### 3.5 Phase 5: Rekursives Splitting

**Datei:** `routes/workflow_api.py`  
**Funktion:** `_split_large_tour_in_workflow()`

#### 3.5.1 Algorithmus

```python
def _split_large_tour_in_workflow(
    tour_name: str,
    stops: List[Dict],
    max_time_without_return: float,
    recursion_depth: int = 0
) -> List[Dict]:
    """
    Rekursives Splitting mit Validierung.
    
    WICHTIG: Jede Route wird nach dem Splitting validiert und bei Bedarf
    weiter aufgeteilt (rekursiv).
    """
    MAX_RECURSION_DEPTH = 10
    
    # Schutz gegen Endlosschleifen
    if recursion_depth >= MAX_RECURSION_DEPTH:
        return [{"tour_id": tour_name, "stops": stops, "warning": "Max. Rekursion erreicht"}]
    
    split_tours = []
    current_route = []
    
    for stop in stops:
        # Teste ob Stop in aktuelle Route passt
        test_route = current_route + [stop]
        estimated_time = _estimate_tour_time_without_return(test_route)
        
        if estimated_time <= max_time_without_return:
            # Passt → hinzufügen
            current_route.append(stop)
        else:
            # Zu groß → neue Route starten
            if current_route:
                final_time = _estimate_tour_time_without_return(current_route)
                
                # Validierung: Falls Route immer noch zu lang → rekursiv weiter aufteilen
                if final_time > max_time_without_return:
                    sub_tours = _split_large_tour_in_workflow(
                        tour_name, current_route, max_time_without_return,
                        recursion_depth + 1
                    )
                    split_tours.extend(sub_tours)
                else:
                    # Route ist OK → speichern
                    split_tours.append({
                        "tour_id": tour_name,
                        "stops": current_route,
                        "estimated_time_minutes": round(final_time, 1)
                    })
            
            # Neue Route mit diesem Stop starten
            current_route = [stop]
    
    # Letzte Route hinzufügen (mit Validierung)
    if current_route:
        final_time = _estimate_tour_time_without_return(current_route)
        if final_time > max_time_without_return:
            # Rekursiv weiter aufteilen
            sub_tours = _split_large_tour_in_workflow(
                tour_name, current_route, max_time_without_return,
                recursion_depth + 1
            )
            split_tours.extend(sub_tours)
        else:
            split_tours.append({
                "tour_id": tour_name,
                "stops": current_route,
                "estimated_time_minutes": round(final_time, 1)
            })
    
    return split_tours
```

#### 3.5.2 Wichtige Eigenschaften

1. **Rekursive Validierung:** Jede Route wird nach dem Splitting validiert
2. **OSRM-Integration:** Verwendet OSRM für präzise Fahrzeiten (wenn verfügbar)
3. **Fallback:** Haversine-Distanz mit 1.3x Faktor für Stadtverkehr
4. **Schutz:** Max. Rekursionstiefe = 10 (verhindert Endlosschleifen)

---

### 3.6 Phase 6: Frontend - Sub-Routen-Verarbeitung

**Datei:** `frontend/index.html`  
**Funktion:** `generateSubRoutes()` (Fortsetzung)

#### 3.6.1 Backend-Response verarbeiten

```javascript
// Prüfe ob Backend bereits Sub-Touren zurückgegeben hat
if (result.is_split && result.sub_tours && result.sub_tours.length > 0) {
    // Backend hat bereits gesplittet → verwende Sub-Touren
    for (const subTour of result.sub_tours) {
        const subRouteLetter = subTour.sub_route_letter; // A, B, C, ...
        const subTourName = `${tour.tour_id} ${subRouteLetter}`;
        
        // Erstelle Sub-Tour-Eintrag
        allTourCustomers[subRouteKey] = {
            name: subTourName,
            customers: subTour.optimized_stops,
            estimated_driving_time_minutes: subTour.estimated_driving_time_minutes,
            estimated_service_time_minutes: subTour.estimated_service_time_minutes,
            estimated_return_time_minutes: subTour.estimated_return_time_minutes,
            _is_sub_route: true,
            _parent_tour_id: tour.tour_id
        };
    }
} else if (timeWithoutReturn > 65) {
    // Fallback: Frontend-Splitting (nur wenn Backend nicht gesplittet hat)
    const subTours = splitTourIntoSubRoutes(tour, result);
    // ...
}
```

#### 3.6.2 Frontend-Splitting (Fallback)

**Datei:** `frontend/index.html`  
**Funktion:** `splitTourIntoSubRoutes()`

```javascript
function splitTourIntoSubRoutes(tour, optimizationResult) {
    const maxTimePerRoute = 65; // Minuten (OHNE Rückfahrt!)
    const serviceTimePerStop = 2; // Minuten
    
    // Verwende variable Distanzen (vom Backend oder berechnet)
    const segmentDistances = optimizationResult.segment_distances || [];
    
    const subRoutes = [];
    let currentRoute = [];
    let currentTime = 0;
    let routeLetter = 'A';
    
    for (let i = 0; i < stops.length; i++) {
        // Berechne Fahrzeit zum nächsten Stop
        const driveTime = getDriveTimeToNextStop(i - 1, i, segmentDistances);
        const serviceTime = serviceTimePerStop;
        const totalTime = driveTime + serviceTime;
        
        if (currentTime + totalTime <= maxTimePerRoute) {
            // Passt in aktuelle Route
            currentRoute.push(stops[i]);
            currentTime += totalTime;
        } else {
            // Route ist voll → speichere und starte neue
            subRoutes.push({
                tour_id: tour.tour_id,
                sub_route: routeLetter,
                stops: currentRoute,
                driving_time: currentTime - (currentRoute.length * serviceTime),
                service_time: currentRoute.length * serviceTime,
                total_time: currentTime
            });
            
            currentRoute = [stops[i]];
            currentTime = totalTime;
            routeLetter = String.fromCharCode(routeLetter.charCodeAt(0) + 1);
        }
    }
    
    // Letzte Route hinzufügen
    if (currentRoute.length > 0) {
        subRoutes.push({...});
    }
    
    return subRoutes;
}
```

**WICHTIG:** Frontend-Splitting ist nur ein Fallback! Das Backend sollte bereits beim initialen Clustering die Touren korrekt aufteilen.

---

## 4. Wichtige Regeln und Constraints

### 4.1 Zeit-Constraints

| Regel | Wert | Beschreibung |
|-------|------|--------------|
| **Max. Zeit ohne Rückfahrt** | 60-65 Minuten | Fahrzeit + Servicezeit (ohne Rückfahrt zum Depot) |
| **Max. Zeit mit Rückfahrt** | 90 Minuten | Gesamtzeit inkl. Rückfahrt zum Depot |
| **Service-Zeit pro Kunde** | 2 Minuten | Feste Annahme |
| **Durchschnittsgeschwindigkeit** | 50 km/h | Für Haversine-Fallback |

### 4.2 Splitting-Regeln

1. **Rückfahrt zählt NICHT:** Die 60-65 Minuten Regel gilt nur für Fahrzeit + Servicezeit, **ohne** Rückfahrt zum Depot
2. **Rekursive Validierung:** Jede Route wird nach dem Splitting validiert und bei Bedarf weiter aufgeteilt
3. **OSRM-Priorität:** Wenn OSRM verfügbar, werden präzise Fahrzeiten verwendet
4. **Fallback:** Haversine-Distanz mit 1.3x Faktor für Stadtverkehr

### 4.3 Tour-Erkennung

- **W-Touren:** Regex `/^W-\d+\.\d+/` → **IMMER** optimieren
- **Große Touren:** > 4 Kunden → **Auch** optimieren
- **Koordinaten erforderlich:** Nur Stopps mit `lat` und `lon` werden verwendet

---

## 5. Beispiel: W-07.00 mit 30 Stopps

### 5.1 Input

```
Tour: W-07.00 Uhr Tour
Stopps: 30 Adressen mit Koordinaten
```

### 5.2 Schritt 1: LLM-Optimierung

```
LLM analysiert geografische Nähe:
- Stopp 5 (Fröbelstraße) → 12 (Hauptstraße) → 3 (Teststraße) → ...
- Ergebnis: Optimierte Reihenfolge [5, 12, 3, 7, 1, 15, ...]
```

### 5.3 Schritt 2: Zeitberechnung

```
Fahrzeit: 45.5 Minuten (OSRM-basiert)
Service-Zeit: 60 Minuten (30 * 2)
Total (ohne Rückfahrt): 105.5 Minuten → ÜBER 60!
```

### 5.4 Schritt 3: Splitting

```
Route A: Stopps [5, 12, 3, 7, 1, 15, 8, 22]
  → 8 Stopps, 58.2 Min (ohne Rückfahrt) ✅

Route B: Stopps [16, 9, 23, 6, 18, 2, 14, 20]
  → 8 Stopps, 59.3 Min (ohne Rückfahrt) ✅

Route C: Stopps [13, 19, 17, 10, 24, 21, 25, 26]
  → 8 Stopps, 61.1 Min (ohne Rückfahrt) ✅

Route D: Stopps [27, 28, 29, 0]
  → 4 Stopps, 42.5 Min (ohne Rückfahrt) ✅
```

### 5.5 Schritt 4: Ergebnis

```
Original: "W-07.00 Uhr Tour" (30 Stopps, 105.5 Min)
↓
4 Sub-Routen:
  - "W-07.00 Uhr Tour A" (8 Stopps, 58.2 Min + 18 Min Rückfahrt = 76.2 Min gesamt)
  - "W-07.00 Uhr Tour B" (8 Stopps, 59.3 Min + 15 Min Rückfahrt = 74.3 Min gesamt)
  - "W-07.00 Uhr Tour C" (8 Stopps, 61.1 Min + 12 Min Rückfahrt = 73.1 Min gesamt)
  - "W-07.00 Uhr Tour D" (4 Stopps, 42.5 Min + 20 Min Rückfahrt = 62.5 Min gesamt)
```

---

## 6. Dateien-Übersicht

### 6.1 Frontend

| Datei | Funktionen | Zeilen |
|-------|-----------|--------|
| `frontend/index.html` | `generateSubRoutes()`, `splitTourIntoSubRoutes()`, `updateToursWithSubRoutes()` | ~3250-4000 |

### 6.2 Backend

| Datei | Funktionen | Zeilen |
|-------|-----------|--------|
| `routes/workflow_api.py` | `optimize_tour_with_ai()`, `enforce_timebox()`, `_split_large_tour_in_workflow()` | ~2000-2500 |
| `routes/engine_api.py` | `split_tour()` (alternativer Endpoint) | ~445-500 |

### 6.3 Services

| Datei | Funktionen | Zeilen |
|-------|-----------|--------|
| `services/llm_optimizer.py` | `optimize_route()` (LLM-Optimierung) | ~100-300 |
| `services/osrm_client.py` | OSRM Table API für Fahrzeiten | - |

### 6.4 Dokumentation

| Datei | Inhalt |
|-------|--------|
| `docs/SUB_ROUTES_GENERATOR_LOGIC.md` | Detaillierte Logik-Beschreibung |
| `docs/SPLITTING_INFO_FLOW.md` | Informationsfluss-Diagramm |

### 6.5 Tests

| Datei | Zweck |
|-------|------|
| `tests/test_subroutes_500_fix.py` | Unit-Tests für Sub-Routen-Generator |
| `scripts/test_w07_split.py` | Test-Script für W-07.00 Splitting |

---

## 7. API-Endpunkte

### 7.1 POST /api/tour/optimize

**Request:**
```json
{
  "tour_id": "W-07.00 Uhr Tour",
  "is_bar_tour": false,
  "stops": [
    {
      "customer_number": "5236",
      "name": "MSM by HUBraum GmbH",
      "address": "Fröbelstraße 20, 01159, Dresden",
      "lat": 51.05214,
      "lon": 13.714627,
      "bar_flag": false
    },
    // ... weitere Stopps
  ]
}
```

**Response (ohne Splitting):**
```json
{
  "success": true,
  "optimized_stops": [...],
  "estimated_driving_time_minutes": 45.5,
  "estimated_service_time_minutes": 60.0,
  "estimated_total_time_minutes": 105.5,
  "estimated_return_time_minutes": 18.0,
  "is_split": false,
  "sub_tours": []
}
```

**Response (mit Splitting):**
```json
{
  "success": true,
  "optimized_stops": [...],
  "is_split": true,
  "split_count": 4,
  "sub_tours": [
    {
      "tour_id": "W-07.00 Uhr Tour",
      "sub_route_index": 0,
      "sub_route_letter": "A",
      "optimized_stops": [...],
      "estimated_driving_time_minutes": 58.2,
      "estimated_service_time_minutes": 16.0,
      "estimated_total_time_minutes": 74.2,
      "estimated_return_time_minutes": 18.0,
      "estimated_total_with_return_minutes": 92.2,
      "stop_count": 8,
      "reasoning": "Sub-Route A von 4 Routen"
    },
    // ... weitere Sub-Touren
  ]
}
```

---

## 8. Fehlerbehandlung

### 8.1 Häufige Fehler

| Fehler | Ursache | Lösung |
|--------|---------|--------|
| **404 auf /api/tour/optimize** | Server nicht neu gestartet | Server neu starten |
| **Index-Mapping-Fehler** | LLM gibt ungültige Indizes zurück | Koordinaten-Match mit Toleranz |
| **Keine Koordinaten** | Stopps ohne lat/lon | Warnung, Stopps werden übersprungen |
| **Max. Rekursion erreicht** | Tour zu groß für Splitting | Tour wird trotzdem zurückgegeben (mit Warnung) |

### 8.2 Logging

Alle kritischen Schritte werden geloggt:

```python
print(f"[TOUR-OPTIMIZE] Anfrage für Tour: {tour_id}, {len(stops)} Stopps")
print(f"[TOUR-OPTIMIZE] Tour {tour_id} wurde in {len(split_tours)} Sub-Touren aufgeteilt")
print(f"[WORKFLOW] Route {tour_name} erstellt: {len(stops)} Stopps, {time:.1f} Min")
```

---

## 9. Performance-Überlegungen

### 9.1 OSRM vs. Haversine

- **OSRM:** Präzise, aber langsamer (API-Call pro Route)
- **Haversine:** Schnell, aber weniger präzise (Luftlinie)

**Strategie:** OSRM wenn verfügbar, sonst Haversine mit 1.3x Faktor

### 9.2 LLM vs. Nearest-Neighbor

- **LLM:** Bessere Optimierung, aber teurer und langsamer
- **Nearest-Neighbor:** Schnell, aber suboptimal

**Strategie:** LLM wenn enabled, sonst Nearest-Neighbor

### 9.3 Rekursionstiefe

- **Max. Tiefe:** 10 (verhindert Endlosschleifen)
- **Typische Tiefe:** 1-3 für normale Touren

---

## 10. Test-Strategie

### 10.1 Unit-Tests

**Datei:** `tests/test_subroutes_500_fix.py`

```python
def test_split_large_tour():
    """Testet Splitting einer großen Tour."""
    stops = [create_stop(i) for i in range(30)]
    split_tours = _split_large_tour_in_workflow("W-07.00", stops, 60.0)
    assert len(split_tours) > 1
    assert all(t["estimated_time_minutes"] <= 60.0 for t in split_tours)
```

### 10.2 Integration-Tests

**Datei:** `scripts/test_w07_split.py`

```python
# Testet vollständigen Workflow:
# 1. CSV-Upload
# 2. Match
# 3. Optimierung
# 4. Splitting
# 5. UI-Rendering
```

---

## 11. Bekannte Probleme und Lösungen

### 11.1 Problem: Sub-Routen werden nicht angezeigt

**Ursache:** Frontend verarbeitet `sub_tours` nicht korrekt

**Lösung:** `allTourCustomers` wird aktualisiert, `renderToursFromCustomers()` wird aufgerufen

### 11.2 Problem: Rückfahrt wird in 60-65 Min Regel gezählt

**Ursache:** Falsche Zeitberechnung

**Lösung:** Rückfahrt wird separat berechnet und zählt **NICHT** in die Regel

### 11.3 Problem: Rekursive Endlosschleife

**Ursache:** Route kann nicht weiter aufgeteilt werden

**Lösung:** Max. Rekursionstiefe = 10, Warnung wird ausgegeben

---

## 12. Zukünftige Verbesserungen

1. **Geografisches Clustering:** Stopps vor Optimierung nach Nähe gruppieren
2. **Intelligenteres Splitting:** Nicht nur sequenziell, sondern nach Clustern
3. **OSRM-Caching:** Fahrzeiten cachen für bessere Performance
4. **UI-Verbesserungen:** Bessere Visualisierung von Sub-Routen

---

## 13. Zusammenfassung

Der Sub-Routen Generator ist ein komplexes System, das:

1. **Große Touren erkennt** (W-Touren oder > 4 Kunden)
2. **Route optimiert** (LLM oder Nearest-Neighbor)
3. **Zeit berechnet** (OSRM oder Haversine)
4. **Bei Bedarf splittet** (rekursiv mit Validierung)
5. **Sub-Routen zurückgibt** (A, B, C, ...)

**Wichtigste Regel:** Fahrzeit + Servicezeit ≤ 60-65 Minuten (ohne Rückfahrt zum Depot)

---

**Ende der Audit-Dokumentation**

