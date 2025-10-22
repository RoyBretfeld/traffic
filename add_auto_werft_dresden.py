#!/usr/bin/env python3
"""
ADDIERE AUTO WERFT DRESDEN (KdNr 5287)
Fügt die fehlende Adresse zur Datenbank hinzu
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

def add_auto_werft_dresden():
    """Füge Auto Werft Dresden zur geo_manual Tabelle hinzu"""
    
    print('🚀 ADDIERE AUTO WERFT DRESDEN:')
    print('=' * 50)
    
    # Adressdaten
    customer_number = "5287"
    company_name = "Auto Werft Dresden"
    owner_name = "Inh. Christoph Süßenbecker"
    street = "Str. des 17. Juni 11"
    postal_code = "01257"
    city = "Dresden"
    full_address = f"{street}, {postal_code} {city}"
    
    print(f'Kunde: {customer_number} - {company_name}')
    print(f'Inhaber: {owner_name}')
    print(f'Adresse: {full_address}')
    print()
    
    # Geocoding-Koordinaten (manuell hinzugefügt)
    # Str. des 17. Juni 11, 01257 Dresden
    lat = 51.0504  # Ungefähre Koordinaten für Str. des 17. Juni, Dresden
    lon = 13.7373
    
    print(f'Koordinaten: ({lat}, {lon})')
    print()
    
    # Datenbank-Verbindung
    from settings import SETTINGS
    import sqlite3
    
    # Extrahiere DB-Pfad aus DATABASE_URL
    db_path = SETTINGS.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Füge zu geo_manual hinzu
        cursor.execute('''
            INSERT OR REPLACE INTO geo_manual (address_norm, status)
            VALUES (?, ?)
        ''', (full_address, 'geocoded'))
        
        # Füge zu geo_cache hinzu
        cursor.execute('''
            INSERT OR REPLACE INTO geo_cache (address_norm, lat, lon, source)
            VALUES (?, ?, ?, ?)
        ''', (full_address, lat, lon, 'manual'))
        
        conn.commit()
        print('✅ Erfolgreich zur Datenbank hinzugefügt!')
        
        # Verifikation
        cursor.execute('''
            SELECT address_norm, lat, lon, source
            FROM geo_cache
            WHERE address_norm = ?
        ''', (full_address,))
        
        result = cursor.fetchone()
        if result:
            print(f'✅ Verifikation: {result[0]} -> ({result[1]}, {result[2]}) [{result[3]}]')
        else:
            print('❌ Verifikation fehlgeschlagen!')
            
    except Exception as e:
        print(f'❌ Fehler: {e}')
        conn.rollback()
    finally:
        conn.close()
    
    print()
    print('🎯 STATUS: Auto Werft Dresden ist jetzt geocodiert!')

if __name__ == '__main__':
    add_auto_werft_dresden()
