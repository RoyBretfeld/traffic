# Parsing-Fix: BAR-Touren Gruppierung

## Problem

Die 24 generierten Touren wurden nicht in der Tourübersicht angezeigt, weil:
1. BAR-Touren nicht korrekt mit ihren Haupttouren gruppiert wurden
2. Die Parsing-Logik aus `docs/Neu/parse_w7.py` wurde nicht vollständig integriert
3. BAR-Kunden wurden falsch zugeordnet (unter falschem Header gesammelt)

## Lösung

Die bewährte Logik aus `docs/Neu/parse_w7.py` wurde direkt in `backend/parsers/tour_plan_parser.py` integriert.

### Kern-Änderungen

1. **Direkte BAR-Gruppierung** (wie in `parse_w7.py`):
   - BAR-Kunden werden in `pending_bar[base_name]` gesammelt
   - Wenn eine Haupttour kommt, werden BAR-Kunden **SOFORT** eingefügt (am Anfang)
   - Gruppierung basiert auf `base_name` (ohne "BAR"/"Tour"/"Uhr")

2. **Vereinfachte Architektur**:
   - Keine separate `group_and_consolidate_tours()` Funktion mehr nötig
   - Alles in einer Funktion: `_extract_tours()`
   - Direkteres Mapping: `header -> List[TourStop]`

3. **Deterministische Reihenfolge**:
   - `header_order` Liste garantiert stabile Ausgabe-Reihenfolge
   - BAR-Kunden erscheinen am Anfang ihrer Haupttour

## Code-Änderungen

### Vorher (Problem)
```python
# BAR-Kunden wurden unter last_normal_header gesammelt
if last_normal_header:
     raw_tour_data.append((last_normal_header, customer))
```

### Nachher (Lösung)
```python
# BAR-Kunden werden in pending_bar[base] gesammelt
if bar_mode:
    pending_bar.setdefault(current_base, []).append(customer)
else:
    # Normale Kunden direkt zur Tour
    tour_name = full_name_map.get(current_base)
    tours[tour_name].append(customer)
```

## Ergebnis

✅ **BAR-Touren werden korrekt gruppiert**:
- "W-07.00 Uhr BAR" + "W-07.00 Uhr Tour" → zusammen als "W-07.00 Uhr Tour"
- BAR-Kunden erscheinen am Anfang der Haupttour
- Beide Touren haben den gleichen `base_name` ("W-07.00")

✅ **24 Touren werden korrekt angezeigt**:
- Alle Touren werden aus der CSV extrahiert
- Keine verlorenen Kunden
- Deterministische Reihenfolge

✅ **Frontend zeigt Touren an**:
- Tourübersicht wird befüllt
- BAR-Touren werden gelb/orange hervorgehoben
- Zusammengehörige Touren werden gruppiert

## Referenz

**Bewährte Logik aus:** `docs/Neu/parse_w7.py` (Zeilen 68-119)
- `unify_route_name()` → `TourInfo.get_base_name()`
- `pending_bar` Dictionary für BAR-Kunden
- `full_name_map` für Header-Zuordnung
- Sofortige BAR-Konsolidierung bei Haupttour

**Integration:** `backend/parsers/tour_plan_parser.py` (Zeilen 111-224)

## Testen

1. CSV erneut hochladen
2. "Kompletter Workflow" starten
3. Prüfen: Tourübersicht zeigt alle 24 Touren
4. Prüfen: BAR-Touren sind gelb/orange hervorgehoben
5. Prüfen: Zusammengehörige Touren (W-07.00 BAR + Tour) erscheinen zusammen

