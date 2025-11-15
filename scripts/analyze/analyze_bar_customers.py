#!/usr/bin/env python3
"""
ERWEITERTE PLZ + NAME-REGEL FÜR BAR-KUNDEN
Löst das Problem mit unvollständigen BAR-Kunden-Adressen
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

def analyze_bar_customers():
    """Analysiere BAR-Kunden mit unvollständigen Adressen"""
    
    print('🔍 ANALYSE BAR-KUNDEN PROBLEM:')
    print('=' * 50)
    
    # Lade CSV-Daten
    from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
    
    csv_file = 'tourplaene/Tourenplan 01.09.2025.csv'
    tour_data = parse_tour_plan_to_dict(csv_file)
    
    # Finde BAR-Kunden mit unvollständigen Adressen
    bar_customers = []
    for customer in tour_data["customers"]:
        if customer.get('bar_flag', False):
            street = customer.get('street', '')
            postal_code = customer.get('postal_code', '')
            city = customer.get('city', '')
            
            # Prüfe auf unvollständige Daten
            if (not street or street.lower() in ['nan', ''] or 
                not postal_code or postal_code.lower() in ['nan', ''] or
                not city or city.lower() in ['nan', '']):
                
                bar_customers.append({
                    'name': customer.get('name', ''),
                    'street': street,
                    'postal_code': postal_code,
                    'city': city,
                    'customer_number': customer.get('customer_number', '')
                })
    
    print(f'BAR-Kunden mit unvollständigen Adressen: {len(bar_customers)}')
    print()
    
    for i, customer in enumerate(bar_customers, 1):
        print(f'{i}. {customer["name"]} (KdNr: {customer["customer_number"]})')
        print(f'   Street: "{customer["street"]}"')
        print(f'   PLZ: "{customer["postal_code"]}"')
        print(f'   Stadt: "{customer["city"]}"')
        print()
    
    return bar_customers

def suggest_bar_customer_solution():
    """Schlage Lösung für BAR-Kunden vor"""
    
    print('💡 LÖSUNGSVORSCHLÄGE FÜR BAR-KUNDEN:')
    print('=' * 50)
    
    print('1. 🏢 DEPOT-ADRESSE FÜR BAR-KUNDEN:')
    print('   - BAR-Kunden ohne Adresse → Depot-Adresse verwenden')
    print('   - Depot: Stuttgarter Str. 33, 01189 Dresden')
    print('   - Begründung: BAR-Kunden werden am Depot abgeholt')
    print()
    
    print('2. 🔍 ERWEITERTE SUCHE:')
    print('   - Suche nach ähnlichen Namen in anderen CSV-Dateien')
    print('   - Verwende Fuzzy-Matching für Namen')
    print('   - Fallback auf Depot bei fehlenden Daten')
    print()
    
    print('3. 📋 MANUELLE ZUWEISUNG:')
    print('   - Liste der BAR-Kunden ohne Adresse')
    print('   - Manuelle Adress-Zuweisung über Interface')
    print('   - Speicherung in geo_manual Tabelle')
    print()
    
    print('4. 🎯 EMPFOHLENE IMPLEMENTIERUNG:')
    print('   - Erweitere normalize_address() um BAR-Kunden-Logik')
    print('   - Bei BAR-Kunden ohne Adresse → Depot-Adresse')
    print('   - Zusätzliche Suche nach ähnlichen Namen')

def create_bar_customer_fix():
    """Erstelle Fix für BAR-Kunden"""
    
    print('\n🛠️ IMPLEMENTIERUNG DES FIXES:')
    print('=' * 50)
    
    fix_code = '''
# Erweiterte normalize_address() Funktion für BAR-Kunden

def normalize_address(addr: str | None, customer_name: str | None = None, 
                     postal_code: str | None = None, is_bar_customer: bool = False) -> str:
    """
    Zentrale Adress-Normalisierung mit BAR-Kunden-Support.
    """
    
    # BAR-Kunden ohne Adresse → Depot-Adresse
    if is_bar_customer and (not addr or str(addr).strip().lower() in ['nan', '']):
        return "Stuttgarter Str. 33, 01189 Dresden"  # FAMO Depot
    
    # Bestehende PLZ + Name-Regel
    if (not addr or str(addr).strip().lower() in ['nan', '']) and customer_name and postal_code:
        full_address = _find_complete_address_by_plz_name(customer_name, postal_code)
        if full_address:
            return full_address
    
    # Bestehende Normalisierung...
    # ... (rest der Funktion)
'''
    
    print('Code für BAR-Kunden-Fix:')
    print(fix_code)

if __name__ == '__main__':
    bar_customers = analyze_bar_customers()
    suggest_bar_customer_solution()
    create_bar_customer_fix()
