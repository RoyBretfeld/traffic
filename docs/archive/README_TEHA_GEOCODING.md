# TEHA-Geocoding: Einmal machen, für immer gesichert

## Das Wichtigste

**TEHA liefert immer die gleichen Adressen** → **Einmal geocodieren** → **Für immer aus DB laden**

## Quick Start

### 1. Coverage prüfen

```bash
python scripts/check_teha_coverage.py TEHA_export.csv
```

**Output:**
- Wie viele Adressen bereits in DB sind
- Wie viele noch geocodiert werden müssen
- Coverage-Prozentsatz

### 2. Bulk-Geocoding (falls nötig)

```bash
# Alle fehlenden Adressen geocodieren
python scripts/teha_bulk_geocode.py TEHA_export.csv

# Oder mit Limit (z.B. 50 Adressen pro Durchlauf)
python scripts/teha_bulk_geocode.py TEHA_export.csv --limit 50
```

### 3. Nochmal prüfen

```bash
python scripts/check_teha_coverage.py TEHA_export.csv
```

**Ziel: 100% Coverage**

## Wie es funktioniert

### DB-First Strategie

1. **Prüfe DB** → Wenn Adresse in `geo_cache` → Verwende Koordinaten
2. **Nicht in DB?** → Geocode & speichere in DB
3. **Nächstes Mal** → Direkt aus DB (Schritt 1)

### Determinismus-Garantien

- ✅ **Keine doppelte Geocodierung**: Adresse wird nur einmal geocodiert
- ✅ **Persistierung**: Ergebnis wird in `geo_cache` gespeichert
- ✅ **DB-First**: Immer zuerst DB prüfen, dann extern
- ✅ **Normalisierung**: Adressen werden vor dem Lookup normalisiert

### TEHA-Integration

- TEHA liefert **immer die gleichen Adressen**
- Diese werden **einmal** geocodiert
- In `geo_cache` **gespeichert**
- **Für immer** aus der DB geladen

## Beispiel-Workflow

```bash
# 1. TEHA-Export bekommen
# → TEHA_export.csv

# 2. Coverage prüfen
python scripts/check_teha_coverage.py TEHA_export.csv
# Output: Coverage 45% → 55 Adressen fehlen noch

# 3. Bulk-Geocoding
python scripts/teha_bulk_geocode.py TEHA_export.csv
# Output: 55 Adressen geocodiert und in DB gespeichert

# 4. Nochmal prüfen
python scripts/check_teha_coverage.py TEHA_export.csv
# Output: Coverage 100% → Fertig!

# 5. Ab jetzt: Alle Adressen kommen automatisch aus der DB
# → Keine weiteren Geocoding-Aufrufe nötig
```

## Garantien

1. ✅ **Determinismus**: Gleiche Adresse = Gleiches Ergebnis
2. ✅ **Persistierung**: Einmal geocodiert = Für immer gespeichert
3. ✅ **Performance**: DB-Lookup ist schneller als externes Geocoding
4. ✅ **Konsistenz**: TEHA-Adressen werden immer gleich behandelt

## Debugging

### Prüfen ob Adresse in DB ist

```python
from repositories.geo_repo import get

result = get("Hauptstr 1, 01067 Dresden")
if result:
    print(f"In DB: {result['lat']}, {result['lon']}")
else:
    print("Nicht in DB - wird geocodiert")
```

### Batch-Status prüfen

```python
from repositories.geo_repo import bulk_get

addresses = ["Adresse 1", "Adresse 2", ...]
results = bulk_get(addresses)

for addr, data in results.items():
    if data:
        print(f"OK {addr}: {data['lat']}, {data['lon']}")
    else:
        print(f"MISSING {addr}: Nicht in DB")
```

## Fazit

- **Einmal** Geocoding für TEHA-Adressen
- **Für immer** aus DB laden
- **Gleiche** Adressen = **Gleiche** Ergebnisse
- **TEHA liefert immer gleich** → Einmal machen, fertig

