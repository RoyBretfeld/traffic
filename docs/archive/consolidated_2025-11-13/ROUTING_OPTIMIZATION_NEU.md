# Routing-Optimierung: Nie wieder Mockup/Placebo

**Datum:** 2025-01-10  
**Status:** Implementierungsplan  
**Ziel:** Endpoint liefert **immer** echte, sinnvolle Optimierung – auch bei Ausfällen

---

## Ziel

**Nie wieder "Mockup" oder Identitäts-Reihenfolge.** Der Endpoint liefert **immer** eine echte, sinnvolle Optimierung – auch bei Ausfällen – und gibt Qualitätskennzahlen mit zurück.

---

## Entscheidungsbaum (deterministisch, ohne Placebo)

1. **Primär:** OSRM **Table API** (Entfernungs-/Dauer-Matrix) → **OR-Tools** Solver.

2. **Sekundär (Routing-Backend down):** **Valhalla** oder **GraphHopper** Table als „Hot-Standby“ (gleiche Schnittstelle). Circuit Breaker wählt den gesunden Upstream.

3. **Tertiär (beide down):** **Lokale Matrix** via Haversine + Geschwindigkeitsprofil + Ampel-/Abbiege-Penalty (parametrierbar). → Das ist kein Mock, sondern deterministische Approximation.

> **Nie**: Identität/Platzhalter. Es wird zumindest Greedy+2‑Opt optimiert – mit Zeitlimit.

---

## Algorithmenwahl

* **n ≤ 12:** OR‑Tools mit `GUIDED_LOCAL_SEARCH` + 3‑Opt (Timelimit 2–5 s).

* **13 ≤ n ≤ 80:** Nearest Insertion → 2‑Opt → (optional) 3‑Opt Feinschliff (Timelimit 2 s).

* **n > 80:** Clustering (K‑Means nach Geodistanz) → je Cluster obige Pipeline → Cluster-Reihenfolge via Metaheuristik (Simulated Annealing, 1 s Budget).

Alle Varianten liefern:

* `total_duration_estimate` (Minuten)
* `gain_vs_nearest_neighbor` (%)
* `solver_used`, `backend_used`

**Qualitätsboden:** Wenn `gain_vs_nearest_neighbor < 3%`, liefern wir die NN‑Lösung (besser reproduzierbar) und markieren `quality: "floor"`.

---

## API‑Kontrakt (Response)

```json
{
  "success": true,
  "tour_id": "...",
  "optimized_stops": [ {"lat": ..., "lon": ..., "id":"..."}, ... ],
  "metrics": {
    "total_duration_minutes": 137.4,
    "gain_vs_nearest_neighbor_pct": 8.2,
    "backend_used": "osrm|valhalla|graphhopper|local_haversine",
    "solver_used": "or_tools|nn_2opt|clustered",
    "time_ms": 920
  },
  "warnings": ["degraded_to_local_matrix"]
}
```

**Nie 500.** Bei fatalen Fehlern: `success:false` + erklärende `error` (HTTP 200/422).

---

## Code‑Skelett (Python)

```python
from ortools.constraint_solver import pywrapcp, routing_enums_pb2

def compute_matrix(points, backend):
    if backend == 'osrm':
        return osrm_table(points)  # echte Fahrzeitsekunden
    if backend == 'valhalla':
        return valhalla_table(points)
    if backend == 'graphhopper':
        return graphhopper_table(points)
    return local_haversine_matrix(points, profile='urban')  # deterministische Approximation

def solve_or_tools(matrix, time_limit_ms=3000):
    n = len(matrix)
    manager = pywrapcp.RoutingIndexManager(n, 1, 0)
    routing = pywrapcp.RoutingModel(manager)
    def transit(i, j):
        return int(matrix[manager.IndexToNode(i)][manager.IndexToNode(j)])
    transit_cb = routing.RegisterTransitCallback(transit)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_cb)
    search = pywrapcp.DefaultRoutingSearchParameters()
    search.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search.time_limit.FromMilliseconds(time_limit_ms)
    sol = routing.SolveWithParameters(search)
    order = []
    i = routing.Start(0)
    while not routing.IsEnd(i):
        order.append(manager.IndexToNode(i))
        i = sol.Value(routing.NextVar(i))
    return order

def nn_two_opt(matrix, time_ms=1200):
    order = nearest_neighbor(matrix)
    order = two_opt(matrix, order, time_ms)
    return order
```

---

## Endpoint‑Flow (vereinheitlicht)

```python
backend = pick_backend_with_circuit_breaker()  # osrm→valhalla→graphhopper→local
M = compute_matrix(stops, backend)
order_nn = nearest_neighbor(M)
order = (
    solve_or_tools(M, 3000) if len(stops) <= 12
    else nn_two_opt(M, 1200)
)
metrics = make_metrics(M, order, order_nn, backend)
return build_response(stops, order, metrics)
```

---

## Circuit Breaker & Health

* `/health/routing`: prüft alle Backends parallel (500ms Connect‑Timeout), gibt Latenz & Status zurück.
* Fuses: Wenn 3 Fehler in 60 s → Backend 2 min sperren.

---

## Tests (akzeptanzkritisch)

* **Never‑500:** 100 Requests mit absichtlich blockiertem Primär‑Backend → alle `success:true`.
* **Qualität:** Gegen NN mindestens +3% Median‑Verbesserung bei 20 zufälligen Tours (n=8–40).
* **Zeitlimit:** P95 < 2 s bei n ≤ 40.

---

## Rollout‑Plan

1. Feature‑Flags: `routing_backend_chain`, `or_tools_enabled`.
2. Schattenbetrieb: nur Metriken sammeln, Ergebnis noch nicht ausliefern.
3. Staged Rollout 10% → 50% → 100%.

---

## Offene Parameter

* Geschwindigkeitsprofil lokal (urban/suburban/rural)
* Penalty‑Gewichte (Linksabbiegen, Ampeln, U‑Turn)
* Qualitätsboden `%`

---

## Implementierungs-Schritte

1. **OR-Tools installieren** (`pip install ortools`)
2. **Routing-Backend-Client erweitern** (Valhalla, GraphHopper)
3. **Matrix-Berechnung** (OSRM Table, Valhalla Table, GraphHopper Table, lokale Haversine)
4. **OR-Tools Solver** implementieren
5. **Nearest Neighbor + 2-Opt** implementieren
6. **Clustering für n > 80** implementieren
7. **Circuit Breaker** für Backend-Auswahl
8. **Health-Checks** für alle Backends
9. **Qualitätskennzahlen** berechnen
10. **Endpoint umbauen** (nie 500, immer success:false mit error)

---

**Ende des Plans**

