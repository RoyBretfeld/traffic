#!/usr/bin/env python3
"""
Test CRM-basierte Adress-Korrekturen
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from common.normalize import normalize_address

def test_crm_corrections():
    """Teste CRM-basierte Adress-Korrekturen"""
    print("🧪 Test CRM-basierte Adress-Korrekturen:")
    print("=" * 60)
    
    test_cases = [
        # Kunde 40700: KFZ-Meisterbetrieb Löscher
        ("Hauptstr. 122, 01816 Bad Gottleuba-Berggießhübel", "Hauptstraße 122, 01816 Bad Gottleuba-Berggießhübel"),
        
        # Kunde 40749: Andreas Ebert
        ("Hauptstr. 16, 01816 Bad Gottleuba-Berggießhübel", "Hauptstraße 16, 01816 Bad Gottleuba-Berggießhübel"),
        
        # Kunde 40778: Schütze Gersdorf  
        ("Gersdorf 43, 01819 Bahretal", "Gersdorf 43, 01819 Bahretal OT Gersdorf"),
        
        # Kunde 5128: Auto Service Meusel
        ("Alte Str. 33, 01768 Glashütte", "Alte Str. 33, 01768 Glashütte OT Hirschbach"),
        
        # Kunde 1077: Motoren-Frech GbR
        ("Hohensteiner Str. 101, 09212 Limbach-O.", "Hohensteiner Str. 101, 09212 Limbach-O./OT Pleißa"),
        
        # Kunde 4514: Karsten Noack
        ("Reinberger Dorfstraße 6a, 01744 Dippoldiswalde", "Reinberger Dorfstraße 6a, 01744 Dippoldiswalde/OT Reinberg"),
        
        # Kunde 5675: Metallbau Kummer
        ("Johnsbacher Hauptstr. 55, 01768 Glashütte", "Johnsbacher Hauptstraße 55, 01768 Glashütte"),
        
        # Kunde 5646: Dippser-Auto-Ecke (bereits korrekt)
        ("Bergstraße 93, 01744 Dippoldiswalde OT Seifersdorf", "Bergstraße 93, 01744 Dippoldiswalde OT Seifersdorf"),
        
        # Zusätzliche Tests für bereits korrigierte Adressen
        ("Hauptstr. 1, 01809 Heidenau", "Hauptstraße 1, 01809 Heidenau"),
        ("Hauptstr. 9a, 01728 Bannewitz", "Hauptstrasse 9a, 01728 Bannewitz/OT Possendorf"),
        ("Hauptstr. 70, 01705 Freital", "Hauptstraße 70, 01705 Freital"),
    ]
    
    for i, (input_addr, expected) in enumerate(test_cases, 1):
        result = normalize_address(input_addr)
        status = "✅" if result == expected else "❌"
        print(f"{i}. {status} {input_addr}")
        print(f"   → {result}")
        if result != expected:
            print(f"   ❌ Erwartet: {expected}")
        print()

if __name__ == "__main__":
    test_crm_corrections()
