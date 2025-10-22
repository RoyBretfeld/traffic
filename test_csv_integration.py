#!/usr/bin/env python3
"""
Test der CSV-Integration mit PLZ + Name-Regel
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict

def test_csv_integration():
    """Teste die CSV-Integration mit der PLZ + Name-Regel"""
    print('🧪 TEST CSV-INTEGRATION MIT PLZ + NAME-REGEL:')
    print('=' * 60)
    
    # Test mit der CSV-Datei, die Astral UG mit leerer Straße hat
    csv_file = 'tourplaene/Tourenplan 09.09.2025.csv'
    
    try:
        print(f'📁 Verarbeite: {csv_file}')
        tour_data = parse_tour_plan_to_dict(csv_file)
        customers = tour_data.get('customers', [])
        
        print(f'📊 Gesamt Kunden: {len(customers)}')
        
        # Suche nach Astral UG
        astral_customers = [c for c in customers if 'Astral' in c.get('name', '')]
        print(f'🔍 Astral UG Kunden gefunden: {len(astral_customers)}')
        
        for i, customer in enumerate(astral_customers):
            name = customer.get('name', 'UNBEKANNT')
            street = customer.get('street', '')
            address = customer.get('address', '')
            customer_id = customer.get('customer_id', '')
            
            print(f'\n  {i+1}. Kunde {customer_id}: {name}')
            print(f'     Street: "{street}"')
            print(f'     Address: "{address}"')
            print(f'     ✅ PLZ+Name-Regel: {"Löbtauer Straße" in address if address else "❌"}')
        
        # Prüfe alle Kunden mit unvollständigen Adressen
        print(f'\n🔍 ALLE KUNDEN MIT UNVOLLSTÄNDIGEN ADRESSEN:')
        incomplete_customers = []
        for customer in customers:
            street = customer.get('street', '').strip()
            if not street or street.lower() in ['nan', '']:
                incomplete_customers.append(customer)
        
        print(f'📊 Unvollständige Adressen: {len(incomplete_customers)}')
        
        # Zeige die ersten 10 unvollständigen Adressen
        for i, customer in enumerate(incomplete_customers[:10]):
            name = customer.get('name', 'UNBEKANNT')
            street = customer.get('street', '')
            address = customer.get('address', '')
            customer_id = customer.get('customer_id', '')
            
            print(f'  {i+1}. Kunde {customer_id}: {name}')
            print(f'     Street: "{street}"')
            print(f'     Address: "{address}"')
            print(f'     ✅ Repariert: {"✅" if address and address != f", {customer.get("postal_code", "")} {customer.get("city", "")}" else "❌"}')
            print()
        
        # Statistiken
        repaired_count = 0
        for customer in incomplete_customers:
            address = customer.get('address', '')
            if address and address.strip():
                repaired_count += 1
        
        print(f'📊 STATISTIKEN:')
        print(f'   Unvollständige Adressen: {len(incomplete_customers)}')
        print(f'   Reparierte Adressen: {repaired_count}')
        print(f'   Reparatur-Rate: {repaired_count/len(incomplete_customers)*100:.1f}%' if incomplete_customers else '   Reparatur-Rate: N/A')
        
    except Exception as e:
        print(f'❌ Fehler beim Verarbeiten von {csv_file}: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_csv_integration()
