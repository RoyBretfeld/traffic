#!/usr/bin/env python3
"""
Fuegt Roswitha mit korrekter Adresse zur Datenbank hinzu
"""
import sys
sys.path.insert(0, '.')

from backend.services.geocode import geocode_address
from backend.db.dao import Kunde, upsert_kunden

# Adresse geocoden
address = "Wilsdruffer Str. 65, 01705 Freital"
name = "41 Roswitha"

print(f"\n{'='*60}")
print(f"GEOCODING: {name}")
print(f"Adresse: {address}")
print(f"{'='*60}\n")

result = geocode_address(address)

if result and result.get('lat') and result.get('lon'):
    print(f"[OK] Koordinaten gefunden:")
    print(f"    Lat: {result['lat']}")
    print(f"    Lon: {result['lon']}")
    print(f"    Provider: {result.get('provider', 'unknown')}")
    
    # In Datenbank speichern
    kunde = Kunde(
        id=None,
        name=name,
        adresse=address,
        lat=result['lat'],
        lon=result['lon']
    )
    
    print(f"\n[SAVE] Speichere in Datenbank...")
    upsert_kunden([kunde])
    print(f"[SUCCESS] {name} erfolgreich gespeichert!")
else:
    print(f"[FEHLER] Geocoding fehlgeschlagen fuer: {address}")
    sys.exit(1)

print(f"\n{'='*60}\n")

