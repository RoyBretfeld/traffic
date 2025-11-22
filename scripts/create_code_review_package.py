#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt ein Code-Review-Paket für externe Code-Reviews.
Enthält alle relevanten Dateien, Dokumentation und Beschreibung.
"""
import zipfile
import os
import shutil
import sys
import io
from pathlib import Path
from datetime import datetime

# Setze UTF-8 Encoding für Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent

def create_code_review_package():
    """Erstellt ein Code-Review-Paket."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_zip = PROJECT_ROOT / f"CODE_REVIEW_PACKAGE_{timestamp}.zip"
    
    print("=" * 60)
    print("Code-Review-Paket erstellen")
    print("=" * 60)
    print()
    
    # Wichtige Verzeichnisse und Dateien
    included_paths = [
        # Dokumentation
        "docs",
        "Regeln",
        "Global",
        "README.md",
        "DOKUMENTATION.md",
        "PROJECT_PROFILE.md",
        "CHANGELOG.md",
        "README_AUDIT_COMPLETE.md",
        
        # Code
        "backend",
        "frontend",
        "routes",
        "services",
        "repositories",
        "db",
        "common",
        
        # Tests
        "tests",
        
        # Scripts
        "scripts",
        
        # Konfiguration
        "requirements.txt",
        ".cursorrules",
        "pyproject.toml",
        ".github",
        
        # Heutige Änderungen
        "docs/AENDERUNGEN_2025-11-20.md",
    ]
    
    # Ausgeschlossene Verzeichnisse
    excluded_dirs = {
        '__pycache__', '.git', 'venv', 'node_modules',
        'data', 'logs', 'backups', 'ZIP', 'temp'
    }
    
    # Ausgeschlossene Datei-Endungen
    excluded_extensions = {
        '.pyc', '.pyo', '.pyd', '.db', '.sqlite3', '.log', '.tmp', '.zip'
    }
    
    file_count = 0
    total_size = 0
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Erstelle README für Code-Review
        readme_content = create_review_readme()
        zipf.writestr("CODE_REVIEW_README.md", readme_content)
        print("[OK] CODE_REVIEW_README.md erstellt")
        
        # Füge Dateien hinzu
        for path_str in included_paths:
            path = PROJECT_ROOT / path_str
            if not path.exists():
                print(f"[WARN] Pfad nicht gefunden: {path_str}")
                continue
            
            if path.is_file():
                # Einzelne Datei
                try:
                    zipf.write(path, path_str)
                    file_count += 1
                    total_size += path.stat().st_size
                except Exception as e:
                    print(f"[WARN] Fehler bei {path_str}: {e}")
            elif path.is_dir():
                # Verzeichnis rekursiv
                for root, dirs, files in os.walk(path):
                    # Filtere ausgeschlossene Verzeichnisse
                    dirs[:] = [d for d in dirs if d not in excluded_dirs and not d.startswith('.')]
                    
                    root_path = Path(root)
                    for file in files:
                        file_path = root_path / file
                        
                        # Prüfe Ausschluss
                        if file_path.suffix in excluded_extensions:
                            continue
                        
                        # Relativer Pfad
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
    print("=" * 60)
    print("Fertig!")
    print(f"[OK] {file_count} Dateien gepackt")
    print(f"[OK] Groesse: {total_size / 1024 / 1024:.2f} MB")
    print(f"[OK] ZIP-Groesse: {output_zip.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"[OK] Datei: {output_zip}")
    print("=" * 60)
    
    return output_zip

def create_review_readme():
    """Erstellt README für Code-Review."""
    return """# Code-Review-Paket – FAMO TrafficApp 3.0

**Erstellt:** 2025-11-20  
**Zweck:** Externes Code-Review

---

## 📋 Projekt-Übersicht

**FAMO TrafficApp 3.0** ist eine Tourenplanungs- und Routenoptimierungs-Anwendung für die FAMO Logistik.

### Stack
- **Backend:** Python 3.10, FastAPI, SQLite
- **Frontend:** Vanilla JavaScript, HTML5, Leaflet (Karten)
- **Infrastruktur:** Proxmox-LXC, Docker (OSRM), SQLite
- **Routing:** OSRM (Open Source Routing Machine)

### Hauptfeatures
- Touren-Workflow (Upload → Geocoding → Optimierung)
- Sub-Routen-Generator (automatische Aufteilung großer Touren)
- OSRM-Routing-Integration
- Live-Traffic-Daten (Blitzer, Hindernisse)
- KI-Integration für Code-Verbesserungen

---

## 🎯 Code-Review-Fokus

### Heutige Änderungen (2025-11-20)

Siehe `docs/AENDERUNGEN_2025-11-20.md` für vollständige Dokumentation.

**Hauptthemen:**
1. **CI-Pipeline-Fix:** pytest.config veraltet → behoben
2. **Kartenansicht:** Karte scrollt jetzt zur ausgewählten Route
3. **Blitzer-System:** Blitzer werden korrekt für verschiedene Kartenbereiche geladen
4. **Test-Blitzer:** Entfernt (verwirrend)

### Kritische Bereiche für Review

1. **Backend:**
   - `backend/services/live_traffic_data.py` - Blitzer-Cache-Logik
   - `tests/test_ki_codechecker.py` - pytest-Integration

2. **Frontend:**
   - `frontend/index.html` - Kartenansicht, Route-Scrolling, Blitzer-Anzeige

3. **Tests:**
   - `tests/conftest.py` - pytest-Konfiguration

---

## 📚 Dokumentation

### Wichtige Dokumente (in dieser Reihenfolge lesen)

1. **`Global/GLOBAL_STANDARDS.md`** - Globale Arbeitsregeln
2. **`PROJECT_PROFILE.md`** - Projektprofil, Stack, Infrastruktur
3. **`Regeln/STANDARDS_QUICK_REFERENCE.md`** - Schnellreferenz
4. **`Regeln/REGELN_AUDITS.md`** - Audit-Regeln
5. **`Regeln/AUDIT_CHECKLISTE.md`** - 9-Punkte-Checkliste
6. **`docs/AENDERUNGEN_2025-11-20.md`** - Heutige Änderungen

### Weitere Dokumentation

- `DOKUMENTATION.md` - Index aller Dokumente
- `README.md` - Projekt-README
- `CHANGELOG.md` - Versionshistorie

---

## 🔍 Review-Schwerpunkte

### 1. Code-Qualität
- [ ] Defensive Programmierung (Null-Checks, Array-Checks)
- [ ] Fehlerbehandlung (Try/Except, Fallbacks)
- [ ] Logging (ausreichend, nicht zu viel)
- [ ] Code-Duplikation

### 2. API-Kontrakt
- [ ] Backend-Response-Schema konsistent
- [ ] Frontend erwartet korrekte Felder
- [ ] Fehler-Responses strukturiert

### 3. Performance
- [ ] Cache-Verhalten korrekt
- [ ] Keine unnötigen API-Calls
- [ ] Effiziente Datenbank-Abfragen

### 4. Tests
- [ ] Tests decken kritische Pfade ab
- [ ] Tests sind deterministisch
- [ ] Keine fehlenden Edge-Cases

### 5. Sicherheit
- [ ] Keine Secrets im Code
- [ ] Input-Validierung vorhanden
- [ ] Fehler-Responses ohne Stacktraces

---

## 🧪 Tests ausführen

```bash
# Alle Tests
pytest -v

# Nur bestimmte Tests
pytest tests/test_ki_codechecker.py -v

# Mit Coverage
pytest --cov=backend --cov=services
```

---

## 🚀 Setup (für lokales Testen)

```bash
# Dependencies installieren
pip install -r requirements.txt

# Server starten
python start_server.py

# Browser öffnen
# http://localhost:8111/
```

---

## 📝 Review-Format

Bitte strukturieren Sie Ihr Review nach:

1. **Executive Summary** - Was ist gut, was sollte verbessert werden?
2. **Kritische Probleme** - Sicherheit, Performance, Bugs
3. **Verbesserungsvorschläge** - Code-Qualität, Architektur
4. **Positive Aspekte** - Was ist gut gelöst?
5. **Nächste Schritte** - Empfohlene Maßnahmen

---

## 🔗 Kontakt & Fragen

Bei Fragen zur Architektur oder Implementierung:
- Siehe `PROJECT_PROFILE.md` für Projekt-Kontext
- Siehe `docs/AENDERUNGEN_2025-11-20.md` für heutige Änderungen
- Siehe `Regeln/STANDARDS.md` für Coding-Standards

---

**Vielen Dank für das Review!** 🙏
"""

if __name__ == "__main__":
    create_code_review_package()

