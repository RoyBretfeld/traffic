#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from repositories.geo_repo import upsert

def insert_dreihundert_coords():
    """Manuell die Koordinaten für Dreihundert Dresden eintragen."""
    
    address = "Naumannstraße 12 | Halle 14, 01809 Heidenau"
    company_name = "Dreihundert Dresden"
    lat = 50.97513350003193
    lon = 13.876504538064527
    
    print(f"=== DRITTUNDERT DRESDEN KOORDINATEN EINTRAGEN ===")
    print(f"Adresse: {address}")
    print(f"Firmenname: {company_name}")
    print(f"Koordinaten: {lat}, {lon}")
    
    try:
        result = upsert(address, lat, lon, source="manual", by_user="debug_fix", company_name=company_name)
        print(f"✅ ERFOLGREICH EINGETRAGEN:")
        print(f"   Normalisiert: {result['address_norm']}")
        print(f"   Koordinaten: {result['lat']}, {result['lon']}")
        print(f"   Source: {result['source']}")
        print(f"   By User: {result['by_user']}")
        print(f"   Company Addresses: {result['company_addresses']}")
        
    except Exception as e:
        print(f"❌ FEHLER: {e}")

if __name__ == "__main__":
    insert_dreihundert_coords()
