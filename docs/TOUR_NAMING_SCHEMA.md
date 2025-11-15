# Tour-Namensschema - Bedeutung der Buchstaben

## Übersicht

Die Buchstaben am Ende von Tournamen (z.B. "W-07.00 Uhr Tour B A A A") zeigen an, wie eine Tour aufgeteilt wurde.

## Bedeutung der Buchstaben

### Einzelne Buchstaben (A, B, C, D, E...)

**Beispiel:** `W-07.00 Uhr Tour A`

- **Bedeutung:** Die Tour wurde in mehrere separate Routen aufgeteilt
- **Grund:** Die Tour war zu groß (überschreitet 65 Min OHNE Rückfahrt oder 90 Min INKL. Rückfahrt)
- **Logik:** 
  - Erste Route → `A`
  - Zweite Route → `B`
  - Dritte Route → `C`
  - etc.

**Code-Stelle:** `routes/workflow_api.py` Zeile 532, 738-739

```python
route_letter = chr(ord('A') + route_idx)  # A, B, C, ...
tour_name_final = f"{tour_name} {route_letter}"
```

### Mehrfache Buchstaben (AA, AB, AC... oder A A A)

**Beispiel:** `W-07.00 Uhr Tour B A A A`

- **Bedeutung:** Rekursive Aufteilung - eine bereits aufgeteilte Tour wurde nochmals aufgeteilt
- **Grund:** Auch nach der ersten Aufteilung war eine Sub-Route noch zu groß
- **Logik:**
  - `W-07.00 Uhr Tour` → zu groß
  - Aufgeteilt in: `W-07.00 Uhr Tour A`, `W-07.00 Uhr Tour B`
  - `W-07.00 Uhr Tour B` → immer noch zu groß
  - Aufgeteilt in: `W-07.00 Uhr Tour B A`, `W-07.00 Uhr Tour B B`
  - `W-07.00 Uhr Tour B A` → immer noch zu groß
  - Aufgeteilt in: `W-07.00 Uhr Tour B A A`, `W-07.00 Uhr Tour B A B`
  - etc.

**Code-Stelle:** `routes/workflow_api.py` Zeile 525-526

```python
# Mehrere Sub-Touren → A, B, C, ...
sub_letter = chr(ord('A') + idx)
sub_tour["tour_id"] = f"{base_name} {route_letter}{sub_letter}"
```

## Wann werden Touren aufgeteilt?

### 1. Automatische Aufteilung bei zu großen Touren

**Bedingung:**
- Tour hat mehr als 7 Kunden ODER
- Geschätzte Zeit > 65 Min (OHNE Rückfahrt) ODER
- Geschätzte Zeit > 90 Min (INKL. Rückfahrt)

**Code-Stelle:** `routes/workflow_api.py` Zeile 1445-1457

### 2. Sektor-Planung für W-Touren

**Bedingung:**
- Tour beginnt mit "W-" (z.B. "W-07.00 Uhr")
- Tour hat mindestens 2 Kunden mit Koordinaten

**Logik:**
- Tour wird nach Himmelsrichtungen aufgeteilt (Nord, Ost, Süd, West)
- Wenn ein Sektor mehrere Routen benötigt → Buchstaben A, B, C...

**Code-Stelle:** `routes/workflow_api.py` Zeile 1377-1400

### 3. PIRNA-Clustering für PIR-Touren

**Bedingung:**
- Tour beginnt mit "PIR"
- Tour hat mindestens 2 Kunden mit Koordinaten

**Logik:**
- Tour wird in geografische Cluster aufgeteilt
- Wenn ein Cluster mehrere Routen benötigt → Buchstaben A, B, C...

**Code-Stelle:** `routes/workflow_api.py` Zeile 1409-1435

### 4. Timebox-Validierung

**Bedingung:**
- Nach jeder Aufteilung wird die Route durch `enforce_timebox()` geprüft
- Wenn Route immer noch zu groß → weitere Aufteilung

**Code-Stelle:** `routes/workflow_api.py` Zeile 347-423

## Beispiel-Ablauf

```
1. Original: "W-07.00 Uhr Tour"
   → 15 Kunden, 120 Min geschätzt
   → ZU GROSS!

2. Erste Aufteilung:
   → "W-07.00 Uhr Tour A" (5 Kunden, 50 Min)
   → "W-07.00 Uhr Tour B" (10 Kunden, 70 Min)
   → "W-07.00 Uhr Tour C" (0 Kunden - Fehler)

3. "W-07.00 Uhr Tour B" immer noch zu groß (70 Min > 65 Min)
   → Zweite Aufteilung:
   → "W-07.00 Uhr Tour B A" (4 Kunden, 40 Min)
   → "W-07.00 Uhr Tour B B" (6 Kunden, 30 Min)

4. "W-07.00 Uhr Tour B A" immer noch zu groß (40 Min OK, aber mit Rückfahrt > 90 Min?)
   → Dritte Aufteilung:
   → "W-07.00 Uhr Tour B A A" (2 Kunden, 20 Min)
   → "W-07.00 Uhr Tour B A B" (2 Kunden, 20 Min)
```

## Maximale Rekursionstiefe

**Schutz gegen Endlosschleifen:**
- Maximale Rekursionstiefe: **10 Ebenen**
- Wenn erreicht: Tour wird trotzdem materialisiert (auch wenn zu groß)

**Code-Stelle:** `routes/workflow_api.py` Zeile 435, 441-450

## Zusammenfassung

| Buchstaben-Muster | Bedeutung | Beispiel |
|------------------|-----------|----------|
| Keine Buchstaben | Original-Tour, nicht aufgeteilt | `W-07.00 Uhr Tour` |
| Ein Buchstabe | Erste Aufteilung | `W-07.00 Uhr Tour A` |
| Zwei Buchstaben | Zweite Aufteilung (rekursiv) | `W-07.00 Uhr Tour B A` |
| Drei Buchstaben | Dritte Aufteilung (rekursiv) | `W-07.00 Uhr Tour B A A` |
| Vier+ Buchstaben | Weitere Aufteilungen (selten) | `W-07.00 Uhr Tour B A A A` |

## Technische Details

- **Buchstaben werden automatisch generiert:** `chr(ord('A') + index)`
- **Jede Aufteilung beginnt bei A:** A, B, C, D, E...
- **Rekursive Aufteilung:** Wenn eine Sub-Route noch zu groß ist, wird sie weiter aufgeteilt
- **Keine manuelle Eingabe:** Alle Buchstaben werden vom System automatisch vergeben

