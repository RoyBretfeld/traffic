import sys
from pathlib import Path
import os

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from repositories.geo_repo import normalize_addr, get, get_address_variants
from repositories.geo_fail_repo import get_fail_status, clear as clear_fail_cache
from db.core import ENGINE
from sqlalchemy import text

def check_dreihundert_dresden():
    address = "Naumannstraße 12 | Halle 14, 01809 Heidenau"
    company_name = "Dreihundert Dresden"
    
    print(f"=== DB-Einträge für '{company_name}' ===")
    print(f"Adresse: {address}")
    
    # Normalisierte Adresse
    norm_addr = normalize_addr(address)
    print(f"Normalisiert: {norm_addr}")
    
    # Direkte Suche in geo_cache
    print(f"\n--- Direkte Suche in geo_cache ---")
    cached_geo = get(norm_addr)
    if cached_geo:
        print(f"✅ Gefunden: Lat={cached_geo['lat']}, Lon={cached_geo['lon']}")
    else:
        print(f"❌ Nicht gefunden")
    
    # Alle Varianten prüfen
    variants = get_address_variants(address, company_name)
    print(f"\n--- Alle {len(variants)} Varianten ---")
    for i, variant in enumerate(variants):
        norm_variant = normalize_addr(variant)
        cached_variant_geo = get(norm_variant)
        if cached_variant_geo:
            print(f"✅ Variant {i+1}: '{variant}' -> Lat={cached_variant_geo['lat']}, Lon={cached_variant_geo['lon']}")
        else:
            print(f"❌ Variant {i+1}: '{variant}' -> NICHT GEFUNDEN")
    
    # Fail-Cache prüfen
    print(f"\n--- Fail-Cache Status ---")
    fail_status = get_fail_status(norm_addr)
    if fail_status:
        print(f"❌ In Fail-Cache: {fail_status['reason']} bis {fail_status['expires_at']}")
    else:
        print(f"✅ Nicht im Fail-Cache")
    
    # Raw-Suche in geo_cache
    print(f"\n--- Raw-Suche nach 'Dreihundert' ---")
    with ENGINE.connect() as conn:
        rows = conn.execute(text(
            "SELECT address_norm, lat, lon, source, by_user FROM geo_cache WHERE address_norm LIKE :s LIMIT 10"
        ), {"s": "%dreihundert%"}).mappings().all()
        
        if rows:
            print(f"Gefunden {len(rows)} Einträge:")
            for row in rows:
                print(f"  - '{row['address_norm']}' -> Lat={row['lat']}, Lon={row['lon']} (Source: {row['source']})")
        else:
            print("Keine Einträge mit 'dreihundert' gefunden")
    
    # Raw-Suche nach 'naumann'
    print(f"\n--- Raw-Suche nach 'Naumann' ---")
    with ENGINE.connect() as conn:
        rows = conn.execute(text(
            "SELECT address_norm, lat, lon, source, by_user FROM geo_cache WHERE address_norm LIKE :s LIMIT 10"
        ), {"s": "%naumann%"}).mappings().all()
        
        if rows:
            print(f"Gefunden {len(rows)} Einträge:")
            for row in rows:
                print(f"  - '{row['address_norm']}' -> Lat={row['lat']}, Lon={row['lon']} (Source: {row['source']})")
        else:
            print("Keine Einträge mit 'naumann' gefunden")

if __name__ == "__main__":
    check_dreihundert_dresden()
