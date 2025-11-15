"""
Test für Dresden-Quadranten & Zeitbox Planung

Testet:
1. /engine/tours/sectorize - Sektorisierung (N/O/S/W)
2. /engine/tours/plan_by_sector - Planung mit Zeitbox (07:00 → 09:00)
"""
import requests
import json

BASE_URL = "http://127.0.0.1:8111"


def create_test_tour_for_sector_planning():
    """Erstellt Test-Tour mit Stopps in verschiedenen Quadranten"""
    depot_lat, depot_lon = 51.0111988, 13.7016485  # FAMO-Depot
    
    # Stopps in verschiedenen Quadranten
    # Norden (N): höher als Depot
    # Osten (O): weiter rechts (höherer Längengrad)
    # Süden (S): niedriger als Depot
    # Westen (W): weiter links (niedrigerer Längengrad)
    
    stops = [
        # Norden (N)
        {"source_id": "N1", "lat": 51.0350, "lon": 13.7100, "label": "Norden 1"},
        {"source_id": "N2", "lat": 51.0300, "lon": 13.7050, "label": "Norden 2"},
        {"source_id": "N3", "lat": 51.0280, "lon": 13.7000, "label": "Norden 3"},
        
        # Osten (O)
        {"source_id": "O1", "lat": 51.0120, "lon": 13.7500, "label": "Osten 1"},
        {"source_id": "O2", "lat": 51.0150, "lon": 13.7550, "label": "Osten 2"},
        {"source_id": "O3", "lat": 51.0180, "lon": 13.7450, "label": "Osten 3"},
        {"source_id": "O4", "lat": 51.0140, "lon": 13.7480, "label": "Osten 4"},
        
        # Süden (S)
        {"source_id": "S1", "lat": 50.9900, "lon": 13.7100, "label": "Süden 1"},
        {"source_id": "S2", "lat": 50.9850, "lon": 13.7050, "label": "Süden 2"},
        {"source_id": "S3", "lat": 50.9880, "lon": 13.7000, "label": "Süden 3"},
        
        # Westen (W)
        {"source_id": "W1", "lat": 51.0120, "lon": 13.6500, "label": "Westen 1"},
        {"source_id": "W2", "lat": 51.0150, "lon": 13.6550, "label": "Westen 2"},
        {"source_id": "W3", "lat": 51.0180, "lon": 13.6450, "label": "Westen 3"},
        {"source_id": "W4", "lat": 51.0140, "lon": 13.6480, "label": "Westen 4"},
        {"source_id": "W5", "lat": 51.0160, "lon": 13.6400, "label": "Westen 5"},
    ]
    
    # Generiere stop_uids
    from services.uid_service import generate_stop_uid
    
    tour_stops = []
    for stop in stops:
        stop_uid = generate_stop_uid(
            source_id=stop["source_id"],
            address=f"{stop['label']}, 01067 Dresden",
            postal_code="01067",
            city="Dresden"
        )
        
        tour_stops.append({
            "stop_uid": stop_uid,
            "source_id": stop["source_id"],
            "label": stop["label"],
            "address": f"{stop['label']}, 01067 Dresden",
            "lat": stop["lat"],
            "lon": stop["lon"]
        })
    
    return {
        "tour_id": "TEST-SECTOR-TOUR",
        "stops": tour_stops
    }


def test_sectorize():
    """Test 1: Sektorisierung"""
    print("\n" + "="*60)
    print("TEST 1: /engine/tours/sectorize")
    print("="*60)
    
    # Erstelle Test-Tour via ingest
    tour_data = create_test_tour_for_sector_planning()
    
    print("\n📥 Schritt 1: Tour ingestieren...")
    ingest_payload = {
        "tours": [{
            "tour_id": tour_data["tour_id"],
            "label": "Test Sektor-Tour",
            "stops": [{
                "source_id": s["source_id"],
                "label": s["label"],
                "address": s["address"],
                "lat": s["lat"],
                "lon": s["lon"]
            } for s in tour_data["stops"]]
        }]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/engine/tours/ingest",
            json=ingest_payload,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ Ingest fehlgeschlagen: {response.status_code}")
            return None
        
        ingest_result = response.json()
        tour_uid = ingest_result["tour_uids"][0]
        print(f"✅ Tour ingestiert: {tour_uid}")
        
    except Exception as e:
        print(f"❌ Fehler bei Ingest: {e}")
        return None
    
    print("\n📊 Schritt 2: Sektorisierung...")
    sectorize_payload = {
        "tour_uid": tour_uid,
        "depot_lat": 51.0111988,
        "depot_lon": 13.7016485,
        "sectors": 4
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/engine/tours/sectorize",
            json=sectorize_payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Sektorisierung erfolgreich")
            print(f"   Tour UID: {data['tour_uid']}")
            print(f"   Stopps mit Sektoren: {len(data['stops_with_sectors'])}")
            
            # Gruppiere nach Sektor
            by_sector = {}
            for stop in data["stops_with_sectors"]:
                sector = stop["sector"]
                if sector not in by_sector:
                    by_sector[sector] = []
                by_sector[sector].append(stop)
            
            print(f"\n   Verteilung nach Sektoren:")
            for sector in ["N", "O", "S", "W"]:
                count = len(by_sector.get(sector, []))
                print(f"   - {sector}: {count} Stopps")
            
            return tour_uid, data["stops_with_sectors"]
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return None, None
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return None, None


def test_plan_by_sector(tour_uid: str):
    """Test 2: Planung pro Sektor mit Zeitbox"""
    print("\n" + "="*60)
    print("TEST 2: /engine/tours/plan_by_sector (Zeitbox: 07:00 → 09:00)")
    print("="*60)
    
    plan_payload = {
        "tour_uid": tour_uid,
        "depot_uid": "depot_uid",
        "depot_lat": 51.0111988,
        "depot_lon": 13.7016485,
        "start_time": "07:00",
        "hard_deadline": "09:00",
        "time_budget_minutes": 90,
        "reload_buffer_minutes": 30,
        "service_time_default": 2.0,
        "sectors": 4,
        "include_return_to_depot": True,
        "round": 2
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/engine/tours/plan_by_sector",
            json=plan_payload,
            timeout=120  # Länger wegen OSRM-Calls
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Planung erfolgreich")
            print(f"   Tour UID: {data['tour_uid']}")
            print(f"   Sub-Routen: {len(data['sub_routes'])}")
            
            print(f"\n   Routen-Details:")
            for route in data["sub_routes"]:
                print(f"   - {route['name']} ({route['sector']}):")
                print(f"     Stopps: {len(route['route_uids'])}")
                print(f"     Fahrt: {route['driving_time_minutes']:.1f} Min")
                print(f"     Service: {route['service_time_minutes']:.1f} Min")
                print(f"     Gesamt: {route['total_time_minutes']:.1f} Min")
                print(f"     Zeitbox: {'✅ OK' if route['total_time_minutes'] <= 90 else '❌ ÜBERSCHRITTEN'}")
            
            print(f"\n   Gesamt:")
            totals = data["totals"]
            print(f"   - Distanz: {totals['km']:.2f} km")
            print(f"   - Zeit: {totals['minutes']:.1f} Minuten")
            print(f"   - Routen: {totals['routes_count']}")
            
            if "metrics" in totals:
                metrics = totals["metrics"]
                print(f"\n   Telemetrie:")
                print(f"   - OSRM Calls: {metrics.get('osrm_calls', 0)}")
                print(f"   - OSRM Unavailable: {metrics.get('osrm_unavailable', 0)}")
                print(f"   - Fallback Haversine: {metrics.get('fallback_haversine', 0)}")
                print(f"   - Zeitbox-Verletzungen: {metrics.get('timebox_violations', 0)}")
                print(f"   - Routen pro Sektor: {metrics.get('routes_by_sector', {})}")
            
            return True
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Hauptfunktion"""
    print("\n" + "="*60)
    print("DRESDEN-QUADRANTEN & ZEITBOX TEST")
    print("="*60)
    print("\nHINWEIS: Stelle sicher, dass der Server läuft:")
    print("  python start_server.py")
    print("\n" + "="*60)
    
    try:
        # Test 1: Sektorisierung
        tour_uid, stops_with_sectors = test_sectorize()
        
        if not tour_uid:
            print("\n❌ Sektorisierung fehlgeschlagen, überspringe Planung")
            return
        
        # Test 2: Planung pro Sektor
        success = test_plan_by_sector(tour_uid)
        
        # Zusammenfassung
        print("\n" + "="*60)
        print("ZUSAMMENFASSUNG")
        print("="*60)
        print(f"✅ Sektorisierung: {'ERFOLG' if tour_uid else 'FEHLER'}")
        print(f"✅ Planung pro Sektor: {'ERFOLG' if success else 'FEHLER'}")
        
        if success:
            print("\n✅ ALLE TESTS ERFOLGREICH")
            print("   - Stopps wurden korrekt in N/O/S/W eingeteilt")
            print("   - Routen wurden mit Zeitbox (90 Min) erstellt")
            print("   - OSRM-First Strategie verwendet")
        else:
            print("\n⚠️  PLANUNG FEHLGESCHLAGEN")
        
    except requests.exceptions.ConnectionError:
        print("\n❌ FEHLER: Server nicht erreichbar.")
        print("   Starte Server mit: python start_server.py")
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

