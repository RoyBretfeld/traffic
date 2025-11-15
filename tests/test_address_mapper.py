#!/usr/bin/env python3
"""
Test-Script für das neue Address-Mapping-System
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.address_mapper import address_mapper
from backend.services.geocode import geocode_address

def test_address_mappings():
    """Teste verschiedene problematische Adressen"""
    
    test_addresses = [
        # BAR-Sondernamen
        "Dreihundert Dresden",
        "Autoservice Mehlig", 
        "Gustavs Autohof",
        "Halle 13 - Teile",
        "Land-Bau-&Fahrzeugtechnik",
        # Problematische Adressen
        "Naumannstraße 12 | Halle 14, 01809 Heidenau",
        "Schulstraße 25, 01468 Moritzburg (OT Boxdorf)",
        "Rundteil 7b, 01728 Bannewitz OT Possendorf",
        "Möglitztalstraße 10, 01773 Altenberg OT Bärenstein",
        "Am Sägewerk 36, 01328 Dresden OT Schönfeld",
        "Ladestraße 2b, 09465 Sehmatal-OT Sehma",
        "Oberer Ladenberg 13, 01816 Bad Gottleuba OT Berggießhübel",
        "Alte Str. 33, 01768 Glashütte OT Hirschbach",
        # Normale Adresse zum Vergleich
        "Normale Adresse, 12345 Stadt",
    ]
    
    print("ADDRESS-MAPPER TEST")
    print("=" * 60)
    
    for address in test_addresses:
        print(f"\nTeste Adresse: {address}")
        print("-" * 40)
        
        # Teste Address-Mapper direkt
        mapping_result = address_mapper.map_address(address)
        print(f"Mapping-Ergebnis:")
        print(f"  Korrigierte Adresse: {mapping_result['corrected_address']}")
        print(f"  Methode: {mapping_result['method']}")
        print(f"  Confidence: {mapping_result['confidence']}")
        if mapping_result['lat'] and mapping_result['lon']:
            print(f"  Koordinaten: {mapping_result['lat']}, {mapping_result['lon']}")
        
        # Teste vollständiges Geocoding
        geo_result = geocode_address(address)
        if geo_result:
            print(f"Geocoding-Ergebnis:")
            print(f"  Koordinaten: {geo_result['lat']}, {geo_result['lon']}")
            print(f"  Provider: {geo_result['provider']}")
        else:
            print("Geocoding-Ergebnis: FEHLGESCHLAGEN")

def test_rule_application():
    """Teste die Regel-Anwendung"""
    
    print("\n\nREGEL-ANWENDUNG TEST")
    print("=" * 60)
    
    test_cases = [
        "Straße 123, 12345 Stadt (OT Ortsteil)",
        "Hauptstraße 45 | Halle 5, 54321 Stadt",
        "Testweg 78, 98765 Stadt OT Testort",
        "Normale Straße 1, 11111 Stadt",
    ]
    
    for address in test_cases:
        corrected = address_mapper.apply_rules(address)
        print(f"Original:  {address}")
        print(f"Korrigiert: {corrected}")
        print()

if __name__ == "__main__":
    test_address_mappings()
    test_rule_application()
