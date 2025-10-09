#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dauerhafte Adress-Mapping-Lösung für Firmenumzüge
"""
import sys
from pathlib import Path

sys.path.insert(0, '.')
from backend.db.dao import Kunde, upsert_kunden

print("\n" + "="*80)
print("ADDRESS-MAPPING: FIRMENUMZÜGE")
print("="*80 + "\n")

# Bekannte Firmenumzüge - alte Adresse -> neue Adresse
address_mappings = {
    "CAR-ART GmbH": {
        "old_addresses": [
            "Bismarkstr. 63, 01257 Dresden",
            "Bismarkstraße 63, 01257 Dresden",
            "Bismarkstr 63, 01257 Dresden"
        ],
        "new_address": "Löbtauer Str. 55, 01159 Dresden",
        "new_coordinates": (51.0462075, 13.7084571)  # Koordinaten der neuen Adresse
    }
}

print(f"[1/3] Erstelle Adress-Mappings für {len(address_mappings)} Firmen...")

for company, mapping in address_mappings.items():
    print(f"\nFirma: {company}")
    print(f"  Alte Adressen: {len(mapping['old_addresses'])}")
    print(f"  Neue Adresse: {mapping['new_address']}")
    
    # Prüfe ob neue Adresse bereits in DB
    from backend.db.dao import get_kunde_id_by_name_adresse
    existing_id = get_kunde_id_by_name_adresse(company, mapping['new_address'])
    
    if existing_id:
        print(f"  [OK] Neue Adresse bereits in DB (ID: {existing_id})")
    else:
        print(f"  [WARNUNG] Neue Adresse nicht in DB - wird hinzugefügt")
        
        # Neue Adresse hinzufügen
        new_customer = Kunde(
            id=None,
            name=company,
            adresse=mapping['new_address'],
            lat=mapping['new_coordinates'][0],
            lon=mapping['new_coordinates'][1]
        )
        upsert_kunden([new_customer])
        print(f"  [DB] Neue Adresse gespeichert!")

print(f"\n[2/3] INTEGRATION IN ADDRESSCORRECTOR")
print("="*80)

# Zeige wie das in den AddressCorrector integriert werden kann
print("""
INTEGRATION IN backend/services/address_corrector.py:

# Firmenumzüge-Mapping
self.company_moves = {
    "CAR-ART GmbH": {
        "Bismarkstr. 63, 01257 Dresden": "Löbtauer Str. 55, 01159 Dresden",
        "Bismarkstraße 63, 01257 Dresden": "Löbtauer Str. 55, 01159 Dresden",
        "Bismarkstr 63, 01257 Dresden": "Löbtauer Str. 55, 01159 Dresden"
    }
}

# In correct_address() Methode hinzufügen:
if customer_name in self.company_moves:
    for old_addr, new_addr in self.company_moves[customer_name].items():
        if old_addr in address:
            corrected_address = address.replace(old_addr, new_addr)
            print(f"   -> Firmenumzug: {old_addr} -> {new_addr}")
            # Geocoding mit neuer Adresse versuchen...
""")

print(f"\n[3/3] NÄCHSTE SCHRITTE")
print("="*80)
print("1. Firmenumzüge in AddressCorrector integrieren")
print("2. CSV-Dateien mit neuen Adressen aktualisieren")
print("3. Alte Adressen aus Datenbank entfernen (optional)")
print("4. System testen")

print("\n" + "="*80 + "\n")
