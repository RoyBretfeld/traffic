# FAMO TrafficApp – Starterpaket
On-Prem Routenplanung mit KI. Dieses Paket richtet Ordner, venv, Linter/Tests ein.

## Schnellstart
1) `cd FAMO_TrafficApp_Starter`
2) Windows: `powershell -ExecutionPolicy Bypass -File .\scripts\setup_venv.ps1`
   Linux:   `chmod +x scripts/setup_venv.sh && ./scripts/setup_venv.sh`
3) `pytest -q` (Smoke-Test)

## Hinweise
- Datenordner (`data/`, `routen/`, `stats/`, `logs/`) sind gitignored – per Drive/NAS synchron halten.
- `.env.example` kopieren zu `.env` und Schlüssel setzen.
