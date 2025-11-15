#!/usr/bin/env python3
"""
Füge die häufigsten BAR-Sondernamen hinzu
"""

import sys
sys.path.append('.')
from backend.services.address_mapper import address_mapper

def add_frequent_bar_names():
    # Füge die häufigsten BAR-Sondernamen hinzu
    bar_names = [
        {
            'name': 'Sven - PF',
            'address': 'Str. des 17. Juni 11, 01257 Dresden',
            'lat': 51.00602518577978,
            'lon': 13.819573083730964,
            'desc': 'BAR-Sondername für Sven - PF (Auto Werft Dresden)',
            'kategorie': 'werkstatt'
        },
        {
            'name': 'Jochen - PF', 
            'address': 'Bärensteinerstr. 27-29, 01277 Dresden',
            'lat': 51.03535954672262,
            'lon': 13.803016081888194,
            'desc': 'BAR-Sondername für Jochen - PF (MotorMafia)',
            'kategorie': 'werkstatt'
        },
        {
            'name': 'MFH - PF',
            'address': 'Froebelstraße 20, 01159 Dresden',
            'lat': 51.052298189996804,
            'lon': 13.714614881889,
            'desc': 'BAR-Sondername für MFH - PF (MSM by HUBraum GmbH)',
            'kategorie': 'werkstatt'
        },
        {
            'name': 'MSM by HUBraum GmbH',
            'address': 'Fröbelstraße 20, 01159 Dresden',
            'lat': 51.052298189996804,
            'lon': 13.714614881889,
            'desc': 'BAR-Sondername für MSM by HUBraum GmbH',
            'kategorie': 'werkstatt'
        },
        {
            'name': 'Motoren-Frech GbR',
            'address': 'Hohensteiner Str. 101, 09212 Limbach-O./OT Pleißa',
            'lat': 50.86719536674177,
            'lon': 13.738570139550008,
            'desc': 'BAR-Sondername für Motoren-Frech GbR',
            'kategorie': 'werkstatt'
        }
    ]

    for bar in bar_names:
        address_mapper.add_bar_sondername(
            sondername=bar['name'],
            echte_adresse=bar['address'],
            lat=bar['lat'],
            lon=bar['lon'],
            beschreibung=bar['desc'],
            kategorie=bar['kategorie']
        )
        print(f'[OK] Hinzugefügt: {bar["name"]}')

    print(f'\n[FERTIG] {len(bar_names)} BAR-Sondernamen hinzugefügt!')

if __name__ == "__main__":
    add_frequent_bar_names()
