#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Füge CAR-ART Bismarkstraße manuell hinzu
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from backend.db.dao import Kunde, upsert_kunden

print("\n" + "="*80)
print("CAR-ART BISMARKSTRASSE - MANUELL HINZUFÜGEN")
print("="*80 + "\n")

# CAR-ART Bismarkstraße mit manuellen Koordinaten
customer = Kunde(
    id=None,
    name="CAR-ART GmbH",
    adresse="Bismarkstr. 63, 01257 Dresden",
    lat=51.05,  # Dresden Bereich
    lon=13.75
)

print(f"Kunde: {customer.name}")
print(f"Adresse: {customer.adresse}")
print(f"Koordinaten: {customer.lat}, {customer.lon}")

# In Datenbank speichern
upsert_kunden([customer])
print(f"[DB] CAR-ART Bismarkstraße gespeichert!")

print("\n" + "="*80)
print("CAR-ART GMBH HAT JETZT BEIDE FILIALEN:")
print("  1. Bismarkstr. 63, 01257 Dresden")
print("  2. Löbtauer Str. 55, 01159 Dresden")
print("="*80 + "\n")
