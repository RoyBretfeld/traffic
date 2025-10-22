#!/usr/bin/env python3
"""
Finde alle unvollständigen Adressen (ohne Straße) in den CSV-Dateien
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict

def find_incomplete_addresses():
    print('🔍 FINDE ALLE UNVOLLSTÄNDIGEN ADRESSEN:')
    print('=' * 60)
    
    tour_plan_dir = Path('tourplaene')
    all_csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    incomplete_addresses = []
    
    for csv_file in all_csv_files:
        try:
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            customers = tour_data.get('customers', [])
            
            for customer in customers:
                street = customer.get('street', '').strip()
                postal_code = customer.get('postal_code', '').strip()
                city = customer.get('city', '').strip()
                name = customer.get('name', '').strip()
                customer_id = customer.get('customer_id')
                
                # Prüfe ob Straße fehlt oder leer ist
                if not street or street.lower() in ['nan', '']:
                    incomplete_addresses.append({
                        'file': csv_file.name,
                        'customer_id': customer_id,
                        'name': name,
                        'street': street,
                        'postal_code': postal_code,
                        'city': city,
                        'full_address': f"{street}, {postal_code} {city}".strip(', ')
                    })
                    
        except Exception as e:
            print(f'❌ Fehler bei {csv_file.name}: {e}')
    
    print(f'📊 UNVOLLSTÄNDIGE ADRESSEN GEFUNDEN: {len(incomplete_addresses)}')
    print('=' * 60)
    
    # Gruppiere nach PLZ + Firmenname für bessere Übersicht
    grouped = {}
    for addr in incomplete_addresses:
        key = f"{addr['postal_code']} {addr['name']}"
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(addr)
    
    for key, addresses in grouped.items():
        print(f'\n📍 {key} ({len(addresses)}x):')
        for addr in addresses:
            print(f'   KdNr: {addr["customer_id"]} | Straße: "{addr["street"]}" | Datei: {addr["file"]}')
    
    # Prüfe ob es vollständige Adressen mit gleicher PLZ + Name gibt
    print(f'\n🔍 PRÜFE AUF VOLLSTÄNDIGE ADRESSEN MIT GLEICHER PLZ + NAME:')
    print('=' * 60)
    
    for csv_file in all_csv_files:
        try:
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            customers = tour_data.get('customers', [])
            
            for customer in customers:
                street = customer.get('street', '').strip()
                postal_code = customer.get('postal_code', '').strip()
                city = customer.get('city', '').strip()
                name = customer.get('name', '').strip()
                customer_id = customer.get('customer_id')
                
                # Prüfe ob es eine vollständige Adresse mit gleicher PLZ + Name gibt
                if street and street.lower() not in ['nan', '']:
                    key = f"{postal_code} {name}"
                    if key in grouped:
                        print(f'✅ VOLLSTÄNDIGE ADRESSE GEFUNDEN:')
                        print(f'   KdNr: {customer_id} | Name: {name}')
                        print(f'   Adresse: {street}, {postal_code} {city}')
                        print(f'   Datei: {csv_file.name}')
                        print(f'   → Kann für {len(grouped[key])} unvollständige Adressen verwendet werden')
                        print()
                        
        except Exception as e:
            continue

if __name__ == '__main__':
    find_incomplete_addresses()
