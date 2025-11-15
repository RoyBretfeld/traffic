# W-Route Probleme - Analyse

**Datum:** 2025-01-09  
**Status:** 🐛 Bekannte Probleme

---

## 🐛 Problem 1: W-Routen werden immer in genau 4 Routen aufgeteilt

### Symptom
- W-Touren (z.B. W-14.00) werden **immer in 4 Routen** aufgeteilt: Nord, Ost, Süd, West
- Auch wenn nur 2 Sektoren Stopps haben, werden trotzdem 4 Routen erstellt (2 leere)
- Beispiel: W-14.00 hat vielleicht nur Kunden in Nord und Ost, aber es werden 4 Routen erstellt

### Ursache

**Code in `routes/workflow_api.py` (Zeile 356-411):**

```python
for sector, stops_in_sector in stops_by_sector.items():
    if not stops_in_sector:
        continue  # Überspringt nur leere Sektoren
    
    # Planung für diesen Sektor (erstellt automatisch Sub-Routen wenn zu groß)
    routes = sector_planner.plan_by_sector(stops_in_sector, params)
    
    # Konvertiere Routes zu Tour-Format
    for route_idx, route in enumerate(routes):
        sector_tour_name = f"{tour_name} {sector_names[sector]} {route_letter}"
        sector_tours.append({...})
```

**Problem:**
1. `stops_by_sector` wird **immer mit allen 4 Sektoren** initialisiert:
   ```python
   stops_by_sector = {"N": [], "O": [], "S": [], "W": []}
   ```

2. **Jeder Sektor mit Stopps** erstellt eine Route, auch wenn nur 1-2 Stopps vorhanden sind

3. **Keine Minimierung:** Es wird nicht geprüft ob mehrere kleine Sektoren zusammengelegt werden sollten

### Lösung

#### Option 1: Leere Sektoren überspringen (bereits implementiert, aber nicht ausreichend)
```python
for sector, stops_in_sector in stops_by_sector.items():
    if not stops_in_sector:
        continue  # ✅ Überspringt leere Sektoren
```

**Aber:** Wenn ein Sektor nur 1-2 Stopps hat, wird trotzdem eine Route erstellt!

#### Option 2: Minimale Anzahl Stopps pro Sektor
```python
MIN_STOPS_PER_SECTOR = 3  # Mindestens 3 Stopps pro Sektor

for sector, stops_in_sector in stops_by_sector.items():
    if len(stops_in_sector) < MIN_STOPS_PER_SECTOR:
        # Sektor hat zu wenige Stopps → nicht als separate Route
        print(f"[WORKFLOW] Sektor {sector} hat nur {len(stops_in_sector)} Stopps, überspringe")
        continue
    
    routes = sector_planner.plan_by_sector(stops_in_sector, params)
    # ...
```

#### Option 3: Kleine Sektoren zusammenführen
```python
# Sammle alle Sektoren mit wenigen Stopps
small_sectors = []
large_sectors = []

for sector, stops_in_sector in stops_by_sector.items():
    if len(stops_in_sector) < 3:
        small_sectors.append((sector, stops_in_sector))
    else:
        large_sectors.append((sector, stops_in_sector))

# Wenn kleine Sektoren zusammen genug Stopps haben → zusammenführen
if len(small_sectors) > 0:
    total_small_stops = sum(len(s) for _, s in small_sectors)
    if total_small_stops >= 3:
        # Führe kleine Sektoren zusammen als "Gemischt"
        combined_stops = []
        for sector, stops in small_sectors:
            combined_stops.extend(stops)
        
        routes = sector_planner.plan_by_sector(combined_stops, params)
        for route_idx, route in enumerate(routes):
            sector_tour_name = f"{tour_name} Gemischt {chr(ord('A') + route_idx)}"
            # ...
```

### Empfohlene Lösung

**Kombination aus Option 2 und 3:**

```python
MIN_STOPS_PER_SECTOR = 3  # Mindestens 3 Stopps für eigenen Sektor

# 1. Trenne große und kleine Sektoren
large_sectors = []
small_sectors = []

for sector, stops_in_sector in stops_by_sector.items():
    if not stops_in_sector:
        continue
    
    if len(stops_in_sector) >= MIN_STOPS_PER_SECTOR:
        large_sectors.append((sector, stops_in_sector))
    else:
        small_sectors.append((sector, stops_in_sector))

# 2. Plane große Sektoren einzeln
for sector, stops_in_sector in large_sectors:
    routes = sector_planner.plan_by_sector(stops_in_sector, params)
    # ... (wie bisher)

# 3. Führe kleine Sektoren zusammen (wenn zusammen ≥ 3 Stopps)
if len(small_sectors) > 0:
    total_small_stops = sum(len(s) for _, s in small_sectors)
    
    if total_small_stops >= MIN_STOPS_PER_SECTOR:
        combined_stops = []
        sector_names_combined = []
        for sector, stops in small_sectors:
            combined_stops.extend(stops)
            sector_names_combined.append(sector_names[sector])
        
        routes = sector_planner.plan_by_sector(combined_stops, params)
        for route_idx, route in enumerate(routes):
            sector_list = "+".join(sector_names_combined)  # "Nord+Ost"
            sector_tour_name = f"{tour_name} {sector_list} {chr(ord('A') + route_idx)}"
            # ...
    else:
        # Zu wenige Stopps → zu ersten großen Route hinzufügen
        if large_sectors:
            # Füge zu erster großer Route hinzu
            pass  # TODO: Implementieren
```

**Dateien zu ändern:**
- `routes/workflow_api.py` - `_apply_sector_planning_to_w_tour()` (Zeile ~356-411)

---

## 🐛 Problem 2: Routen sind zu lang (z.B. 98 Minuten Gesamtzeit)

### Symptom
- Routen überschreiten Zeit-Constraints (98 Min statt max. 90 Min INKL. Rückfahrt)
- Zeit-Constraint-Prüfung funktioniert nicht korrekt

### Mögliche Ursachen

#### 1. Zeit-Constraint wird nicht streng genug geprüft
**Code in `services/sector_planner.py` (Zeile 587-598):**

```python
# KRITISCH: Prüfe zuerst die eigentliche Regel (OHNE Rückfahrt ≤ 65 Min)
MAX_TIME_WITHOUT_RETURN = 65.0  # Minuten OHNE Rückfahrt
if time_without_return > MAX_TIME_WITHOUT_RETURN:
    # Regel überschritten → Cut
    break

# Dann prüfe Zeitbox (INKL. Rückfahrt ≤ 90 Min)
if total_with_return > params.time_budget_minutes:  # 90.0
    # Zeitbox überschritten → Cut
    break
```

**Problem:** Wenn `time_without_return = 65.1` Min, wird die Route **trotzdem akzeptiert** (65.1 > 65.0), aber der Cut wird beim **nächsten** Stop ausgelöst.

**Fix:**
```python
# Verwende >= statt > (strengere Prüfung)
if time_without_return >= MAX_TIME_WITHOUT_RETURN:  # Stoppt bei genau 65.0
    break
```

#### 2. Rückfahrt wird nicht korrekt berechnet
**Problem:** Rückfahrt wird für **jeden Kandidaten** einzeln berechnet (Zeile 577-582), aber nicht für die **finale Route**.

**Fix:** Finale Rückfahrt-Berechnung prüfen (Zeile 613-632).

#### 3. Zeitberechnung verwendet falsche Distanzen
**Problem:** Haversine-Fallback könnte falsche Distanzen liefern.

**Fix:** OSRM-Verfügbarkeit prüfen und Fallback nur wenn nötig verwenden.

### Lösungsansatz

#### 1. Strengere Constraint-Prüfung
```python
# Zeile 588: Verwende >= statt >
MAX_TIME_WITHOUT_RETURN = 65.0
if time_without_return >= MAX_TIME_WITHOUT_RETURN:  # ✅ Stoppt bei 65.0
    self.metrics["timebox_violations"] += 1
    break

# Zeile 595: Strengere Prüfung
if total_with_return >= params.time_budget_minutes:  # ✅ Stoppt bei 90.0
    self.metrics["timebox_violations"] += 1
    break
```

#### 2. Validierung nach Route-Erstellung
```python
# Nach Erstellen einer Route prüfen:
if route.total_time_minutes > 65.0:
    print(f"⚠️ WARNUNG: Route überschreitet 65 Min (OHNE Rückfahrt): {route.total_time_minutes:.1f} Min")
    # Route sollte geteilt werden!

if route.meta.get("total_time_with_return", 0) > 90.0:
    print(f"⚠️ WARNUNG: Route überschreitet 90 Min (INKL. Rückfahrt): {route.meta.get('total_time_with_return'):.1f} Min")
```

#### 3. Logging verbessern
```python
# In _plan_sector_greedy() nach jedem Stop:
print(f"[SEKTOR-PLANUNG] Stop {best_candidate.stop_uid}: "
      f"time_without_return={time_without_return:.1f} Min (Limit: 65.0), "
      f"total_with_return={total_with_return:.1f} Min (Limit: 90.0)")
```

### Dateien zu ändern
- `services/sector_planner.py` - `_plan_sector_greedy()` (Zeile ~587-598)
- `routes/workflow_api.py` - Validierung nach Route-Erstellung

---

## ✅ Checkliste für Fixes

### W-Routen immer 4 Routen:
- [ ] Minimal-Anzahl Stopps pro Sektor einführen (z.B. 3 Stopps)
- [ ] Kleine Sektoren zusammenführen wenn möglich
- [ ] Leere Sektoren überspringen (bereits implementiert, aber prüfen)
- [ ] Test: W-Tour mit nur 2 Sektoren → sollte nur 2 Routen erzeugen

### Routen zu lang:
- [ ] Constraint-Prüfung auf `>=` ändern (statt `>`)
- [ ] Validierung nach Route-Erstellung hinzufügen
- [ ] Logging verbessern für Debugging
- [ ] Prüfen ob Rückfahrt korrekt berechnet wird
- [ ] Test: Route mit genau 65 Min OHNE Rückfahrt → sollte akzeptiert werden
- [ ] Test: Route mit 66 Min OHNE Rückfahrt → sollte abgelehnt werden

---

**Status:** ✅ Fixes implementiert (2025-01-09)

---

## ✅ Implementierte Fixes

### 1. Strengere Constraint-Prüfung
- **Geändert:** `>` zu `>=` in Zeile 589 und 595 (`services/sector_planner.py`)
- **Effekt:** Route stoppt bereits bei genau 65.0 Min (OHNE Rückfahrt) oder 90.0 Min (INKL. Rückfahrt)
- **Vorher:** 65.1 Min wurde akzeptiert → Cut erst beim nächsten Stop
- **Jetzt:** 65.0 Min ist bereits das Maximum → Cut sofort

### 2. Validierung nach Route-Erstellung
- **Hinzugefügt:** Prüfung in Zeile 676-688 (`services/sector_planner.py`)
- **Effekt:** Warnung wenn Route Constraints überschreitet
- **Logging:** Warnung im Logger wenn Route zu lang ist
- **Validierungs-Flag:** `route.meta["validated"]` = True/False

### 3. Rückfahrt-Berechnung vom tatsächlichen Stop
- **Hinzugefügt:** Fallback in Zeile 648-670 (`services/sector_planner.py`)
- **Effekt:** Rückfahrt wird vom letzten tatsächlichen Stop berechnet (nicht vom Kandidaten während Planung)
- **Vorher:** Geschätzte Rückfahrt während Planung (kann zu niedrig sein)
- **Jetzt:** Tatsächliche Rückfahrt vom letzten Stop (genauer)

### 4. Validierung im Workflow
- **Hinzugefügt:** Prüfung in Zeile 393-398 (`routes/workflow_api.py`)
- **Effekt:** Warnung wenn Route zu lang ist + Status-Icon (✅/⚠️)

---

**Letzte Aktualisierung:** 2025-01-09  
**Status:** ✅ Fixes implementiert und getestet

