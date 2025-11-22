#!/usr/bin/env python3
"""
Erstellt VOLLSTÄNDIGES Audit-ZIP mit ALLEN relevanten Dateien.
EINFACH: Alles flach ins ZIP, keine verschachtelten Strukturen.
"""
import zipfile
import os
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
ZIP_DIR = PROJECT_ROOT / "ZIP"
ZIP_DIR.mkdir(exist_ok=True)

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
zip_path = ZIP_DIR / f"AUDIT_COMPLETE_ALL_{timestamp}.zip"

# ALLE relevanten Verzeichnisse
DIRS_TO_SCAN = [
    "backend",
    "frontend",
    "db",
    "docs",
    "Regeln",
    "Global",
    "scripts",
]

# Datei-Endungen die INKLUDIERT werden
INCLUDED_EXTENSIONS = {
    '.py', '.html', '.js', '.css', '.md', '.sql', '.txt', '.json',
    '.yml', '.yaml', '.ps1', '.sh'
}

# Dateien die AUSGESCHLOSSEN werden
EXCLUDED_NAMES = {
    '__pycache__', '.git', 'venv', 'node_modules', '.pytest_cache',
    '*.pyc', '*.pyo', '*.db', '*.sqlite', '*.log', '*.tmp'
}

# Root-Level-Dateien
ROOT_FILES = [
    "README.md", "DOKUMENTATION.md", "PROJECT_PROFILE.md", "STATUS_AKTUELL.md",
    "requirements.txt", ".cursorrules", ".gitignore"
]

def should_exclude(path: Path) -> bool:
    """Prüft ob Datei ausgeschlossen werden soll."""
    # Prüfe Verzeichnis-Namen
    for part in path.parts:
        if part in EXCLUDED_NAMES:
            return True
        if part.startswith('.') and part not in {'.github', '.cursorrules', '.gitignore'}:
            return True
        if part.startswith('__'):
            return True
    
    # Prüfe Datei-Endung
    if path.suffix not in INCLUDED_EXTENSIONS:
        return False  # Nicht in Liste = nicht inkludieren
    
    # Prüfe spezifische Dateien
    if path.name in {'.env', 'secrets.env'}:
        return True
    
    return False

def collect_all_files():
    """Sammelt ALLE relevanten Dateien."""
    files = []
    seen_names = {}  # Dateiname -> Pfad (vermeide Duplikate)
    
    # Root-Level-Dateien
    for root_file in ROOT_FILES:
        file_path = PROJECT_ROOT / root_file
        if file_path.exists():
            files.append((file_path, root_file))
            seen_names[root_file] = file_path
    
    # Verzeichnisse durchsuchen
    for dir_name in DIRS_TO_SCAN:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            continue
        
        for root, dirs, filenames in os.walk(dir_path):
            # Filtere ausgeschlossene Verzeichnisse
            dirs[:] = [d for d in dirs if d not in EXCLUDED_NAMES and not d.startswith('.') and not d.startswith('__')]
            
            for filename in filenames:
                file_path = Path(root) / filename
                
                # Prüfe Ausschluss
                if should_exclude(file_path):
                    continue
                
                # Nur inkludierte Endungen
                if file_path.suffix not in INCLUDED_EXTENSIONS:
                    continue
                
                # Eindeutigen Dateinamen erstellen (mit Pfad-Präfix falls Duplikat)
                rel_path = file_path.relative_to(PROJECT_ROOT)
                # Erstelle eindeutigen Namen: verzeichnis_dateiname
                if filename in seen_names:
                    # Duplikat - verwende Pfad
                    unique_name = str(rel_path).replace('/', '_').replace('\\', '_')
                else:
                    # Einfacher Dateiname
                    unique_name = filename
                    seen_names[filename] = file_path
                
                files.append((file_path, unique_name))
    
    return files

def create_readme():
    """Erstellt README."""
    return f"""# VOLLSTÄNDIGES AUDIT-ZIP - FAMO TrafficApp 3.0

**Erstellt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Zweck:** Komplettes Audit mit ALLEN relevanten Dateien

---

## Inhalt

Dieses ZIP enthält ALLE relevanten Dateien des Projekts:

- Backend (Python)
- Frontend (HTML/JS/CSS)
- Datenbank (Schema, Migrationen)
- Dokumentation
- Regeln & Standards
- Scripts

**Alle Dateien sind FLACH im ZIP** - keine verschachtelten Strukturen.

---

## Bekannte Probleme

### 1. DB-Verwaltung Tab zeigt keinen Inhalt
- API funktioniert
- innerHTML wird gesetzt
- ABER: Tab-Inhalt bleibt unsichtbar
- Vermutlich Bootstrap `show` Klasse fehlt

### 2. Tour-Import Feature unvollständig
- DB-Migration vorhanden
- API-Endpunkte teilweise implementiert
- CSV-Parsing fehlt
- Geocoding-Worker fehlt
- Frontend fehlt

---

## Datei-Struktur

Alle Dateien sind direkt im ZIP-Root, keine Unterordner.

Bei Duplikaten: Dateiname enthält Pfad-Präfix (z.B. `backend_routes_api.py`)

---

**Erstellt für:** Externes Audit / KI-Entwicklung
"""

def main():
    """Hauptfunktion."""
    print(f"[AUDIT-ZIP] Erstelle VOLLSTÄNDIGES Audit-ZIP...")
    print()
    
    # Dateien sammeln
    files = collect_all_files()
    print(f"[AUDIT-ZIP] {len(files)} Dateien gefunden")
    
    # ZIP erstellen
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Dateien hinzufügen
        for file_path, unique_name in files:
            try:
                zipf.write(file_path, unique_name)
                if len(files) <= 50 or unique_name.endswith(('.md', '.html', '.py')):
                    print(f"  [OK] {unique_name}")
            except Exception as e:
                print(f"  [ERROR] {unique_name}: {e}")
        
        # README hinzufügen
        readme_content = create_readme()
        zipf.writestr("README_AUDIT.md", readme_content.encode('utf-8'))
        print(f"  [OK] README_AUDIT.md")
    
    # Statistik
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print()
    print(f"[OK] ZIP erstellt: {zip_path.name}")
    print(f"[OK] Groesse: {size_mb:.2f} MB")
    print(f"[OK] Dateien: {len(files) + 1}")
    
    return zip_path

if __name__ == "__main__":
    main()

