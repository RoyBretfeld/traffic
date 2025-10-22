#!/usr/bin/env python3
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

from repositories.geo_repo import normalize_addr, get, bulk_get
from repositories.geo_fail_repo import get_fail_status
from db.core import ENGINE
from sqlalchemy import text

def check_dreihundert():
    print("=== DRITTUNDERT DRESDEN DB-CHECK ===")
    
    address = "Naumannstraße 12 | Halle 14, 01809 Heidenau"
    company_name = "Dreihundert Dresden"
    
    print(f"Adresse: {address}")
    print(f"Firmenname: {company_name}")
    
    # 1. Normalisierte Adresse
    norm_addr = normalize_addr(address)
    print(f"Normalisiert: {norm_addr}")
    
    # 2. Direkte Suche
    print(f"\n--- Direkte Suche ---")
    result = get(norm_addr)
    if result:
        print(f"✅ GEFUNDEN: Lat={result['lat']}, Lon={result['lon']}")
    else:
        print(f"❌ NICHT GEFUNDEN")
    
    # 3. Bulk-Get Test
    print(f"\n--- Bulk-Get Test ---")
    bulk_result = bulk_get([norm_addr])
    if norm_addr in bulk_result:
        print(f"✅ Bulk-Get: {bulk_result[norm_addr]}")
    else:
        print(f"❌ Bulk-Get: Nicht gefunden")
    
    # 4. Fail-Cache Check
    print(f"\n--- Fail-Cache Check ---")
    fail_status = get_fail_status(norm_addr)
    if fail_status:
        print(f"❌ In Fail-Cache: {fail_status}")
    else:
        print(f"✅ Nicht im Fail-Cache")
    
    # 5. Raw DB Query
    print(f"\n--- Raw DB Query ---")
    with ENGINE.begin() as conn:
        # Suche nach Naumann
        rows = conn.execute(text(
            "SELECT address_norm, lat, lon, source, by_user FROM geo_cache WHERE address_norm LIKE :s LIMIT 5"
        ), {"s": "%naumann%"}).mappings().all()
        
        print(f"Naumann-Einträge ({len(rows)}):")
        for row in rows:
            print(f"  - {row['address_norm']} -> {row['lat']}, {row['lon']} (Source: {row['source']})")
        
        # Suche nach Dreihundert
        rows = conn.execute(text(
            "SELECT address_norm, lat, lon, source, by_user FROM geo_cache WHERE address_norm LIKE :s LIMIT 5"
        ), {"s": "%dreihundert%"}).mappings().all()
        
        print(f"\nDreihundert-Einträge ({len(rows)}):")
        for row in rows:
            print(f"  - {row['address_norm']} -> {row['lat']}, {row['lon']} (Source: {row['source']})")

if __name__ == "__main__":
    check_dreihundert()
