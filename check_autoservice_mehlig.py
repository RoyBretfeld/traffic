#!/usr/bin/env python3
"""
PRÜFE AUTOSERVICE MEHLIG PROBLEM
"""
import sqlite3
from pathlib import Path

def check_autoservice_mehlig():
    """Prüfe Autoservice Mehlig Problem"""
    
    db_path = Path('data/traffic.db')
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print('🔍 PRÜFE AUTOSERVICE MEHLIG:')
    print('=' * 50)
    
    # Suche nach Autoservice Mehlig
    cursor.execute('''
        SELECT address_norm, lat, lon, source 
        FROM geo_cache 
        WHERE address_norm LIKE '%Mehlig%'
        OR address_norm LIKE '%Schulstraße%'
        OR address_norm LIKE '%Moritzburg%'
        OR address_norm LIKE '%Boxdorf%'
    ''')
    
    results = cursor.fetchall()
    print(f'Gefundene Einträge: {len(results)}')
    for addr, lat, lon, source in results:
        print(f'  ✅ "{addr}" -> ({lat}, {lon}) [{source}]')
    
    # Prüfe spezifisch nach der Adresse
    specific_addresses = [
        "Schulstraße 25, 01468 Moritzburg (OT Boxdorf)",
        "Schulstraße 25, 01468 Moritzburg OT Boxdorf",
        "Schulstraße 25, 01468 Moritzburg",
        "Schulstraße 25, Moritzburg"
    ]
    
    print(f'\n🔍 SPEZIFISCHE ADRESS-SUCHE:')
    for addr in specific_addresses:
        cursor.execute('SELECT lat, lon, source FROM geo_cache WHERE address_norm = ?', (addr,))
        result = cursor.fetchone()
        if result:
            lat, lon, source = result
            print(f'  ✅ "{addr}" -> ({lat}, {lon}) [{source}]')
        else:
            print(f'  ❌ "{addr}" -> NICHT GEFUNDEN')
    
    conn.close()

if __name__ == '__main__':
    check_autoservice_mehlig()
