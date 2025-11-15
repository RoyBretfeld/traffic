#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Korrigiere CAR-ART Bismarkstr. 63 mit den richtigen Koordinaten von Maps
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from backend.db.dao import Kunde, upsert_kunden

print("\n" + "="*80)
print("CAR-ART BISMARKSTR. 63 - RICHTIGE KOORDINATEN VON MAPS")
print("="*80 + "\n")

# CAR-ART Bismarkstraße
customer_name = "CAR-ART GmbH"
address = "Bismarkstr. 63, 01257 Dresden"

print(f"Kunde: {customer_name}")
print(f"Adresse: {address}")

# HIER DIE RICHTIGEN KOORDINATEN VON MAPS EINGEBEN:
# Beispiel: lat = 51.05, lon = 13.75
lat = 51.05   # <-- HIER DIE RICHTIGE LATITUDE VON MAPS EINGEBEN
lon = 13.75   # <-- HIER DIE RICHTIGE LONGITUDE VON MAPS EINGEBEN

print(f"\nKoordinaten von Maps:")
print(f"  Latitude:  {lat}")
print(f"  Longitude: {lon}")

# In Datenbank speichern (überschreibt die alten manuellen Koordinaten)
customer = Kunde(
    id=None,
    name=customer_name,
    adresse=address,
    lat=lat,
    lon=lon
)

upsert_kunden([customer])
print(f"\n[DB] CAR-ART Bismarkstr. 63 mit richtigen Koordinaten gespeichert!")

print("\n" + "="*80)
print("CAR-ART GMBH HAT JETZT BEIDE FILIALEN MIT RICHTIGEN KOORDINATEN:")
print("  1. Bismarkstr. 63, 01257 Dresden")
print("  2. Löbtauer Str. 55, 01159 Dresden")
print("="*80 + "\n")
