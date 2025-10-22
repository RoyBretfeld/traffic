#!/usr/bin/env python3
"""
Test Astral UG Adress-Korrektur
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from common.normalize import normalize_address
from repositories.geo_repo import get as geo_get

def test_astral_fix():
    print('🧪 TEST ASTRAL UG ADRESS-KORREKTUR:')
    print('=' * 50)
    
    # Teste die Astral UG Adresse mit der neuen Korrektur
    address = 'Löbtauer Strae 89, 01159 Dresden'
    normalized = normalize_address(address)
    
    print(f'Original: {address}')
    print(f'Normalisiert: {normalized}')
    print(f'Korrektur funktioniert: {"Straße" in normalized}')
    
    # Prüfe ob im Geo-Cache vorhanden
    geo_result = geo_get(normalized)
    print(f'Im Geo-Cache: {geo_result is not None}')
    
    if geo_result:
        print(f'Koordinaten: {geo_result["lat"]}, {geo_result["lon"]}')

if __name__ == '__main__':
    test_astral_fix()
