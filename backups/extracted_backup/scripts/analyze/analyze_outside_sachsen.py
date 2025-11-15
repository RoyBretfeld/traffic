#!/usr/bin/env python3
"""
Analyse der Adressen außerhalb Sachsens
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

def analyze_outside_sachsen():
    """Analysiere Adressen außerhalb Sachsens"""
    print(f"🔍 ANALYSE: ADRESSEN AUSSERHALB SACHSENS")
    print("=" * 80)
    
    tour_plan_dir = Path('tourplaene')
    all_csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    # Sachsens PLZ-Bereiche (01xxx-09xxx)
    sachsen_plz_patterns = [
        "01", "02", "03", "04", "05", "06", "07", "08", "09"
    ]
    
    outside_sachsen = []
    total_customers = 0
    
    for csv_file in all_csv_files:
        try:
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            
            for customer in tour_data.get('customers', []):
                total_customers += 1
                full_address = customer.get('address')
                customer_id = customer.get('customer_id')
                customer_name = customer.get('name')
                
                if full_address and not geo_get(full_address):
                    # Prüfe PLZ
                    plz = ""
                    for part in full_address.split(','):
                        part = part.strip()
                        if part.isdigit() and len(part) == 5:
                            plz = part
                            break
                    
                    is_sachsen = any(plz.startswith(prefix) for prefix in sachsen_plz_patterns)
                    
                    if not is_sachsen and plz:
                        outside_sachsen.append({
                            'address': full_address,
                            'customer_id': customer_id,
                            'customer_name': customer_name,
                            'file': csv_file.name,
                            'plz': plz
                        })
                        
        except Exception as e:
            print(f"❌ Fehler bei {csv_file.name}: {e}")
    
    print(f"\n📊 GESAMTSTATISTIK:")
    print(f"  Gesamt Kunden: {total_customers}")
    print(f"  Außerhalb Sachsens: {len(outside_sachsen)}")
    print(f"  Anteil: {len(outside_sachsen)/total_customers:.1%}")
    
    print(f"\n🌍 ADRESSEN AUSSERHALB SACHSENS:")
    print("-" * 60)
    
    # Gruppiere nach Bundesland/Region
    by_region = defaultdict(list)
    
    for addr in outside_sachsen:
        plz = addr['plz']
        if plz.startswith('04'):
            region = "Thüringen"
        elif plz.startswith('06'):
            region = "Hessen"
        elif plz.startswith('99'):
            region = "Thüringen"
        elif plz.startswith('35'):
            region = "Hessen"
        elif plz.startswith('63'):
            region = "Hessen"
        elif plz.startswith('02'):
            region = "Brandenburg"
        else:
            region = f"Unbekannt (PLZ {plz[:2]})"
        
        by_region[region].append(addr)
    
    for region, addresses in by_region.items():
        print(f"\n📍 {region} ({len(addresses)} Adressen):")
        for addr in addresses:
            print(f"   Kunde {addr['customer_id']}: {addr['customer_name']}")
            print(f"   Adresse: {addr['address']}")
            print(f"   Datei: {addr['file']}")
            print()
    
    print(f"\n💡 EMPFEHLUNG:")
    if len(outside_sachsen) > 0:
        print(f"  - {len(outside_sachsen)} Kunden außerhalb Sachsens")
        print(f"  - Können für Tourenplanung relevant sein")
        print(f"  - Empfehlung: Geocodieren und in DB speichern")
        print(f"  - Tourenplanung kann dann entscheiden ob einbezogen")
    else:
        print(f"  - Alle Kunden sind in Sachsen")
        print(f"  - Keine weiteren Geocoding-Schritte nötig")

if __name__ == "__main__":
    analyze_outside_sachsen()
