#!/usr/bin/env python3
"""
Prüft den aktuellen Geocoding-Status - schnell und einfach!
"""

import sys
import os
sys.path.append('backend')

from pathlib import Path
import pandas as pd
from backend.db.dao import _connect

def check_geocoding_status():
    """Prüft den aktuellen Geocoding-Status."""
    
    print("🔍 Geocoding-Status Check")
    print("=" * 50)
    
    try:
        conn = _connect()
        cursor = conn.cursor()
        
        # Gesamt-Statistik
        cursor.execute("SELECT COUNT(*) FROM kunden")
        total_kunden = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NOT NULL AND lon IS NOT NULL")
        geocoded_kunden = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NULL OR lon IS NULL")
        unerkannte_kunden = cursor.fetchone()[0]
        
        print(f"📊 Gesamt-Statistik:")
        print(f"   📍 Gesamt Kunden: {total_kunden}")
        print(f"   ✅ Geocoded: {geocoded_kunden}")
        print(f"   ❌ Unerkannt: {unerkannte_kunden}")
        print(f"   📈 Geocoding-Quote: {(geocoded_kunden/total_kunden*100):.1f}%" if total_kunden > 0 else "0%")
        
        # Unerkannte Kunden analysieren
        print(f"\n🔍 Unerkannte Kunden (erste 10):")
        cursor.execute("""
            SELECT name, adresse, lat, lon 
            FROM kunden 
            WHERE lat IS NULL OR lon IS NULL 
            ORDER BY name
            LIMIT 10
        """)
        unerkannte = cursor.fetchall()
        
        if unerkannte:
            for i, (name, adresse, lat, lon) in enumerate(unerkannte, 1):
                print(f"   {i:2d}. {name}")
                print(f"       {adresse}")
                print(f"       Lat: {lat}, Lon: {lon}")
                print()
        else:
            print("   🎉 Alle Kunden sind geocoded!")
        
        # Adressen mit Problemen analysieren
        print(f"🔍 Adressen-Analyse:")
        cursor.execute("""
            SELECT adresse, COUNT(*) as count
            FROM kunden 
            WHERE lat IS NULL OR lon IS NULL 
            GROUP BY adresse
            ORDER BY count DESC
            LIMIT 5
        """)
        problem_adressen = cursor.fetchall()
        
        if problem_adressen:
            print(f"   Häufigste problematische Adressen:")
            for adresse, count in problem_adressen:
                print(f"     {count}x: {adresse}")
        
        # Mojibake-Zeichen in Adressen prüfen
        print(f"\n🔍 Mojibake-Zeichen Check:")
        mojibake_chars = ['┬', '├', 'á', '@', ']', 'é', 'Ã¤', 'Ã¶', 'Ã¼', 'ÃŸ']
        mojibake_count = 0
        
        cursor.execute("SELECT adresse FROM kunden WHERE lat IS NULL OR lon IS NULL")
        adressen = cursor.fetchall()
        
        for (adresse,) in adressen:
            for char in mojibake_chars:
                if char in adresse:
                    mojibake_count += 1
                    if mojibake_count <= 5:  # Erste 5 Beispiele
                        print(f"   ❌ Mojibake: {adresse}")
                    break
        
        print(f"   📊 Adressen mit Mojibake: {mojibake_count}")
        
        if mojibake_count == 0:
            print("   ✅ Keine Mojibake-Zeichen in unerkannten Adressen!")
        else:
            print("   ⚠️  Mojibake-Zeichen gefunden - Reparatur nötig!")
        
        conn.close()
        
        # Fazit
        print(f"\n📋 Fazit:")
        if unerkannte_kunden == 0:
            print("   🎉 PERFEKT! Alle Kunden sind geocoded!")
        elif mojibake_count == 0:
            print("   ✅ Keine Mojibake-Probleme - andere Ursachen für unerkannte Kunden")
        else:
            print("   ⚠️  Mojibake-Probleme gefunden - Reparatur nötig")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_geocoding_status()
