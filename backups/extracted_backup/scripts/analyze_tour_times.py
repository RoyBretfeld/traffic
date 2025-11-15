"""
Analysiert Tour-Zeiten und prüft warum Routen zu lang sind.

Nutzung:
    python scripts/analyze_tour_times.py "Tourenplan 08.09.2025.csv"
"""
import sys
import os
from pathlib import Path

# Füge Projekt-Root zum Python-Path hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from routes.workflow_api import _estimate_tour_time_without_return, _apply_sector_planning_to_w_tour
import json

def analyze_tour_file(csv_path: str):
    """Analysiert eine Tourplan-CSV und zeigt Zeitberechnungen"""
    
    if not os.path.exists(csv_path):
        print(f"[FEHLER] Datei nicht gefunden: {csv_path}")
        return
    
    print(f"=== Analysiere: {csv_path} ===\n")
    
    # Parse CSV
    try:
        tour_data = parse_tour_plan_to_dict(csv_path)
    except Exception as e:
        print(f"[FEHLER] Fehler beim Parsen: {e}")
        return
    
    tours = tour_data.get('tours', [])
    print(f"Gefundene Touren: {len(tours)}\n")
    
    for tour in tours:
        tour_name = tour.get('name', 'Unbekannt')
        customers = tour.get('customers', [])
        
        # Filtere Kunden mit Koordinaten
        customers_with_coords = [
            c for c in customers 
            if c.get('lat') and c.get('lon')
        ]
        
        if not customers_with_coords:
            print(f"[WARNUNG] {tour_name}: Keine Kunden mit Koordinaten")
            continue
        
        # Konvertiere zu Stops-Format
        stops = []
        for c in customers_with_coords:
            stops.append({
                'customer_number': c.get('customer_number', ''),
                'name': c.get('name', ''),
                'lat': float(c.get('lat')),
                'lon': float(c.get('lon')),
                'address': c.get('address', ''),
                'bar_flag': c.get('bar_flag', False)
            })
        
        # Berechne Zeit OHNE Rückfahrt
        time_without_return = _estimate_tour_time_without_return(stops)
        
        # Schätze Rückfahrt (vom letzten Stop zum Depot)
        if len(stops) > 0:
            last_stop = stops[-1]
            import math
            def haversine_distance(lat1, lon1, lat2, lon2):
                R = 6371.0
                lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
                dlat = lat2 - lat1
                dlon = lon2 - lon1
                a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
                return 2 * R * math.asin(math.sqrt(a))
            
            depot_lat, depot_lon = 51.0111988, 13.7016485
            return_distance = haversine_distance(
                last_stop['lat'], last_stop['lon'],
                depot_lat, depot_lon
            ) * 1.3  # Faktor für Stadtverkehr
            return_time = (return_distance / 50.0) * 60  # 50 km/h
        else:
            return_time = 0
        
        total_with_return = time_without_return + return_time
        
        # Prüfe ob W-Tour
        is_w_tour = tour_name.upper().startswith('W') or 'W-' in tour_name
        
        # Status
        status = "[OK]" if time_without_return <= 65 else "[ZU LANG]"
        
        print(f"{status} {tour_name}:")
        print(f"  Kunden: {len(customers_with_coords)}")
        print(f"  Zeit OHNE Rueckfahrt: {time_without_return:.1f} Min (Regel: <= 65 Min)")
        print(f"  Rueckfahrt: {return_time:.1f} Min")
        print(f"  Gesamt INKL. Rueckfahrt: {total_with_return:.1f} Min")
        print(f"  Ist W-Tour: {is_w_tour}")
        
        if time_without_return > 65:
            print(f"  PROBLEM: {time_without_return:.1f} Min > 65 Min (ohne Rueckfahrt)")
            print(f"     -> Sollte in mehrere Touren aufgeteilt werden!")
        
        print()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: python scripts/analyze_tour_times.py <csv-datei>")
        print("\nBeispiele:")
        print("  python scripts/analyze_tour_times.py \"tourplaene/Tourenplan 08.09.2025.csv\"")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    analyze_tour_file(csv_path)

