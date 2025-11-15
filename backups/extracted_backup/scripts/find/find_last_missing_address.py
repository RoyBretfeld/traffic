#!/usr/bin/env python3
"""
Finde die letzte fehlende Adresse
"""
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.private_customer_filter import filter_private_customers
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get

def find_last_missing_address():
    print('🔍 FINDE DIE LETZTE FEHLENDE ADRESSE:')
    print('=' * 60)
    
    tour_plan_dir = Path('tourplaene')
    all_csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    missing_addresses = []
    
    for csv_file in all_csv_files:
        try:
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            customers = tour_data.get('customers', [])
            
            # Filtere private Kunden
            filtered_customers = filter_private_customers(customers)
            
            for customer in filtered_customers:
                address = customer.get('address')
                if address and not geo_get(address):
                    missing_addresses.append({
                        'file': csv_file.name,
                        'customer_id': customer.get('customer_id'),
                        'name': customer.get('name'),
                        'address': address,
                        'street': customer.get('street'),
                        'postal_code': customer.get('postal_code'),
                        'city': customer.get('city')
                    })
                    
        except Exception as e:
            print(f'❌ Fehler bei {csv_file.name}: {e}')
    
    print(f'📊 FEHLENDE ADRESSEN GEFUNDEN: {len(missing_addresses)}')
    print('=' * 60)
    
    for i, missing in enumerate(missing_addresses, 1):
        print(f'{i}. {missing["name"]} (KdNr: {missing["customer_id"]})')
        print(f'   Adresse: {missing["address"]}')
        print(f'   Straße: {missing["street"]}')
        print(f'   PLZ: {missing["postal_code"]}')
        print(f'   Ort: {missing["city"]}')
        print(f'   Datei: {missing["file"]}')
        print()

if __name__ == '__main__':
    find_last_missing_address()
