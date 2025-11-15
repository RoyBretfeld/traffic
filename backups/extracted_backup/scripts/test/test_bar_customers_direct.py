#!/usr/bin/env python3
"""
DIREKTE ÜBERPRÜFUNG DER BAR-KUNDEN
Testet ob BAR-Kunden wirklich geocodiert sind
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

def test_bar_customers_direct():
    """Teste BAR-Kunden direkt"""
    
    print('🔍 DIREKTE ÜBERPRÜFUNG BAR-KUNDEN:')
    print('=' * 50)
    
    # Lade CSV-Daten
    from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
    
    csv_file = 'tourplaene/Tourenplan 01.09.2025.csv'
    tour_data = parse_tour_plan_to_dict(csv_file)
    
    # Finde alle BAR-Kunden
    bar_customers = []
    for customer in tour_data["customers"]:
        if customer.get('bar_flag', False):
            bar_customers.append({
                'name': customer.get('name', ''),
                'street': customer.get('street', ''),
                'postal_code': customer.get('postal_code', ''),
                'city': customer.get('city', ''),
                'address': customer.get('address', ''),
                'customer_number': customer.get('customer_number', '')
            })
    
    print(f'BAR-Kunden gefunden: {len(bar_customers)}')
    print()
    
    # Prüfe jeden BAR-Kunden
    for i, customer in enumerate(bar_customers, 1):
        print(f'{i}. {customer["name"]} (KdNr: {customer["customer_number"]})')
        print(f'   Street: "{customer["street"]}"')
        print(f'   PLZ: "{customer["postal_code"]}"')
        print(f'   Stadt: "{customer["city"]}"')
        print(f'   Address: "{customer["address"]}"')
        
        # Prüfe ob Adresse vollständig ist
        is_complete = (customer["street"] and customer["street"].lower() not in ['nan', ''] and
                      customer["postal_code"] and customer["postal_code"].lower() not in ['nan', ''] and
                      customer["city"] and customer["city"].lower() not in ['nan', ''])
        
        print(f'   ✅ Vollständig: {is_complete}')
        print()
    
    return bar_customers

def test_api_for_bar_customers():
    """Teste API für BAR-Kunden"""
    
    print('🔍 API-TEST FÜR BAR-KUNDEN:')
    print('=' * 50)
    
    # Teste API direkt
    from routes.tourplan_match import api_tourplan_match
    import asyncio
    
    async def test_api():
        try:
            result = await api_tourplan_match('tourplaene/Tourenplan 01.09.2025.csv')
            
            # Finde BAR-Kunden in API-Ergebnis
            bar_items = []
            for item in result['items']:
                if 'BAR' in item.get('customer_name', ''):
                    bar_items.append(item)
            
            print(f'BAR-Kunden in API-Ergebnis: {len(bar_items)}')
            print()
            
            for i, item in enumerate(bar_items, 1):
                print(f'{i}. {item["customer_name"]}')
                print(f'   Address: "{item["address"]}"')
                print(f'   Has Geo: {item["has_geo"]}')
                print(f'   Status: {item["status"]}')
                if item["has_geo"]:
                    print(f'   Geo: ({item["geo"]["lat"]}, {item["geo"]["lon"]})')
                print()
                
        except Exception as e:
            print(f'❌ API-Fehler: {e}')
    
    asyncio.run(test_api())

if __name__ == '__main__':
    bar_customers = test_bar_customers_direct()
    test_api_for_bar_customers()
