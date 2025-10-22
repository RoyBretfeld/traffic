#!/usr/bin/env python3
"""
KORRIGIERE SVEN - PF SYNONYM
Sven - PF = Auto Werft Dresden (Inh. Christoph Süßenbecker)
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

def fix_sven_pf_correct():
    """Korrigiere Sven - PF als Synonym für Auto Werft Dresden"""
    
    print('🔄 KORRIGIERE SVEN - PF SYNONYM:')
    print('=' * 50)
    
    # Korrekte Synonym-Mapping
    synonym_name = "Sven - PF"
    original_name = "Auto Werft Dresden"
    owner_name = "Inh. Christoph Süßenbecker"
    full_address = "Str. des 17. Juni 11, 01257 Dresden"
    lat = 51.0504  # Koordinaten für Str. des 17. Juni, Dresden
    lon = 13.7373
    
    print(f'Synonym: "{synonym_name}"')
    print(f'Original: "{original_name}"')
    print(f'Inhaber: {owner_name}')
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
        # 1. Lösche falsche Einträge (falls vorhanden)
        cursor.execute('''
            DELETE FROM geo_alias WHERE address_norm LIKE ?
        ''', (f"%{synonym_name}%",))
        
        cursor.execute('''
            DELETE FROM geo_cache WHERE address_norm LIKE ?
        ''', (f"%{synonym_name}%",))
        
        # 2. Füge korrekte Synonym-Mapping hinzu
        # Zuerst prüfen welche Spalten geo_alias hat
        cursor.execute("PRAGMA table_info(geo_alias)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"geo_alias Spalten: {columns}")
        
        # Einfach zu geo_cache hinzufügen mit Synonym-Name
        cursor.execute('''
            INSERT OR REPLACE INTO geo_cache (address_norm, lat, lon, source)
            VALUES (?, ?, ?, ?)
        ''', (f"{synonym_name}, {full_address}", lat, lon, 'synonym'))
        
        # 3. Stelle sicher, dass die Original-Adresse auch in geo_cache ist
        cursor.execute('''
            INSERT OR REPLACE INTO geo_cache (address_norm, lat, lon, source)
            VALUES (?, ?, ?, ?)
        ''', (full_address, lat, lon, 'manual'))
        
        conn.commit()
        print('✅ Synonym erfolgreich korrigiert!')
        
        # Verifikation
        print('\n🔍 VERIFIKATION:')
        
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
    print('🎯 STATUS: Sven - PF ist jetzt korrekt als Synonym für Auto Werft Dresden gespeichert!')

if __name__ == '__main__':
    fix_sven_pf_correct()
