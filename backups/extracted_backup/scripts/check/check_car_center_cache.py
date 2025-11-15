#!/usr/bin/env python3
"""
CACHE-PROBLEM LÖSEN: CAR - CENTER ADRESSE PRÜFEN
"""
import sqlite3
from pathlib import Path

def check_car_center_address():
    """Prüfe ob CAR - Center Adresse geocodiert ist"""
    
    db_path = Path('data/traffic.db')
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print('🔍 PRÜFE CAR - CENTER ADRESSE:')
    print('=' * 50)
    
    # Suche nach CAR - Center
    cursor.execute('''
        SELECT address_norm, lat, lon, source 
        FROM geo_cache 
        WHERE address_norm LIKE '%CAR%' 
        OR address_norm LIKE '%Center%'
        OR address_norm LIKE '%Crimmitschauer%'
    ''')
    
    results = cursor.fetchall()
    print(f'Gefundene Einträge in geo_cache: {len(results)}')
    for addr, lat, lon, source in results:
        print(f'  ✅ "{addr}" -> ({lat}, {lon}) [{source}]')
    
    # Prüfe auch geo_manual
    cursor.execute('''
        SELECT address_norm, lat, lon 
        FROM geo_manual 
        WHERE address_norm LIKE '%CAR%' 
        OR address_norm LIKE '%Crimmitschauer%'
    ''')
    
    manual_results = cursor.fetchall()
    print(f'\nManuelle Einträge in geo_manual: {len(manual_results)}')
    for addr, lat, lon in manual_results:
        print(f'  ✅ "{addr}" -> ({lat}, {lon})')
    
    # Prüfe spezifisch nach "Crimmitschauer Straße 50a"
    specific_address = "Crimmitschauer Straße 50a, 04626 Schmölln/Thür"
    cursor.execute('SELECT lat, lon, source FROM geo_cache WHERE address_norm = ?', (specific_address,))
    specific_result = cursor.fetchone()
    
    if specific_result:
        lat, lon, source = specific_result
        print(f'\n✅ SPEZIFISCHE ADRESSE GEFUNDEN:')
        print(f'   "{specific_address}"')
        print(f'   Koordinaten: ({lat}, {lon})')
        print(f'   Quelle: {source}')
    else:
        print(f'\n❌ SPEZIFISCHE ADRESSE NICHT GEFUNDEN:')
        print(f'   "{specific_address}"')
        print('   → Muss manuell geocodiert werden!')
    
    conn.close()

def clear_frontend_cache():
    """Lösche Frontend-Cache"""
    print('\n🧹 FRONTEND-CACHE LÖSCHEN:')
    print('=' * 50)
    
    # Browser-Cache löschen (Anweisungen)
    print('1. 🌐 BROWSER-CACHE LÖSCHEN:')
    print('   - Strg + Shift + R (Hard Refresh)')
    print('   - Oder: Strg + F5')
    print('   - Oder: Entwicklertools → Network → "Disable cache"')
    print()
    
    print('2. 🔄 SERVER NEUSTART:')
    print('   - Server stoppen (Strg + C)')
    print('   - Server neu starten: python start_server.py')
    print()
    
    print('3. 🗄️ DATENBANK-CACHE PRÜFEN:')
    print('   - Prüfe ob Adresse in geo_cache existiert')
    print('   - Falls nicht: Manuell geocodieren')

if __name__ == '__main__':
    check_car_center_address()
    clear_frontend_cache()
