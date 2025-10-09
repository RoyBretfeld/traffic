#!/usr/bin/env python3
"""
Füge die häufigsten nicht erkannten Kunden hinzu
"""

import sys
sys.path.append('.')
from backend.services.address_mapper import address_mapper

def add_remaining_customers():
    # Füge alle Kunden hinzu
    customers = [
        {
            'name': 'Auto Haase',
            'address': 'Coschützer Straße 46, 01705 Freital',
            'lat': 51.01362710956123,
            'lon': 13.670696708019069,
            'desc': 'BAR-Sondername für Auto Haase',
            'kategorie': 'autohaus'
        },
        {
            'name': 'Reifen Roespel GmbH',
            'address': 'Wilsdruffer Straße 7, 01705 Freital',
            'lat': 51.00946210262034,
            'lon': 13.653609796612802,
            'desc': 'BAR-Sondername für Reifen Roespel GmbH',
            'kategorie': 'reifenservice'
        },
        {
            'name': 'FTT Fahrzeug Technik Tharandt',
            'address': 'Dresdner Straße 36b, 01737 Tharandt',
            'lat': 50.98413405290646,
            'lon': 13.594823664067814,
            'desc': 'BAR-Sondername für FTT Fahrzeug Technik Tharandt',
            'kategorie': 'werkstatt'
        },
        {
            'name': 'Autohaus Hüttel',
            'address': 'Dresdner Landstr. 14 F, 01744 Oberhäßlich',
            'lat': 50.907906007826206,
            'lon': 13.691358468386824,
            'desc': 'BAR-Sondername für Autohaus Hüttel GmbH by Elitzsch',
            'kategorie': 'autohaus'
        },
        {
            'name': 'Marco Wagner',
            'address': 'Niedermühle 117, 01738 Dorfhain',
            'lat': 50.93817618042221,
            'lon': 13.567243939553348,
            'desc': 'BAR-Sondername für Marco Wagner',
            'kategorie': 'werkstatt'
        },
        {
            'name': '41 Roswitha',
            'address': 'Helmut Hammerschmidt KFZ',
            'lat': 51.01536990899636,
            'lon': 13.642450656740625,
            'desc': 'BAR-Sondername für 41 Roswitha (Helmut Hammerschmidt KFZ)',
            'kategorie': 'werkstatt'
        },
        {
            'name': '36 Nici zu RP',
            'address': 'Automatikgetriebeservice',
            'lat': 51.01285800880643,
            'lon': 13.80619352971347,
            'desc': 'BAR-Sondername für 36 Nici zu RP (Automatikgetriebeservice)',
            'kategorie': 'werkstatt'
        },
        {
            'name': 'Schleich',
            'address': 'Schleich',
            'lat': 50.936861237397174,
            'lon': 13.919838297223063,
            'desc': 'BAR-Sondername für Schleich',
            'kategorie': 'werkstatt'
        },
        {
            'name': 'Büttner',
            'address': 'Büttner',
            'lat': 50.998685726633234,
            'lon': 13.68799380277926,
            'desc': 'BAR-Sondername für Büttner',
            'kategorie': 'werkstatt'
        }
    ]

    for customer in customers:
        address_mapper.add_bar_sondername(
            sondername=customer['name'],
            echte_adresse=customer['address'],
            lat=customer['lat'],
            lon=customer['lon'],
            beschreibung=customer['desc'],
            kategorie=customer['kategorie']
        )
        print(f'[OK] Hinzugefügt: {customer["name"]}')

    print(f'\n[FERTIG] {len(customers)} Kunden hinzugefügt!')

if __name__ == "__main__":
    add_remaining_customers()
