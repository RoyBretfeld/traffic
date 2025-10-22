#!/usr/bin/env python3
"""
Test der reparierten OT-Normalisierung
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common.normalize import normalize_address

def test_ot_fix():
    """Teste die reparierte OT-Normalisierung"""
    print(f"🧪 Test reparierte OT-Normalisierung:")
    print("=" * 60)
    
    test_cases = [
        # Doppelte OT-Suffixe
        "Gersdorf 43, 01819 Bahretal OT Gersdorf OT Gersdorf",
        "Alte Str. 33, 01768 Glashütte OT Hirschbach OT Hirschbach", 
        "Hohensteiner Str. 101, 09212 Limbach-O./OT Pleißa.",
        
        # Normale Fälle (sollten unverändert bleiben)
        "Gersdorf 43, 01819 Bahretal OT Gersdorf",
        "Alte Str. 33, 01768 Glashütte OT Hirschbach",
        "Hohensteiner Str. 101, 09212 Limbach-O./OT Pleißa",
        
        # Fälle ohne OT (sollten OT bekommen)
        "Gersdorf 43, 01819 Bahretal",
        "Alte Str. 33, 01768 Glashütte",
        "Hohensteiner Str. 101, 09212 Limbach-O.",
    ]
    
    for i, addr in enumerate(test_cases, 1):
        result = normalize_address(addr)
        print(f"{i:2d}. Vorher:  {addr}")
        print(f"    Nachher: {result}")
        print()

if __name__ == "__main__":
    test_ot_fix()
