#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Füge Auto Service Meusel mit den richtigen Koordinaten hinzu
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from backend.db.dao import Kunde, upsert_kunden

print("\n" + "="*80)
print("AUTO SERVICE MEUSEL - MIT RICHTIGEN KOORDINATEN")
print("="*80 + "\n")

# Auto Service Meusel
customer_name = "Auto Service Meusel"
address = "Alte Str. 33, 01768 Glashütte OT Hirschbach"

print(f"Kunde: {customer_name}")
print(f"Adresse: {address}")

# HIER DIE KOORDINATEN VON MAPS EINGEBEN:
# Beispiel: lat = 50.8670563, lon = 13.7387662
lat = 50.8670563  # <-- HIER DIE LATITUDE VON MAPS EINGEBEN
lon = 13.7387662  # <-- HIER DIE LONGITUDE VON MAPS EINGEBEN

print(f"\nKoordinaten von Maps:")
print(f"  Latitude:  {lat}")
print(f"  Longitude: {lon}")

# In Datenbank speichern
customer = Kunde(
    id=None,
    name=customer_name,
    adresse=address,
    lat=lat,
    lon=lon
)

upsert_kunden([customer])
print(f"\n[DB] Auto Service Meusel gespeichert!")

print("\n" + "="*80 + "\n")
