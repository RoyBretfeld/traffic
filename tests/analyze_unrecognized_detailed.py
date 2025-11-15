#!/usr/bin/env python3
"""
Analysiere die 136 nicht erkannten Kunden und prüfe welche bereits in der Datenbank sind
"""

import requests
import sys
sys.path.append('.')
from backend.db.dao import get_kunde_id_by_name_adresse, get_kunde_by_id

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
                address = f"{customer.get('street', '')}, {customer.get('postal_code', '')} {customer.get('city', '')}".strip(', ')
                unrecognized.append({
                    'name': customer.get('name', ''),
                    'street': customer.get('street', ''),
                    'postal_code': customer.get('postal_code', ''),
                    'city': customer.get('city', ''),
                    'address': address,
                    'tour': tour.get('name', '')
                })

    print(f'NICHT ERKANNTE KUNDEN ({len(unrecognized)}):')
    print('=' * 60)

    # Prüfe jeden nicht erkannten Kunden in der Datenbank
    found_in_db = []
    not_found = []
    
    for i, customer in enumerate(unrecognized, 1):
        name = customer['name']
        address = customer['address']
        
        print(f'{i:3d}. {name}')
        if address:
            print(f'     Adresse: {address}')
        print(f'     Tour: {customer["tour"]}')
        
        # Prüfe in der Datenbank
        if name and address:
            kunde_id = get_kunde_id_by_name_adresse(name, address)
            if kunde_id:
                kunde_obj = get_kunde_by_id(kunde_id)
                if kunde_obj and kunde_obj.lat and kunde_obj.lon:
                    print(f'     [GEFUNDEN IN DB] ID: {kunde_id}, Koordinaten: {kunde_obj.lat}, {kunde_obj.lon}')
                    found_in_db.append({
                        'name': name,
                        'address': address,
                        'kunde_id': kunde_id,
                        'lat': kunde_obj.lat,
                        'lon': kunde_obj.lon
                    })
                else:
                    print(f'     [IN DB ABER OHNE KOORDINATEN] ID: {kunde_id}')
                    not_found.append(customer)
            else:
                print(f'     [NICHT IN DB]')
                not_found.append(customer)
        else:
            print(f'     [KEINE VOLLSTÄNDIGEN DATEN]')
            not_found.append(customer)
        print()

    print('\n' + '='*60)
    print('ZUSAMMENFASSUNG:')
    print(f'Gefunden in DB: {len(found_in_db)}')
    print(f'Nicht gefunden: {len(not_found)}')
    print(f'Gesamt: {len(unrecognized)}')
    
    if found_in_db:
        print('\nKUNDEN DIE IN DER DB GEFUNDEN WURDEN:')
        print('='*50)
        for customer in found_in_db:
            print(f'{customer["name"]} - {customer["address"]}')
            print(f'  ID: {customer["kunde_id"]}, Koordinaten: {customer["lat"]}, {customer["lon"]}')
            print()

if __name__ == "__main__":
    analyze_unrecognized_customers()
