#!/usr/bin/env python3
"""
Test-Skript um zu prüfen, ob der /api/tour/optimize Endpoint erreichbar ist
"""

import requests
import json

def test_optimize_endpoint():
    """Testet den /api/tour/optimize Endpoint"""
    url = "http://127.0.0.1:8111/api/tour/optimize"
    
    # Test-Daten
    test_data = {
        "tour_id": "TEST-TOUR",
        "stops": [
            {
                "customer_number": "123",
                "name": "Test Kunde 1",
                "address": "Fröbelstraße 1, 01159 Dresden",
                "lat": 51.0491695,
                "lon": 13.698383,
                "street": "Fröbelstraße",
                "postal_code": "01159",
                "city": "Dresden"
            },
            {
                "customer_number": "456",
                "name": "Test Kunde 2",
                "address": "Hauptstraße 5, 01067 Dresden",
                "lat": 51.0504,
                "lon": 13.7373,
                "street": "Hauptstraße",
                "postal_code": "01067",
                "city": "Dresden"
            }
        ]
    }
    
    print(f"Teste Endpoint: {url}")
    print(f"Request Body: {json.dumps(test_data, indent=2)}")
    print("-" * 60)
    
    try:
        response = requests.post(
            url,
            json=test_data,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Status Text: {response.reason}")
        print(f"Headers: {dict(response.headers)}")
        
        if response.status_code == 404:
            print("\n❌ FEHLER: Endpoint nicht gefunden (404)")
            print("\nMögliche Ursachen:")
            print("1. Server läuft nicht")
            print("2. Router nicht korrekt registriert")
            print("3. Endpoint-Pfad falsch")
            print("\nPrüfe:")
            print("- Läuft der Server? (http://127.0.0.1:8111)")
            print("- Ist der Router in backend/app.py registriert?")
            print("- Server-Logs für Fehler prüfen")
        elif response.status_code == 200:
            print("\n✅ ERFOLG: Endpoint erreichbar")
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"\n⚠️  UNERWARTETER STATUS: {response.status_code}")
            try:
                error_data = response.json()
                print(f"Error Response: {json.dumps(error_data, indent=2, ensure_ascii=False)}")
            except:
                print(f"Error Text: {response.text[:500]}")
                
    except requests.exceptions.ConnectionError:
        print("\n❌ VERBINDUNGSFEHLER: Server läuft nicht oder nicht erreichbar")
        print("Starte den Server mit: python start_server.py")
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_optimize_endpoint()

