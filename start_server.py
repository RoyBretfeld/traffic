#!/usr/bin/env python3
"""
FAMO TrafficApp - Einfacher Server-Start
Löst das PowerShell-Problem durch direkten Python-Start
"""

import sys
import os
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Startup-Skript importieren (stellt DB-Schema sicher)
import app_startup  # noqa: F401

# Temp-Cleanup importieren und ausführen
from services.temp_cleanup import cleanup_old_temp_files, ensure_temp_dir
ensure_temp_dir()
cleanup_old_temp_files()

import uvicorn

if __name__ == "__main__":
    print("\n" + "="*60)
    print("   FAMO TrafficApp wird gestartet...")
    print("="*60)
    print(f"Server läuft auf: http://127.0.0.1:8111")
    print(f"Frontend UI:      http://127.0.0.1:8111")
    print(f"API Docs:         http://127.0.0.1:8111/docs")
    print(f"Beenden mit:      Ctrl+C")
    print("="*60 + "\n")

    try:
        uvicorn.run(
            "backend.app:app",  # Import-String für reload
            host="127.0.0.1",
            port=8111,
            reload=True,  # Automatischer Neustart bei Code-Änderungen
            log_level="info",
        )
    except KeyboardInterrupt:
        print("\n\nServer wurde beendet.")
    except Exception as e:
        print(f"\n\nFehler beim Starten des Servers: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
