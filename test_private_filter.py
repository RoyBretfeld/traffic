#!/usr/bin/env python3
"""
Test für Private Customer Filter
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.private_customer_filter import filter_private_customers, get_ignored_customers_summary
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get

def test_private_customer_filter():
    print('🧪 TEST PRIVATE CUSTOMER FILTER:')
    print('=' * 50)
    
    # Teste mit einer CSV-Datei
    csv_file = 'tourplaene/Tourenplan 09.09.2025.csv'
    tour_data = parse_tour_plan_to_dict(csv_file)
    customers = tour_data.get('customers', [])
    
    print(f'📊 Vor Filterung: {len(customers)} Kunden')
    
    # Filtere private Kunden heraus
    filtered_customers = filter_private_customers(customers)
    
    print(f'📊 Nach Filterung: {len(filtered_customers)} Kunden')
    print(f'📊 Ignoriert: {len(customers) - len(filtered_customers)} Kunden')
    
    # Prüfe Erkennungsrate nur für gefilterte Kunden
    geocoded_count = 0
    missing_addresses = []
    
    for customer in filtered_customers:
        address = customer.get('address')
        if address and geo_get(address):
            geocoded_count += 1
        elif address:
            missing_addresses.append(address)
    
    recognition_rate = (geocoded_count / len(filtered_customers)) * 100 if filtered_customers else 0
    
    print(f'\n📊 ERKENNUNGSRATE (ohne private Kunden):')
    print(f'  Geocodiert: {geocoded_count}/{len(filtered_customers)}')
    print(f'  Erkennungsrate: {recognition_rate:.1f}%')
    
    if missing_addresses:
        print(f'\n❌ Noch fehlende Adressen:')
        for addr in missing_addresses[:5]:  # Zeige nur erste 5
            print(f'  - {addr}')
    else:
        print(f'\n✅ Alle Adressen sind geocodiert!')
    
    # Zeige Zusammenfassung der ignorierten Kunden
    summary = get_ignored_customers_summary()
    print(f'\n📋 IGNORIERTE KUNDEN:')
    print(f'  Explizit ignorierte Kunden: {summary["total_ignored_customers"]}')
    print(f'  Ignor-Patterns: {summary["total_ignored_patterns"]}')

if __name__ == '__main__':
    test_private_customer_filter()
