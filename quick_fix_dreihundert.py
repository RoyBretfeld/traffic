#!/usr/bin/env python3
"""
Schnelle direkte Datenbank-Korrektur für Dreihundert Dresden
"""
import sys
from pathlib import Path
import os

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent))

# Set environment variables
os.environ.setdefault('DATABASE_URL', 'sqlite:///data/traffic.db')

from db.core import ENGINE
from sqlalchemy import text
from repositories.geo_repo import normalize_addr

def quick_fix_dreihundert():
    """Schnelle direkte Datenbank-Korrektur."""
    
    print("=== SCHNELLE DRITTUNDERT DRESDEN KORREKTUR ===")
    
    address = "Naumannstraße 12 | Halle 14, 01809 Heidenau"
    company_name = "Dreihundert Dresden"
    lat = 50.97513350003193
    lon = 13.876504538064527
    
    print(f"Adresse: {address}")
    print(f"Firmenname: {company_name}")
    print(f"Koordinaten: {lat}, {lon}")
    
    # Normalisierte Adressen
    norm_addr = normalize_addr(address)
    company_addr = f"{company_name}, {address}"
    company_norm = normalize_addr(company_addr)
    
    print(f"Normalisiert: {norm_addr}")
    print(f"Firmenname + Adresse: {company_norm}")
    
    try:
        with ENGINE.begin() as conn:
            print(f"\n--- Direkte Datenbank-Korrektur ---")
            
            # 1. Hauptadresse eintragen/aktualisieren
            conn.execute(text(
                "INSERT OR REPLACE INTO geo_cache (address_norm, lat, lon, source, by_user) VALUES (:a, :lat, :lon, :source, :by_user)"
            ), {
                "a": norm_addr,
                "lat": lat,
                "lon": lon,
                "source": "manual",
                "by_user": "quick_fix"
            })
            print(f"✅ Hauptadresse eingetragen: {norm_addr}")
            
            # 2. Firmenname + Adresse eintragen/aktualisieren
            conn.execute(text(
                "INSERT OR REPLACE INTO geo_cache (address_norm, lat, lon, source, by_user) VALUES (:a, :lat, :lon, :source, :by_user)"
            ), {
                "a": company_norm,
                "lat": lat,
                "lon": lon,
                "source": "manual",
                "by_user": "quick_fix"
            })
            print(f"✅ Firmenname + Adresse eingetragen: {company_norm}")
            
            # 3. Fail-Cache löschen (falls vorhanden)
            conn.execute(text("DELETE FROM geo_fail WHERE address_norm = :a"), {"a": norm_addr})
            conn.execute(text("DELETE FROM geo_fail WHERE address_norm = :a"), {"a": company_norm})
            print(f"✅ Fail-Cache gelöscht für beide Varianten")
            
            # 4. Aus Manual-Queue entfernen (falls vorhanden)
            conn.execute(text("DELETE FROM geo_manual WHERE address_norm = :a"), {"a": norm_addr})
            conn.execute(text("DELETE FROM geo_manual WHERE address_norm = :a"), {"a": company_norm})
            print(f"✅ Aus Manual-Queue entfernt")
            
        # 5. Schnelle Verifikation
        print(f"\n--- VERIFIKATION ---")
        with ENGINE.begin() as conn:
            # Hauptadresse prüfen
            row = conn.execute(text(
                "SELECT address_norm, lat, lon, source FROM geo_cache WHERE address_norm = :a"
            ), {"a": norm_addr}).mappings().first()
            
            if row:
                print(f"✅ Hauptadresse: {row['address_norm']} -> {row['lat']}, {row['lon']} ({row['source']})")
            else:
                print(f"❌ Hauptadresse nicht gefunden!")
                return False
            
            # Firmenname + Adresse prüfen
            row = conn.execute(text(
                "SELECT address_norm, lat, lon, source FROM geo_cache WHERE address_norm = :a"
            ), {"a": company_norm}).mappings().first()
            
            if row:
                print(f"✅ Firmenname + Adresse: {row['address_norm']} -> {row['lat']}, {row['lon']} ({row['source']})")
            else:
                print(f"❌ Firmenname + Adresse nicht gefunden!")
                return False
        
        print(f"\n🎉 DRITTUNDERT DRESDEN ERFOLGREICH KORRIGIERT!")
        return True
        
    except Exception as e:
        print(f"❌ FEHLER: {e}")
        return False

if __name__ == "__main__":
    success = quick_fix_dreihundert()
    if success:
        print("\n✅ Das Problem sollte jetzt behoben sein!")
        print("🔄 Bitte den Server neu starten und die Tourplan-Seite neu laden!")
    else:
        print("\n❌ Das Problem konnte nicht behoben werden!")
