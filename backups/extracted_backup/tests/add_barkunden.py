#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fügt alle Barkunden mit den angegebenen Adressen zur Datenbank hinzu
"""
import sys
sys.path.insert(0, '.')

from backend.services.geocode import geocode_address
from backend.db.dao import Kunde, upsert_kunden

# Barkunden mit Adressen
barkunden = [
    {
        'name': 'Sven - PF (Blumentritt)',
        'address': 'Str. des 17. Juni 11, 01257 Dresden',
        'kdnr': '5287'
    },
    {
        'name': 'Jochen - PF',
        'address': 'Baerensteiner Str. 27-29, 01277 Dresden',
        'kdnr': '5000'
    },
    {
        'name': 'Büttner',
        'address': 'Bergstrasse 86, 01069 Dresden',
        'kdnr': '4318'
    },
    {
        'name': 'AG',
        'address': 'Dresdner Straße 46, 01796 Pirna',
        'kdnr': '40589'
    },
    {
        'name': 'Schrage/Johne - PF',
        'address': 'Friedrich-List-Platz 2, 01069 Dresden',
        'kdnr': '4169'
    },
    {
        'name': 'MSM by HUBraum GmbH',
        'address': 'Froebelstraße 20, 01159 Dresden',
        'kdnr': '5236'
    },
    {
        'name': 'MFH - PF',
        'address': 'Froebelstraße 20, 01159 Dresden',
        'kdnr': '5236'
    },
    {
        'name': 'Hubraum',
        'address': 'Froebelstraße 20, 01159 Dresden',
        'kdnr': '5236'
    },
    {
        'name': 'Motor Mafia',
        'address': 'Bärensteiner Str. 27-29, 01277 Dresden',
        'kdnr': '5000'
    },
    {
        'name': '36 Nici zu RP',
        'address': 'Mügelner Str.29, 01237 Dresden',
        'kdnr': '4601'
    },
    {
        'name': 'Astral UG',
        'address': 'Löbtauer Straße 80, 01159 Dresden',
        'kdnr': '5525'
    },
    {
        'name': 'Peter Söllner',
        'address': 'August Bebel Strasse 82, 01728 Bannewitz',
        'kdnr': '4426'
    },
    {
        'name': 'Jens Spahn - PF',
        'address': 'Burgker Straße 145, 01705 Freital',
        'kdnr': '4043'
    },
    {
        'name': 'Schleich',
        'address': 'Liebstädter Str. 45, 01796 Pirna',
        'kdnr': '44993'
    },
    # Aliases
    {
        'name': 'Blumentritt',
        'address': 'Str. des 17. Juni 11, 01257 Dresden',
        'kdnr': '5287'
    },
]

print("\n" + "="*80)
print("BARKUNDEN GEOCODING UND IMPORT")
print("="*80 + "\n")

print(f"[1/3] Geocode {len(barkunden)} Barkunden...\n")

successfully_geocoded = []
failed = []

for i, kunde in enumerate(barkunden, 1):
    print(f"[{i}/{len(barkunden)}] {kunde['name']}")
    print(f"         Adresse: {kunde['address']}")
    
    result = geocode_address(kunde['address'])
    
    if result and result.get('lat') and result.get('lon'):
        print(f"         [OK] Lat: {result['lat']}, Lon: {result['lon']}")
        
        successfully_geocoded.append(Kunde(
            id=None,
            name=kunde['name'],
            adresse=kunde['address'],
            lat=result['lat'],
            lon=result['lon']
        ))
    else:
        print(f"         [X] Geocoding fehlgeschlagen")
        failed.append(kunde)
    print()

print(f"[2/3] Speichere in Datenbank...")

if successfully_geocoded:
    upsert_kunden(successfully_geocoded)
    print(f"[OK] {len(successfully_geocoded)} Kunden gespeichert!")
else:
    print("[WARNUNG] Keine Kunden zum Speichern")

print(f"\n[3/3] ERGEBNIS")
print(f"{'='*80}")
print(f"Erfolgreich: {len(successfully_geocoded)}/{len(barkunden)}")
print(f"Fehlgeschlagen: {len(failed)}")

if failed:
    print(f"\nFEHLGESCHLAGEN:")
    for kunde in failed:
        print(f"  - {kunde['name']}: {kunde['address']}")

print(f"\n{'='*80}\n")

