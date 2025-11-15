#!/usr/bin/env python3
"""
FINALE ERKENNUNGSRATE TEST
Testet die 100% Erkennungsrate nach allen Fixes
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

def test_final_recognition_rate():
    """Teste die finale Erkennungsrate"""
    
    print('🎯 FINALE ERKENNUNGSRATE TEST:')
    print('=' * 50)
    
    from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
    
    # Teste einen repräsentativen Tourplan
    csv_file = 'tourplaene/Tourenplan 01.09.2025.csv'
    tour_data = parse_tour_plan_to_dict(csv_file)
    
    customers = tour_data.get('customers', [])
    total_customers = len(customers)
    
    print(f'📊 GESAMT KUNDEN: {total_customers}')
    print()
    
    # Kategorisiere Kunden
    geocoded = 0
    bar_customers = 0
    bar_geocoded = 0
    missing_addresses = []
    
    for customer in customers:
        name = customer.get('name', '')
        street = customer.get('street', '')
        postal_code = customer.get('postal_code', '')
        city = customer.get('city', '')
        address = customer.get('address', '')
        is_bar = customer.get('bar_flag', False)
        
        # Prüfe ob Adresse vollständig ist
        is_complete = (street and street.lower() not in ['nan', ''] and
                      postal_code and postal_code.lower() not in ['nan', ''] and
                      city and city.lower() not in ['nan', ''])
        
        if is_complete:
            geocoded += 1
            if is_bar:
                bar_geocoded += 1
        else:
            missing_addresses.append({
                'name': name,
                'street': street,
                'postal_code': postal_code,
                'city': city,
                'address': address,
                'is_bar': is_bar
            })
        
        if is_bar:
            bar_customers += 1
    
    # Berechne Erkennungsrate
    recognition_rate = (geocoded / total_customers) * 100 if total_customers > 0 else 0
    bar_recognition_rate = (bar_geocoded / bar_customers) * 100 if bar_customers > 0 else 0
    
    print(f'✅ GEOCODED: {geocoded}/{total_customers} ({recognition_rate:.2f}%)')
    print(f'🏢 BAR-KUNDEN: {bar_customers}')
    print(f'✅ BAR GEOCODED: {bar_geocoded}/{bar_customers} ({bar_recognition_rate:.2f}%)')
    print()
    
    if missing_addresses:
        print(f'❌ FEHLENDE ADRESSEN: {len(missing_addresses)}')
        for i, missing in enumerate(missing_addresses, 1):
            print(f'  {i}. {missing["name"]} (BAR: {missing["is_bar"]})')
            print(f'     Street: "{missing["street"]}"')
            print(f'     PLZ: "{missing["postal_code"]}"')
            print(f'     Stadt: "{missing["city"]}"')
            print(f'     Address: "{missing["address"]}"')
            print()
    else:
        print('🎉 ALLE ADRESSEN SIND VOLLSTÄNDIG!')
    
    print(f'📊 FINALE ERKENNUNGSRATE: {recognition_rate:.2f}%')
    
    if recognition_rate >= 100.0:
        print('🏆 ZIEL ERREICHT: 100% ERKENNUNGSRATE!')
    elif recognition_rate >= 99.0:
        print('🎯 SEHR GUT: Fast 100% Erkennungsrate!')
    else:
        print('⚠️ VERBESSERUNG ERFORDERLICH')

if __name__ == '__main__':
    test_final_recognition_rate()
