#!/usr/bin/env python3
"""
Debug der Astral UG Suche
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from common.normalize import _find_complete_address_by_plz_name, clear_address_cache

def debug_astral_search():
    """Debug die Astral UG Suche"""
    print('🔍 DEBUG ASTRAL UG SUCHE:')
    print('=' * 50)
    
    clear_address_cache()
    
    # Test verschiedene Varianten
    test_cases = [
        ('Astral UG', '01159'),
        ('astral ug', '01159'),
        ('ASTRAL UG', '01159'),
        ('Astral', '01159'),
        ('UG', '01159'),
    ]
    
    for name, plz in test_cases:
        result = _find_complete_address_by_plz_name(name, plz)
        print(f'   "{name}" + "{plz}": "{result}"')
    
    print()
    
    # Manuell in CSV suchen
    print('🔍 MANUELLE CSV-SUCHE:')
    tour_plan_dir = Path('tourplaene')
    csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    for csv_file in csv_files[:3]:  # Nur erste 3 Dateien
        print(f'\n📁 {csv_file.name}:')
        try:
            with open(csv_file, 'r', encoding='cp850', errors='ignore') as f:
                lines = f.readlines()
            
            # Header finden
            header_line = None
            for i, line in enumerate(lines):
                if 'Kdnr' in line and 'Name' in line and 'Straße' in line:
                    header_line = i
                    break
            
            if header_line is not None:
                # Nach Astral suchen
                for i, line in enumerate(lines[header_line + 1:], header_line + 1):
                    if 'astral' in line.lower():
                        parts = line.strip().split(';')
                        if len(parts) >= 6:
                            print(f'   Zeile {i}: {parts[1]} | {parts[2]} | {parts[3]} | {parts[4]}')
                            
        except Exception as e:
            print(f'   Fehler: {e}')

if __name__ == '__main__':
    debug_astral_search()
