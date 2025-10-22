#!/usr/bin/env python3
"""
Extrahiere Kundennummern für fehlende Adressen direkt aus CSV-Dateien
"""
import sys
import glob
from pathlib import Path
from collections import Counter

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict

def find_customer_numbers_for_missing_addresses():
    """Finde Kundennummern für alle fehlenden Adressen"""
    print("🔍 KUNDENNUMMERN FÜR FEHLENDE ADRESSEN:")
    print("=" * 80)
    
    # Bekannte problematische Adressen (aus der Analyse)
    problematic_addresses = [
        "Hauptstr. 9a, 01728 Bannewitz",
        "An der Triebe 25, 01468 Moritzburg", 
        "Hauptstr. 1, 01809 Heidenau",
        "Hauptstr. 70, 01705 Freital",
        "Hohensteiner Str. 101, 09212 Limbach-O.",
        "Alte Str. 33, 01768 Glashütte OT Hirschbach",
        "Gersdorf 43, 01819 Bahretal OT Gersdorf",
        "Johnsbacher Hauptstr. 55, 01768 Glashütte",
        "Bergstraße 93, 01744 Dippoldiswalde OT Seifersdorf",
        "Reinberger Dorfstraße 6a, 01744 Dippoldiswalde",
        "Hauptstr. 16, 01816 Bad Gottleuba-Berggießhübel",
        "Hauptstr. 110, 01809 Heidenau",
        "Hauptstr. 122, 01816 Bad Gottleuba-Berggießhübel"
    ]
    
    print(f"📊 Suche nach {len(problematic_addresses)} problematischen Adressen")
    print("=" * 80)
    
    # Durchsuche alle CSV-Dateien nach Kundennummern
    files = glob.glob('tourplaene/*.csv')
    customer_data = {}  # addr -> [(file, customer_number, company_name)]
    
    for file_path in files:
        try:
            result = parse_tour_plan_to_dict(file_path)
            customers = result.get('customers', [])
            
            for customer in customers:
                addr = customer.get('address', '')
                if addr in problematic_addresses:
                    if addr not in customer_data:
                        customer_data[addr] = []
                    customer_data[addr].append((
                        file_path,
                        customer.get('customer_number', 'UNBEKANNT'),
                        customer.get('name', 'UNBEKANNT')
                    ))
                    
        except Exception as e:
            print(f"❌ Fehler beim Parsen von {file_path}: {e}")
    
    # Zeige Ergebnisse gruppiert nach Adresse
    counter = Counter()
    for addr, entries in customer_data.items():
        counter[addr] = len(entries)
    
    print("📋 TOP-PROBLEME (Häufigkeit):")
    print("-" * 50)
    for addr, count in counter.most_common(15):
        print(f"{count:2d}x {addr}")
        # Zeige erste Kundennummer als Beispiel
        if addr in customer_data:
            first_entry = customer_data[addr][0]
            print(f"    Beispiel: Kunde {first_entry[1]} ({first_entry[2]}) in {Path(first_entry[0]).name}")
        print()
    
    print("=" * 80)
    print("🔍 DETAILLIERTE KUNDENNUMMERN:")
    print("=" * 80)
    
    # Zeige alle Kundennummern für die Top-Probleme
    for addr, count in counter.most_common(10):
        print(f"\n📍 {addr} ({count}x):")
        if addr in customer_data:
            for file_path, customer_number, company_name in customer_data[addr]:
                file_name = Path(file_path).name
                print(f"   Kunde {customer_number}: {company_name} ({file_name})")

if __name__ == "__main__":
    find_customer_numbers_for_missing_addresses()