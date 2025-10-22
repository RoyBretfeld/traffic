#!/usr/bin/env python3
"""
Fehlende Adressen mit Kundennummern finden
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get
from collections import defaultdict

def find_missing_with_customer_numbers():
    print('🔍 FEHLENDE ADRESSEN MIT KUNDENNUMMERN:')
    print('=' * 80)
    
    tour_plan_dir = Path('tourplaene')
    all_csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    missing_customer_data = defaultdict(list)
    
    for csv_file in all_csv_files:
        try:
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            
            for customer in tour_data.get('customers', []):
                full_address = customer.get('address')
                customer_id = customer.get('customer_id')
                customer_name = customer.get('name')
                
                if full_address and not geo_get(full_address):
                    missing_customer_data[full_address].append({
                        'customer_id': customer_id,
                        'customer_name': customer_name,
                        'file': csv_file.name
                    })
                    
        except Exception as e:
            print(f'❌ Fehler bei {csv_file.name}: {e}')
    
    print(f'📊 GESAMT: {len(missing_customer_data)} einzigartige fehlende Adressen')
    print()
    
    for i, (addr, customers) in enumerate(missing_customer_data.items(), 1):
        print(f'{i}. {addr}')
        for customer in customers:
            print(f'   KdNr: {customer["customer_id"]} | {customer["customer_name"]} | {customer["file"]}')
        print()

if __name__ == "__main__":
    find_missing_with_customer_numbers()
