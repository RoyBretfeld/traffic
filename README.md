# FAMO TrafficApp – Starterpaket
On-Prem Routenplanung mit KI. Dieses Paket richtet Ordner, venv, Linter/Tests ein.

## Schnellstart
1) `cd FAMO_TrafficApp_Starter`
2) Windows: `powershell -ExecutionPolicy Bypass -File .\scripts\setup_venv.ps1`
   Linux:   `chmod +x scripts/setup_venv.sh && ./scripts/setup_venv.sh`
3) `pytest -q` (Smoke-Test)

## CSV → Tour Schnellstart
1. Beispiel-CSV kopieren: `cp docs/sample_customers.csv my_customers.csv` und mit eigenen Kunden ergänzen.
2. Pipeline ausführen: `python -m traffic.cli my_customers.csv --output-dir output`.
3. Ergebnisse anschauen:
   - `output/tours.json` – strukturierte Tourdaten
   - `output/tour_summary.csv` – Zeitüberblick je Untertour
   - `output/tours_map.html` – interaktive Karte (im Browser öffnen)

Optional: `--use-nominatim` aktivieren, falls Koordinaten im CSV fehlen (Internet nötig). Die SQLite-Geocache wird im Output-Ordner angelegt.

## Hinweise
- Datenordner (`data/`, `routen/`, `stats/`, `logs/`) sind gitignored – per Drive/NAS synchron halten.
- `.env.example` kopieren zu `.env` und Schlüssel setzen.
