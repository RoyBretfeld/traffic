#!/usr/bin/env python3
"""
Analysiere Olaf Streit Einträge
"""

import requests

def analyze_olaf_streit():
    response = requests.post('http://localhost:8111/api/tourplan-analysis')
    data = response.json()

    print('OLAF STREIT ANALYSE:')
    print('=' * 50)

    # Suche alle Olaf Streit Einträge
    olaf_entries = []
    for tour in data.get('tours', []):
        for customer in tour.get('customers', []):
            if 'Olaf Streit' in customer.get('name', ''):
                olaf_entries.append({
                    'name': customer.get('name', ''),
                    'street': customer.get('street', ''),
                    'postal_code': customer.get('postal_code', ''),
                    'city': customer.get('city', ''),
                    'tour': tour.get('name', ''),
                    'is_recognized': customer.get('is_recognized', False)
                })

    print(f'Gefunden: {len(olaf_entries)} Olaf Streit Einträge')
    print()

    for i, entry in enumerate(olaf_entries, 1):
        print(f'{i}. Name: {entry["name"]}')
        print(f'   Straße: {entry["street"]}')
        print(f'   PLZ: {entry["postal_code"]}')
        print(f'   Stadt: {entry["city"]}')
        print(f'   Tour: {entry["tour"]}')
        print(f'   Erkannt: {entry["is_recognized"]}')
        print()

if __name__ == "__main__":
    analyze_olaf_streit()
