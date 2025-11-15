#!/usr/bin/env python3
"""
Test OT-Entfernung in der Normalisierung
"""
import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.normalize import normalize_address

def test_ot_removal():
    """Teste OT-Entfernung"""
    print("🧪 Test OT-Entfernung:")
    print("=" * 50)
    
    test_cases = [
        "Alte Str. 33, 01768 Glashütte OT Hirschbach",
        "Gersdorf 43, 01819 Bahretal OT Gersdorf", 
        "Schulstraße 25, 01468 Moritzburg (OT Boxdorf)",
        "Kertitzer Str. 7, 04509 Delitzsch / OT Schenkenberg",
        "Hauptstr. 11, 01728 Bannewitz / OT Possendorf"
    ]
    
    for i, addr in enumerate(test_cases, 1):
        print(f"{i}. Vorher:  {addr}")
        print(f"   Nachher: {normalize_address(addr)}")
        print()

if __name__ == "__main__":
    test_ot_removal()
