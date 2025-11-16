# Venv Health Check - Automatische Prüfung und Reparatur

## Übersicht

Der **Venv Health Check** prüft beim Server-Start automatisch den Status des Python venv und repariert Probleme wenn möglich.

## Was wird geprüft?

1. **Venv existiert** - Prüft ob `venv/` Verzeichnis vorhanden ist
2. **Python-Pfad** - Prüft ob venv-Python verwendet wird (nicht System-Python)
3. **Kritische Packages** - Prüft ob SQLAlchemy, FastAPI, Uvicorn, Pandas importierbar sind
4. **METADATA-Dateien** - Prüft ob `.dist-info/METADATA` Dateien fehlen (Hinweis auf beschädigtes venv)
5. **Pip funktioniert** - Prüft ob pip grundsätzlich funktioniert

## Automatische Reparatur

Der Health Check versucht automatisch zu reparieren:

- **Fehlende Packages:** Installiert automatisch aus `requirements.txt`
- **Beschädigte Packages (1-3):** Repariert einzelne Packages mit `--force-reinstall`
- **Beschädigte Packages (>3):** Empfiehlt venv-Neu-Erstellung (keine automatische Reparatur)

## Verwendung

### Automatisch beim Server-Start

Der Health Check läuft automatisch beim Start:

```powershell
.\START_SERVER.ps1
# oder
python start_server.py
```

### Manuell ausführen

```powershell
python scripts\venv_health_check_standalone.py
```

## Ausgabe

```
======================================================================
VENV HEALTH CHECK
======================================================================
Venv existiert: True
Python-Pfad OK: True (E:\...\venv\Scripts\python.exe)
Kritische Packages OK: True
  - SQLAlchemy: True
  - FastAPI: True
  - Uvicorn: True
  - Pandas: True
METADATA OK: True
Pip funktioniert: True
Status: OK
Empfehlung: Alles OK - Server kann gestartet werden
======================================================================
[OK] Venv Health Check: OK - Server kann gestartet werden
```

## Fehlerbehandlung

### Venv nicht aktiviert

```
Status: WARNING
Empfehlung: Venv nicht aktiviert. Bitte aktivieren: .\venv\Scripts\Activate.ps1
```

### Beschädigtes venv

```
Status: ERROR
Empfehlung: Venv beschädigt (5 Packages). Bitte venv neu erstellen: .\recreate_venv.ps1
```

### Fehlende Packages

```
Status: ERROR
Empfehlung: Kritische Packages fehlen: sqlalchemy, fastapi. Bitte installieren: pip install -r requirements.txt
```

## Integration

Der Health Check ist integriert in:

- `start_server.py` - Läuft automatisch vor Server-Start
- `START_SERVER.ps1` - Optionaler Pre-Check (wird auch in start_server.py gemacht)
- `scripts/venv_health_check_standalone.py` - Standalone-Version

## Technische Details

- **Datei:** `backend/utils/venv_health_check.py`
- **Klasse:** `VenvHealthCheck`
- **Funktion:** `run_venv_health_check(auto_fix=True)`
- **Timeout:** 5 Sekunden für pip-Checks, 60 Sekunden pro Package-Reparatur

## Prävention

Der Health Check verhindert:

- Server-Start mit beschädigtem venv
- Import-Fehler durch fehlende Packages
- Verwirrung durch System-Python statt venv-Python
- Zeitverschwendung durch manuelle Fehlersuche

## Siehe auch

- `recreate_venv.ps1` - Venv komplett neu erstellen
- `fix_venv.ps1` - Venv reparieren (ohne Neu-Erstellung)
- `Regeln/LESSONS_LOG.md` - Dokumentierte venv-Probleme
- `docs/ERROR_CATALOG.md` - Fehlerkatalog mit venv-Problemen

