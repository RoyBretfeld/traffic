#!/usr/bin/env python3
"""
Analysiere die ignorierten Privatkunden - prüfe welche gültige Adressen haben
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.private_customer_filter import is_private_customer
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get

def analyze_ignored_private_customers():
    print('🔍 ANALYSE DER IGNORIERTEN PRIVATKUNDEN:')
    print('=' * 70)
    
    tour_plan_dir = Path('tourplaene')
    all_csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    ignored_customers = []
    valid_address_customers = []
    invalid_address_customers = []
    
    for csv_file in all_csv_files:
        try:
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            customers = tour_data.get('customers', [])
            
            for customer in customers:
                if is_private_customer(customer):
                    ignored_customers.append({
                        'file': csv_file.name,
                        'customer_id': customer.get('customer_id'),
                        'name': customer.get('name'),
                        'address': customer.get('address'),
                        'street': customer.get('street'),
                        'postal_code': customer.get('postal_code'),
                        'city': customer.get('city'),
                        'bar_flag': customer.get('bar_flag')
                    })
                    
        except Exception as e:
            print(f'❌ Fehler bei {csv_file.name}: {e}')
    
    print(f'📊 GESAMT IGNORIERTE KUNDEN: {len(ignored_customers)}')
    print('=' * 70)
    
    # Kategorisiere die ignorierten Kunden
    for customer in ignored_customers:
        address = customer['address']
        street = customer['street']
        postal_code = customer['postal_code']
        city = customer['city']
        
        # Prüfe ob die Adresse gültig ist
        has_valid_address = (
            address and 
            address.strip() not in ['', 'nan', 'None'] and
            street and 
            street.strip() not in ['', 'nan', 'None'] and
            postal_code and 
            postal_code.strip() not in ['', 'nan', 'None'] and
            city and 
            city.strip() not in ['', 'nan', 'None']
        )
        
        if has_valid_address:
            valid_address_customers.append(customer)
        else:
            invalid_address_customers.append(customer)
    
    print(f'✅ KUNDEN MIT GÜLTIGEN ADRESSEN: {len(valid_address_customers)}')
    print(f'❌ KUNDEN MIT UNVOLLSTÄNDIGEN ADRESSEN: {len(invalid_address_customers)}')
    print()
    
    # Zeige Kunden mit gültigen Adressen
    if valid_address_customers:
        print('📋 KUNDEN MIT GÜLTIGEN ADRESSEN (sollten ausgeliefert werden):')
        print('-' * 70)
        for i, customer in enumerate(valid_address_customers[:20], 1):  # Zeige erste 20
            print(f'{i:2d}. {customer["name"]} (KdNr: {customer["customer_id"]})')
            print(f'    Adresse: {customer["address"]}')
            print(f'    Datei: {customer["file"]}')
            print()
        
        if len(valid_address_customers) > 20:
            print(f'    ... und {len(valid_address_customers) - 20} weitere')
        print()
    
    # Zeige Kunden mit unvollständigen Adressen
    if invalid_address_customers:
        print('📋 KUNDEN MIT UNVOLLSTÄNDIGEN ADRESSEN (korrekt ignoriert):')
        print('-' * 70)
        for i, customer in enumerate(invalid_address_customers[:20], 1):  # Zeige erste 20
            print(f'{i:2d}. {customer["name"]} (KdNr: {customer["customer_id"]})')
            print(f'    Adresse: {customer["address"]}')
            print(f'    Straße: {customer["street"]}')
            print(f'    PLZ: {customer["postal_code"]}')
            print(f'    Ort: {customer["city"]}')
            print(f'    Datei: {customer["file"]}')
            print()
        
        if len(invalid_address_customers) > 20:
            print(f'    ... und {len(invalid_address_customers) - 20} weitere')
        print()
    
    # Prüfe Geocoding-Status für gültige Adressen
    if valid_address_customers:
        print('🗺️ GEOCODING-STATUS FÜR GÜLTIGE ADRESSEN:')
        print('-' * 70)
        geocoded_count = 0
        missing_count = 0
        
        for customer in valid_address_customers:
            address = customer['address']
            if geo_get(address):
                geocoded_count += 1
            else:
                missing_count += 1
                print(f'❌ NICHT GEOCODET: {customer["name"]} - {address}')
        
        print(f'✅ Geocodiert: {geocoded_count}')
        print(f'❌ Fehlend: {missing_count}')
        print(f'📊 Erkennungsrate: {geocoded_count/len(valid_address_customers)*100:.1f}%')

if __name__ == '__main__':
    analyze_ignored_private_customers()
