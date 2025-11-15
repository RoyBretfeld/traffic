#!/usr/bin/env python3
"""
Batch-Import von manuell korrigierten Kunden
"""
import sys
sys.path.insert(0, '.')

from backend.db.dao import upsert_kunden, Kunde

# Liste der korrigierten Kunden
kunden = [
    Kunde(
        id=None,
        name="Dietze & Schindler",
        adresse="Ladestrasse 2B, 09465 Sehmatal",
        lat=50.5328184,
        lon=12.9930792
    ),
    Kunde(
        id=None,
        name="CAR-Center",
        adresse="Crimmitschauer Str. 50 a, 04626 Schmoelln",
        lat=50.8898627,
        lon=12.3490547
    ),
    Kunde(
        id=None,
        name="Klaus Brandner GbR",
        adresse="Kaltes Feld 36, 08468 Heinsdorfergrund",
        lat=50.59956,
        lon=12.331687
    ),
]

print(f"Trage {len(kunden)} Kunden ein...\n")

for kunde in kunden:
    print(f"  - {kunde.name}")
    print(f"    Adresse: {kunde.adresse}")
    print(f"    Koordinaten: {kunde.lat}, {kunde.lon}")

ids = upsert_kunden(kunden)

print(f"\n[OK] {len(ids)} Kunden erfolgreich eingetragen!")
print(f"IDs: {ids}")

