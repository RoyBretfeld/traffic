"""
Test für W-07.00 Tour mit 30 Stopps → sollte in 5-6 Sub-Routen aufgeteilt werden
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8111"


def create_test_tour_w07_with_30_stops():
    """Erstellt Test-Tour W-07.00 mit 30 Stopps (realistische Koordinaten in Dresden)"""
    # Realistische Koordinaten in Dresden-Umgebung
    dresden_coords = [
        (51.0492, 13.6984),  # Fröbelstraße
        (51.0504, 13.7372),  # Hauptstraße
        (51.0531, 13.7073),  # Löbtauer Straße
        (51.0550, 13.7200),  # Pirnaische Straße
        (51.0580, 13.7400),  # Prager Straße
        (51.0450, 13.6900),  # Reick
        (51.0400, 13.6800),  # Niedersedlitz
        (51.0600, 13.7500),  # Neustadt
        (51.0350, 13.6700),  # Heidenau
        (51.0620, 13.7600),  # Pieschen
        (51.0480, 13.6950),  # Striesen
        (51.0560, 13.7300),  # Altstadt
        (51.0420, 13.6850),  # Dobritz
        (51.0390, 13.6750),  # Seidnitz
        (51.0540, 13.7150),  # Johannstadt
        (51.0460, 13.7000),  # Blasewitz
        (51.0370, 13.6650),  # Lockwitz
        (51.0610, 13.7550),  # Äußere Neustadt
        (51.0590, 13.7450),  # Innere Neustadt
        (51.0510, 13.7100),  # Südvorstadt
        (51.0430, 13.6880),  # Tolkewitz
        (51.0380, 13.6720),  # Laubegast
        (51.0470, 13.7020),  # Striesen-Süd
        (51.0520, 13.7080),  # Strehlen
        (51.0440, 13.6860),  # Gruna
        (51.0570, 13.7350),  # Innere Altstadt
        (51.0630, 13.7650),  # Pieschen-Süd
        (51.0360, 13.6680),  # Kleinzschachwitz
        (51.0410, 13.6830),  # Großzschachwitz
        (51.0555, 13.7220),  # Hellerau
    ]
    
    stops = []
    for i, (lat, lon) in enumerate(dresden_coords):
        stops.append({
            "customer_number": f"600{i+1}",
            "name": f"Test Kunde {i+1}",
            "address": f"Teststraße {i+1}, 01067 Dresden",
            "lat": lat,
            "lon": lon
        })
    
    return {
        "tour_id": "W-07.00",
        "stops": stops
    }


def test_optimize_and_split():
    """Test: Optimiere Tour und splitte sie"""
    print("="*60)
    print("TEST: W-07.00 mit 30 Stopps → Splitting")
    print("="*60)
    
    # 1. Erstelle Test-Tour
    tour_data = create_test_tour_w07_with_30_stops()
    print(f"\n✅ Test-Tour erstellt: {tour_data['tour_id']} mit {len(tour_data['stops'])} Stopps")
    
    # 2. Optimiere Tour
    print("\n📊 Schritt 1: Optimiere Tour...")
    try:
        response = requests.post(
            f"{BASE_URL}/api/tour/optimize",
            json=tour_data,
            timeout=60
        )
        
        if response.status_code != 200:
            print(f"❌ Optimierung fehlgeschlagen: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return
        
        optimize_result = response.json()
        print(f"✅ Optimierung erfolgreich")
        print(f"   Methode: {optimize_result.get('optimization_method', 'unknown')}")
        print(f"   Geschätzte Zeit: {optimize_result.get('estimated_total_time_minutes', 0):.1f} Minuten")
        print(f"   Optimierte Stopps: {len(optimize_result.get('optimized_stops', []))}")
        
        total_time = optimize_result.get('estimated_total_time_minutes', 0)
        estimated_routes = max(1, int(total_time / 60) + 1)
        print(f"   Erwartete Sub-Routen: ~{estimated_routes} (bei 60 Min pro Route)")
        
    except Exception as e:
        print(f"❌ Fehler bei Optimierung: {e}")
        return
    
    # 3. Simuliere Frontend-Splitting-Logik
    print("\n📦 Schritt 2: Splitting-Logik (Frontend-Simulation)...")
    optimized_stops = optimize_result.get('optimized_stops', [])
    if not optimized_stops:
        print("❌ Keine optimierten Stopps zum Aufteilen")
        return
    
    # Frontend-Logik (vereinfacht)
    max_time_per_route = 60
    service_time_per_stop = 2
    estimated_driving_time = optimize_result.get('estimated_driving_time_minutes', 0)
    estimated_service_time = optimize_result.get('estimated_service_time_minutes', len(optimized_stops) * 2)
    total_time_actual = optimize_result.get('estimated_total_time_minutes', estimated_driving_time + estimated_service_time)
    
    print(f"   Gesamtzeit: {total_time_actual:.1f} Min")
    print(f"   Fahrtzeit: {estimated_driving_time:.1f} Min")
    print(f"   Service-Zeit: {estimated_service_time:.1f} Min")
    
    if total_time_actual <= max_time_per_route:
        print(f"   ✅ Tour passt in eine Route ({total_time_actual:.1f} Min <= {max_time_per_route} Min)")
        print(f"   Anzahl Sub-Routen: 1")
        return
    
    # Berechne Splitting
    estimated_routes_needed = int(total_time_actual / max_time_per_route) + 1
    stops_per_route_estimate = len(optimized_stops) / estimated_routes_needed
    
    print(f"\n   Benötigte Routen (geschätzt): {estimated_routes_needed}")
    print(f"   Stopps pro Route (geschätzt): ~{stops_per_route_estimate:.1f}")
    
    # Simuliere Splitting mit Frontend-Logik
    sub_routes = []
    current_route = []
    current_driving_time = 0
    current_service_time = 0
    route_letter = 'A'
    
    # Frontend verwendet: 5 Min pro Stop geschätzt
    estimated_drive_time_per_stop = 5
    
    for stop in optimized_stops:
        estimated_drive_time = estimated_drive_time_per_stop if current_route else 0
        estimated_service_time_for_stop = service_time_per_stop
        total_for_stop = estimated_drive_time + estimated_service_time_for_stop
        
        if (current_driving_time + current_service_time + total_for_stop) <= max_time_per_route:
            current_route.append(stop)
            current_driving_time += estimated_drive_time
            current_service_time += estimated_service_time_for_stop
        else:
            if current_route:
                sub_routes.append({
                    "sub_route": route_letter,
                    "stops": len(current_route),
                    "driving_time": current_driving_time,
                    "service_time": current_service_time,
                    "total_time": current_driving_time + current_service_time
                })
                route_letter = chr(ord(route_letter) + 1)
            current_route = [stop]
            current_driving_time = estimated_drive_time
            current_service_time = estimated_service_time_for_stop
    
    if current_route:
        sub_routes.append({
            "sub_route": route_letter,
            "stops": len(current_route),
            "driving_time": current_driving_time,
            "service_time": current_service_time,
            "total_time": current_driving_time + current_service_time
        })
    
    print(f"\n✅ Splitting-Ergebnis:")
    print(f"   Anzahl Sub-Routen: {len(sub_routes)}")
    for i, sub_route in enumerate(sub_routes, 1):
        print(f"   Route {sub_route['sub_route']}: {sub_route['stops']} Stopps, "
              f"{sub_route['total_time']:.1f} Min (Fahrt: {sub_route['driving_time']:.1f}, Service: {sub_route['service_time']:.1f})")
    
    # Bewertung
    print(f"\n📊 BEWERTUNG:")
    if len(sub_routes) >= 5:
        print(f"   ✅ ERFOLG: {len(sub_routes)} Sub-Routen erstellt (erwartet: 5-6)")
    elif len(sub_routes) >= 3:
        print(f"   ⚠️  TEILWEISE: {len(sub_routes)} Sub-Routen (erwartet: 5-6, aber funktioniert)")
    else:
        print(f"   ❌ PROBLEM: Nur {len(sub_routes)} Sub-Routen (erwartet: 5-6)")
    
    # Prüfe ob alle Routen < 60 Min
    all_under_60 = all(sr['total_time'] <= 60 for sr in sub_routes)
    if all_under_60:
        print(f"   ✅ Alle Routen < 60 Minuten")
    else:
        print(f"   ⚠️  Einige Routen > 60 Minuten")


if __name__ == "__main__":
    print("\n" + "="*60)
    print("W-07.00 SPLITTING-TEST")
    print("="*60)
    print("\nHINWEIS: Stelle sicher, dass der Server läuft:")
    print("  python start_server.py")
    print("\n" + "="*60)
    
    try:
        test_optimize_and_split()
    except requests.exceptions.ConnectionError:
        print("\n❌ FEHLER: Server nicht erreichbar.")
        print("   Starte Server mit: python start_server.py")
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()

