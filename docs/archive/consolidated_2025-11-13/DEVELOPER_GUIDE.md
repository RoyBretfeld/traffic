# FAMO TrafficApp 3.0 - Entwicklerhandbuch

## 🚀 Schnellstart

### Voraussetzungen
- Python 3.10+
- Git
- Docker (optional)

### Installation
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

## 🏗️ Architektur

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

## 🔧 Entwicklung

### Code-Standards
- **Python:** PEP 8 mit Black-Formatierung
- **Typing:** Vollständige Type Hints
- **Dokumentation:** Docstrings für alle Funktionen
- **Tests:** Pytest mit Coverage

### Pre-commit Hooks
```bash
# Hooks installieren
pre-commit install

# Manuell ausführen
pre-commit run --all-files
```

### Testing
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

## 📊 Datenbank

### Schema
- **`kunden`** - Kundendaten mit Koordinaten
- **`touren`** - Tourinformationen
- **`geo_cache`** - Geocoding-Cache
- **`geo_fail`** - Fehlgeschlagene Geocodierungen
- **`geo_alias`** - Adress-Aliase
- **`geo_manual`** - Manuelle Koordinaten-Eingaben
- **`manual_queue`** - Warteschlange für manuelle Bearbeitung

### Migrationen
```bash
# Schema aktualisieren
python -c "from db.schema import ensure_schema; ensure_schema()"

# Migrationen ausführen
python -c "from db.migrate_schema import migrate_geo_cache_schema; migrate_geo_cache_schema()"
```

## 🛣️ Routing & OSRM (lokal)

1. **Daten beschaffen**: Lade ein geeignetes OpenStreetMap-PBF (z. B. `germany-latest.osm.pbf` oder ein regional zugeschnittenes Extrakt) und lege es im neuen Verzeichnis `osrm/` ab.
2. **Preprocessing ausführen** (erfordert Docker). Beispiel für PowerShell:
   ```powershell
   $root = (Get-Location).Path
   docker run --rm -t -v "$root/osrm:/data" osrm/osrm-backend osrm-extract -p /opt/car.lua /data/germany-latest.osm.pbf
   docker run --rm -t -v "$root/osrm:/data" osrm/osrm-backend osrm-partition /data/germany-latest.osrm
   docker run --rm -t -v "$root/osrm:/data" osrm/osrm-backend osrm-customize /data/germany-latest.osrm
   Get-ChildItem "$root/osrm/germany-latest.osrm*" | ForEach-Object {
     $target = $_.Name -replace '^germany-latest', 'osrm-data'
     Rename-Item $_.FullName $target
   }
   ```
   Die resultierenden Dateien (`*.osrm`, `*.osrm.mld`, …) bleiben im `osrm/`-Ordner. Die `docker-compose.yml` erwartet standardmäßig eine Datei `osrm-data.osrm`; passe den Dateinamen entsprechend an oder aktualisiere die Compose-Datei.
   > **Hinweis:** Unter Linux/macOS analog, mit `$(pwd)/osrm:/data` anstelle von `$root/osrm:/data` und entsprechendem `mv`/`rename`-Befehl.
3. **OSRM starten**: `docker-compose up osrm` (optional mit `-d`). Der Dienst lauscht lokal auf `http://localhost:5000`.
4. **App konfigurieren**:
   - `.env` oder `config.env` mit `OSRM_BASE_URL=http://osrm:5000` (bzw. `http://localhost:5000` außerhalb von Docker) versehen.
   - Optional `MAPBOX_ACCESS_TOKEN` leer lassen, wenn ausschließlich OSRM genutzt werden soll.
5. **Routing testen**: Nach dem Start `docker-compose up app` ausführen und eine Route über die entsprechenden API-Endpunkte oder Tests abrufen.

## 🌐 API-Entwicklung

### Neue Endpoints hinzufügen
1. **Route-Datei erstellen** in `routes/`
2. **Router registrieren** in `backend/app.py`
3. **Tests schreiben** in `tests/`
4. **Dokumentation aktualisieren**

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
from ingest.http_responses import create_utf8_json_response
return create_utf8_json_response({
    "success": False,
    "error": "Custom error message"
})
```

## 🔍 Debugging

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info("Info message")
logger.error("Error message")
```

### Debug-Endpoints
- **`/health/db`** - Datenbank-Status
- **`/audit/orig-integrity`** - Original-CSV-Integrität
- **`/api/tourplan/status`** - Tourplan-Status

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

## 🚀 Deployment

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
export GEOCODER_BASE="https://nominatim.openstreetmap.org/search"
export LOG_LEVEL="INFO"

# Server starten
uvicorn backend.app:app --host 0.0.0.0 --port 8111
```

## 📚 Weiterführende Dokumentation

- **Architektur:** `docs/Architecture.md`
- **API-Dokumentation:** `docs/Api_Docs.md`
- **Datenbankschema:** `docs/DATABASE_SCHEMA.md`
- **Installation:** `docs/INSTALLATION_GUIDE.md`

## 🤝 Beitragen

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

## 📞 Support

Bei Fragen oder Problemen:
1. **Issues erstellen** auf GitHub
2. **Dokumentation durchsuchen**
3. **Logs analysieren** in `logs/`
4. **Team kontaktieren**
