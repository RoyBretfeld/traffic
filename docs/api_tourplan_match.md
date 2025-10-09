# API-Route: `/api/tourplan/match`

## Übersicht

Die Route `/api/tourplan/match` matcht Adressen aus einem Tourplan gegen die `geo_cache` Datenbank und gibt den Status je Zeile zurück.

**Keine Geocoding-Aufrufe** - nur DB-Lookup gegen bereits vorhandene Geo-Daten.

## Endpoint

```
GET /api/tourplan/match?file=<pfad_zur_csv>
```

### Parameter

- `file` (string, required): Pfad zur Original-CSV unter `./Tourplaene`

### Beispiel-Request

```bash
curl "http://localhost:8000/api/tourplan/match?file=./Tourplaene/Tourenplan%2001.09.2025.csv"
```

### Response-Format

```json
{
  "file": "./Tourplaene/Tourenplan 01.09.2025.csv",
  "rows": 150,
  "ok": 142,
  "warn": 8,
  "bad": 0,
  "items": [
    {
      "row": 1,
      "address": "Löbtauer Straße 1, 01809 Heidenau",
      "has_geo": true,
      "geo": {
        "lat": 50.9836,
        "lon": 13.8663
      },
      "markers": [],
      "status": "ok"
    },
    {
      "row": 2,
      "address": "Unbekannte Straße 123, 99999 Teststadt",
      "has_geo": false,
      "geo": null,
      "markers": [],
      "status": "warn"
    }
  ]
}
```

## Status-Codes

- **`ok`**: Adresse hat Geo-Daten UND keine Mojibake-Marker
- **`warn`**: Adresse hat keine Geo-Daten ABER keine Mojibake-Marker
- **`bad`**: Adresse enthält Mojibake-Marker (Encoding-Probleme)

## Funktionsweise

1. **CSV-Ingest**: Verwendet zentralen `ingest.reader.read_tourplan()` (CP850→UTF-8)
2. **Adress-Extraktion**: Automatische Erkennung der Adressspalte
3. **Normalisierung**: Unicode NFC + Whitespace-Bereinigung
4. **DB-Lookup**: `bulk_get()` gegen `geo_cache` Tabelle
5. **Status-Bewertung**: Kombination aus Geo-Daten und Mojibake-Markern

## Fehlerbehandlung

- **404**: Datei nicht gefunden
- **500**: Interner Serverfehler (DB-Verbindung, CSV-Parsing)

## Abhängigkeiten

- `ingest.reader.read_tourplan()` - Zentraler CSV-Ingest
- `repositories.geo_repo.bulk_get()` - Bulk-DB-Lookup
- `ingest.guards.BAD_MARKERS` - Mojibake-Erkennung
