# Geocoding-Determinismus: Einmal geocodiert = Immer dasselbe Ergebnis

## Ziel

**Einmal geocodiert = Immer dasselbe Ergebnis aus der DB**

Adressen aus TEHA kommen immer gleich → Einmal geocodieren → Für immer aus DB laden.

## Workflow

### 1. DB-First Strategie

```
Adresse eingegeben
  ↓
1. Bereits Koordinaten vorhanden? → Verwenden
  ↓
2. In geo_cache (DB)? → Aus DB laden
  ↓
3. Nicht in DB? → Geocode & speichern
  ↓
4. Beim nächsten Mal: Direkt aus DB (Schritt 2)
```

### 2. Determinismus-Garantien

- ✅ **Keine doppelte Geocodierung**: Adresse wird nur einmal geocodiert
- ✅ **Persistierung**: Ergebnis wird in `geo_cache` gespeichert
- ✅ **DB-First**: Immer zuerst DB prüfen, dann extern
- ✅ **Normalisierung**: Adressen werden vor dem Lookup normalisiert

### 3. TEHA-Integration

TEHA liefert immer die gleichen Adressen → Diese sollten:
1. **Einmal** geocodiert werden
2. In `geo_cache` gespeichert werden
3. **Für immer** aus der DB kommen

## Implementierung

### CachedGeocoder

```python
class CachedGeocoder(Geocoder):
    """
    DB-First Geocoder: Einmal geocodiert = immer aus DB (nicht anders).
    
    Workflow:
    1. Prüfe ob Koordinaten bereits im Stop vorhanden
    2. Prüfe geo_cache (Datenbank)
    3. Falls nicht gefunden: Geocode und speichere in DB
    4. Beim nächsten Mal: Direkt aus DB (Schritt 2)
    """
```

### Normalisierung

- Alle Adressen werden vor dem DB-Lookup normalisiert
- Gleiche Adresse = Gleiche Normalisierung = Gleiche DB-Abfrage

### Persistierung

- `geo_repo.upsert()`: Speichert Adresse + Koordinaten in `geo_cache`
- `geo_repo.get()`: Lädt aus `geo_cache`
- Source-Tracking: `source='geocoded'`, `source='synonym'`, etc.

## TEHA-Import

### Option 1: CSV-Import mit automatischem Geocoding

```python
from backend.pipeline.csv_ingest_strict import parse_csv
from backend.services.synonyms import SynonymStore

# TEHA-CSV einlesen
synonym_store = SynonymStore(Path('data/address_corrections.sqlite3'))
rows = parse_csv(Path('TEHA_export.csv'), synonym_store)

# Automatisches Geocoding für fehlende Adressen
for row in rows:
    if not row.get('lat') or not row.get('lon'):
        # Geocode und speichere
        geocode_and_save(row)
```

### Option 2: Bulk-Import mit Geocoding

```python
# TEHA-Adressen direkt importieren
teha_addresses = [
    {"customer": "Kunde 1", "street": "Hauptstr 1", "postal_code": "01067", "city": "Dresden"},
    # ...
]

# Batch-Geocoding
from services.geocode_fill import fill_missing

results = await fill_missing(
    [f"{a['street']}, {a['postal_code']} {a['city']}" for a in teha_addresses],
    limit=100
)
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
        print(f"✓ {addr}: {data['lat']}, {data['lon']}")
    else:
        print(f"✗ {addr}: Nicht in DB")
```

## Best Practices

1. **TEHA-Export**: CSV mit allen Adressen exportieren
2. **Bulk-Import**: Alle Adressen auf einmal geocodieren lassen
3. **Persistierung prüfen**: Sicherstellen, dass alle in `geo_cache` sind
4. **Monitoring**: Erkennungsrate regelmäßig prüfen

## TEHA-Workflow

### Schritt 1: Coverage prüfen

```bash
python scripts/check_teha_coverage.py TEHA_export.csv
```

Zeigt:
- Wie viele Adressen bereits in DB sind
- Wie viele noch geocodiert werden müssen
- Coverage-Prozentsatz

### Schritt 2: Bulk-Geocoding (falls nötig)

```bash
# Alle fehlenden Adressen geocodieren
python scripts/teha_bulk_geocode.py TEHA_export.csv

# Oder mit Limit (z.B. 50 Adressen)
python scripts/teha_bulk_geocode.py TEHA_export.csv --limit 50

# Dry-Run (ohne DB-Updates)
python scripts/teha_bulk_geocode.py TEHA_export.csv --dry-run
```

### Schritt 3: Nochmal prüfen

```bash
python scripts/check_teha_coverage.py TEHA_export.csv
```

Sollte jetzt **100% Coverage** zeigen.

## Fazit

- **Einmal** Geocoding für TEHA-Adressen
- **Für immer** aus DB laden
- **Gleiche** Adressen = **Gleiche** Ergebnisse
- **TEHA liefert immer gleich** → Einmal machen, fertig

