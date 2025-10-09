# FAMO Traffic – Setup & Installation (Stand 30.09.2025)

## 1. Voraussetzungen
- Windows 10/11 (getestet) oder vergleichbares System
- Python 3.10+
- PowerShell oder Bash
- Optional: Ollama (für lokale KI) und OpenRouteService-API-Key (Routing)

## 2. Projekt-Setup
```powershell
cd "C:\Users\Bretfeld\Meine Ablage\_________FAMO"
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

## 3. Server starten
```powershell
python start_server.py
```
Server läuft standardmäßig auf `http://127.0.0.1:8111`. Frontend `/ui/`, API-Docs `/docs`.

## 4. Workflow nutzen
1. Browser öffnen: `http://127.0.0.1:8111/ui/`
2. CSV wählen → "Nur parsen" (Schritt 1) oder "Workflow starten" (Schritte 1–6)
3. Akkordeon rechts zeigt Touren (Parser- oder Workflow-Ergebnis) inkl. BAR-Filter

API-Alternative:
- `POST /api/parse-csv-tourplan` – Schritt 1
- `POST /api/process-csv-modular` – Workflow (Parser ➝ KI ➝ Subtouren)

## 5. Optional: KI & Routing
- Ollama installieren, Modell `qwen2.5:0.5b` (für `ai_optimizer.py`)
- OpenRouteService-Key in `backend/services/real_routing.py` eintragen (Routing-Ausbau)

## 6. Tests & Logs
- Parser-Golden-Test: `python scripts/test_csv_parser.py`
- Logs: `logs/csv_import_debug.log`
- Workflow-Info: `GET /api/workflow-info`

## 7. Troubleshooting
- Server-Health: `curl http://127.0.0.1:8111/health`
- Workflow-Fehler: Logs prüfen (`logs/`)
- KI-Kommentare fallen aus → Ollama-Status prüfen (`http://localhost:11434/api/tags`)

## 8. Weiterführende Dokumente
- `docs/Api_Docs.md` – API-Details
- `docs/Architecture.md` – 8-Schritte-Architektur
- `docs/FAMO_TrafficApp_MasterDoku.md` – Gesamtüberblick
- `docs/FORTSCHRITT_22_09_2025.md` – aktueller Fortschritt
