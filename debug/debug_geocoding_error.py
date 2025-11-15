#!/usr/bin/env python3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.geocode import geocode_address

def test_geocoding_error():
    """Teste den spezifischen Geocoding-Fehler"""
    
    # Test-Adressen
    test_addresses = [
        "Schulstraße 25, 01468 Moritzburg (OT Boxdorf)",
        "Rundteil 7b, 01728 Bannewitz OT Possendorf",
        "Möglitztalstraße 10, 01773 Altenberg OT Bärenstein"
    ]
    
    for address in test_addresses:
        print(f"\nTeste Adresse: {address}")
        try:
            result = geocode_address(address)
            if result:
                print(f"  OK: {result}")
            else:
                print(f"  Kein Ergebnis")
        except Exception as e:
            print(f"  ERROR: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_geocoding_error()
