#!/usr/bin/env python3
"""
Test der Integration der zentralen Adress-Normalisierung
"""
import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict

def test_dreihundert_normalization():
    """Test: Prüfe ob Dreihundert Dresden normalisiert wird"""
    print("🧪 Teste Dreihundert Dresden Normalisierung...")
    
    # Teste verschiedene CSV-Dateien
    test_files = [
        'tourplaene/Tourenplan 01.09.2025.csv',
        'tourplaene/Tourenplan 25.08.2025.csv',
        'tourplaene/Tourenplan 06.10.2025.csv'  # Der neue Plan mit Dreihundert
    ]
    
    total_dreihundert = 0
    total_pipe_addresses = 0
    
    for csv_file in test_files:
        try:
            print(f"\n📁 Teste: {csv_file}")
            result = parse_tour_plan_to_dict(csv_file)
            customers = result.get('customers', [])
            
            # Suche nach Dreihundert Dresden
            dreihundert = [c for c in customers if 'Dreihundert' in c.get('name', '')]
            total_dreihundert += len(dreihundert)
            
            print(f"  Dreihundert Kunden: {len(dreihundert)}")
            
            for i, customer in enumerate(dreihundert[:2]):
                name = customer.get('name', 'UNBEKANNT')
                address = customer.get('address', 'KEINE ADRESSE')
                street = customer.get('street', '')
                
                print(f"    {i+1}. {name}")
                print(f"       Street: {street}")
                print(f"       Address: {address}")
                print(f"       Pipe in Address: {'|' in address}")
            
            # Prüfe Pipe-Adressen
            pipe_addresses = [c for c in customers if '|' in c.get('address', '')]
            total_pipe_addresses += len(pipe_addresses)
            print(f"  Pipe-Adressen: {len(pipe_addresses)}")
                
        except Exception as e:
            print(f"  ❌ Fehler bei {csv_file}: {e}")
    
    print(f"\n📊 GESAMTERGEBNIS:")
    print(f"  Dreihundert Kunden gesamt: {total_dreihundert}")
    print(f"  Pipe-Adressen gesamt: {total_pipe_addresses}")
    
    if total_pipe_addresses > 0:
        print("❌ PROBLEM: Es gibt noch Adressen mit Pipe-Zeichen!")
        return False
    else:
        print("✅ ERFOLG: Alle Adressen sind normalisiert!")
        return True

if __name__ == "__main__":
    success = test_dreihundert_normalization()
    print(f"\n🎯 Test {'erfolgreich' if success else 'fehlgeschlagen'}!")
    sys.exit(0 if success else 1)
