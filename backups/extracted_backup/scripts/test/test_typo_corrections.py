#!/usr/bin/env python3
"""
Test Schreibfehler-Korrekturen
"""
import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.normalize import normalize_address

def test_typo_corrections():
    """Teste Schreibfehler-Korrekturen"""
    print("🧪 Test Schreibfehler-Korrekturen:")
    print("=" * 50)
    
    test_cases = [
        "Johnsbacher Haupstr. 55, 01768 Glashütte",
        "Hauptstrasse 9a, 01728 Bannewitz", 
        "Hauptstraße 123, 01069 Dresden",
        "Alte Str. 33, 01768 Glashütte OT Hirschbach",
        "Gersdorf 43, 01819 Bahretal OT Gersdorf"
    ]
    
    for i, addr in enumerate(test_cases, 1):
        print(f"{i}. Vorher:  {addr}")
        print(f"   Nachher: {normalize_address(addr)}")
        print()

if __name__ == "__main__":
    test_typo_corrections()
