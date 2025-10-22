#!/usr/bin/env python3
"""
Korrigiere Dreihundert Dresden mit den verbesserten Fail-Cache-Funktionen
"""
import sys
from pathlib import Path
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'sqlite:///data/traffic.db')

from repositories.geo_repo import upsert, normalize_addr, get
from repositories.geo_fail_repo import clear, get_fail_status, cleanup_expired
from repositories.manual_repo import remove_open as manual_remove

def fix_dreihundert_with_improvements():
    """Korrigiere Dreihundert Dresden mit verbesserten Fail-Cache-Funktionen."""
    
    print("=== DRITTUNDERT DRESDEN FIX (MIT VERBESSERTEN FAIL-CACHE) ===")
    
    address = "Naumannstraße 12 | Halle 14, 01809 Heidenau"
    company_name = "Dreihundert Dresden"
    lat = 50.97513350003193
    lon = 13.876504538064527
    
    print(f"Adresse: {address}")
    print(f"Firmenname: {company_name}")
    print(f"Koordinaten: {lat}, {lon}")
    
    # 1. Normalisierte Adresse
    norm_addr = normalize_addr(address)
    print(f"Normalisiert: {norm_addr}")
    
    # 2. Fail-Cache-Status prüfen (mit verbesserter Funktion)
    print(f"\n--- Fail-Cache-Status prüfen ---")
    fail_status = get_fail_status(norm_addr)
    if fail_status:
        print(f"❌ Im Fail-Cache: {fail_status['reason']} bis {fail_status['until']}")
        print(f"   🗑️  Lösche aus Fail-Cache...")
        clear(norm_addr)
        print(f"   ✅ Aus Fail-Cache entfernt")
    else:
        print(f"✅ Nicht im Fail-Cache")
    
    # 3. Aktueller Geo-Cache-Status
    print(f"\n--- Geo-Cache-Status prüfen ---")
    current = get(norm_addr)
    if current:
        print(f"⚠️  Bereits vorhanden: Lat={current['lat']}, Lon={current['lon']}")
    else:
        print(f"❌ Nicht gefunden - wird eingetragen")
    
    # 4. Koordinaten eintragen (mit Firmenname für bessere Suche)
    print(f"\n--- Koordinaten eintragen ---")
    try:
        result = upsert(
            address=address,
            lat=lat,
            lon=lon,
            source="manual",
            by_user="improved_fix",
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
    
    # 5. Aus Manual-Queue entfernen (falls vorhanden)
    print(f"\n--- Manual-Queue bereinigen ---")
    try:
        manual_remove(norm_addr)
        print(f"✅ Aus Manual-Queue entfernt: {norm_addr}")
    except Exception as e:
        print(f"⚠️  Manual-Queue-Entfernung: {e}")
    
    # 6. Fail-Cache bereinigen (mit verbesserter Funktion)
    print(f"\n--- Fail-Cache bereinigen ---")
    try:
        cleaned = cleanup_expired()
        print(f"✅ {cleaned} abgelaufene Einträge bereinigt")
    except Exception as e:
        print(f"⚠️  Fail-Cache-Bereinigung: {e}")
    
    # 7. Verifikation
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
    
    # 8. Firmenname + Adresse prüfen
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
    print(f"\n📋 Was wurde gemacht:")
    print(f"   ✅ Koordinaten eingetragen (Hauptadresse + Firmenname)")
    print(f"   ✅ Fail-Cache gelöscht (mit verbesserter Funktion)")
    print(f"   ✅ Manual-Queue bereinigt")
    print(f"   ✅ Abgelaufene Fail-Cache-Einträge bereinigt")
    print(f"   ✅ Verifikation erfolgreich")
    
    return True

if __name__ == "__main__":
    success = fix_dreihundert_with_improvements()
    if success:
        print("\n✅ Das Problem sollte jetzt behoben sein!")
        print("🔄 Bitte den Server neu starten und die Tourplan-Seite neu laden!")
        print("\n💡 Tipp: Mit den verbesserten Fail-Cache-Funktionen kannst du jetzt:")
        print("   - /api/geocode/fail-status?address=... prüfen")
        print("   - /api/geocode/force-retry?address=... für Retry verwenden")
        print("   - /api/geocode/fail-stats für Statistiken abrufen")
    else:
        print("\n❌ Das Problem konnte nicht behoben werden!")
