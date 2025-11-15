#!/usr/bin/env python3
import sys
from pathlib import Path
import os

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'sqlite:///data/traffic.db')

# Import after setting environment
from repositories.geo_repo import upsert, normalize_addr, get
from repositories.geo_fail_repo import clear as clear_fail_cache
from repositories.manual_repo import remove_open as manual_remove

def main():
    """Korrigiere Dreihundert Dresden - Koordinaten eintragen und Fail-Cache löschen."""
    
    print("=== DRITTUNDERT DRESDEN FIX ===")
    
    address = "Naumannstraße 12 | Halle 14, 01809 Heidenau"
    company_name = "Dreihundert Dresden"
    lat = 50.97513350003193
    lon = 13.876504538064527
    
    print(f"Adresse: {address}")
    print(f"Firmenname: {company_name}")
    print(f"Koordinaten: {lat}, {lon}")
    
    # 1. Normalisierte Adresse prüfen
    norm_addr = normalize_addr(address)
    print(f"Normalisiert: {norm_addr}")
    
    # 2. Aktueller Status prüfen
    current = get(norm_addr)
    if current:
        print(f"⚠️  Bereits vorhanden: {current}")
    else:
        print(f"❌ Nicht gefunden - wird eingetragen")
    
    # 3. Koordinaten eintragen (mit Firmenname für bessere Suche)
    try:
        result = upsert(
            address=address,
            lat=lat,
            lon=lon,
            source="manual",
            by_user="debug_fix",
            company_name=company_name
        )
        
        print(f"✅ ERFOLGREICH EINGETRAGEN:")
        print(f"   Normalisiert: {result['address_norm']}")
        print(f"   Koordinaten: {result['lat']}, {result['lon']}")
        print(f"   Source: {result['source']}")
        print(f"   By User: {result['by_user']}")
        print(f"   Company Addresses: {result['company_addresses']}")
        
    except Exception as e:
        print(f"❌ FEHLER beim Eintragen: {e}")
        return False
    
    # 4. Fail-Cache löschen (falls vorhanden)
    try:
        clear_fail_cache(norm_addr)
        print(f"✅ Fail-Cache gelöscht für: {norm_addr}")
    except Exception as e:
        print(f"⚠️  Fail-Cache-Löschung: {e}")
    
    # 5. Aus Manual-Queue entfernen (falls vorhanden)
    try:
        manual_remove(norm_addr)
        print(f"✅ Aus Manual-Queue entfernt: {norm_addr}")
    except Exception as e:
        print(f"⚠️  Manual-Queue-Entfernung: {e}")
    
    # 6. Verifikation
    print(f"\n--- VERIFIKATION ---")
    verify = get(norm_addr)
    if verify:
        print(f"✅ VERIFIKATION ERFOLGREICH:")
        print(f"   Lat: {verify['lat']}")
        print(f"   Lon: {verify['lon']}")
        print(f"   Source: {verify.get('source', 'unknown')}")
    else:
        print(f"❌ VERIFIKATION FEHLGESCHLAGEN - Nicht gefunden!")
        return False
    
    print(f"\n🎉 DRITTUNDERT DRESDEN ERFOLGREICH KORRIGIERT!")
    return True

if __name__ == "__main__":
    success = main()
    if success:
        print("\n✅ Das Problem sollte jetzt behoben sein!")
    else:
        print("\n❌ Das Problem konnte nicht behoben werden!")
