# Code-Audit: Tour-Splitting-Logik

## Übersicht

Dieses Dokument listet alle Dateien auf, die die Tour-Splitting-Logik betreffen, und beschreibt ihre Funktionen und Interaktionen.

---

## Kritische Regel

**MAX_TIME_WITHOUT_RETURN = 65 Minuten** (OHNE Rückfahrt zum Depot!)

- Fahrzeit + Servicezeit ≤ 65 Minuten
- Rückfahrt zählt NICHT in diese 65 Minuten
- Gesamtzeit MIT Rückfahrt kann > 65 Min sein (wird separat angezeigt)

---

## Dateien-Übersicht

### 1. `routes/workflow_api.py` ⚠️ **HAUPT-LOGIK**

**Zuständigkeit:** Haupt-Splitting-Logik für alle Touren (außer W-Touren mit Sektor-Planung)

**Wichtige Funktionen:**

#### `_split_large_tour_in_workflow(tour_name, stops, max_time_without_return)`
- **Zeile:** 283-442
- **Zweck:** Splittet große Touren in mehrere Routen (A, B, C, D, E, ...)
- **Limit:** `max_time_without_return = 65` Minuten
- **Problem:** 
  - Wird für W-Touren NICHT verwendet, wenn Sektor-Planung aktiv ist
  - Wird nur für Touren mit > 7 Kunden verwendet (Zeile 1177)
- **Logik:**
  - Iteriert durch Stopps
  - Prüft ob `estimated_time <= 65 Min` für aktuelle Route
  - Wenn zu lang → neue Route starten
  - Letzte Route wird am Ende validiert
  - Finale Validierung aller Routen

#### `_estimate_tour_time_without_return(stops, use_osrm=True)`
- **Zeile:** 202-280
- **Zweck:** Berechnet Zeit OHNE Rückfahrt
- **Verwendet:** OSRM wenn verfügbar, sonst Haversine
- **Berechnet:** Depot → alle Stopps (OHNE Rückfahrt!)

#### `_calculate_tour_time(stops)`
- **Zeile:** 2043-2095
- **Zweck:** Berechnet Gesamtzeit für Tour
- **Verwendet:** OSRM wenn verfügbar, sonst Haversine

#### Workflow-Integration:
- **Zeile 1177-1191:** Prüft ob Tour > 7 Kunden hat → ruft `_split_large_tour_in_workflow` auf
- **Zeile 1191-1205:** W-Touren werden an Sektor-Planung weitergegeben (ÜBERSCHREIBT normales Splitting!)

---

### 2. `services/sector_planner.py` ⚠️ **W-TOUREN LOGIK**

**Zuständigkeit:** Automatische Sektor-Planung für W-Touren (N/O/S/W)

**Wichtige Funktionen:**

#### `SectorPlanner.plan_by_sector(stops_with_sectors, params)`
- **Zweck:** Erstellt Sub-Routen pro Sektor mit Zeitbox (07:00 → 09:00)
- **Zeitbudget:** `time_budget_minutes = 90` (Standard)
- **Problem:** 
  - Verwendet 90 Minuten Zeitbudget, nicht 65 Minuten!
  - Erstellt Routen pro Sektor, die dann möglicherweise zu lang sind
  - Validiert nicht gegen 65-Minuten-Limit

#### `SectorPlanner._get_osrm_table_for_candidates()`
- **Zweck:** Verwendet OSRM Table API für Distanzberechnungen
- **Fallback:** Haversine × 1.3

#### Integration in Workflow:
- **workflow_api.py Zeile 1191-1205:** W-Touren werden an `_apply_sector_planning_to_w_tour()` weitergegeben
- **workflow_api.py Zeile 380-465:** `_apply_sector_planning_to_w_tour()` ruft `SectorPlanner` auf

**⚠️ KRITISCH:** Sektor-Planung verwendet 90 Minuten Zeitbudget, nicht 65 Minuten!

---

### 3. `services/pirna_clusterer.py`

**Zuständigkeit:** Clustering für PIR-Touren

**Wichtige Funktionen:**

#### `PirnaClusterer.cluster_stops(stops, params)`
- **Zeitlimit:** `max_time_per_cluster_minutes = 120` (Zeile 612 in workflow_api.py)
- **Problem:** Verwendet 120 Minuten, nicht 65 Minuten!

#### Integration in Workflow:
- **workflow_api.py Zeile 1149-1166:** PIR-Touren werden an `_apply_pirna_clustering_to_tour()` weitergegeben

**⚠️ KRITISCH:** PIRNA-Clustering verwendet 120 Minuten, nicht 65 Minuten!

---

### 4. `routes/engine_api.py`

**Zuständigkeit:** Engine API für Tour-Splitting (separater Endpoint)

**Wichtige Funktionen:**

#### `split_tour(request: SplitRequest)`
- **Zeile:** 434-518
- **Zweck:** POST `/engine/tours/split` Endpoint
- **Standard-Limit:** `max_duration_minutes = 60` (vom Request)
- **Verwendet:** `_split_tour_with_osrm()` oder `_split_tour_with_heuristic()`

#### `_split_tour_with_osrm(stops, distance_matrix, max_duration_minutes, max_stops_per_route)`
- **Zeile:** 521-565
- **Zweck:** Splitting mit OSRM-Distanzen
- **Logik:** Prüft ob `current_duration + travel_time + service_time <= max_duration_minutes`

#### `_split_tour_with_heuristic(stops, max_duration_minutes, max_stops_per_route)`
- **Zeile:** 568-617
- **Zweck:** Splitting mit Haversine × 1.3
- **Logik:** Gleiche Prüfung wie OSRM-Version

---

### 5. `frontend/index.html`

**Zuständigkeit:** Frontend Splitting-Logik (Fallback)

**Wichtige Funktionen:**

#### `splitTourIntoSubRoutes(tour, optimizationResult)`
- **Zeile:** 3131-3192
- **Zweck:** Frontend-Fallback-Splitting (nur wenn Backend versagt)
- **Limit:** `maxTimePerRoute = 65` Minuten
- **Hinweis:** Sollte eigentlich nicht benötigt werden, wenn Backend korrekt splittet

---

### 6. `services/osrm_client.py`

**Zuständigkeit:** OSRM Client für Distanz- und Zeitberechnungen

**Wichtige Funktionen:**

#### `OSRMClient.get_route(coords)`
- **Zweck:** Berechnet Route zwischen Koordinaten
- **Gibt zurück:** `{"distance_km": float, "duration_min": float, "source": "osrm"|"haversine"}`

#### `OSRMClient.get_distance_matrix(coords, sources, destinations)`
- **Zweck:** Berechnet Distanz-Matrix (alle zu allen)
- **Gibt zurück:** `Dict[(i, j), {"km": float, "minutes": float}]`

---

## Logik-Flows

### Flow 1: Normale Touren (> 7 Kunden, keine W-Tour)

```
workflow_upload()
  → Tour hat > 7 Kunden?
  → _estimate_tour_time_without_return() prüft Gesamtzeit
  → Wenn > 65 Min:
     → _split_large_tour_in_workflow(tour_name, stops, 65)
        → Iteriert durch Stopps
        → Prüft estimated_time <= 65 Min
        → Erstellt Routen A, B, C, D, ...
        → Validiert alle Routen am Ende
```

**✅ Problem:** Funktioniert nur für Touren mit > 7 Kunden!

---

### Flow 2: W-Touren (Sektor-Planung)

```
workflow_upload()
  → Tour ist W-Tour? (Regex: W-\d+\.\d+)
  → _apply_sector_planning_to_w_tour()
     → SectorPlanner.plan_by_sector()
        → Zeitbudget: 90 Minuten (NICHT 65!)
        → Erstellt Sub-Routen pro Sektor
        → Keine Validierung gegen 65-Minuten-Limit!
```

**⚠️ KRITISCH:** W-Touren verwenden 90 Minuten Zeitbudget, nicht 65 Minuten!

**⚠️ KRITISCH:** W-Touren werden NICHT durch `_split_large_tour_in_workflow` verarbeitet!

---

### Flow 3: PIR-Touren (Clustering)

```
workflow_upload()
  → Tour ist PIR-Tour? (Regex: PIR-\d+\.\d+)
  → _apply_pirna_clustering_to_tour()
     → PirnaClusterer.cluster_stops()
        → Zeitlimit: 120 Minuten (NICHT 65!)
        → Erstellt Cluster-Routen
        → Keine Validierung gegen 65-Minuten-Limit!
```

**⚠️ KRITISCH:** PIR-Touren verwenden 120 Minuten Zeitlimit, nicht 65 Minuten!

---

## Identifizierte Probleme

### Problem 1: W-Touren überschreiten 65-Minuten-Limit
- **Ursache:** `SectorPlanner` verwendet 90 Minuten Zeitbudget
- **Datei:** `services/sector_planner.py`
- **Zeile:** `time_budget_minutes: int = 90` (Standard)
- **Beispiel:** "W-14.00 Uhr Tour A" mit 119.5 Min Fahrzeit

### Problem 2: PIR-Touren überschreiten 65-Minuten-Limit
- **Ursache:** `PirnaClusterer` verwendet 120 Minuten Zeitlimit
- **Datei:** `routes/workflow_api.py` Zeile 612
- **Zeile:** `max_time_per_cluster_minutes=120`

### Problem 3: Normale Touren werden nur bei > 7 Kunden gesplittet
- **Ursache:** Splitting-Logik wird nur für Touren mit > 7 Kunden aufgerufen
- **Datei:** `routes/workflow_api.py` Zeile 1177
- **Problem:** Tour mit 6 Kunden kann > 65 Min haben, wird aber nicht gesplittet!

### Problem 4: Keine finale Validierung nach Sektor-Planung
- **Ursache:** `SectorPlanner` validiert nicht gegen 65-Minuten-Limit
- **Datei:** `services/sector_planner.py`
- **Problem:** Routen können > 65 Min sein, werden aber nicht weiter aufgeteilt

### Problem 5: Keine finale Validierung nach PIRNA-Clustering
- **Ursache:** `PirnaClusterer` validiert nicht gegen 65-Minuten-Limit
- **Datei:** `services/pirna_clusterer.py`
- **Problem:** Cluster können > 65 Min sein, werden aber nicht weiter aufgeteilt

---

## Empfohlene Fixes

### Fix 1: Sektor-Planung auf 65 Minuten begrenzen
- **Datei:** `services/sector_planner.py`
- **Änderung:** `time_budget_minutes: int = 65` (statt 90)
- **Zusätzlich:** Finale Validierung aller Routen gegen 65-Minuten-Limit

### Fix 2: PIRNA-Clustering auf 65 Minuten begrenzen
- **Datei:** `routes/workflow_api.py` Zeile 612
- **Änderung:** `max_time_per_cluster_minutes=65` (statt 120)
- **Zusätzlich:** Finale Validierung aller Cluster gegen 65-Minuten-Limit

### Fix 3: Splitting für ALLE Touren, nicht nur > 7 Kunden
- **Datei:** `routes/workflow_api.py` Zeile 1177
- **Änderung:** Prüfe Zeit statt Anzahl Kunden
- **Logik:** Wenn `estimated_time > 65 Min` → split, unabhängig von Kundenanzahl

### Fix 4: Finale Validierung nach Sektor-Planung
- **Datei:** `routes/workflow_api.py` Zeile 1200 (nach `_apply_sector_planning_to_w_tour`)
- **Änderung:** Validiere alle resultierenden Routen gegen 65-Minuten-Limit
- **Wenn zu lang:** Rufe `_split_large_tour_in_workflow` auf

### Fix 5: Finale Validierung nach PIRNA-Clustering
- **Datei:** `routes/workflow_api.py` Zeile 1161 (nach `_apply_pirna_clustering_to_tour`)
- **Änderung:** Validiere alle resultierenden Routen gegen 65-Minuten-Limit
- **Wenn zu lang:** Rufe `_split_large_tour_in_workflow` auf

---

## Zusammenfassung

| Datei | Funktion | Zeitlimit | Problem |
|-------|----------|-----------|---------|
| `routes/workflow_api.py` | `_split_large_tour_in_workflow` | 65 Min | ✅ Korrekt, aber nur für > 7 Kunden |
| `services/sector_planner.py` | `plan_by_sector` | 90 Min | ❌ Zu hoch! |
| `services/pirna_clusterer.py` | `cluster_stops` | 120 Min | ❌ Zu hoch! |
| `routes/engine_api.py` | `split_tour` | 60 Min (Request) | ✅ OK |
| `frontend/index.html` | `splitTourIntoSubRoutes` | 65 Min | ✅ OK (Fallback) |

**Hauptproblem:** W-Touren und PIR-Touren verwenden höhere Zeitlimits und werden nicht gegen 65 Minuten validiert!

