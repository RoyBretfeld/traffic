#!/usr/bin/env python3
"""
ADDIERE SVEN - PF SYNONYM
Mappt "Sven - PF" zu "Sven Teichmann" in der geo_alias Tabelle
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

def add_sven_pf_synonym():
    """Füge Sven - PF als Synonym für Sven Teichmann hinzu"""
    
    print('🔄 ADDIERE SVEN - PF SYNONYM:')
    print('=' * 50)
    
    # Synonym-Mapping
    synonym_name = "Sven - PF"
    original_name = "Sven Teichmann"
    full_address = "An der Triebe 25, 01468 Moritzburg / OT Boxdorf"
    lat = 51.10396585223666
    lon = 13.613554730385008
    
    print(f'Synonym: "{synonym_name}"')
    print(f'Original: "{original_name}"')
    print(f'Adresse: {full_address}')
    print(f'Koordinaten: ({lat}, {lon})')
    print()
    
    # Datenbank-Verbindung
    from settings import SETTINGS
    import sqlite3
    
    db_path = SETTINGS.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 1. Füge zu geo_alias hinzu (Synonym-Mapping)
        cursor.execute('''
            INSERT OR REPLACE INTO geo_alias (address_norm, canonical_address)
            VALUES (?, ?)
        ''', (f"{synonym_name}, {full_address}", full_address))
        
        # 2. Füge zu geo_cache hinzu (falls noch nicht vorhanden)
        cursor.execute('''
            INSERT OR REPLACE INTO geo_cache (address_norm, lat, lon, source)
            VALUES (?, ?, ?, ?)
        ''', (f"{synonym_name}, {full_address}", lat, lon, 'synonym'))
        
        # 3. Füge auch die Original-Adresse zu geo_cache hinzu (falls noch nicht vorhanden)
        cursor.execute('''
            INSERT OR REPLACE INTO geo_cache (address_norm, lat, lon, source)
            VALUES (?, ?, ?, ?)
        ''', (full_address, lat, lon, 'manual'))
        
        conn.commit()
        print('✅ Synonym erfolgreich hinzugefügt!')
        
        # Verifikation
        print('\n🔍 VERIFIKATION:')
        
        # Prüfe geo_alias
        cursor.execute('''
            SELECT address_norm, canonical_address
            FROM geo_alias
            WHERE address_norm LIKE ?
        ''', (f"%{synonym_name}%",))
        
        alias_result = cursor.fetchone()
        if alias_result:
            print(f'✅ geo_alias: "{alias_result[0]}" -> "{alias_result[1]}"')
        else:
            print('❌ geo_alias: Nicht gefunden')
        
        # Prüfe geo_cache für Synonym
        cursor.execute('''
            SELECT address_norm, lat, lon, source
            FROM geo_cache
            WHERE address_norm LIKE ?
        ''', (f"%{synonym_name}%",))
        
        cache_result = cursor.fetchone()
        if cache_result:
            print(f'✅ geo_cache (Synonym): "{cache_result[0]}" -> ({cache_result[1]}, {cache_result[2]}) [{cache_result[3]}]')
        else:
            print('❌ geo_cache (Synonym): Nicht gefunden')
        
        # Prüfe geo_cache für Original
        cursor.execute('''
            SELECT address_norm, lat, lon, source
            FROM geo_cache
            WHERE address_norm = ?
        ''', (full_address,))
        
        original_result = cursor.fetchone()
        if original_result:
            print(f'✅ geo_cache (Original): "{original_result[0]}" -> ({original_result[1]}, {original_result[2]}) [{original_result[3]}]')
        else:
            print('❌ geo_cache (Original): Nicht gefunden')
            
    except Exception as e:
        print(f'❌ Fehler: {e}')
        conn.rollback()
    finally:
        conn.close()
    
    print()
    print('🎯 STATUS: Sven - PF ist jetzt als Synonym für Sven Teichmann gespeichert!')

if __name__ == '__main__':
    add_sven_pf_synonym()
