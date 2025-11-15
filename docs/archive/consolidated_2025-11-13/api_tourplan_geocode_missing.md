# API-Route: `/api/tourplan/geocode-missing`

## Übersicht

Die Route `/api/tourplan/geocode-missing` geokodiert fehlende Adressen aus einem Tourplan über Nominatim und aktualisiert den `geo_cache`.

**Rate-Limited** - Respektiert Nominatim-Policy (max. 1 Request/Sekunde).

## Endpoint

```
GET /api/tourplan/geocode-missing?file=<pfad>&limit=<anzahl>&dry_run=<boolean>
```

### Parameter

- `file` (string, required): Pfad zur Original-CSV unter `./Tourplaene`
- `limit` (int, optional): Maximale Anzahl zu geokodierender Adressen (1-100, default: 20)
- `dry_run` (boolean, optional): Wenn `true`, keine DB-Updates (default: false)

### Beispiel-Requests

```bash
# Dry-Run: Nur testen, keine DB-Updates
curl "http://localhost:8000/api/tourplan/geocode-missing?file=./Tourplaene/Tourenplan%2001.09.2025.csv&limit=5&dry_run=true"

# Echte Geocoding: Aktualisiert geo_cache
curl "http://localhost:8000/api/tourplan/geocode-missing?file=./Tourplaene/Tourenplan%2001.09.2025.csv&limit=10&dry_run=false"
```

### Response-Format

```json
{
  "file": "./Tourplaene/Tourenplan 01.09.2025.csv",
  "requested": 15,
  "processed": 10,
  "dry_run": false,
  "items": [
    {
      "address": "Löbtauer Straße 1, 01809 Heidenau",
      "result": {
        "lat": 50.9836,
        "lon": 13.8663
      }
    },
    {
      "address": "Unbekannte Straße 123",
      "result": null
    },
    {
      "_meta": {
        "t_sec": 12.5,
        "count": 10,
        "dry_run": false,
        "delay_sec": 1.0
      }
    }
  ]
}
```

## Funktionsweise

1. **CSV-Ingest**: Verwendet zentralen `ingest.reader.read_tourplan()`
2. **Adress-Extraktion**: Automatische Erkennung der Adressspalte
3. **Cache-Filter**: Schließt bereits vorhandene Adressen aus (`bulk_get()`)
4. **Geocoding**: Nominatim-API mit Rate-Limiting (1 Req/s)
5. **DB-Update**: Schreibt nur bei `dry_run=false` in `geo_cache`

## Rate-Limiting & Policy

- **Delay**: Mindestens 1 Sekunde zwischen Requests
- **User-Agent**: `tourplan-geocoder/1.0 (kontakt@example.com)`
- **Timeout**: 20 Sekunden pro Request
- **Limit**: Maximal 100 Adressen pro Request

## Fehlerbehandlung

- **404**: Datei nicht gefunden
- **HTTP-Fehler**: Werden geloggt, führen zu `result: null`
- **Timeout**: 20s pro Request, dann Abbruch
- **Ungültige Responses**: Werden zu `result: null`

## Abhängigkeiten

- `services.geocode_fill.fill_missing()` - Geocoding-Service
- `repositories.geo_repo.bulk_get()` - Cache-Lookup
- `repositories.geo_repo.upsert()` - Cache-Update
- `ingest.guards.assert_no_mojibake()` - Mojibake-Prüfung

## Sicherheitshinweise

- **Nominatim-Policy**: Respektiert Rate-Limits und User-Agent
- **Dry-Run**: Immer zuerst testen mit `dry_run=true`
- **Limit**: Verwende kleine Limits für Tests (5-10 Adressen)
- **Monitoring**: Prüfe `_meta.t_sec` für Performance-Überwachung
