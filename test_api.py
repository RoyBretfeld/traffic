#!/usr/bin/env python3
"""
Test der reparierten API-Endpoints
"""

import requests
import json

def test_api_endpoints():
    """Teste die reparierten API-Endpoints"""
    print("Teste API-Endpoints...")
    
    # Test-Datei
    csv_file = "tourplaene/Tourenplan 04.09.2025.csv"
    
    try:
        # Test 1: /api/parse-csv-tourplan
        print("\n1. Teste /api/parse-csv-tourplan")
        url = 'http://127.0.0.1:8111/api/parse-csv-tourplan'
        files = {'file': open(csv_file, 'rb')}
        
        response = requests.post(url, files=files)
        files['file'].close()
        
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"Success: {data.get('success')}")
            print(f"File: {data.get('file_name')}")
            print(f"Tours: {len(data.get('tours', []))}")
            print(f"Customers: {len(data.get('customers', []))}")
            geocoding = data.get('geocoding', {})
            print(f"Geocoding Stats:")
            print(f"  Total: {geocoding.get('total', 0)}")
            print(f"  From DB: {geocoding.get('from_db', 0)}")
            print(f"  From Geocoding: {geocoding.get('from_geocoding', 0)}")
            print(f"  Failed: {geocoding.get('failed', 0)}")
        else:
            print(f"Error: {response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    test_api_endpoints()
