# Deterministisches CSV-Parsing & Synonym-Resolver

## Übersicht

Das deterministische CSV-Parsing garantiert **immer gleiche Ergebnisse** beim Einlesen der Tour-CSV – keine "Überraschungen", keine wechselnde Interpretation. Plus: **Synonymliste** (Alias→Kunde/Adresse/Koordinaten) wird **persistiert** und **vor** allem anderen angewandt.

## Kernprinzipien

- ✅ **Kein Sniffing**: CSV-Dialekt fest verdrahtet (`;`, `"`, `\\`)
- ✅ **Encoding fix**: `utf-8-sig` → BOM wird sauber geschluckt; optional Fallback auf `cp1252` mit Audit-Log
- ✅ **Unicode-Normalisierung**: NFC + unsichtbare Steuerzeichen raus
- ✅ **Reihenfolge stabil**: pro Zeile `row_no` mitführen, deterministisch sortieren
- ✅ **Synonyme First**: Alias-Auflösung **bevor** Geocoder/Parser zuschlagen
- ✅ **Quarantäne statt Chaos**: fehlerhafte Zeilen landen in `state/quarantine.csv` mit Grund
- ✅ **Golden-Tests**: identische Ausgaben garantieren bewusst stabile Parser-Versionen

## Komponenten

### 1. Datenbank – Synonymliste (SQLite)

**Migration:** `db/migrations/003_synonyms.sql`

- Tabelle `address_synonyms`: Alias → Customer/Address/Coordinates
- Tabelle `synonym_hits`: Nutzungsstatistik
- Indizes für schnelle Suche
- Triggers für automatische Timestamps

### 2. Text-Normalisierung

**Datei:** `backend/services/text_normalize.py`

- `normalize_token()`: Unicode NFC + Whitespace + Steuerzeichen entfernen
- `normalize_key()`: Normalisierter Schlüssel aus mehreren Teilen

### 3. Synonym-Store

**Datei:** `backend/services/synonyms.py`

- `SynonymStore`: Persistenter Store für Adress-Synonyme
- `resolve()`: Löst Alias auf (wird VOR Geocoding verwendet)
- `upsert()`: Fügt/aktualisiert Synonyme
- `list_all()`: Listet alle Synonyme
- `delete()`: Deaktiviert Synonyme

### 4. CSV-Ingest (Strict)

**Datei:** `backend/pipeline/csv_ingest_strict.py`

- Deterministisches Parsing (kein Sniffing)
- Synonym-Auflösung VOR Normalisierung
- Quarantäne für fehlerhafte Zeilen
- Deterministische Reihenfolge

## Verwendung

### Synonym hinzufügen

**Via CLI:**
```bash
python scripts/synonym_upsert.py "Roswitha" "Hauptstr 1" "01067" "Dresden" 51.0500 13.7373
```

**Via Admin-API:**
```bash
curl -X POST http://localhost:8111/api/synonyms/upsert \
  -H "Content-Type: application/json" \
  -d '{
    "alias": "Roswitha",
    "street": "Hauptstr 1",
    "postal_code": "01067",
    "city": "Dresden",
    "country": "DE",
    "lat": 51.0500,
    "lon": 13.7373,
    "priority": 0,
    "active": 1
  }'
```

**Via Admin-UI:**
- Öffne `http://localhost:8111/admin`
- Navigiere zu "Synonyme"
- Füge neues Synonym hinzu

### CSV-Parsing mit Synonymen

```python
from backend.pipeline.csv_ingest_strict import parse_csv
from backend.services.synonyms import SynonymStore
from pathlib import Path

synonym_store = SynonymStore(Path('data/address_corrections.sqlite3'))
rows = parse_csv(Path('Tourplaene/tour.csv'), synonym_store)

# Synonyme sind bereits aufgelöst
for row in rows:
    if row['synonym_applied']:
        print(f"Synonym verwendet: {row['customer']} → {row['street']}")
    if row['lat'] and row['lon']:
        print(f"Koordinaten aus Synonym: {row['lat']}, {row['lon']}")
```

## Workflow

1. **CSV-Lesen** → Deterministisches Parsing (`csv_ingest_strict.py`)
2. **Synonym-Resolver** → Prüft `customer` und `street` gegen `address_synonyms`
3. **Wenn Synonym gefunden:**
   - Verwendet `street`, `postal_code`, `city` aus Synonym
   - Verwendet `lat`, `lon` aus Synonym (falls vorhanden)
   - Überspringt Geocoding
4. **Wenn kein Synonym:**
   - Normale Normalisierung
   - Geocoding über Nominatim/OSRM
   - Speicherung in `geo_cache`

## Tests

**Golden File Tests:** `tests/test_csv_ingest_strict.py`

- Deterministisches Parsing
- Synonym-Auflösung
- Quarantäne für fehlerhafte Zeilen
- Fehlende Pflichtspalten

```bash
pytest tests/test_csv_ingest_strict.py -v
```

## Betrieb – Harte Garantien

- ✅ `csv.DictReader(..., delimiter=';', quotechar='"', escapechar='\\')` – **kein** Dialekt-Sniffing
- ✅ `utf-8-sig` als **einzige** Quelle; `cp1252` nur mit Log-Warnung
- ✅ **Vor** jeder Pipeline: `normalize_token()` auf alle Textfelder
- ✅ **Immer zuerst** `SynonymStore.resolve()` auf `customer` **und** `street`
- ✅ **Nie** parallele Parser-Threads – Reihenfolge bleibt Input-Order
- ✅ `state/quarantine.csv` prüfen; gelistete Alias sofort als Synonym einpflegen

## Ergebnis

- ✅ "Roswitha"/Alias-Fälle werden **sofort** aufgelöst – ohne LLM, ohne Ratespiel
- ✅ CSV-Parsing ist **stabil** und **deterministisch**; Sonderzeichen sind beherrscht
- ✅ Alles, was einmal funktioniert, bleibt **persistiert** (Synonymliste + Corrections)
- ✅ Fehlerfälle landen reproduzierbar in der **Quarantäne** statt "Anarchie & Chaos"

