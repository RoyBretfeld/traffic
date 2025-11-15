"""
Test-Skript für Phase 1: Basis-Funktionalität prüfen

Tests:
1. /api/tour/optimize Endpoint (alten Endpoint testen)
2. /engine/tours/ingest Endpoint (neue Engine-API testen)
3. /engine/tours/optimize Endpoint (OSRM-First Strategie)
4. /engine/tours/split Endpoint (Splitting-Logik)
"""
import requests
import json
from typing import Dict, List

BASE_URL = "http://127.0.0.1:8111"


def test_old_optimize_endpoint():
    """Test des alten /api/tour/optimize Endpoints"""
    print("\n" + "="*60)
    print("TEST 1: /api/tour/optimize (alter Endpoint)")
    print("="*60)
    
    test_stops = [
        {
            "customer_number": "1001",
            "name": "Test Kunde 1",
            "address": "Fröbelstraße 1, 01309 Dresden",
            "lat": 51.0492,
            "lon": 13.6984
        },
        {
            "customer_number": "1002",
            "name": "Test Kunde 2",
            "address": "Hauptstraße 10, 01067 Dresden",
            "lat": 51.0504,
            "lon": 13.7372
        },
        {
            "customer_number": "1003",
            "name": "Test Kunde 3",
            "address": "Löbtauer Straße 5, 01159 Dresden",
            "lat": 51.0531,
            "lon": 13.7073
        }
    ]
    
    payload = {
        "tour_id": "TEST-TOUR-1",
        "stops": test_stops
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/tour/optimize",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolg: {len(data.get('optimized_stops', []))} Stopps optimiert")
            print(f"   Methode: {data.get('optimization_method', 'unknown')}")
            print(f"   Geschätzte Zeit: {data.get('estimated_total_time_minutes', 0):.1f} Minuten")
            if data.get('reasoning'):
                print(f"   Reasoning: {data.get('reasoning')[:100]}...")
            return True
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print("❌ FEHLER: Server nicht erreichbar. Starte Server mit: python start_server.py")
        return False
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def test_engine_ingest():
    """Test des neuen /engine/tours/ingest Endpoints"""
    print("\n" + "="*60)
    print("TEST 2: /engine/tours/ingest (neue Engine-API)")
    print("="*60)
    
    payload = {
        "tours": [
            {
                "tour_id": "ext-2025-11-01-TEST",
                "label": "Test Tour",
                "stops": [
                    {
                        "source_id": "ROW-1",
                        "label": "Test Kunde 1",
                        "address": "Fröbelstraße 1, 01309 Dresden",
                        "lat": 51.0492,
                        "lon": 13.6984
                    },
                    {
                        "source_id": "ROW-2",
                        "label": "Test Kunde 2",
                        "address": "Hauptstraße 10, 01067 Dresden",
                        "lat": 51.0504,
                        "lon": 13.7372
                    }
                ]
            }
        ]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/engine/tours/ingest",
            json=payload,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolg: {data.get('tours_ingested', 0)} Touren ingestiert")
            print(f"   Tour UIDs: {data.get('tour_uids', [])}")
            print(f"   Stopps mit UID: {data.get('stops_with_uid', 0)}")
            print(f"   Stopps pending Geo: {data.get('stops_pending_geo', 0)}")
            if data.get('warnings'):
                print(f"   Warnungen: {data.get('warnings')}")
            return data.get('tour_uids', [])[0] if data.get('tour_uids') else None
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return None
            
    except requests.exceptions.ConnectionError:
        print("❌ FEHLER: Server nicht erreichbar.")
        return None
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return None


def test_engine_status(tour_uid: str):
    """Test des /engine/tours/{tour_uid}/status Endpoints"""
    print("\n" + "="*60)
    print(f"TEST 3: /engine/tours/{tour_uid}/status")
    print("="*60)
    
    try:
        response = requests.get(
            f"{BASE_URL}/engine/tours/{tour_uid}/status",
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolg: Tour Status abgerufen")
            print(f"   Tour ID: {data.get('tour_id')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Stopps: {data.get('stop_count', 0)} total, {data.get('stops_with_geo', 0)} mit Geo")
            print(f"   Optimiert: {data.get('optimized', False)}")
            return True
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def test_engine_optimize(tour_uid: str):
    """Test des /engine/tours/optimize Endpoints"""
    print("\n" + "="*60)
    print(f"TEST 4: /engine/tours/optimize (OSRM-First)")
    print("="*60)
    
    payload = {
        "tour_uid": tour_uid
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/engine/tours/optimize",
            json=payload,
            timeout=60  # Länger wegen OSRM-Call
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Erfolg: Tour optimiert")
            print(f"   Tour UID: {data.get('tour_uid')}")
            print(f"   Route: {len(data.get('route', []))} Stopps")
            print(f"   Methode: {data.get('meta', {}).get('method', 'unknown')}")
            print(f"   Erste 5 stop_uids: {data.get('route', [])[:5]}")
            return True
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def test_engine_split(tour_uid: str):
    """Test des /engine/tours/split Endpoints"""
    print("\n" + "="*60)
    print(f"TEST 5: /engine/tours/split (Splitting-Logik)")
    print("="*60)
    
    payload = {
        "tour_uid": tour_uid,
        "max_duration_minutes": 60,
        "max_stops_per_route": None
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/engine/tours/split",
            json=payload,
            timeout=60
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            sub_routes = data.get('sub_routes', [])
            print(f"✅ Erfolg: Tour in {len(sub_routes)} Sub-Routen aufgeteilt")
            for i, sub_route in enumerate(sub_routes, 1):
                print(f"   Sub-Route {i}: {sub_route.get('stop_count', 0)} Stopps, "
                      f"~{sub_route.get('estimated_duration_minutes', 0):.1f} Min")
            return True
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(f"   Response: {response.text[:300]}")
            return False
            
    except Exception as e:
        print(f"❌ Fehler: {e}")
        return False


def main():
    """Hauptfunktion: Führt alle Tests aus"""
    print("\n" + "="*60)
    print("PHASE 1 TESTS: Basis-Funktionalität")
    print("="*60)
    print("\nHINWEIS: Stelle sicher, dass der Server läuft:")
    print("  python start_server.py")
    print("\n" + "="*60)
    
    results = {}
    
    # Test 1: Alter Optimize-Endpoint
    results['old_optimize'] = test_old_optimize_endpoint()
    
    # Test 2-5: Neue Engine-API
    tour_uid = test_engine_ingest()
    if tour_uid:
        results['ingest'] = True
        results['status'] = test_engine_status(tour_uid)
        results['optimize'] = test_engine_optimize(tour_uid)
        if results['optimize']:
            results['split'] = test_engine_split(tour_uid)
        else:
            results['split'] = False
            print("\n⚠️  Split-Test übersprungen (Optimierung fehlgeschlagen)")
    else:
        results['ingest'] = False
        results['status'] = False
        results['optimize'] = False
        results['split'] = False
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    print(f"✅ /api/tour/optimize: {'ERFOLG' if results.get('old_optimize') else 'FEHLER'}")
    print(f"✅ /engine/tours/ingest: {'ERFOLG' if results.get('ingest') else 'FEHLER'}")
    print(f"✅ /engine/tours/status: {'ERFOLG' if results.get('status') else 'FEHLER'}")
    print(f"✅ /engine/tours/optimize: {'ERFOLG' if results.get('optimize') else 'FEHLER'}")
    print(f"✅ /engine/tours/split: {'ERFOLG' if results.get('split') else 'FEHLER'}")
    
    all_passed = all(results.values())
    print("\n" + "="*60)
    if all_passed:
        print("✅ ALLE TESTS ERFOLGREICH")
    else:
        print("⚠️  EINIGE TESTS FEHLGESCHLAGEN")
    print("="*60)


if __name__ == "__main__":
    main()

