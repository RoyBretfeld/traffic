#!/usr/bin/env python3
"""
Debug der PLZ + Name-Regel
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.normalize import _find_complete_address_by_plz_name, clear_address_cache

def debug_plz_name_rule():
    """Debug die PLZ + Name-Suche"""
    print('🔍 DEBUG PLZ + NAME-SUCHE:')
    print('=' * 50)
    
    clear_address_cache()
    
    # Test 1: Direkte Suche nach Astral UG
    print('1. Direkte Suche nach Astral UG:')
    result = _find_complete_address_by_plz_name('Astral UG', '01159')
    print(f'   Suche: "Astral UG" + "01159"')
    print(f'   Ergebnis: "{result}"')
    print()
    
    # Test 2: Suche nach anderen Kunden
    print('2. Suche nach anderen Kunden:')
    test_cases = [
        ('Sven Teichmann', '01468'),
        ('Test GmbH', '01067'),
        ('Unbekannt', '99999')
    ]
    
    for name, plz in test_cases:
        result = _find_complete_address_by_plz_name(name, plz)
        print(f'   {name} + {plz}: "{result}"')
    
    print()
    
    # Test 3: CSV-Dateien durchsuchen
    print('3. CSV-Dateien durchsuchen:')
    tour_plan_dir = Path('tourplaene')
    csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    print(f'   Gefundene CSV-Dateien: {len(csv_files)}')
    
    # Erste CSV-Datei analysieren
    if csv_files:
        csv_file = csv_files[0]
        print(f'   Analysiere: {csv_file.name}')
        
        try:
            with open(csv_file, 'r', encoding='cp850', errors='ignore') as f:
                lines = f.readlines()
            
            print(f'   Zeilen in CSV: {len(lines)}')
            
            # Header finden
            header_line = None
            for i, line in enumerate(lines):
                if 'Kdnr' in line and 'Name' in line and 'Straße' in line:
                    header_line = i
                    print(f'   Header gefunden in Zeile {i}: {line.strip()}')
                    break
            
            if header_line is not None:
                # Erste Datenzeilen zeigen
                print(f'   Erste Datenzeilen:')
                for i, line in enumerate(lines[header_line + 1:header_line + 6]):
                    parts = line.strip().split(';')
                    if len(parts) >= 6:
                        print(f'     {i+1}. {parts[1]} | {parts[2]} | {parts[3]} | {parts[4]}')
                        
        except Exception as e:
            print(f'   Fehler: {e}')

if __name__ == '__main__':
    debug_plz_name_rule()
