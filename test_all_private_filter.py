#!/usr/bin/env python3
"""
Test Private Customer Filter für alle CSV-Dateien
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.private_customer_filter import filter_private_customers
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get

def test_all_csv_files():
    print('🧪 TEST PRIVATE CUSTOMER FILTER - ALLE CSV-DATEIEN:')
    print('=' * 70)
    
    tour_plan_dir = Path('tourplaene')
    all_csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    total_customers = 0
    total_filtered = 0
    total_ignored = 0
    total_geocoded = 0
    
    for csv_file in all_csv_files:
        try:
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            customers = tour_data.get('customers', [])
            
            # Filtere private Kunden
            filtered_customers = filter_private_customers(customers)
            
            # Zähle geocodierte Adressen
            geocoded_count = 0
            for customer in filtered_customers:
                address = customer.get('address')
                if address and geo_get(address):
                    geocoded_count += 1
            
            ignored_count = len(customers) - len(filtered_customers)
            recognition_rate = (geocoded_count / len(filtered_customers)) * 100 if filtered_customers else 0
            
            print(f'📁 {csv_file.name}:')
            print(f'   Vorher: {len(customers)}, Nachher: {len(filtered_customers)}, Ignoriert: {ignored_count}')
            print(f'   Geocodiert: {geocoded_count}/{len(filtered_customers)} ({recognition_rate:.1f}%)')
            
            total_customers += len(customers)
            total_filtered += len(filtered_customers)
            total_ignored += ignored_count
            total_geocoded += geocoded_count
            
        except Exception as e:
            print(f'❌ Fehler bei {csv_file.name}: {e}')
    
    # Gesamtstatistik
    overall_recognition_rate = (total_geocoded / total_filtered) * 100 if total_filtered else 0
    
    print(f'\n📊 GESAMTSTATISTIK:')
    print(f'  Gesamt Kunden: {total_customers}')
    print(f'  Nach Filterung: {total_filtered}')
    print(f'  Ignoriert (Privatkunden): {total_ignored}')
    print(f'  Geocodiert: {total_geocoded}/{total_filtered}')
    print(f'  Erkennungsrate: {overall_recognition_rate:.1f}%')
    
    if overall_recognition_rate >= 100.0:
        print(f'\n🎉 PERFEKT! 100% Erkennungsrate erreicht!')
    else:
        print(f'\n⚠️ Noch {total_filtered - total_geocoded} Adressen fehlen')

if __name__ == '__main__':
    test_all_csv_files()
