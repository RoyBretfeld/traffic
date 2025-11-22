#!/usr/bin/env python3
"""
Erstellt Audit-ZIP für DB-Verwaltung Fehler und Tour-Import Feature.
EINFACH: Alle Dateien flach ins ZIP, keine komplizierten Strukturen.
"""
import zipfile
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
ZIP_DIR = PROJECT_ROOT / "ZIP"
ZIP_DIR.mkdir(exist_ok=True)

# Timestamp für Dateinamen
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
zip_path = ZIP_DIR / f"AUDIT_DB_VERWALTUNG_TOUR_IMPORT_{timestamp}.zip"

# ALLE Dateien - einfach und direkt
FILES_TO_INCLUDE = [
    # Fehler-Beschreibungen
    "docs/AUDIT_FEHLER_DB_VERWALTUNG_2025-11-19.md",
    "docs/AUDIT_TOUR_IMPORT_FEATURE_2025-11-19.md",
    "docs/AUDIT_DB_VERWALTUNG_TOUR_IMPORT_2025-11-19.md",  # Zusammenfassung
    
    # DB-Verwaltung Fehler
    "frontend/admin.html",
    "backend/routes/db_management_api.py",
    
    # Tour-Import Feature
    "backend/routes/tour_import_api.py",
    "backend/app_setup.py",
    "db/migrations/020_import_batches.sql",
    "db/schema.py",
    
    # Dokumentation
    "Regeln/LESSONS_LOG.md",
    "PROJECT_PROFILE.md",
    "STATUS_AKTUELL.md",
    "README.md",
    "DOKUMENTATION.md",
    "Regeln/STANDARDS.md",
    "Regeln/CURSOR_WORKFLOW.md",
    "Global/GLOBAL_STANDARDS.md",
]

def collect_files():
    """Sammelt alle Dateien - einfach und direkt."""
    files = []
    
    for file_path_str in FILES_TO_INCLUDE:
        file_path = PROJECT_ROOT / file_path_str
        if file_path.exists():
            files.append(file_path)
        else:
            print(f"[WARN] Datei nicht gefunden: {file_path_str}")
    
    return files

def create_readme():
    """Erstellt README für das Audit-ZIP."""
    return f"""# Audit-ZIP: DB-Verwaltung Fehler & Tour-Import Feature

**Erstellt:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Zweck:** Externes Audit für zwei kritische Probleme

---

## 📋 Inhalt dieses ZIPs

### 1. 🔴 KRITISCHER FEHLER: DB-Verwaltung Tab zeigt keinen Inhalt

**Problem:** 
- API-Aufrufe funktionieren korrekt
- innerHTML wird gesetzt (1663, 15184 Zeichen)
- ABER: Tab-Inhalt bleibt komplett weiß/leer

**Dateien:**
- `docs/AUDIT_FEHLER_DB_VERWALTUNG_2025-11-19.md` - Vollständige Fehler-Beschreibung
- `frontend/admin.html` - Frontend-Code (Zeile 2208-2343)
- `backend/routes/db_management_api.py` - Backend API-Endpunkte
- `Regeln/LESSONS_LOG.md` - Eintrag 2025-11-19

**Status:** ❌ NICHT GELÖST

---

### 2. 🟡 FEATURE IN ENTWICKLUNG: Tour-Import & Vorladen

**Problem:**
- Grundstruktur erstellt (DB-Migration, API-Endpunkte)
- CSV-Parsing, Geocoding-Worker und Frontend fehlen noch

**Dateien:**
- `docs/AUDIT_TOUR_IMPORT_FEATURE_2025-11-19.md` - Feature-Beschreibung
- `backend/routes/tour_import_api.py` - API-Endpunkte (teilweise implementiert)
- `db/migrations/020_import_batches.sql` - DB-Migration
- `db/schema.py` - Migration-Integration
- `backend/app_setup.py` - Router-Registrierung

**Status:** 🚧 IN ENTWICKLUNG

---

## 🎯 Was die externe KI tun soll

### Für DB-Verwaltung Fehler:
1. Console-Logs analysieren (innerHTML wird gesetzt, aber nichts sichtbar)
2. CSS/Visibility-Problem identifizieren
3. Parent-Container prüfen (display: none, visibility: hidden)
4. Bootstrap Tab-Pane Rendering prüfen
5. Fix vorschlagen und implementieren

### Für Tour-Import Feature:
1. CSV-Parsing implementieren (bestehenden Parser nutzen)
2. Geocoding-Worker für Hintergrund-Verarbeitung
3. Frontend-Seite `tour-import.html` erstellen
4. Navigation im Admin-Bereich erweitern
5. Import-Status und Füllstände-Anzeige

---

## 📁 Projekt-Struktur

- `backend/` - Python Backend (FastAPI)
- `frontend/` - HTML/JS/CSS Frontend
- `db/` - Datenbank-Schema und Migrationen
- `docs/` - Dokumentation
- `Regeln/` - Projekt-Standards und Workflows

---

## 🔗 Wichtige Dokumentation

- `PROJECT_PROFILE.md` - Projekt-Übersicht
- `STATUS_AKTUELL.md` - Aktueller System-Status
- `Regeln/STANDARDS.md` - Code-Standards
- `Regeln/CURSOR_WORKFLOW.md` - Workflow-Prozess

---

**Erstellt für:** Externes Audit / KI-Entwicklung
**Version:** 1.0
"""

def main():
    """Hauptfunktion: Erstellt das Audit-ZIP."""
    print(f"[AUDIT-ZIP] Erstelle Audit-ZIP: {zip_path.name}")
    print()
    
    # Dateien sammeln
    files = collect_files()
    print(f"[AUDIT-ZIP] {len(files)} Dateien gefunden")
    
    # ZIP erstellen - ALLES FLACH, keine verschachtelten Pfade
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Dateien hinzufügen - nur Dateiname, kein Pfad
        for file_path in files:
            file_name = file_path.name  # Nur Dateiname, kein Pfad!
            try:
                zipf.write(file_path, file_name)
                print(f"  [OK] {file_name}")
            except Exception as e:
                print(f"  [ERROR] Fehler bei {file_name}: {e}")
        
        # README hinzufügen
        readme_content = create_readme()
        zipf.writestr("README_AUDIT.md", readme_content.encode('utf-8'))
        print(f"  [OK] README_AUDIT.md")
    
    # Statistik
    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print()
    print(f"[OK] ZIP erstellt: {zip_path}")
    print(f"[OK] Größe: {size_mb:.2f} MB")
    print(f"[OK] Dateien: {len(files) + 1}")  # +1 für README
    
    return zip_path

if __name__ == "__main__":
    main()

