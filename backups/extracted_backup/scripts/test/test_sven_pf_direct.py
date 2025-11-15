#!/usr/bin/env python3
"""
TESTE SVEN - PF DIREKT
Testet ob das Synonym im System funktioniert
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

def test_sven_pf_direct():
    """Teste Sven - PF direkt"""
    
    print('🔍 TESTE SVEN - PF DIREKT:')
    print('=' * 50)
    
    from settings import SETTINGS
    import sqlite3
    
    db_path = SETTINGS.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Test 1: Suche nach "Sven - PF" in geo_cache
    print('1. Suche nach "Sven - PF" in geo_cache:')
    cursor.execute('''
        SELECT address_norm, lat, lon, source
        FROM geo_cache
        WHERE address_norm LIKE ?
    ''', ('%Sven - PF%',))
    
    results = cursor.fetchall()
    if results:
        for result in results:
            print(f'   ✅ Gefunden: "{result[0]}" -> ({result[1]}, {result[2]}) [{result[3]}]')
    else:
        print('   ❌ Nicht gefunden')
    
    # Test 2: Suche nach "Str. des 17. Juni" in geo_cache
    print('\n2. Suche nach "Str. des 17. Juni" in geo_cache:')
    cursor.execute('''
        SELECT address_norm, lat, lon, source
        FROM geo_cache
        WHERE address_norm LIKE ?
    ''', ('%Str. des 17. Juni%',))
    
    results = cursor.fetchall()
    if results:
        for result in results:
            print(f'   ✅ Gefunden: "{result[0]}" -> ({result[1]}, {result[2]}) [{result[3]}]')
    else:
        print('   ❌ Nicht gefunden')
    
    # Test 3: Teste normalize_address mit Sven - PF
    print('\n3. Teste normalize_address mit Sven - PF:')
    from common.normalize import normalize_address, clear_address_cache
    
    clear_address_cache()
    
    # Test mit verschiedenen Eingaben
    test_cases = [
        ('', 'Sven - PF', 'nan'),
        ('nan', 'Sven - PF', 'nan'),
        ('', 'Sven - PF', '01257'),
        ('', 'Sven - PF', None),
    ]
    
    for i, (addr, name, plz) in enumerate(test_cases, 1):
        result = normalize_address(addr, name, plz)
        print(f'   Test {i}: "{addr}" + "{name}" + "{plz}" -> "{result}"')
        if 'Str. des 17. Juni' in result:
            print(f'   ✅ Erfolg!')
        else:
            print(f'   ❌ Fehlgeschlagen')
    
    conn.close()

if __name__ == '__main__':
    test_sven_pf_direct()
