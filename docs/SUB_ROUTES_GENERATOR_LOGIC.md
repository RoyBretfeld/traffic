# Sub-Routen Generator - Logik & Datenfluss

## Übersicht

Der Sub-Routen Generator teilt große Touren (insbesondere W-Touren) in mehrere optimierte Sub-Routen auf, die jeweils maximal 60-65 Minuten dauern sollen.

**Beispiel:** W-07.00 mit 30 Adressen → 4-6 Sub-Routen (W-07.00 A, W-07.00 B, W-07.00 C, ...)

**WICHTIG:** Seit der Verbesserung verwendet das Splitting **variable Distanzen** zwischen jedem Stopp-Paar (nicht mehr Durchschnittswerte). Siehe `SPLITTING_INFO_FLOW.md` für Details.

---

## Schritt-für-Schritt: Wie funktioniert es?

### Phase 1: Vorbereitung (Frontend)

**Datei:** `frontend/index.html` - Funktion `generateSubRoutes()`

```javascript
1. Finde alle Touren die optimiert werden müssen:
   - W-Touren (Regex: /^W-\d+\.\d+/) → IMMER optimieren
   - Andere Touren mit > 4 Kunden → Auch optimieren

2. Filtere Stopps mit Koordinaten:
   - Nur Stopps mit lat && lon werden verwendet
   - Warnung wenn keine Koordinaten vorhanden

3. Für jede Tour:
   - Bereite Stopps für API vor (customer_number, name, address, lat, lon, ...)
   - Sende POST-Request an /api/tour/optimize
```

**Beispiel für W-07.00:**
```javascript
tour_id: "W-07.00 Uhr Tour"
stops: [
  { customer: "Kunde 1", lat: 51.05, lon: 13.74, ... },
  { customer: "Kunde 2", lat: 51.06, lon: 13.75, ... },
  // ... 30 Stopps total
]
```

---

### Phase 2: API-Request (Backend)

**Endpoint:** `POST /api/tour/optimize`

**Datei:** `routes/workflow_api.py` - Funktion `optimize_tour_with_ai()`

```python
1. Request Body empfangen:
   {
     "tour_id": "W-07.00 Uhr Tour",
     "stops": [30 Stopps mit Koordinaten]
   }

2. Validierung:
   - Filtere Stopps mit gültigen Koordinaten (-90 <= lat <= 90, -180 <= lon <= 180)
   - Prüfe ob mindestens 1 gültiger Stopp vorhanden

3. Optimierungs-Strategie:
   A) LLM-Optimierung (wenn enabled)
   B) Nearest-Neighbor Fallback (wenn LLM fehlschlägt)
```

---

### Phase 3: AI-Optimierung (LLM)

**Datei:** `services/llm_optimizer.py` - Funktion `optimize_route()`

#### Schritt 3.1: Prompt erstellen

```python
Prompt für W-07.00 (30 Stopps):
"""
Optimiere die Route für 30 Stopps in Dresden.

Stopps:
0: Kunde 1 - Fröbelstraße 1, Dresden (51.0492, 13.6984)
1: Kunde 2 - Hauptstraße 5, Dresden (51.0504, 13.7373)
...
29: Kunde 30 - Teststraße 99, Dresden (51.0520, 13.7400)

Berücksichtige:
- Minimale Gesamtfahrzeit
- Logische geografische Reihenfolge
- Start/Ende: FAMO-Depot (51.0111988, 13.7016485)

Gib die optimale Reihenfolge als Liste von Indizes zurück (z.B. [0, 3, 1, 2]).
"""
```

#### Schritt 3.2: LLM-Call

```python
OpenAI API-Call:
- Model: gpt-4o-mini
- Temperature: 0.3 (niedrig für konsistente Ergebnisse)
- Response Format: JSON
- Max Tokens: 1000
```

#### Schritt 3.3: Response parsen

```python
LLM Response (JSON):
{
  "optimized_route": [5, 12, 3, 7, 1, 15, ...],  # Indizes in optimierter Reihenfolge
  "reasoning": "Ich habe die Stopps nach geografischer Nähe gruppiert...",
  "estimated_driving_time_minutes": 45.5,
  "estimated_service_time_minutes": 60.0,  # 30 Kunden * 2 Min
  "estimated_total_time_minutes": 105.5
}
```

**→ Problem:** 105.5 Minuten > 60 Minuten → Muss gesplittet werden!

#### Schritt 3.4: Index-Mapping

```python
# WICHTIG: LLM gibt Indizes zurück, nicht Objekte
optimized_indices = result.optimized_route  # [5, 12, 3, 7, ...]

# Mappe Indizes zu originalen Stopp-Objekten
optimized_stops = [valid_stops[i] for i in optimized_indices]

# Beispiel:
# valid_stops[5] → Kunde 6 (wird jetzt als erster gefahren)
# valid_stops[12] → Kunde 13 (wird jetzt als zweiter gefahren)
```

**⚠️ Hier passiert der Fehler manchmal:**
- Wenn Index-Mapping unvollständig ist → Exception
- Wenn Koordinaten nicht matchen → Exception

---

### Phase 4: Fallback (Nearest-Neighbor)

**Datei:** `routes/workflow_api.py` - Funktion `optimize_tour_stops()`

Wenn LLM fehlschlägt oder deaktiviert:

```python
1. Starte mit erstem Stopp
2. Finde nächsten unbesuchten Stopp (Haversine-Distanz)
3. Füge zu Route hinzu
4. Wiederhole bis alle Stopps besucht

Beispiel für 30 Stopps:
optimized = [0]  # Start mit Stopp 0
remaining = [1, 2, 3, ..., 29]

while remaining:
    last = optimized[-1]
    nearest = min(remaining, key=lambda i: distance(last, i))
    optimized.append(nearest)
    remaining.remove(nearest)

Resultat: [0, 5, 12, 3, 7, 1, 15, ...]  # Nearest-Neighbor Route
```

---

### Phase 5: Zeitberechnung

**Datei:** `routes/workflow_api.py` - Funktion `_calculate_tour_time()`

```python
1. Fahrzeit zwischen Stopps (Haversine):
   - Stopp 0 → Stopp 1: 2.5 km → 3 Minuten (50 km/h)
   - Stopp 1 → Stopp 2: 1.8 km → 2.2 Minuten
   - ...

2. Service-Zeit:
   - 2 Minuten pro Kunde
   - 30 Kunden = 60 Minuten Service-Zeit

3. Gesamtzeit:
   - Fahrzeit: 45.5 Minuten
   - Service-Zeit: 60 Minuten
   - Total: 105.5 Minuten

4. Rückfahrt zum Depot:
   - Letzter Stopp → FAMO: 15 km → 18 Minuten
   - Total mit Rückfahrt: 123.5 Minuten
```

**→ Warnung:** Überschreitung der 60-Minuten-Grenze!

---

### Phase 6: Splitting in Sub-Routen

**Datei:** `frontend/index.html` - Funktion `splitTourIntoSubRoutes()`

```javascript
if (estimated_total_time_minutes > 60) {
    // Tour muss gesplittet werden
    
    1. Initialisiere:
       - maxTimePerRoute = 60 Minuten
       - serviceTimePerStop = 2 Minuten
       - currentRoute = []
       - subRoutes = []
       - routeLetter = 'A'
    
    2. Iteriere über optimierte Stopps:
       for (stop of optimized_stops) {
           estimatedDrivingTime = calculateDrivingTime(currentRoute + stop)
           estimatedServiceTime = (currentRoute.length + 1) * 2
           totalTime = estimatedDrivingTime + estimatedServiceTime
           
           if (totalTime <= 60) {
               // Füge Stopp zur aktuellen Route hinzu
               currentRoute.push(stop)
           } else {
               // Aktuelle Route ist voll → Speichere und starte neue
               subRoutes.push({
                   tour_id: "W-07.00 Uhr Tour",
                   sub_route: routeLetter,
                   stops: currentRoute,
                   total_time: previousTotalTime
               })
               currentRoute = [stop]  // Neue Route mit diesem Stopp
               routeLetter = 'B'  // Nächster Buchstabe
           }
       }
    
    3. Beispiel-Ergebnis für W-07.00 (30 Stopps, 105 Min):
       Sub-Route A: Stopps 0-9  (10 Stopps, 58 Min)
       Sub-Route B: Stopps 10-19 (10 Stopps, 59 Min)
       Sub-Route C: Stopps 20-29 (10 Stopps, 60 Min)
}
```

**Beispiel für W-07.00:**
```
Original: W-07.00 Uhr Tour (30 Stopps, 105 Min)
↓ Split
Sub-Route A: W-07.00 Uhr Tour A (10 Stopps, 58 Min)
Sub-Route B: W-07.00 Uhr Tour B (10 Stopps, 59 Min)
Sub-Route C: W-07.00 Uhr Tour C (10 Stopps, 60 Min)
```

---

### Phase 7: UI-Update

**Datei:** `frontend/index.html` - Funktion `updateToursWithSubRoutes()`

```javascript
1. Gruppiere Sub-Routen nach ursprünglicher Tour-ID

2. Ersetze Original-Tour durch Sub-Routen:
   workflowResult.tours = workflowResult.tours.map(tour => {
       if (tour.tour_id === "W-07.00 Uhr Tour" && grouped[tour.tour_id]) {
           // Ersetze durch Sub-Routen
           return grouped[tour.tour_id].map(sub => ({
               ...tour,
               tour_id: `${tour.tour_id} ${sub.sub_route}`,  // "W-07.00 Uhr Tour A"
               stops: sub.stops,
               total_time_minutes: sub.total_time
           }))
       }
       return tour
   }).flat()

3. Rendere Tour-Liste neu
4. Speichere in localStorage
```

---

## Datenfluss-Diagramm

```
[Frontend: generateSubRoutes()]
    ↓
[Filter: W-Touren & >4 Kunden finden]
    ↓
[Für jede Tour: API-Request vorbereiten]
    ↓
    POST /api/tour/optimize
    ↓
[Backend: optimize_tour_with_ai()]
    ↓
[Validierung: Koordinaten prüfen]
    ↓
[LLM-Optimierung ODER Nearest-Neighbor]
    ↓
[Zeitberechnung: Fahrzeit + Service-Zeit]
    ↓
[Response: optimized_stops, estimated_total_time_minutes]
    ↓
[Frontend: splitTourIntoSubRoutes() wenn > 60 Min]
    ↓
[Sub-Routen erstellen (A, B, C, ...)]
    ↓
[updateToursWithSubRoutes()]
    ↓
[UI: Tour-Liste aktualisieren]
```

---

## Aktuelle Probleme & Lösungen

### Problem 1: 404-Fehler auf `/api/tour/optimize`

**Ursache:**
- Server wurde nicht neu gestartet nach Änderungen
- Router nicht korrekt registriert

**Lösung:**
- Server neu starten: `python start_server.py`
- Prüfen: `http://127.0.0.1:8111/docs` → `/api/tour/optimize` sollte sichtbar sein

---

### Problem 2: Index-Mapping-Fehler

**Ursache:**
- `optimize_tour_stops()` gibt neue Objekt-Referenzen zurück
- `valid_stops.index(opt_stop)` schlägt fehl (Objekte nicht identisch)

**Lösung (bereits implementiert):**
```python
# Koordinaten-Match mit Toleranz
if (abs(v_lat - opt_lat) < 0.0001 and 
    abs(v_lon - opt_lon) < 0.0001):
    optimized_indices.append(i)
```

---

### Problem 3: Alle Touren schlagen fehl

**Ursache:**
- LLM-Fehler → Nearest-Neighbor schlägt auch fehl
- Index-Mapping unvollständig

**Lösung:**
- Robusteres Mapping mit Fallback
- Fehlende Indizes automatisch hinzufügen
- Detailliertes Logging für Debugging

---

## Beispiel: W-07.00 mit 30 Adressen

### Input:
```
Tour: W-07.00 Uhr Tour
Stopps: 30 Adressen mit Koordinaten
```

### Schritt 1: LLM-Optimierung
```
LLM analysiert geografische Nähe:
- Stopp 5 (Fröbelstraße) → 12 (Hauptstraße) → 3 (Teststraße) → ...
- Ergebnis: Optimierte Reihenfolge [5, 12, 3, 7, 1, 15, ...]
```

### Schritt 2: Zeitberechnung
```
Fahrzeit: 45.5 Minuten
Service-Zeit: 60 Minuten (30 * 2)
Total: 105.5 Minuten → ÜBER 60!
```

### Schritt 3: Splitting
```
Sub-Route A: Stopps [5, 12, 3, 7, 1, 15, 8, 22, 11, 4]
  → 10 Stopps, 58 Minuten ✅

Sub-Route B: Stopps [16, 9, 23, 6, 18, 2, 14, 20, 13, 19]
  → 10 Stopps, 59 Minuten ✅

Sub-Route C: Stopps [17, 10, 24, 21, 25, 26, 27, 28, 29, 0]
  → 10 Stopps, 60 Minuten ✅
```

### Schritt 4: Ergebnis
```
Original: "W-07.00 Uhr Tour" (30 Stopps)
↓
3 Sub-Routen:
  - "W-07.00 Uhr Tour A" (10 Stopps, 58 Min)
  - "W-07.00 Uhr Tour B" (10 Stopps, 59 Min)
  - "W-07.00 Uhr Tour C" (10 Stopps, 60 Min)
```

---

## Nächste Schritte (Morgen)

1. **404-Fehler beheben:**
   - Server neu starten
   - Endpoint testen

2. **Index-Mapping robuster machen:**
   - Koordinaten-Match verbessern
   - Fallback für fehlende Matches

3. **LLM-Optimierung debuggen:**
   - Warum schlägt LLM fehl?
   - Response-Parsing prüfen

4. **Splitting-Logik verbessern:**
   - Intelligentere Aufteilung (nicht nur sequenziell)
   - Geografische Clustering vor Splitting

---

## Dateien-Übersicht

- **Frontend:** `frontend/index.html`
  - `generateSubRoutes()` - Hauptfunktion
  - `splitTourIntoSubRoutes()` - Splitting-Logik
  - `updateToursWithSubRoutes()` - UI-Update

- **Backend:** `routes/workflow_api.py`
  - `optimize_tour_with_ai()` - API-Endpoint
  - `optimize_tour_stops()` - Nearest-Neighbor Fallback
  - `_calculate_tour_time()` - Zeitberechnung

- **AI-Service:** `services/llm_optimizer.py`
  - `optimize_route()` - LLM-Optimierung
  - `_fallback_optimization()` - Nearest-Neighbor

---

## Fragen für morgen

1. Warum gibt LLM keine Antwort?
2. Warum schlägt Nearest-Neighbor manchmal fehl?
3. Wie können wir die Splitting-Logik intelligenter machen?
4. Sollte geografisches Clustering VOR Optimierung passieren?

