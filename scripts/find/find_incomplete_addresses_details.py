#!/usr/bin/env python3
"""
Details für unvollständige Adressen finden
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get

def find_incomplete_addresses_details():
    print('🔍 UNVOLLSTÄNDIGE ADRESSEN - VOLLSTÄNDIGE DETAILS:')
    print('=' * 80)
    
    # Unvollständige Adressen
    incomplete_addresses = [
        '01159 Dresden',
        'nan, nan Pulsnitz'
    ]
    
    tour_plan_dir = Path('tourplaene')
    all_csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    for csv_file in all_csv_files:
        try:
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            
            for i, customer in enumerate(tour_data.get('customers', [])):
                full_address = customer.get('address')
                customer_id = customer.get('customer_id')
                customer_name = customer.get('name')
                
                if full_address in incomplete_addresses:
                    print(f'📋 DATEI: {csv_file.name}')
                    print(f'   ZEILE: {i + 1} (in der Kundenliste)')
                    print(f'   KdNr: {customer_id}')
                    print(f'   Firma: {customer_name}')
                    print(f'   Adresse: {full_address}')
                    print(f'   Straße: {customer.get("street", "N/A")}')
                    print(f'   PLZ: {customer.get("postal_code", "N/A")}')
                    print(f'   Ort: {customer.get("city", "N/A")}')
                    print(f'   Bar-Flag: {customer.get("bar_flag", "N/A")}')
                    print('-' * 60)
                    
        except Exception as e:
            print(f'❌ Fehler bei {csv_file.name}: {e}')

if __name__ == "__main__":
    find_incomplete_addresses_details()
