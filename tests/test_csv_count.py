#!/usr/bin/env python3
"""
Test: CSV-Dateien zählen
"""

import requests
import json

def test_csv_bulk():
    try:
        print("🔍 Teste CSV Bulk Processor...")
        
        # API aufrufen
        response = requests.post("http://127.0.0.1:8111/api/csv-bulk-process")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Erfolgreich!")
            print(f"📊 Ergebnisse:")
            print(f"   - Gesamte Kunden: {data.get('total_customers', 0)}")
            print(f"   - Eindeutige Kunden: {data.get('unique_customers', 0)}")
            print(f"   - Touren: {data.get('total_tours', 0)}")
            print(f"   - Dateien: {data.get('files_processed', 0)}")
        else:
            print(f"❌ Fehler: {response.status_code}")
            print(response.text)
            
    except Exception as e:
        print(f"❌ Fehler: {e}")

if __name__ == "__main__":
    test_csv_bulk()
