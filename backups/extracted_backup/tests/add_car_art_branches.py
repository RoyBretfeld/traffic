#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Füge beide CAR-ART Filialen in die Datenbank hinzu
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from backend.services.geocode import geocode_address
from backend.db.dao import Kunde, upsert_kunden

print("\n" + "="*80)
print("CAR-ART GMBH - BEIDE FILIALEN HINZUFÜGEN")
print("="*80 + "\n")

# Beide CAR-ART Filialen
car_art_branches = [
    {
        'name': "CAR-ART GmbH",
        'address': "Bismarkstr. 63, 01257 Dresden",
        'branch': "Filiale 1 (Bismarkstraße)"
    },
    {
        'name': "CAR-ART GmbH", 
        'address': "Löbtauer Str. 55, 01159 Dresden",
        'branch': "Filiale 2 (Löbtauer Straße)"
    }
]

print(f"[1/2] Füge {len(car_art_branches)} CAR-ART Filialen hinzu...")

successful = []
failed = []

for i, branch in enumerate(car_art_branches, 1):
    print(f"\n[{i}/{len(car_art_branches)}] {branch['branch']}")
    print(f"   Adresse: {branch['address']}")
    
    # Geocoding versuchen
    result = geocode_address(branch['address'])
    
    if result and result.get('lat') and result.get('lon'):
        print(f"   [OK] Gefunden: {result['lat']}, {result['lon']}")
        print(f"   Provider: {result.get('provider', 'unknown')}")
        
        successful.append(Kunde(
            id=None,
            name=branch['name'],
            adresse=branch['address'],
            lat=result['lat'],
            lon=result['lon']
        ))
    else:
        print(f"   [X] Nicht gefunden")
        failed.append(branch)

print(f"\n[2/2] SPEICHERE IN DATENBANK")
print("="*80)

if successful:
    print(f"\n[SAVE] {len(successful)} Filialen werden gespeichert...")
    upsert_kunden(successful)
    print(f"[OK] {len(successful)} Filialen gespeichert!")

if failed:
    print(f"\n[FAILED] {len(failed)} Filialen konnten nicht geocodet werden:")
    for branch in failed:
        print(f"  - {branch['branch']}: {branch['address']}")

print(f"\n{'='*80}")
print("ZUSAMMENFASSUNG:")
print(f"  Erfolgreich: {len(successful)}")
print(f"  Fehlgeschlagen: {len(failed)}")
print(f"  CAR-ART GmbH hat jetzt {len(successful)} Filialen in der DB!")
print("="*80 + "\n")
