#!/usr/bin/env python3
"""
Letzte manuelle Korrekturen
"""
import sys
sys.path.insert(0, '.')

from backend.db.dao import upsert_kunden, Kunde

# Korrigierte Kunden
kunden = [
    Kunde(
        id=None,
        name="Saegner's Fahrzeugtechnik",
        adresse="Burgstaedteler Str. 3, 01219 Dresden",
        lat=51.0037703,
        lon=13.7650329
    ),
    Kunde(
        id=None,
        name="Rob`s Kfz-Service",
        adresse="Enno-Heidebroek-Strasse 11, 01237 Dresden",
        lat=51.0160119,
        lon=13.7961524
    ),
    Kunde(
        id=None,
        name="CAR-ART GmbH",
        adresse="Loebtauer Str. 55, 01159 Dresden",
        lat=51.0462075,
        lon=13.7084571
    ),
    Kunde(
        id=None,
        name="AUTO OTTO",
        adresse="Dresdener Str. 5, 02977 Hoyerswerda",
        lat=51.4305207,
        lon=14.2327649
    ),
]

print(f"Trage {len(kunden)} korrigierte Kunden ein...\n")

for kunde in kunden:
    print(f"  - {kunde.name}")
    print(f"    Adresse: {kunde.adresse}")
    print(f"    Koordinaten: {kunde.lat}, {kunde.lon}")

ids = upsert_kunden(kunden)

print(f"\n[OK] {len(ids)} Kunden erfolgreich eingetragen!")
print(f"IDs: {ids}")

