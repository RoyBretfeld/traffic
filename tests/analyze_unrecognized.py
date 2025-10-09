#!/usr/bin/env python3
"""
Analysiere nicht erkannte Kunden aus der Tourplan-Analyse
"""

import requests
import json

def analyze_unrecognized_customers():
    print("Lade Tourplan-Analyse...")
    
    response = requests.post('http://localhost:8111/api/tourplan-analysis')
    data = response.json()

    print('AKTUELLE STATISTIKEN:')
    print('Erkannt:', data.get('recognized_customers', 0))
    print('Nicht erkannt:', data.get('unrecognized_customers', 0))
    print('Erfolgsquote:', data.get('success_rate', 0), '%')
    print()

    # Sammle alle nicht erkannten Kunden
    unrecognized = []
    for tour in data.get('tours', []):
        for customer in tour.get('customers', []):
            if not customer.get('is_recognized', False):
                unrecognized.append({
                    'name': customer.get('name', ''),
                    'street': customer.get('street', ''),
                    'postal_code': customer.get('postal_code', ''),
                    'city': customer.get('city', ''),
                    'tour': tour.get('name', '')
                })

    print(f'NICHT ERKANNTE KUNDEN ({len(unrecognized)}):')
    print('=' * 50)

    # Zeige alle nicht erkannten Kunden
    for i, customer in enumerate(unrecognized, 1):
        address = f"{customer['street']}, {customer['postal_code']} {customer['city']}".strip(', ')
        print(f'{i:3d}. {customer["name"]}')
        print(f'     Adresse: {address}')
        print(f'     Tour: {customer["tour"]}')
        print()

    # Gruppiere nach Namen für bessere Analyse
    print('\nGRUPPIERUNG NACH NAMEN:')
    print('=' * 30)
    
    name_groups = {}
    for customer in unrecognized:
        name = customer['name']
        if name not in name_groups:
            name_groups[name] = []
        name_groups[name].append(customer)
    
    for name, customers in sorted(name_groups.items()):
        print(f'{name} ({len(customers)}x):')
        for customer in customers:
            address = f"{customer['street']}, {customer['postal_code']} {customer['city']}".strip(', ')
            print(f'  - {address} ({customer["tour"]})')
        print()

if __name__ == "__main__":
    analyze_unrecognized_customers()
