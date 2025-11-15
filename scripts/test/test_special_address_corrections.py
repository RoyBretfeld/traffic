#!/usr/bin/env python3
"""
Test spezielle Adress-Korrekturen
"""
import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.normalize import normalize_address

def test_special_address_corrections():
    """Teste spezielle Adress-Korrekturen"""
    print("🧪 Test spezielle Adress-Korrekturen:")
    print("=" * 50)
    
    test_cases = [
        "Hauptstr. 1, 01809 Heidenau",
        "Hauptstr. 9a, 01728 Bannewitz",
        "Hauptstr. 70, 01705 Freital",
        "Hauptstraße 1, 01809 Heidenau",  # Sollte unverändert bleiben
        "Hauptstrasse 9a, 01728 Bannewitz",  # Sollte unverändert bleiben
        "Hauptstraße 70, 01705 Freital"  # Sollte unverändert bleiben
    ]
    
    for i, addr in enumerate(test_cases, 1):
        print(f"{i}. Vorher:  {addr}")
        print(f"   Nachher: {normalize_address(addr)}")
        print()

if __name__ == "__main__":
    test_special_address_corrections()
