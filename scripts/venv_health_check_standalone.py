#!/usr/bin/env python3
"""
Standalone Venv Health Check - Kann unabhängig vom Server ausgeführt werden.
"""
import sys
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.utils.venv_health_check import run_venv_health_check

if __name__ == "__main__":
    print("=" * 70)
    print("VENV HEALTH CHECK (Standalone)")
    print("=" * 70)
    print()
    
    ok = run_venv_health_check(auto_fix=True)
    
    print()
    if ok:
        print("[OK] Venv ist gesund - Server kann gestartet werden")
        sys.exit(0)
    else:
        print("[FEHLER] Venv hat Probleme - bitte beheben")
        print()
        print("Empfehlungen:")
        print("  1. Venv aktivieren: .\\venv\\Scripts\\Activate.ps1")
        print("  2. Oder venv neu erstellen: .\\recreate_venv.ps1")
        sys.exit(1)

