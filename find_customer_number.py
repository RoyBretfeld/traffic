#!/usr/bin/env python3
"""
Suche Kundennummer für Johnsbacher Haupstr. 55
"""
import sys
from pathlib import Path
import glob

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict

def find_customer_number():
    """Suche Kundennummer für Johnsbacher Haupstr. 55"""
    print("🔍 Suche Kundennummer für: Johnsbacher Haupstr. 55, 01768 Glashütte")
    print("=" * 70)
    
    files = glob.glob('tourplaene/*.csv')
    found = False
    
    for f in files:
        try:
            result = parse_tour_plan_to_dict(f)
            customers = result.get('customers', [])
            
            for c in customers:
                addr = c.get('address', '')
                if 'Johnsbacher Haupstr. 55' in addr:
                    print(f"📁 Datei: {f}")
                    print(f"🔢 Kundennummer: {c.get('customer_number', 'UNBEKANNT')}")
                    print(f"🏢 Firma: {c.get('name', 'UNBEKANNT')}")
                    print(f"📍 Adresse: {addr}")
                    print(f"🏠 Street: {c.get('street', 'UNBEKANNT')}")
                    print(f"📮 PLZ: {c.get('postal_code', 'UNBEKANNT')}")
                    print(f"🏙️ City: {c.get('city', 'UNBEKANNT')}")
                    found = True
                    break
            
            if found:
                break
                
        except Exception as e:
            print(f"❌ Fehler bei {f}: {e}")
    
    if not found:
        print("❌ Adresse nicht gefunden!")

if __name__ == "__main__":
    find_customer_number()
