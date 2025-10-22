#!/usr/bin/env python3
"""
Direkte Korrektur für Dreihundert Dresden über Repository-Funktionen
"""
import sys
from pathlib import Path
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'sqlite:///data/traffic.db')

# Import after setting environment
from repositories.geo_repo import upsert, normalize_addr, get
from repositories.geo_fail_repo import clear, get_fail_status, cleanup_expired
from repositories.manual_repo import remove_open as manual_remove

def direct_fix_dreihundert():
    """Direkte Korrektur über Repository-Funktionen."""
    
    print("=== DIREKTE DRITTUNDERT DRESDEN KORREKTUR ===")
    
    address = "Naumannstraße 12 | Halle 14, 01809 Heidenau"
    company_name = "Dreihundert Dresden"
    lat = 50.97513350003193
    lon = 13.876504538064527
    
    print(f"Adresse: {address}")
    print(f"Firmenname: {company_name}")
    print(f"Koordinaten: {lat}, {lon}")
    
    # Normalisierte Adresse
    norm_addr = normalize_addr(address)
    print(f"Normalisiert: {norm_addr}")
    
    # 1. Fail-Cache-Status prüfen
    print(f"\n--- Fail-Cache-Status prüfen ---")
    fail_status = get_fail_status(norm_addr)
    if fail_status:
        print(f"❌ Im Fail-Cache: {fail_status['reason']} bis {fail_status['until']}")
        clear(norm_addr)
        print(f"✅ Aus Fail-Cache entfernt")
    else:
        print(f"✅ Nicht im Fail-Cache")
    
    # 2. Aktueller Status prüfen
    current = get(norm_addr)
    if current:
        print(f"⚠️  Bereits vorhanden: Lat={current['lat']}, Lon={current['lon']}")
    else:
        print(f"❌ Nicht gefunden - wird eingetragen")
    
    # 3. Koordinaten eintragen (mit Firmenname für bessere Suche)
    print(f"\n--- Koordinaten eintragen ---")
    try:
        result = upsert(
            address=address,
            lat=lat,
            lon=lon,
            source="manual",
            by_user="direct_fix",
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
    
    # 4. Aus Manual-Queue entfernen (falls vorhanden)
    try:
        manual_remove(norm_addr)
        print(f"✅ Aus Manual-Queue entfernt: {norm_addr}")
    except Exception as e:
        print(f"⚠️  Manual-Queue-Entfernung: {e}")
    
    # 5. Fail-Cache bereinigen
    try:
        cleaned = cleanup_expired()
        print(f"✅ {cleaned} abgelaufene Einträge bereinigt")
    except Exception as e:
        print(f"⚠️  Fail-Cache-Bereinigung: {e}")
    
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
    
    # 7. Firmenname + Adresse prüfen
    company_addr = f"{company_name}, {address}"
    company_norm = normalize_addr(company_addr)
    company_verify = get(company_norm)
    if company_verify:
        print(f"✅ FIRMENNAME + ADRESSE GEFUNDEN:")
        print(f"   {company_norm} -> Lat={company_verify['lat']}, Lon={company_verify['lon']}")
    else:
        print(f"❌ FIRMENNAME + ADRESSE NICHT GEFUNDEN!")
        return False
    
    print(f"\n🎉 DRITTUNDERT DRESDEN ERFOLGREICH KORRIGIERT!")
    return True

if __name__ == "__main__":
    success = direct_fix_dreihundert()
    if success:
        print("\n✅ Das Problem sollte jetzt behoben sein!")
        print("🔄 Bitte den Server neu starten und die Tourplan-Seite neu laden!")
    else:
        print("\n❌ Das Problem konnte nicht behoben werden!")
