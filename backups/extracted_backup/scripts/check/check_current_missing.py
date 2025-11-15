#!/usr/bin/env python3
"""
Aktuelle Analyse der wirklich noch fehlenden Adressen
"""
import sys
from pathlib import Path
from collections import defaultdict

# Projekt-Root zum Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get

def check_current_missing():
    """Prüfe welche Adressen aktuell noch nicht geocodiert sind"""
    print(f"🔍 AKTUELLE FEHLENDE ADRESSEN:")
    print("=" * 80)
    
    tour_plan_dir = Path('tourplaene')
    all_csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    missing_addresses = defaultdict(list)
    total_customers = 0
    missing_count = 0

    for csv_file in all_csv_files:
        try:
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            customers = tour_data.get('customers', [])
            total_customers += len(customers)
            
            for customer in customers:
                full_address = customer.get('address')
                customer_id = customer.get('customer_id')
                customer_name = customer.get('name')
                
                if full_address and not geo_get(full_address):
                    missing_addresses[full_address].append({
                        'customer_id': customer_id,
                        'customer_name': customer_name,
                        'file': csv_file.name
                    })
                    missing_count += 1
                    
        except Exception as e:
            print(f"❌ Fehler beim Verarbeiten von {csv_file.name}: {e}")

    print(f"📊 GESAMTSTATISTIK:")
    print(f"  Gesamt Kunden: {total_customers}")
    print(f"  Fehlende Adressen: {missing_count}")
    print(f"  Erkennungsrate: {((total_customers - missing_count) / total_customers * 100):.1f}%")
    
    print(f"\n📋 FEHLENDE ADRESSEN (Top 20):")
    print("-" * 50)
    
    sorted_missing = sorted(missing_addresses.items(), key=lambda x: len(x[1]), reverse=True)
    
    for i, (addr, customers) in enumerate(sorted_missing[:20]):
        print(f"{i+1:2d}. {addr} ({len(customers)}x)")
        if customers:
            first_customer = customers[0]
            print(f"     Beispiel: Kunde {first_customer['customer_id']} ({first_customer['customer_name']})")
        print()

if __name__ == "__main__":
    check_current_missing()
