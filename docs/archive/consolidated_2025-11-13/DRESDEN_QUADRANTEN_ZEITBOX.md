# Dresden-Quadranten & Zeitbox – Implementierung

## Übersicht

**Ziel:** Touren in Dresden vorstrukturieren durch Sektorisierung (N/O/S/W) und Zeitbox-Erzwingung (07:00 Start, 09:00 Rückkehr).

**Prinzip:** OSRM-First (exakte Distanzen/Zeiten), dann deterministisches Bauen der Route je Sektor (LLM optional, strikt validiert). Frontend rechnet nichts.

**⚠️ WICHTIG:** Sektor-Planung gilt **NUR für W-Touren**:
- **W-Touren**: Touren mit Tour-ID Pattern `W-XX.XX` (z.B. "W-07.00 Uhr Tour")
  - **Grund**: W-Touren gehen über das ganze Dresden-Kreuz und müssen in Sektoren aufgeteilt werden (N/O/S/W)

**CB (Cottbus), BZ (Bautzen), PIR (Pirna)** gehen in eine Richtung raus aus Dresden und brauchen **KEINE** Sektorisierung.

**Alle anderen Touren** (z.B. T-Touren, etc.) verwenden **nicht** die Sektor-Planung.

---

## Implementierte Komponenten

### 1. `services/sector_planner.py`

**Hauptklasse:** `SectorPlanner`

- **`should_use_sector_planning(tour_id)`**: Prüft ob Tour Sektor-Planung verwenden soll (CB/BZ/PIR)
- **`calculate_bearing()`**: Berechnet Bearing/Azimut (0°=Norden, 90°=Osten, etc.)
- **`assign_sector()`**: Ordnet Bearing einem Sektor zu (N/O/S/W, deterministisch)
- **`sectorize_stops()`**: Weist allen Stopps Sektoren zu
- **`plan_by_sector()`**: Plant Routen pro Sektor mit Greedy + Zeitbox
- **`_plan_sector_greedy()`**: Greedy-Algorithmus für einen Sektor

**Telemetrie:**
- `osrm_calls`: Anzahl OSRM-Table-API-Calls
- `osrm_unavailable`: Anzahl OSRM-Fehler
- `fallback_haversine`: Anzahl Fallback-Distanzen
- `timebox_violations`: Anzahl Zeitbox-Überschreitungen
- `routes_by_sector`: Anzahl Routen pro Sektor

---

### 2. `routes/engine_api.py` – Neue Endpoints

#### 2.1 `POST /engine/tours/sectorize`

**Request:**
```json
{
  "tour_uid": "sha256:...",
  "depot_lat": 51.0111988,
  "depot_lon": 13.7016485,
  "sectors": 4
}
```

**Response:**
```json
{
  "tour_uid": "sha256:...",
  "stops_with_sectors": [
    {
      "stop_uid": "sha256:...",
      "lat": 51.0350,
      "lon": 13.7100,
      "sector": "N",
      "bearing_deg": 15.3,
      "distance_from_depot_km": 2.65
    },
    ...
  ]
}
```

**Zweck:** Weist allen Stopps einer Tour Sektoren zu (N/O/S/W).

**⚠️ Eingeschränkt auf:** Nur W-Touren (z.B. "W-07.00").  
Bei anderen Touren: HTTP 400 Fehler mit entsprechendem Hinweis.

---

#### 2.2 `POST /engine/tours/plan_by_sector`

**Request:**
```json
{
  "tour_uid": "sha256:...",
  "depot_uid": "depot_uid",
  "depot_lat": 51.0111988,
  "depot_lon": 13.7016485,
  "start_time": "07:00",
  "hard_deadline": "09:00",
  "time_budget_minutes": 90,
  "reload_buffer_minutes": 30,
  "service_time_default": 2.0,
  "service_time_per_stop": {"uid123": 4},
  "sectors": 4,
  "include_return_to_depot": true,
  "round": 2
}
```

**Response:**
```json
{
  "tour_uid": "sha256:...",
  "params": {
    "time_budget_minutes": 90,
    "include_return_to_depot": true,
    "sectors": 4,
    "start_time": "07:00",
    "hard_deadline": "09:00"
  },
  "sub_routes": [
    {
      "name": "West A",
      "sector": "W",
      "route_uids": ["depot_uid", "uid7", "uid9", "uid4", "depot_uid"],
      "segments": [
        {
          "from_uid": "depot_uid",
          "to_uid": "uid7",
          "km": 3.40,
          "minutes": 8.1
        },
        ...
      ],
      "service_time_minutes": 10.0,
      "driving_time_minutes": 62.3,
      "total_time_minutes": 72.3,
      "meta": {
        "source": "osrm",
        "llm_choices": 0
      }
    },
    ...
  ],
  "totals": {
    "km": 124.6,
    "minutes": 348.1,
    "routes_count": 4,
    "metrics": {
      "osrm_calls": 15,
      "osrm_unavailable": 0,
      "fallback_haversine": 3,
      "timebox_violations": 0,
      "routes_by_sector": {"N": 1, "O": 1, "S": 1, "W": 1}
    }
  }
}
```

**Zweck:** Plant Routen pro Sektor mit Greedy-Algorithmus und Zeitbox-Validierung.

**⚠️ Eingeschränkt auf:** Nur W-Touren (z.B. "W-07.00").  
Bei anderen Touren: HTTP 400 Fehler mit entsprechendem Hinweis.

---

### 3. OSRM Table API Erweiterung

**`services/osrm_client.py` – `get_distance_matrix()`:**

- **Neu:** Unterstützung für `sources` und `destinations` Parameter
- **Format:** `GET /table/v1/driving/{coords}?annotations=duration&sources=0&destinations=1;2;3;...`
- **Rückgabe:** `{(i, j): {"km": ..., "minutes": ...}}`

**Verwendung:**
```python
# Nur vom aktuellen Punkt (Index 0) zu Kandidaten (Indizes 1, 2, 3, ...)
distance_matrix = osrm_client.get_distance_matrix(
    coords,
    sources=[0],
    destinations=[1, 2, 3, ...]
)
```

---

## Sektorlogik (4er-Kreuz)

**Bearing-Berechnung:**
```
θ = atan2( sin(Δλ)*cos(φ2), cos(φ1)*sin(φ2) − sin(φ1)*cos(φ2)*cos(Δλ) )
θ_deg = (θ * 180/π + 360) mod 360
```

**Sektorzuordnung:**
- **N (Norden)**: 315°-360° ∪ 0°-45°
- **O (Osten)**: 45°-135°
- **S (Süden)**: 135°-225°
- **W (Westen)**: 225°-315°

**Kantenfall:** Liegt θ exakt auf Achse (z.B. 45°), ordne deterministisch zum links folgenden Sektor zu (O→N).

---

## Planungslogik (Greedy + Zeitbox)

**Pseudocode:**
```python
def plan_sector(stops, depot, time_budget, include_return=True):
    routes = []
    remaining = sort_seed(stops)  # dist->θ->uid
    
    while remaining:
        cur = depot
        route, t_drive, t_service = [depot.uid], 0.0, 0.0
        
        while remaining:
            cands = osrm_table(cur, remaining)  # minutes, km
            next_uid = choose_llm_or_first(cands)  # validate strictly
            seg = cands[next_uid]
            
            if include_return:
                back = osrm_duration(next_uid, depot.uid)
            else:
                back = 0.0
            
            if (t_drive + seg.minutes + t_service + service_time(next_uid) + back) > time_budget:
                break  # cut
            
            # accept
            route.append(next_uid)
            t_drive += seg.minutes
            t_service += service_time(next_uid)
            cur = next_uid
            remaining.remove(next_uid)
        
        if include_return:
            route.append(depot.uid)
            t_drive += osrm_duration(cur, depot.uid)
        
        routes.append(materialize(route, t_drive, t_service))
    
    return routes
```

**Schritte:**
1. **Bucket**: Weise alle Stopps per Bearing ihrem Sektor zu
2. **Sortier-Seed**: Primär Entfernung vom Depot, sekundär Winkel, tertiär `stop_uid`
3. **Route bauen (Greedy, OSRM-next)**:
   - Start: Depot
   - Wähle per OSRM-Table den schnellsten Kandidaten im Sektor
   - Addiere Segmentdauer + Service-Zeit
   - Wiederhole vom neuen aktuellen Punkt
   - **Cut**: Wenn `total_minutes + return_to_depot_minutes` > `time_budget_minutes`, starte neue Route
4. **Rückfahrt**: Falls `include_return_to_depot` true, hänge Depot an

---

## Zeitbox-Regel (07:00 → 09:00)

**Harte Zeitbox:**
- `time_budget_minutes` (Default **90**) + optionaler `reload_buffer_minutes` (**30**) = **120** Gesamtfenster
- Erfüllt die 09:00-Regel bei Start 07:00

**Aktion bei Überschreitung:**
- Sofortiger **Cut** und neue Subroute im gleichen Sektor (z.B. "West A", "West B")

**Alarm/Metric:**
- `timebox_violation_total` sollte **0** bleiben

---

## Edge-Cases & Toleranzen

### 1. Stopps direkt auf Achsen
- **Lösung**: Deterministische Sektorzuteilung (links folgender Sektor)

### 2. Sehr ungleich verteilte Stopps
- **Optional**: Radius-Ring (Innen/Außen) pro Sektor (z.B. 0–5 km, 5–10 km) und erst inneren Ring bedienen

### 3. OSRM down
- **Lösung**: Backend rechnet Fallback (Haversine × 1.3) und kennzeichnet Segmente mit `source="fallback_haversine"`
- Frontend rechnet nie

### 4. Fehlende Koordinaten
- **Lösung**: Tour auf `pending_geo`, keine Planung bis GeoQueue erledigt ist

---

## LLM-Integration (optional, strikt)

**Betriebsordnung §6:**
- **Input ans LLM**: Sortierte Kandidatenliste ab aktuellem Punkt, je Kandidat `{stop_uid, km, minutes}`
- **Schema (strict)**: `{ "choose": "<stop_uid>" }`
- **Validierung**: `choose ∈ candidates`; sonst Fallback = erster Kandidat (kürzeste Dauer)
- **Telemetrie**: `llm_calls_total`, `llm_invalid_schema_total`, `llm_decision_usage_total{method=llm|heuristic}`

**Status:** TODO (aktuell: Greedy wählt immer kürzesten)

---

## Test-Skript

**Datei:** `scripts/test_sector_planning.py`

**Verwendung:**
```bash
python scripts/test_sector_planning.py
```

**Testet:**
1. `/engine/tours/sectorize` – Sektorisierung (N/O/S/W)
2. `/engine/tours/plan_by_sector` – Planung mit Zeitbox (07:00 → 09:00)

---

## Definition of Done (DoD)

✅ Alle Stopps bekommen deterministisch **N/O/S/W**  
✅ Jede Subroute hält **time_budget_minutes** (inkl. Rückfahrt & Servicezeiten) ein  
✅ **OSRM-first** ist aktiv; Fallback wird gezählt & markiert  
✅ Frontend rechnet **nichts**, zeigt nur Subrouten & Zeiten  
✅ Telemetrie: `routes_by_sector`, `timebox_violation_total`, `osrm_unavailable`, `llm_decision_usage_total`

---

## Nächste Schritte

1. **LLM-Integration**: Optional für Entscheidung zwischen mehreren guten Kandidaten
2. **Frontend-Integration**: UI für Dresden-Quadranten & Zeitbox-Planung
3. **8er-Sektoren**: Implementierung für N, NO, O, SO, S, SW, W, NW
4. **Radius-Ring**: Optional für ungleich verteilte Stopps

---

## Beispiel-Workflow

1. **Tour ingestieren**: `POST /engine/tours/ingest`
   - Beispiel: Tour-ID `"W-07.00 Uhr Tour"` (nur W-Touren!)
2. **Prüfung**: System prüft automatisch ob `should_use_sector_planning(tour_id)` → True
3. **Sektorisierung**: `POST /engine/tours/sectorize` → Stopps mit Sektoren
4. **Planung**: `POST /engine/tours/plan_by_sector` → Routen pro Sektor (07:00 → 09:00)
5. **Ergebnis**: Mehrere Routen je Sektor (z.B. "West A", "West B"), alle halten Zeitbox ein

**Beispiel für nicht-berechtigte Tour:**
- Tour-ID: `"CB T2/11"` → `should_use_sector_planning()` → False
- Endpoint gibt HTTP 400: "Sektor-Planung gilt nur für W-Touren (z.B. 'W-07.00'), die über das ganze Dresden-Kreuz verteilt sind."

---

## Tour-Filter-Logik

**Funktion:** `should_use_sector_planning(tour_id: str) -> bool`

**Regeln:**
1. Prüft ob Tour-ID Pattern **`W-XX.XX`** entspricht → W-Tour ✅ (über ganz Dresden-Kreuz)

**CB (Cottbus), BZ (Bautzen), PIR (Pirna)** werden **NICHT** akzeptiert, weil sie in eine Richtung gehen.

**Beispiele:**
- `"W-07.00 Uhr Tour"` → ✅ True (W-Tour, über ganz Dresden-Kreuz)
- `"W-12.30 BAR"` → ✅ True (W-Tour)
- `"CB T2/11"` → ❌ False (geht in eine Richtung, keine Sektorisierung nötig)
- `"BZ Anlief. 11.30 Uhr"` → ❌ False (geht in eine Richtung)
- `"PIR Tour"` → ❌ False (geht in eine Richtung)
- `"T17"` → ❌ False
- `"Anlief. T5, 9.30 Uhr"` → ❌ False

