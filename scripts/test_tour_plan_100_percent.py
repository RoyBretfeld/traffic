#!/usr/bin/env python3
"""
Test-Skript für 100% Erkennungsrate
Analysiert Tourenplan 10.09.2025.csv und prüft:
- Alle Kunden werden erkannt
- Korrekte Anzahl pro Tour
- Keine Duplikate
- 100% Erkennungsrate
"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get
import logging

# Logging konfigurieren
logging.basicConfig(level=logging.INFO, format='%(message)s')

def test_tour_plan_100_percent():
    """Teste Tourenplan 10.09.2025.csv auf 100% Erkennungsrate"""
    
    csv_file = project_root / 'tourplaene' / 'Tourenplan 10.09.2025.csv'
    
    if not csv_file.exists():
        print(f"❌ Datei nicht gefunden: {csv_file}")
        return False
    
    print("\n" + "="*70)
    print("  TEST: 100% ERKENNUNGSRATE - Tourenplan 10.09.2025.csv")
    print("="*70 + "\n")
    
    try:
        # UTF-8 Encoding für Windows
        import sys
        if sys.platform == 'win32':
            import io
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        
        # Parse Tourplan
        print("[TEST] Lese Tourplan...")
        tour_data = parse_tour_plan_to_dict(str(csv_file))
        
        tours = tour_data.get('tours', [])
        all_customers = tour_data.get('customers', [])
        
        print(f"[OK] Tourplan gelesen: {len(tours)} Touren, {len(all_customers)} Kunden gesamt\n")
        
        # Prüfe jede Tour
        total_with_address = 0
        total_with_coords = 0
        total_without_coords = 0
        missing_addresses = []
        duplicate_customers = []
        
        tour_stats = []
        
        for tour in tours:
            tour_name = tour.get('name', 'Unbekannt')
            customers = tour.get('customers', [])
            
            # Prüfe auf Duplikate innerhalb der Tour
            seen = set()
            tour_duplicates = []
            for customer in customers:
                key = (
                    customer.get('customer_number', ''),
                    customer.get('name', ''),
                    customer.get('street', ''),
                    customer.get('postal_code', ''),
                    customer.get('city', '')
                )
                if key in seen:
                    tour_duplicates.append(customer.get('name', 'Unbekannt'))
                seen.add(key)
            
            # Statistiken für diese Tour
            tour_with_address = 0
            tour_with_coords = 0
            tour_without_coords = 0
            
            for customer in customers:
                street = customer.get('street', '').strip()
                postal_code = customer.get('postal_code', '').strip()
                city = customer.get('city', '').strip()
                lat = customer.get('lat')
                lon = customer.get('lon')
                
                # Hat vollständige Adresse?
                has_address = bool(street and postal_code and city and 
                                  street.lower() not in ['nan', ''] and
                                  postal_code.lower() not in ['nan', ''] and
                                  city.lower() not in ['nan', ''])
                
                if has_address:
                    tour_with_address += 1
                    total_with_address += 1
                    
                    # Hat Koordinaten?
                    if lat and lon:
                        tour_with_coords += 1
                        total_with_coords += 1
                    else:
                        # Versuche Geocoding
                        address = f"{street}, {postal_code} {city}"
                        geo_result = geo_get(address)
                        if geo_result:
                            tour_with_coords += 1
                            total_with_coords += 1
                        else:
                            tour_without_coords += 1
                            total_without_coords += 1
                            missing_addresses.append({
                                'tour': tour_name,
                                'name': customer.get('name', 'Unbekannt'),
                                'address': address
                            })
                else:
                    # Unvollständige Adresse
                    missing_addresses.append({
                        'tour': tour_name,
                        'name': customer.get('name', 'Unbekannt'),
                        'address': f"{street}, {postal_code} {city}".strip(', ')
                    })
            
            # Tour-Statistik speichern
            tour_stats.append({
                'name': tour_name,
                'total': len(customers),
                'bar_count': sum(1 for c in customers if c.get('bar_flag', False)),
                'with_address': tour_with_address,
                'with_coords': tour_with_coords,
                'without_coords': tour_without_coords,
                'duplicates': len(tour_duplicates),
                'duplicate_names': tour_duplicates
            })
        
        # Ausgabe der Ergebnisse
        print("="*70)
        print("📊 TOUR-STATISTIKEN")
        print("="*70 + "\n")
        
        for stat in tour_stats:
            tour_name = stat['name']
            total = stat['total']
            bar_count = stat['bar_count']
            with_coords = stat['with_coords']
            without_coords = stat['without_coords']
            duplicates = stat['duplicates']
            
            # Erkenne Tour-Typ
            is_w07 = 'W-07.00' in tour_name
            is_w09 = 'W-09.00' in tour_name
            
            status = "[OK]" if with_coords == total else "[WARN]"
            dup_status = "[DUP]" if duplicates > 0 else "[OK]"
            
            print(f"{status} {tour_name}")
            print(f"   Gesamt: {total} (BAR: {bar_count}, Normal: {total - bar_count})")
            
            if is_w07:
                expected_normal = 33
                expected_total = 36
                actual_normal = total - bar_count
                if actual_normal == expected_normal and total == expected_total:
                    print(f"   [OK] Erwartete Anzahl: {expected_normal} normal + {bar_count} BAR = {expected_total}")
                else:
                    print(f"   [WARN] Erwartet: {expected_normal} normal + {expected_total - expected_normal} BAR = {expected_total}")
                    print(f"   [WARN] Tatsaechlich: {actual_normal} normal + {bar_count} BAR = {total}")
            
            if is_w09:
                expected_normal = 30
                expected_total = 35
                actual_normal = total - bar_count
                if actual_normal == expected_normal and total == expected_total:
                    print(f"   [OK] Erwartete Anzahl: {expected_normal} normal + {bar_count} BAR = {expected_total}")
                else:
                    print(f"   [WARN] Erwartet: ~{expected_normal} normal + {expected_total - expected_normal} BAR = {expected_total}")
                    print(f"   [WARN] Tatsaechlich: {actual_normal} normal + {bar_count} BAR = {total}")
            
            print(f"   Mit Koordinaten: {with_coords}/{total} ({100*with_coords/total:.1f}%)")
            if without_coords > 0:
                print(f"   [WARN] Ohne Koordinaten: {without_coords}")
            if duplicates > 0:
                print(f"   {dup_status} Duplikate: {duplicates} ({', '.join(stat['duplicate_names'][:3])})")
            print()
        
        # Gesamt-Statistik
        print("="*70)
        print("📈 GESAMT-STATISTIK")
        print("="*70 + "\n")
        
        total_customers = len(all_customers)
        recognition_rate = (total_with_coords / total_customers * 100) if total_customers > 0 else 0
        
        print(f"Gesamt Kunden:           {total_customers}")
        print(f"Mit vollständiger Adresse: {total_with_address} ({100*total_with_address/total_customers:.1f}%)")
        print(f"Mit Koordinaten:         {total_with_coords} ({100*total_with_coords/total_customers:.1f}%)")
        print(f"Ohne Koordinaten:        {total_without_coords}")
        print(f"\n🎯 ERKENNUNGSRATE: {recognition_rate:.2f}%")
        
        # Fehlende Adressen
        if missing_addresses:
            print(f"\n[WARN] FEHLENDE ADRESSEN/KOORDINATEN: {len(missing_addresses)}")
            for i, missing in enumerate(missing_addresses[:10], 1):
                print(f"  {i}. [{missing['tour']}] {missing['name']}")
                print(f"     Adresse: {missing['address'] or '(leer)'}")
            if len(missing_addresses) > 10:
                print(f"  ... und {len(missing_addresses) - 10} weitere")
        else:
            print("\n[OK] ALLE ADRESSEN HABEN KOORDINATEN!")
        
        # Fazit
        print("\n" + "="*70)
        if recognition_rate >= 100.0:
            print("[SUCCESS] ZIEL ERREICHT: 100% ERKENNUNGSRATE!")
        elif recognition_rate >= 99.0:
            print(f"[GOOD] SEHR GUT: {recognition_rate:.2f}% Erkennungsrate (fast 100%)")
        else:
            print(f"[WARN] VERBESSERUNG ERFORDERLICH: {recognition_rate:.2f}% Erkennungsrate")
        print("="*70 + "\n")
        
        return recognition_rate >= 99.9
        
    except Exception as e:
        print(f"\n[ERROR] FEHLER: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = test_tour_plan_100_percent()
    sys.exit(0 if success else 1)

