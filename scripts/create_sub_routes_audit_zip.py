#!/usr/bin/env python3
"""
Erstellt ein ZIP-Archiv mit allen Dateien für den Sub-Routen-Generator
und eine umfassende Audit-Dokumentation.
"""
import zipfile
import os
from datetime import datetime
from pathlib import Path

# Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent
ZIP_DIR = PROJECT_ROOT / "ZIP"

# Relevante Dateien für Sub-Routen-Generator
FILES_TO_INCLUDE = [
    # Frontend
    "frontend/index.html",
    
    # Backend - Hauptdateien
    "routes/workflow_api.py",
    "routes/engine_api.py",
    
    # Services
    "services/llm_optimizer.py",
    
    # Dokumentation
    "docs/SUB_ROUTES_GENERATOR_LOGIC.md",
    "docs/SPLITTING_INFO_FLOW.md",
    "docs/AUDIT_SUB_ROUTEN_GENERATOR.md",  # Audit-Dokumentation
    
    # Tests
    "tests/test_subroutes_500_fix.py",
    
    # Scripts
    "scripts/test_w07_split.py",
    "scripts/create_sub_routes_audit_zip.py",  # Dieses Skript selbst
]

def create_zip():
    """Erstellt ZIP-Archiv mit allen relevanten Dateien."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = ZIP_DIR / f"SUB_ROUTEN_GENERATOR_AUDIT_{timestamp}.zip"
    
    # Erstelle ZIP-Verzeichnis falls nicht vorhanden
    ZIP_DIR.mkdir(exist_ok=True)
    
    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Füge alle Dateien hinzu
        for file_path in FILES_TO_INCLUDE:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                # Speichere mit relativem Pfad
                zipf.write(full_path, file_path)
                print(f"[OK] {file_path}")
            else:
                print(f"[FEHLT] {file_path} (nicht gefunden)")
    
    print(f"\n[OK] ZIP erstellt: {zip_filename}")
    return zip_filename

if __name__ == "__main__":
    create_zip()

