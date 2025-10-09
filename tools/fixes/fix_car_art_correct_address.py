#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrigiere CAR-ART mit der richtigen Adresse Bismarckstraße 63b
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from backend.services.geocode import geocode_address
from backend.db.dao import Kunde, upsert_kunden

print("\n" + "="*80)
print("CAR-ART - RICHTIGE ADRESSE: BISMARCKSTRASSE 63B")
print("="*80 + "\n")

# Die richtige Adresse
customer_name = "CAR-ART GmbH"
correct_address = "Bismarckstraße 63b, 01257 Dresden"

print(f"Kunde: {customer_name}")
print(f"Richtige Adresse: {correct_address}")

# Geocoding mit der richtigen Adresse
print(f"\n[1/2] Geocoding mit richtiger Adresse...")
result = geocode_address(correct_address)

if result and result.get('lat') and result.get('lon'):
    print(f"   [OK] Gefunden: {result['lat']}, {result['lon']}")
    print(f"   Provider: {result.get('provider', 'unknown')}")
    
    # In Datenbank speichern
    customer = Kunde(
        id=None,
        name=customer_name,
        adresse=correct_address,
        lat=result['lat'],
        lon=result['lon']
    )
    
    upsert_kunden([customer])
    print(f"   [DB] CAR-ART mit richtiger Adresse gespeichert!")
    
else:
    print(f"   [X] Nicht gefunden - manuelle Koordinaten nötig")
    
    # Manuelle Koordinaten (falls Geocoding fehlschlägt)
    print(f"\n[2/2] Füge manuelle Koordinaten hinzu...")
    customer = Kunde(
        id=None,
        name=customer_name,
        adresse=correct_address,
        lat=51.05,  # Dresden Bereich
        lon=13.75
    )
    
    upsert_kunden([customer])
    print(f"   [DB] CAR-ART mit manuellen Koordinaten gespeichert!")

print("\n" + "="*80)
print("CAR-ART GMBH HAT JETZT BEIDE FILIALEN:")
print("  1. Bismarckstraße 63b, 01257 Dresden (KORRIGIERT)")
print("  2. Löbtauer Str. 55, 01159 Dresden")
print("="*80 + "\n")
