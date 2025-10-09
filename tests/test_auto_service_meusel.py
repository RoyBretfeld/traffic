#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Teste Auto Service Meusel mit OT-Korrektur
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from backend.services.geocode import geocode_address
from backend.db.dao import Kunde, upsert_kunden

print("\n" + "="*80)
print("AUTO SERVICE MEUSEL - OT-KORREKTUR")
print("="*80 + "\n")

# Original-Adresse mit OT
original_address = "Alte Str. 33, 01768 Glashütte OT Hirschbach"
customer_name = "Auto Service Meusel"

print(f"Kunde: {customer_name}")
print(f"Original: {original_address}")

# Teste intelligente OT-Korrektur
print(f"\n[1/3] Teste intelligente OT-Korrektur...")
result = geocode_address(original_address)

if result and result.get('lat') and result.get('lon'):
    print(f"   [OK] Gefunden: {result['lat']}, {result['lon']}")
    print(f"   Provider: {result.get('provider', 'unknown')}")
    print(f"   Korrektur: {result.get('correction_type', 'unknown')}")
    
    # In Datenbank speichern
    customer = Kunde(
        id=None,
        name=customer_name,
        adresse=original_address,
        lat=result['lat'],
        lon=result['lon']
    )
    
    upsert_kunden([customer])
    print(f"   [DB] Kunde gespeichert!")
    
else:
    print(f"   [X] Nicht gefunden")
    
    # Teste manuelle OT-Korrektur
    print(f"\n[2/3] Teste manuelle OT-Korrektur...")
    corrected_address = "Alte Str. 33, 01768 Glashütte"  # OT entfernt
    
    result2 = geocode_address(corrected_address)
    
    if result2 and result2.get('lat') and result2.get('lon'):
        print(f"   [OK] Gefunden: {result2['lat']}, {result2['lon']}")
        print(f"   Provider: {result2.get('provider', 'unknown')}")
        
        # In Datenbank speichern
        customer = Kunde(
            id=None,
            name=customer_name,
            adresse=corrected_address,
            lat=result2['lat'],
            lon=result2['lon']
        )
        
        upsert_kunden([customer])
        print(f"   [DB] Kunde gespeichert!")
    else:
        print(f"   [X] Auch korrigierte Adresse nicht gefunden")
        
        # Manuelle Koordinaten
        print(f"\n[3/3] Füge manuelle Koordinaten hinzu...")
        customer = Kunde(
            id=None,
            name=customer_name,
            adresse=original_address,
            lat=50.8670563,  # Glashütte Bereich
            lon=13.7387662
        )
        
        upsert_kunden([customer])
        print(f"   [DB] Kunde mit manuellen Koordinaten gespeichert!")

print("\n" + "="*80 + "\n")
