#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste die Firmenumzug-Lösung
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from backend.services.geocode import geocode_address

print("\n" + "="*80)
print("TEST: FIRMENUMZUG-LÖSUNG")
print("="*80 + "\n")

# Test-Adressen mit alten CAR-ART Adressen
test_addresses = [
    "CAR-ART GmbH, Bismarkstr. 63, 01257 Dresden",
    "CAR-ART GmbH, Bismarkstraße 63, 01257 Dresden", 
    "CAR-ART GmbH, Bismarkstr 63, 01257 Dresden"
]

print(f"[1/2] Teste {len(test_addresses)} alte CAR-ART Adressen...")

for i, address in enumerate(test_addresses, 1):
    print(f"\n[{i}/{len(test_addresses)}] Teste: {address}")
    
    # Geocoding mit AddressCorrector
    result = geocode_address(address)
    
    if result and result.get('lat') and result.get('lon'):
        print(f"   [OK] Gefunden: {result['lat']}, {result['lon']}")
        print(f"   Provider: {result.get('provider', 'unknown')}")
        print(f"   Korrektur: {result.get('correction_type', 'unknown')}")
    else:
        print(f"   [X] Nicht gefunden")

print(f"\n[2/2] ZUSAMMENFASSUNG")
print("="*80)
print("Die Firmenumzug-Lösung sollte automatisch:")
print("  - Alte CAR-ART Adressen erkennen")
print("  - Auf neue Adresse 'Löbtauer Str. 55, 01159 Dresden' umleiten")
print("  - Geocoding mit neuer Adresse durchführen")
print("  - Ergebnis in Cache speichern")

print("\n" + "="*80 + "\n")
