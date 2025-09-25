# CSV-Workflow Quickstart

Der Schnellstart richtet sich an Teams, die ohne PDF-Parser direkt mit strukturierten Kundendaten arbeiten wollen.

## CSV-Schema
Pflichtspalten:

| Spalte | Beschreibung |
| --- | --- |
| `customer_id` | Eindeutige ID je Kunde/Stopp |
| `name` | Anzeigename auf Karte und in Listen |
| `address` | Vollständige Adresse (für Geocoding & Reporting) |
| `service_minutes` | Geplante Aufenthaltsdauer vor Ort |

Optionale Spalten:

| Spalte | Beschreibung |
| --- | --- |
| `latitude`, `longitude` | Vorgegebene Koordinaten; beschleunigt Geocoding |
| `time_window_start`, `time_window_end` | Service-Zeitfenster (`HH:MM`) |
| weitere | werden als `metadata` in die JSON-Ausgabe übernommen |

Eine Beispiel-Datei liegt unter [`docs/sample_customers.csv`](./sample_customers.csv).

## Ausführung
```bash
python -m traffic.cli pfad/zur/customers.csv --output-dir output
```

Erzeugte Artefakte:

- `tours.json` – strukturierte Tourdaten für Folgeprozesse
- `tour_summary.csv` – Übersicht mit Stopanzahl, Zeiten und Dauer
- `tours_map.html` – interaktive Leaflet-Karte mit Depot, Untertouren und Stops

Die Pipeline legt außerdem einen SQLite-Geocache (`geocache.sqlite`) im Output-Ordner an.

## Geocoding
- Sind `latitude`/`longitude` gesetzt, werden diese direkt genutzt.
- Fehlen Koordinaten, kann optional OpenStreetMap/Nominatim zugeschaltet werden:
  ```bash
  python -m traffic.cli customers.csv --output-dir output --use-nominatim
  ```
- Für Offline-Betrieb empfiehlt es sich, Koordinaten einmalig zu berechnen und direkt im CSV zu hinterlegen.

## Parameter
| Parameter | Wirkung |
| --- | --- |
| `--tour-limit` | Maximale Dauer pro Untertour in Minuten (Standard: 60) |
| `--speed` | Angenommene Fahrgeschwindigkeit in km/h (Standard: 35) |

## Nächste Schritte
- JSON-Ausgabe (`tours.json`) in Modul 05 (Touren-Manager) einspeisen
- Routing (Modul 04) anschließen, sobald API-Schlüssel vorliegt
- Frontend (Modul 07) mit `tours_map.html` oder eigener Leaflet-Integration erweitern
