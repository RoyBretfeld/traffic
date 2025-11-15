#!/usr/bin/env python3
"""
Test der PLZ + Name-Regel für unvollständige Adressen
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.normalize import normalize_address, clear_address_cache

def test_plz_name_rule():
    """Teste die PLZ + Name-Regel mit Astral UG"""
    print('🧪 TEST PLZ + NAME-REGEL:')
    print('=' * 50)
    
    # Cache leeren für sauberen Test
    clear_address_cache()
    
    # Test 1: Unvollständige Adresse (leere Straße)
    print('1. Unvollständige Adresse (leere Straße):')
    result1 = normalize_address('', 'Astral UG', '01159')
    print(f'   Input: "" + "Astral UG" + "01159"')
    print(f'   Output: "{result1}"')
    print(f'   ✅ Erfolg: {"Löbtauer Straße" in result1 if result1 else "❌"}\n')
    
    # Test 2: Unvollständige Adresse (nan)
    print('2. Unvollständige Adresse (nan):')
    result2 = normalize_address('nan', 'Astral UG', '01159')
    print(f'   Input: "nan" + "Astral UG" + "01159"')
    print(f'   Output: "{result2}"')
    print(f'   ✅ Erfolg: {"Löbtauer Straße" in result2 if result2 else "❌"}\n')
    
    # Test 3: Normale Adresse (sollte normalisiert werden)
    print('3. Normale Adresse (sollte normalisiert werden):')
    result3 = normalize_address('Hauptstraße 1, 01067 Dresden', 'Test GmbH', '01067')
    print(f'   Input: "Hauptstraße 1, 01067 Dresden" + "Test GmbH" + "01067"')
    print(f'   Output: "{result3}"')
    print(f'   ✅ Erfolg: {"Hauptstr. 1" in result3}\n')
    
    # Test 4: Unbekannter Kunde (sollte unverändert bleiben)
    print('4. Unbekannter Kunde (sollte unverändert bleiben):')
    result4 = normalize_address('', 'Unbekannter Kunde', '99999')
    print(f'   Input: "" + "Unbekannter Kunde" + "99999"')
    print(f'   Output: "{result4}"')
    print(f'   ✅ Erfolg: {result4 == ""}\n')
    
    # Test 5: Cache-Test (zweiter Aufruf sollte aus Cache kommen)
    print('5. Cache-Test (zweiter Aufruf):')
    clear_address_cache()  # Cache leeren
    result5a = normalize_address('', 'Astral UG', '01159')
    result5b = normalize_address('', 'Astral UG', '01159')
    print(f'   Erster Aufruf: "{result5a}"')
    print(f'   Zweiter Aufruf: "{result5b}"')
    print(f'   ✅ Erfolg: {result5a == result5b and "Löbtauer Straße" in result5a}\n')
    
    print('=' * 50)
    print('📊 TEST-ERGEBNIS:')
    success_count = sum([
        "Löbtauer Straße" in result1 if result1 else False,
        "Löbtauer Straße" in result2 if result2 else False,
        "Hauptstraße 1" in result3,
        result4 == "",
        result5a == result5b and "Löbtauer Straße" in result5a
    ])
    print(f'   Erfolgreiche Tests: {success_count}/5')
    print(f'   Status: {"✅ ALLE TESTS BESTANDEN" if success_count == 5 else "❌ EINIGE TESTS FEHLGESCHLAGEN"}')

if __name__ == '__main__':
    test_plz_name_rule()
