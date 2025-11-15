from pathlib import Path
import json
import sys
import os

# Füge den Backend-Ordner zum Python-Pfad hinzu
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.parsers import parse_tour_plan_to_dict


def test_csv_parser():
    """Testet den neuen CSV-Parser mit einer Tourenplan-Datei."""
    csv_file_path = Path("tourplaene/Tourenplan 14.08.2025.csv")
    
    if not csv_file_path.exists():
        print(f"Fehler: CSV-Datei nicht gefunden unter {csv_file_path.resolve()}")
        return
    
    print(f"Starte Test des neuen CSV-Parsers für {csv_file_path}")
    print("=" * 60)
    
    try:
        # Test 1: Hauptparser
        print("Test 1: parse_tour_plan_to_dict()")
        print("-" * 40)
        parsed_data = parse_tour_plan_to_dict(str(csv_file_path))
        
        print("Parsing erfolgreich!")
        print(f"Lieferdatum: {parsed_data.get('metadata', {}).get('delivery_date', 'N/A')}")
        print(f"Gesamtkunden: {parsed_data.get('stats', {}).get('total_customers', 'N/A')}")
        print(f"Touren gefunden: {len(parsed_data.get('tours', []))}")
        
        # Tour-Details anzeigen
        for i, tour in enumerate(parsed_data.get('tours', [])[:3]):  # Erste 3 Touren
            print(f"  Tour {i+1}: {tour.get('tour_type', 'N/A')} um {tour.get('time', 'N/A')}")
            print(f"    Kunden: {len(tour.get('customers', []))}")
        
        print()
        
        # Test 2: Zusammenfassung
        print("Parsing abgeschlossen!")
        
    except Exception as e:
        print(f"Fehler beim Testen des CSV-Parsers: {e}")
        import traceback
        traceback.print_exc()


def test_multiple_csv_files():
    """Testet mehrere CSV-Dateien im tourplaene-Ordner."""
    tourplaene_dir = Path("tourplaene")
    
    if not tourplaene_dir.exists():
        print(f"Fehler: tourplaene-Ordner nicht gefunden")
        return
    
    csv_files = list(tourplaene_dir.glob("*.csv"))
    
    if not csv_files:
        print("Keine CSV-Dateien im tourplaene-Ordner gefunden")
        return
    
    print(f"Teste {len(csv_files)} CSV-Dateien...")
    print("=" * 60)
    
    for csv_file in csv_files:
        print(f"\nTeste: {csv_file.name}")
        print("-" * 40)
        
        try:
            parsed = parse_tour_plan_to_dict(str(csv_file))
            stats = parsed.get('stats', {})
            print("Erfolgreich geparst:")
            print(f"  Datum: {parsed.get('metadata', {}).get('delivery_date', 'N/A')}")
            print(f"  Touren: {stats.get('total_tours', 'N/A')}")
            print(f"  Kunden: {stats.get('total_customers', 'N/A')}")

        except Exception as e:
            print(f"Fehler: {e}")


if __name__ == "__main__":
    print("CSV-Parser Test Suite")
    print("=" * 60)
    
    # Einzelnen Parser testen
    test_csv_parser()
    
    print("\n" + "=" * 60)
    
    # Mehrere Dateien testen
    test_multiple_csv_files()
