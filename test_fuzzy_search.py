#!/usr/bin/env python3
"""
TESTE FUZZY-SUCHE FÜR SVEN - PF
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

def test_fuzzy_search():
    """Teste die Fuzzy-Suche direkt"""
    
    print('🔍 TESTE FUZZY-SUCHE:')
    print('=' * 50)
    
    from common.normalize import normalize_address, clear_address_cache
    
    # Cache leeren
    clear_address_cache()
    
    # Test 1: Sven - PF mit nan PLZ
    print('1. Test: Sven - PF mit nan PLZ')
    result1 = normalize_address('', 'Sven - PF', 'nan')
    print(f'   Input: "" + "Sven - PF" + "nan"')
    print(f'   Output: "{result1}"')
    print(f'   ✅ Erfolg: {"An der Triebe" in result1 if result1 else "❌"}\n')
    
    # Test 2: Sven - PF ohne PLZ
    print('2. Test: Sven - PF ohne PLZ')
    result2 = normalize_address('', 'Sven - PF', None)
    print(f'   Input: "" + "Sven - PF" + None')
    print(f'   Output: "{result2}"')
    print(f'   ✅ Erfolg: {"An der Triebe" in result2 if result2 else "❌"}\n')
    
    # Test 3: Direkte Fuzzy-Match-Test
    print('3. Test: Direkte Fuzzy-Match-Test')
    from common.normalize import _fuzzy_name_match
    match1 = _fuzzy_name_match('Sven - PF', 'Sven Teichmann')
    match2 = _fuzzy_name_match('Sven - PF', 'Peter Söllner')
    print(f'   "Sven - PF" matches "Sven Teichmann": {match1}')
    print(f'   "Sven - PF" matches "Peter Söllner": {match2}')
    print()

if __name__ == '__main__':
    test_fuzzy_search()
