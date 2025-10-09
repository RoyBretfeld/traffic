#!/usr/bin/env python3
"""
Manuelles Hinzufügen eines Kunden mit korrigierten Koordinaten
"""
import sys
sys.path.insert(0, '.')

from backend.db.dao import upsert_kunden, Kunde

# Kunde 1: Dietze & Schindler
kunde = Kunde(
    id=None,
    name="Dietze & Schindler",
    adresse="Ladestraße 2B, 09465 Sehmatal",
    lat=50.5328184,
    lon=12.9930792
)

print(f"Trage Kunden ein: {kunde.name}")
print(f"Adresse: {kunde.adresse}")
print(f"Koordinaten: {kunde.lat}, {kunde.lon}")

ids = upsert_kunden([kunde])

print(f"\n[OK] Kunde erfolgreich eingetragen mit ID: {ids[0]}")

