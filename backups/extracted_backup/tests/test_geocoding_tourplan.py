#!/usr/bin/env python3
"""
Test-Script für Geocoding verschiedener Tourpläne
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from backend.services.geocode import geocode_address
from backend.db.dao import get_kunde_id_by_name_adresse, get_kunde_by_id
import json

def test_tourplan_geocoding(csv_file):
    """Teste Geocoding für einen Tourplan"""
    print(f"\nTESTE TOURPLAN: {csv_file}")
    print("=" * 60)
    
    try:
        # CSV parsen
        result = parse_tour_plan_to_dict(csv_file)
        
        if not result or 'tours' not in result:
            print("ERROR: CSV-Parsing fehlgeschlagen")
            return
            
        print(f"OK: CSV geparst: {len(result['tours'])} Touren gefunden")
        
        # Geocoding-Statistiken
        geocoding_stats = {
            "total": 0,
            "from_db": 0,
            "geocoded": 0,
            "failed": 0,
            "no_address": 0
        }
        
        # Alle Kunden durchgehen
        for tour in result['tours']:
            tour_name = tour.get('name', 'Unbekannt')
            customers = tour.get('customers', [])
            
            print(f"\nTour: {tour_name} ({len(customers)} Kunden)")
            
            for customer in customers:
                geocoding_stats["total"] += 1
                
                # Kunden-Daten extrahieren
                name = customer.get("name", "").strip()
                street = customer.get("street", "").strip()
                postal_code = customer.get("postal_code", "").strip()
                city = customer.get("city", "").strip()
                
                print(f"  Kunde: {name}")
                
                # Prüfen ob Adresse vollständig
                if not street or not postal_code or not city:
                    print(f"    ERROR: Unvollständige Adresse: {street}, {postal_code} {city}")
                    geocoding_stats["no_address"] += 1
                    continue
                
                full_address = f"{street}, {postal_code} {city}"
                
                # 1. VERSUCH: Aus Datenbank laden
                kunde_id = get_kunde_id_by_name_adresse(name, full_address)
                if kunde_id:
                    kunde_obj = get_kunde_by_id(kunde_id)
                    if kunde_obj and kunde_obj.lat and kunde_obj.lon:
                        print(f"    OK: Aus DB: {kunde_obj.lat}, {kunde_obj.lon}")
                        geocoding_stats["from_db"] += 1
                        continue
                
                # 2. VERSUCH: Geocoding
                print(f"    Geocoding: {full_address}")
                geo_result = geocode_address(full_address)
                
                if geo_result and geo_result.get('lat') and geo_result.get('lon'):
                    lat = geo_result['lat']
                    lon = geo_result['lon']
                    provider = geo_result.get('provider', 'unknown')
                    print(f"    OK: Geocoded: {lat}, {lon} (via {provider})")
                    geocoding_stats["geocoded"] += 1
                else:
                    print(f"    ERROR: Geocoding fehlgeschlagen")
                    geocoding_stats["failed"] += 1
        
        # Statistiken ausgeben
        print(f"\nGEOCODING-STATISTIKEN:")
        print(f"  Gesamt Kunden: {geocoding_stats['total']}")
        print(f"  Aus DB: {geocoding_stats['from_db']} ({geocoding_stats['from_db']/geocoding_stats['total']*100:.1f}%)")
        print(f"  Geocoded: {geocoding_stats['geocoded']} ({geocoding_stats['geocoded']/geocoding_stats['total']*100:.1f}%)")
        print(f"  Fehlgeschlagen: {geocoding_stats['failed']} ({geocoding_stats['failed']/geocoding_stats['total']*100:.1f}%)")
        print(f"  Unvollständige Adresse: {geocoding_stats['no_address']} ({geocoding_stats['no_address']/geocoding_stats['total']*100:.1f}%)")
        
        success_rate = (geocoding_stats['from_db'] + geocoding_stats['geocoded']) / geocoding_stats['total'] * 100
        print(f"\nERFOLGSQUOTE: {success_rate:.1f}%")
        
        return geocoding_stats
        
    except Exception as e:
        print(f"ERROR beim Testen von {csv_file}: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Teste verschiedene Tourpläne"""
    print("FAMO TrafficApp - Geocoding Test")
    print("=" * 50)
    
    # Test-Dateien
    test_files = [
        "tourplaene/Tourenplan 16.09.2025.csv",
        "tourplaene/Tourenplan 15.09.2025.csv", 
        "tourplaene/Tourenplan 14.08.2025.csv",
        "tourplaene/Tourenplan 13.08.2025.csv",
        "tourplaene/Tourenplan 12.08.2025.csv"
    ]
    
    all_stats = []
    
    for csv_file in test_files:
        if os.path.exists(csv_file):
            stats = test_tourplan_geocoding(csv_file)
            if stats:
                all_stats.append((csv_file, stats))
        else:
            print(f"WARNUNG: Datei nicht gefunden: {csv_file}")
    
    # Gesamtstatistik
    if all_stats:
        print(f"\nGESAMTSTATISTIK ({len(all_stats)} Pläne):")
        print("=" * 50)
        
        total_customers = sum(stats['total'] for _, stats in all_stats)
        total_from_db = sum(stats['from_db'] for _, stats in all_stats)
        total_geocoded = sum(stats['geocoded'] for _, stats in all_stats)
        total_failed = sum(stats['failed'] for _, stats in all_stats)
        total_no_address = sum(stats['no_address'] for _, stats in all_stats)
        
        print(f"  Gesamt Kunden: {total_customers}")
        print(f"  Aus DB: {total_from_db} ({total_from_db/total_customers*100:.1f}%)")
        print(f"  Geocoded: {total_geocoded} ({total_geocoded/total_customers*100:.1f}%)")
        print(f"  Fehlgeschlagen: {total_failed} ({total_failed/total_customers*100:.1f}%)")
        print(f"  Unvollständige Adresse: {total_no_address} ({total_no_address/total_customers*100:.1f}%)")
        
        overall_success = (total_from_db + total_geocoded) / total_customers * 100
        print(f"\nGESAMTERFOLGSQUOTE: {overall_success:.1f}%")
        
        if overall_success >= 95:
            print("EXZELLENT! Geocoding funktioniert sehr gut!")
        elif overall_success >= 85:
            print("GUT! Geocoding funktioniert gut, kleine Verbesserungen möglich")
        elif overall_success >= 70:
            print("OK! Geocoding funktioniert, aber Verbesserungen nötig")
        else:
            print("SCHLECHT! Geocoding braucht dringend Verbesserungen")

if __name__ == "__main__":
    main()
