#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste die reine Adresse ohne Firmenname
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from backend.services.geocode import geocode_address

print("\n" + "="*80)
print("TEST: REINE ADRESSE OHNE FIRMENNAME")
print("="*80 + "\n")

# Test nur die reine Adresse
pure_address = "Löbtauer Str. 55, 01159 Dresden"

print(f"Teste reine Adresse: {pure_address}")

result = geocode_address(pure_address)

if result and result.get('lat') and result.get('lon'):
    print(f"[OK] Gefunden: {result['lat']}, {result['lon']}")
    print(f"Provider: {result.get('provider', 'unknown')}")
else:
    print(f"[X] Nicht gefunden")

print("\n" + "="*80 + "\n")
