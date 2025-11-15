#!/usr/bin/env python3
"""
Erstellt ein vollständiges Audit-Paket für den Server-Start-Fehler.
Sammelt alle relevanten Dateien und erstellt eine detaillierte Fehlerbeschreibung.
"""

import zipfile
import os
from datetime import datetime
from pathlib import Path

# Projekt-Root
PROJECT_ROOT = Path(__file__).parent.parent
ZIP_DIR = PROJECT_ROOT / "Zip"
ZIP_DIR.mkdir(exist_ok=True)

# Relevante Dateien für Server-Start-Fehler
FILES_TO_INCLUDE = [
    # Hauptdateien
    "backend/app.py",
    "start_server.py",
    "app_startup.py",
    
    # Middleware & Error Handling
    "backend/core/error_handlers.py",
    "backend/middlewares/trace_id.py",
    "backend/middlewares/error_envelope.py",
    
    # Config & Setup
    "backend/config.py",
    "backend/__init__.py",
    
    # Debug Routes
    "backend/debug/__init__.py",
    "backend/debug/routes.py",
    
    # Health Routes
    "backend/routes/health.py",
    "backend/routes/debug_health.py",
    
    # Utils
    "backend/utils/encoding_guards.py",
    
    # DB Schema
    "db/schema.py",
    "db/core.py",
    
    # Logging
    "backend/utils/json_logging.py",
    
    # Dokumentation
    "README.md",
    "requirements.txt",
]

def create_audit_zip():
    """Erstellt ZIP-Archiv mit allen relevanten Dateien."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename = ZIP_DIR / f"SERVER_STARTUP_AUDIT_{timestamp}.zip"
    
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
        
        # Füge auch die Audit-Dokumentation hinzu
        audit_doc = PROJECT_ROOT / "Zip" / "FEHLER_AUDIT_APP_NAMEERROR_2025-11-10.md"
        if audit_doc.exists():
            zipf.write(audit_doc, "FEHLER_AUDIT_APP_NAMEERROR_2025-11-10.md")
            print(f"[OK] FEHLER_AUDIT_APP_NAMEERROR_2025-11-10.md")
    
    print(f"\n[OK] ZIP erstellt: {zip_filename}")
    return zip_filename

if __name__ == "__main__":
    create_audit_zip()

