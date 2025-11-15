# FAMO TrafficApp 3.0 - Entwicklerhandbuch

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-13

---

## Inhaltsverzeichnis

1. [Schnellstart](#schnellstart)
2. [Installation & Setup](#installation--setup)
3. [Projektstruktur](#projektstruktur)
4. [Entwicklung](#entwicklung)
5. [Testing](#testing)
6. [Datenbank](#datenbank)
7. [Routing & OSRM](#routing--osrm)
8. [API-Entwicklung](#api-entwicklung)
9. [Debugging](#debugging)
10. [Deployment](#deployment)
11. [Troubleshooting](#troubleshooting)

---

## Schnellstart

### Voraussetzungen
- Python 3.10+
- Git
- Docker (optional, für OSRM)

### Installation (60 Sekunden)

```bash
# Repository klonen
git clone https://github.com/famo/trafficapp.git
cd trafficapp

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder
venv\Scripts\activate    # Windows

# Abhängigkeiten installieren
pip install -r requirements.txt

# Pre-commit Hooks aktivieren
pre-commit install

# Umgebungsvariablen konfigurieren
cp env.example .env
# .env Datei nach Bedarf anpassen

# Server starten
python start_server.py
```

### Erste Schritte
1. **App öffnen:** http://127.0.0.1:8111
2. **API Docs:** http://127.0.0.1:8111/docs
3. **Health Check:** http://127.0.0.1:8111/health/db

---

## Installation & Setup

### Windows Setup

```powershell
# Verzeichnis vorbereiten
cd "C:\Users\Bretfeld\Meine Ablage\_________FAMO\Traffic"

# Virtual Environment
python -m venv .venv
& ".\.venv\Scripts\Activate.ps1"
pip install -r requirements.txt
```

### AI-System (optional)

#### Ollama installieren
1. Download: https://ollama.ai/download/windows
2. Standardinstallation durchführen
3. Ollama starten (automatisch im Hintergrund)

#### Qwen-Modell installieren
```powershell
ollama pull qwen2.5:0.5b
ollama list  # Sollte qwen2.5:0.5b anzeigen
```

#### Modelle-Verzeichnis (optional)
```powershell
$env:OLLAMA_MODELS = "C:\Users\Bretfeld\Meine Ablage\_________FAMO\Traffic\ai_models"
```

### Datenbank-Setup

#### Automatische Initialisierung
```bash
# Beim ersten Start wird automatisch erstellt:
python start_server.py
```

#### Manuelle Initialisierung
```bash
python -c "from db.schema import ensure_schema; ensure_schema()"
```

### System starten

```bash
python start_server.py
```

**Erfolgsmeldung:**
```
🚀 FAMO TrafficApp wird gestartet...
📍 Server läuft auf: http://127.0.0.1:8111
🌐 Frontend UI: http://127.0.0.1:8111/ui/
📚 API Docs: http://127.0.0.1:8111/docs
❌ Beenden mit: Ctrl+C
```

### Frontend aufrufen

- **Haupt-UI:** http://127.0.0.1:8111/ui/
- **API-Docs:** http://127.0.0.1:8111/docs
- **Startseite:** http://127.0.0.1:8111/

---

## Projektstruktur

### Schichtarchitektur
```
Frontend (HTML/CSS/JS)
    ↓
API Layer (FastAPI Routes)
    ↓
Business Logic (Services)
    ↓
Data Access (Repositories)
    ↓
Database (SQLite)
```

### Kernmodule

#### `common/` - Gemeinsame Komponenten
- **`normalize.py`** - Adress-Normalisierung mit Mojibake-Schutz
- **`tour_data_models.py`** - Datenstrukturen für Touren
- **`synonyms.py`** - PF-Kunden-Synonyme
- **`text_cleaner.py`** - Text-Bereinigung und Encoding-Fixes

#### `backend/` - Hauptanwendungslogik
- **`app.py`** - FastAPI-Anwendung mit allen Routen
- **`parsers/`** - CSV-Parser für Tourpläne
- **`services/`** - Geschäftslogik (Geocoding, Routing, AI)
- **`utils/`** - Hilfsfunktionen

#### `repositories/` - Datenbankzugriff
- **`geo_repo.py`** - Geocoding-Repository mit Cache
- **`manual_repo.py`** - Manuelle Koordinaten-Eingaben
- **`geo_fail_repo.py`** - Fehlgeschlagene Geocodierungen

#### `routes/` - API-Endpoints
- **`tourplan_*.py`** - Tourplan-Management
- **`audit_*.py`** - Audit und Monitoring
- **`health_check.py`** - System-Status

---

## Entwicklung

### Code-Standards

Siehe **[STANDARDS.md](STANDARDS.md)** für vollständige Coding-Standards.

**Kurzfassung:**
- **Python:** PEP 8 mit Black-Formatierung
- **Typing:** Vollständige Type Hints
- **Dokumentation:** Docstrings für alle Funktionen
- **Tests:** Pytest mit Coverage ≥ 80%

### Pre-commit Hooks

```bash
# Hooks installieren
pre-commit install

# Manuell ausführen
pre-commit run --all-files
```

### Code-Qualität

```bash
# Formatierung
black .
isort .

# Linting
ruff check .
mypy .

# Alle Checks
pre-commit run --all-files
```

---

## Testing

### Test-Ausführung

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=backend --cov=repositories --cov=services

# Spezifische Tests
pytest tests/test_geocode_robust_simple.py -v

# Integration Tests
pytest -m integration
```

### Test-Struktur

```
tests/
├── unit/           # Unit-Tests
├── integration/    # Integration-Tests
├── e2e/            # End-to-End-Tests
└── fixtures/       # Test-Daten
```

### Coverage-Anforderungen

- **Minimum:** 80% Code-Coverage
- **Kritische Pfade:** 100% Coverage
- **CI-Fail:** Wenn Coverage unter 80% fällt

---

## Datenbank

### Schema

- **`kunden`** - Kundendaten mit Koordinaten
- **`touren`** - Tourinformationen
- **`geo_cache`** - Geocoding-Cache
- **`geo_fail`** - Fehlgeschlagene Geocodierungen
- **`geo_alias`** - Adress-Aliase
- **`geo_manual`** - Manuelle Koordinaten-Eingaben
- **`manual_queue`** - Warteschlange für manuelle Bearbeitung

**Vollständiges Schema:** Siehe `docs/DATABASE_SCHEMA.md`

### Migrationen

```bash
# Schema aktualisieren
python -c "from db.schema import ensure_schema; ensure_schema()"

# Migrationen ausführen
python -c "from db.migrate_schema import migrate_geo_cache_schema; migrate_geo_cache_schema()"
```

---

## Routing & OSRM

### Lokale OSRM-Installation

1. **Daten beschaffen**: Lade ein geeignetes OpenStreetMap-PBF (z. B. `germany-latest.osm.pbf` oder ein regional zugeschnittenes Extrakt) und lege es im Verzeichnis `osrm/` ab.

2. **Preprocessing ausführen** (erfordert Docker):

**PowerShell:**
```powershell
$root = (Get-Location).Path
docker run --rm -t -v "$root/osrm:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/germany-latest.osm.pbf
docker run --rm -t -v "$root/osrm:/data" osrm/osrm-backend osrm-partition /data/germany-latest.osrm
docker run --rm -t -v "$root/osrm:/data" osrm/osrm-backend osrm-customize /data/germany-latest.osrm
```

**Linux/macOS:**
```bash
docker run --rm -t -v "$(pwd)/osrm:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/germany-latest.osm.pbf
docker run --rm -t -v "$(pwd)/osrm:/data" osrm/osrm-backend osrm-partition /data/germany-latest.osrm
docker run --rm -t -v "$(pwd)/osrm:/data" osrm/osrm-backend osrm-customize /data/germany-latest.osrm
```

3. **OSRM starten**: `docker-compose up osrm` (optional mit `-d`). Der Dienst lauscht lokal auf `http://localhost:5000`.

4. **App konfigurieren**:
   - `.env` oder `config.env` mit `OSRM_BASE_URL=http://osrm:5000` (bzw. `http://localhost:5000` außerhalb von Docker) versehen.
   - Optional `MAPBOX_ACCESS_TOKEN` leer lassen, wenn ausschließlich OSRM genutzt werden soll.

5. **Routing testen**: Nach dem Start `docker-compose up app` ausführen und eine Route über die entsprechenden API-Endpunkte oder Tests abrufen.

### Proxmox/LXC Setup

Siehe **[CODE_AUDIT_PLAYBOOK.md](STANDARDS/CODE_AUDIT_PLAYBOOK.md)** Abschnitt 10 für Proxmox-spezifische Anleitung.

---

## API-Entwicklung

### Neue Endpoints hinzufügen

1. **Route-Datei erstellen** in `routes/`
2. **Router registrieren** in `backend/app.py`
3. **Tests schreiben** in `tests/`
4. **Dokumentation aktualisieren** in `docs/API.md`

### Beispiel-Route

```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/example", tags=["example"])

class ExampleResponse(BaseModel):
    message: str
    status: str

@router.get("/", response_model=ExampleResponse)
async def get_example():
    return ExampleResponse(message="Hello World", status="ok")
```

### Error Handling

```python
from fastapi import HTTPException

# Standard HTTP-Fehler
raise HTTPException(status_code=404, detail="Resource not found")

# Custom Error Response
from backend.utils.responses import create_json_response
return create_json_response({
    "success": False,
    "error": "Custom error message"
})
```

**Vollständige API-Dokumentation:** Siehe `docs/API.md`

---

## Debugging

### Logging

```python
import logging

logger = logging.getLogger(__name__)
logger.info("Info message")
logger.error("Error message")
```

### Debug-Endpoints

- **`/health/db`** - Datenbank-Status
- **`/health/osrm`** - OSRM-Status
- **`/audit/orig-integrity`** - Original-CSV-Integrität
- **`/api/tourplan/status`** - Tourplan-Status
- **`/_debug/routes`** - Alle registrierten Routen

### Häufige Probleme

#### Import-Fehler
```python
# Falsch
from .normalize import normalize_addr  # Funktion existiert nicht

# Richtig
from common.normalize import normalize_address
```

#### Encoding-Probleme
```python
# Mojibake-Schutz aktivieren
from common.normalize import normalize_address
normalized = normalize_address(address)
```

#### Datenbank-Fehler
```python
# Schema sicherstellen
from db.schema import ensure_schema
ensure_schema()
```

---

## Deployment

### Docker

```bash
# Container bauen
docker build -t famo-trafficapp .

# Mit Docker Compose
docker-compose up --build

# Health Check
curl http://localhost:8111/health/db
```

### Produktionsumgebung

```bash
# Umgebungsvariablen setzen
export DATABASE_URL="sqlite:///data/traffic.db"
export OSRM_BASE_URL="http://172.16.1.191:5011"
export LOG_LEVEL="INFO"

# Server starten
uvicorn backend.app:app --host 0.0.0.0 --port 8111
```

### Windows Task Scheduler

```powershell
.\scripts\schedule_backup_windows.ps1
```

---

## Troubleshooting

### Problem: Ollama nicht gefunden

```powershell
# Prüfen ob Ollama läuft:
curl http://localhost:11434/api/tags

# Falls Fehler, Ollama neu starten:
ollama serve
```

### Problem: Datenbank-Fehler

```powershell
# Datenbank neu erstellen:
Remove-Item "data\traffic.db" -ErrorAction SilentlyContinue
python -c "from db.schema import ensure_schema; ensure_schema()"
```

### Problem: Port 8111 belegt

```powershell
# Port ändern in start_server.py:
# uvicorn.run(app, host="127.0.0.1", port=8112)
```

### Problem: Geocoding funktioniert nicht

```powershell
# Internet-Verbindung prüfen
# Geopy-Cache löschen:
Remove-Item "data\geocache.db" -ErrorAction SilentlyContinue
```

### System-Check

**Alles funktioniert wenn:**
- ✅ **Server startet** ohne Fehler
- ✅ **http://127.0.0.1:8111/health** zeigt `{"status": "ok"}`
- ✅ **Frontend lädt** Karte und Touren
- ✅ **KI-Summary** wird generiert
- ✅ **Kunden-Validierung** zeigt Ergebnisse

**Health-Check-Commands:**
```powershell
# API testen:
curl http://127.0.0.1:8111/health
curl http://127.0.0.1:8111/health/db
curl http://127.0.0.1:8111/health/osrm

# Ollama testen:
curl http://localhost:11434/api/tags
```

---

## Updates & Wartung

### System-Update

```bash
# Dependencies aktualisieren:
pip install -r requirements.txt --upgrade

# Ollama-Modelle aktualisieren:
ollama pull qwen2.5:0.5b
```

### Backup wichtiger Daten

```powershell
# Sicherung erstellen:
Copy-Item "data\" "backup\data_$(Get-Date -Format 'yyyyMMdd')\" -Recurse
```

### Logs prüfen

```powershell
# Server-Logs ansehen:
Get-Content "logs\server.log" -Tail 20

# Oder direkt beim Start:
python start_server.py | Tee-Object -FilePath "logs\server.log"
```

---

## Weiterführende Dokumentation

- **[STANDARDS.md](STANDARDS.md)** - Entwicklungsstandards & Richtlinien
- **[Architecture.md](Architecture.md)** - System-Architektur
- **[API.md](API.md)** - API-Dokumentation
- **[DATABASE_SCHEMA.md](DATABASE_SCHEMA.md)** - Datenbankschema
- **[CODE_AUDIT_PLAYBOOK.md](STANDARDS/CODE_AUDIT_PLAYBOOK.md)** - Code-Audit Playbook

---

## Beitragen

### Pull Request Workflow

1. **Feature Branch erstellen**
2. **Änderungen implementieren**
3. **Tests schreiben/aktualisieren**
4. **Pre-commit Hooks ausführen**
5. **Pull Request erstellen**

### Code-Review Checkliste

- [ ] Tests vorhanden und bestanden
- [ ] Dokumentation aktualisiert
- [ ] Pre-commit Hooks bestanden
- [ ] Keine Breaking Changes
- [ ] Performance-Impact berücksichtigt

---

**Dieses Entwicklerhandbuch konsolidiert Installation, Setup und Entwicklung in einem Dokument.**

