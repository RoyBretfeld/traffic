#!/usr/bin/env python3
"""
Erstellt ein komplettes Code-Audit-Paket für KI-Analyse.

Dieses Script erstellt eine ZIP-Datei mit allen relevanten Dateien für ein Code-Audit:
- Backend-Code (Python)
- Frontend-Code (HTML/JS/CSS)
- Dokumentation (Markdown)
- Konfiguration
- Tests
- Regeln und Standards

AUSGESCHLOSSEN:
- Dependencies (venv, node_modules)
- Datenbanken (*.db, *.sqlite3)
- Logs und temporäre Dateien
- Build-Artefakte
- Git-Verzeichnis
"""

import os
import zipfile
import shutil
from datetime import datetime
from pathlib import Path

# Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent

# Ausgeschlossene Verzeichnisse
EXCLUDED_DIRS = {
    'venv', '__pycache__', '.git', 'node_modules', 'dist', 'build',
    '*.egg-info', '.pytest_cache', '.mypy_cache', 'htmlcov',
    'temp_zip_extract', 'backups', 'ZIP',  # Alte Backups und ZIPs
    'data',  # Datenbanken und Daten
    'logs',  # Log-Dateien
}

# Ausgeschlossene Datei-Endungen
EXCLUDED_EXTENSIONS = {
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.exe',
    '.db', '.sqlite3', '.sqlite',  # Datenbanken
    '.log', '.tmp', '.cache',  # Temporäre Dateien
    '.zip',  # Andere ZIP-Dateien
}

# Wichtige Verzeichnisse die INKLUDIERT werden sollen
INCLUDED_DIRS = {
    'backend', 'frontend', 'routes', 'services', 'db', 'tests', 'scripts',
    'Regeln', 'Global', 'docs', '.github', 'repositories', 'common', 'tools'
}

# Wichtige Datei-Endungen
INCLUDED_EXTENSIONS = {
    '.py', '.html', '.js', '.css', '.md', '.sql', '.txt', '.yml', '.yaml',
    '.json', '.ps1', '.env.example', '.cursorrules'
}

# Wichtige Root-Level-Dateien
INCLUDED_ROOT_FILES = {
    'requirements.txt', 'README.md', 'DOKUMENTATION.md', 'PROJECT_PROFILE.md',
    'start_server.py', 'START_ANLEITUNG.md', '.cursorrules', '.gitignore'
}

def should_exclude(path: Path) -> bool:
    """Prüft ob ein Pfad ausgeschlossen werden soll."""
    # Prüfe Verzeichnis-Namen
    for part in path.parts:
        if part in EXCLUDED_DIRS:
            return True
        if part.startswith('.') and part != '.github':
            return True
    
    # Prüfe Datei-Endung
    if path.suffix in EXCLUDED_EXTENSIONS:
        return True
    
    # Prüfe spezifische Dateien
    if path.name in {'.gitignore', '.env', 'secrets.env'}:
        return True
    
    return False

def should_include(path: Path) -> bool:
    """Prüfe ob ein Pfad inkludiert werden soll."""
    rel_path = path.relative_to(PROJECT_ROOT)
    rel_str = str(rel_path).replace('\\', '/')
    
    # Prüfe Root-Level-Dateien
    if rel_path.parent == PROJECT_ROOT:
        if path.name in INCLUDED_ROOT_FILES:
            return True
        if path.suffix in INCLUDED_EXTENSIONS:
            return True
    
    # Prüfe Verzeichnisse
    parts = rel_path.parts
    if len(parts) > 0:
        first_dir = parts[0]
        if first_dir in INCLUDED_DIRS:
            # Prüfe Datei-Endung
            if path.suffix in INCLUDED_EXTENSIONS:
                return True
    
    return False

def create_audit_zip(output_path: Path):
    """Erstellt das Code-Audit-ZIP-Paket."""
    print(f"[ZIP] Erstelle Code-Audit-Paket: {output_path.name}")
    print(f"[ZIP] Projekt-Root: {PROJECT_ROOT}")
    print()
    
    file_count = 0
    total_size = 0
    
    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Durchsuche Projekt-Root
        for root, dirs, files in os.walk(PROJECT_ROOT):
            root_path = Path(root)
            
            # Filtere ausgeschlossene Verzeichnisse
            dirs[:] = [d for d in dirs if not should_exclude(root_path / d)]
            
            for file in files:
                file_path = root_path / file
                
                # Prüfe Ausschluss
                if should_exclude(file_path):
                    continue
                
                # Prüfe Inklusion
                if not should_include(file_path):
                    continue
                
                # Relativer Pfad für ZIP
                rel_path = file_path.relative_to(PROJECT_ROOT)
                
                try:
                    zipf.write(file_path, rel_path)
                    file_count += 1
                    total_size += file_path.stat().st_size
                    if file_count % 50 == 0:
                        print(f"   [{file_count}] {rel_path}")
                except Exception as e:
                    print(f"   [WARN] Fehler bei {rel_path}: {e}")
    
    print()
    print(f"[OK] ZIP erstellt: {output_path.name}")
    print(f"[OK] Dateien: {file_count}")
    print(f"[OK] Groesse: {total_size / 1024 / 1024:.2f} MB")
    print(f"[OK] ZIP-Groesse: {output_path.stat().st_size / 1024 / 1024:.2f} MB")

def create_readme(output_path: Path):
    """Erstellt README für das Audit-Paket."""
    timestamp_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    zip_name = output_path.name
    
    readme_content = f"""# Code-Audit-Paket – FAMO TrafficApp 3.0

**Erstellt:** {timestamp_str}

**Zweck:** Vollständiges Code-Audit für KI-Analyse (Backend + Frontend + DB + Infrastruktur)

---

## 1️⃣ Was dieses Paket ist

Dieses Paket ist der **vollständige, bereinigte Projekt-Snapshot** für strukturierte Audits. Es ist so gebaut, dass **eine Audit-KI (z.B. Cursor)** ohne Ratespiel sofort loslegen kann.

Es enthält alles Wichtige – aber keine sensiblen Daten oder unnötigen Build-Artefakte.

---

## 2️⃣ Inhalt (High-Level)

### ✅ Enthalten

* **Backend-Code**

  `backend/`, `routes/`, `services/`, `db/schema.py`, `start_server.py`

* **Frontend-Code**

  `frontend/` (HTML, JavaScript, CSS, Panel-Files, Sub-Routen-UI)

* **Datenbank & Schema**

  `db/` (Schema-Definitionen, Migrations, Helper)

* **Tests**

  `tests/` (Unit-/Integrationstests, Test-Hooks für neue Audits)

* **Scripts & Tools**

  `scripts/`, `tools/` (Audit-ZIP-Erstellung, Hilfstools)

* **Dokumentation & Regeln**

  `PROJECT_PROFILE.md` – Projektprofil

  `DOKUMENTATION.md` – Index aller wichtigen Docs

  `Global/GLOBAL_STANDARDS.md` – globale Standards

  `Regeln/STANDARDS.md` – Projekt-Standards

  `Regeln/STANDARDS_QUICK_REFERENCE.md` – Quick-Ref

  `Regeln/REGELN_AUDITS.md` – Audit-Regeln

  `Regeln/AUDIT_CHECKLISTE.md` – 9-Punkte-Checkliste

  `Regeln/AUDIT_FLOW_ROUTING.md` – Routing/OSRM-Audit

  `Regeln/CURSOR_PROMPT_TEMPLATE.md` – fertige Audit-Prompts

  `Regeln/LESSONS_LOG.md` – echte Fehler + Learnings

* **Konfiguration (ohne Secrets)**

  Sanitisiertes Config/ENV, Beispiel-Configs, OSRM-/DB-Settings

### ❌ Ausgeschlossen

* Virtuelle Umgebungen (`venv/`, `node_modules/`)

* Build-/Cache-Artefakte (`__pycache__/`, `dist/`, `build/`)

* Logs & temporäre Dateien (`logs/`, `*.log`, `*.tmp`)

* Reale Datenbanken (`*.sqlite3`, `*.db`)

* Git-Metadaten (`.git/`)

* Reale `.env` / API-Keys / Secrets

---

## 3️⃣ Einstieg für die Audit-KI

**Immer in dieser Reihenfolge lesen:**

1. `Global/GLOBAL_STANDARDS.md`

2. `PROJECT_PROFILE.md`

3. `Regeln/STANDARDS_QUICK_REFERENCE.md`

4. `Regeln/REGELN_AUDITS.md` + `Regeln/AUDIT_CHECKLISTE.md`

5. `Regeln/LESSONS_LOG.md` (für bekannte Fehler)

**Für Routing- / Sub-Routen-Themen zusätzlich:**

* `Regeln/AUDIT_FLOW_ROUTING.md`

* `Regeln/CURSOR_PROMPT_TEMPLATE.md` → Routing-/Sub-Routen-Templates

---

## 4️⃣ Hotspots im Code (wo sich Audits lohnen)

### Touren-Workflow & Sub-Routen-Generator

* Backend:

  * `routes/tourplan_analysis.py`

  * `routes/tourplan_geofill.py`

  * `routes/tour_routes.py` (falls vorhanden)

  * `services/osrm_client.py`

  * `services/tour_optimizer.py`

  * `services/subroute_generator.py` (Name exemplarisch – realen Pfad im Projekt prüfen)

* Frontend:

  * `frontend/index.html` – Haupt-UI (Tourenliste, Sub-Routen, Buttons)

  * `frontend/js/*.js` – Rendering, Event-Handler, API-Calls

  * Panel-Files: `frontend/panel-map.html`, `frontend/panel-tours.html`, `frontend/js/panel-ipc.js`

### OSRM / Routing / Infrastruktur

* `services/osrm_client.py` – OSRM-Aufrufe, Timeouts, Fallbacks

* `routes/health_osrm.py` / Health-Endpoints – OSRM-Status

* ENV/Config – `OSRM_BASE_URL`, Timeouts, Ports

### KI / LLM-Integration

* `services/llm_optimizer.py`

* `routes/ai_test.py`, `routes/code_checker.py` (oder ähnlich benannte Files)

---

## 5️⃣ Wie ein Audit ideal abläuft (Kurz-Workflow)

Die Details stehen in `Regeln/REGELN_AUDITS.md` und `Regeln/AUDIT_CHECKLISTE.md`. Hier die Kurzform:

1. **Vorbereitung**

   * Scope klar definieren (z.B. „Sub-Routen-Generator zeigt keine Routen")

   * Relevante Dateien einsammeln (Backend + Frontend + ggf. DB/Infra)

2. **Analyse (ganzheitlich!)**

   * Backend-Logik + Frontend-Rendering + API-Kontrakt zusammen prüfen

   * Besonders: Response-Schema vs. Frontend-Erwartung (snake_case, Feldnamen)

3. **Diagnose**

   * **Root Cause klar benennen**, nicht nur Symptome

4. **Fix-Vorschläge mit Kontext**

   * Diffs pro Datei

   * Defensive Checks (Null-Checks, Array-Checks, Try/Except)

   * Verbesserte Logs (inkl. Korrelations-ID, Tour-IDs, etc.)

5. **Tests & Verifikation**

   * Mindestens **1 Backend-Test** + **1 Frontend-Test** vorschlagen

   * Ggf. konkrete `pytest`-/Browser-Commands nennen

6. **Dokumentation & ZIP**

   * Audit-Report nach `Regeln/REGELN_AUDITS.md` (Abschnitt 9)

   * Audit-ZIP nach Struktur aus `Regeln/REGELN_AUDITS.md` / `GLOBAL_STANDARDS.md`

---

## 6️⃣ Tests & Commands (Baseline)

Beispiele, die eine Audit-KI vorschlagen oder verwenden kann:

```bash
# Backend Syntax + Tests
python -m py_compile $(git ls-files "backend/*.py" "routes/*.py")
pytest -q

# Server lokal starten
python start_server.py
# Dann im Browser: http://localhost:8111/

# Health-Checks
curl http://localhost:8111/health
curl http://localhost:8111/health/osrm

# Optional: Audit-ZIP bauen
python tools/make_audit_zip.py
```

Frontend-Tests können z.B. als manuelle Schrittfolge beschrieben werden (Buttons klicken, erwartetes Verhalten, Konsole prüfen).

---

## 7️⃣ Sicherheit & Datenschutz

* **Keine echten Secrets in diesem Paket** (ENV ist sanitisiert).

* Audit-KI darf **niemals**:

  * reale API-Keys, Passwörter oder Tokens erzeugen oder loggen,

  * Konfiguration so umbauen, dass Secrets im Klartext im Code landen.

* Security-Fokus:

  * Input-Validierung (Backend + Frontend)

  * Fehler-Responses ohne Stacktrace nach außen

  * Logs ohne vollständige Adressen / personenbezogene Daten

Details: `Global/GLOBAL_STANDARDS.md` → Abschnitt „Security".

---

## 8️⃣ Erwartete Ausgabe einer Audit-KI

Ein gutes Audit auf Basis dieses Pakets sollte immer liefern:

1. **Executive Summary** – Was war kaputt, was wurde verbessert?

2. **Root Cause** – 1–3 Sätze, warum das Problem wirklich auftrat.

3. **Fix-Vorschläge** – Diffs pro Datei (Backend + Frontend, wenn betroffen).

4. **Tests** – Konkrete Vorschläge für Regressionstests.

5. **Lessons Learned** – Vorschlag für neuen Eintrag in `Regeln/LESSONS_LOG.md` (falls neuer Fehlertyp).

6. **Nächste Schritte** – Was als Nächstes gehärtet werden sollte.

---

## 9️⃣ Meta / Version

**Projekt:** FAMO TrafficApp 3.0

**Stack:** Python 3.10, FastAPI, Vanilla JS, SQLite

**Infra:** Proxmox-LXC, Docker (OSRM), Leaflet

**Stand:** {datetime.now().strftime('%Y-%m-%d')}

**Audit-Paket:** `{zip_name}`

Aktuellen Gesamtstatus immer in `DOKUMENTATION.md` / `STATUS_AKTUELL.md` nachlesen.
"""
    
    readme_path = PROJECT_ROOT / 'ZIP' / 'README_AUDIT_COMPLETE.md'
    readme_path.write_text(readme_content, encoding='utf-8')
    print(f"[OK] README erstellt: {readme_path}")

if __name__ == '__main__':
    # Erstelle Timestamp
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    zip_name = f'trafficapp_audit_complete_{timestamp}.zip'
    zip_path = PROJECT_ROOT / 'ZIP' / zip_name
    
    # Erstelle ZIP-Verzeichnis falls nicht vorhanden
    zip_path.parent.mkdir(exist_ok=True)
    
    # Erstelle ZIP
    create_audit_zip(zip_path)
    
    # Erstelle README
    create_readme(zip_path)
    
    print()
    print("=" * 60)
    print("[OK] CODE-AUDIT-PAKET ERSTELLT")
    print("=" * 60)
    print(f"[ZIP] Datei: {zip_path}")
    print(f"[DOC] README: ZIP/README_AUDIT_COMPLETE.md")
    print()
    print("Naechste Schritte:")
    print("1. Pruefe ZIP-Inhalt")
    print("2. Verwende fuer KI-Analyse")
    print("3. Alte ZIP-Dateien koennen archiviert werden")

