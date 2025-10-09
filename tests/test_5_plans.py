#!/usr/bin/env python3
"""
Kurztest mit 5 Tourplänen
"""

import requests
import json
from pathlib import Path

def test_5_tourplans():
    """Testet 5 Tourpläne mit der kanonischen Pipeline."""
    
    print("🧪 Kurztest mit 5 Tourplänen")
    print("=" * 40)
    
    # Wähle 5 Tourpläne aus
    canonical_dir = Path("tourplaene_canonical")
    csv_files = list(canonical_dir.glob("*.csv"))[:5]
    
    print(f"📁 Teste {len(csv_files)} kanonische Dateien:")
    for csv_file in csv_files:
        print(f"  - {csv_file.name}")
    
    print(f"\n🌐 Teste Backend-API...")
    
    try:
        # Teste Backend-Status
        response = requests.get("http://127.0.0.1:8111/api/status", timeout=10)
        if response.status_code == 200:
            print("✅ Backend erreichbar")
        else:
            print(f"❌ Backend-Fehler: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ Backend nicht erreichbar: {e}")
        return
    
    # Teste CSV-Bulk-Processing mit 5 Dateien
    print(f"\n📤 Sende 5 Dateien an Backend...")
    
    try:
        files = []
        for csv_file in csv_files:
            files.append(('csv_files', (csv_file.name, open(csv_file, 'rb'), 'text/csv')))
        
        response = requests.post(
            "http://127.0.0.1:8111/api/csv-bulk-process",
            files=files,
            timeout=60
        )
        
        # Schließe Dateien
        for _, (_, file_obj, _) in files:
            file_obj.close()
        
        if response.status_code == 200:
            result = response.json()
            print("✅ CSV-Verarbeitung erfolgreich!")
            print(f"📊 Verarbeitete Dateien: {result.get('processed_files', 0)}")
            print(f"📊 Gesamtkunden: {result.get('total_customers', 0)}")
            print(f"📊 Erkannte Kunden: {result.get('recognized_customers', 0)}")
            print(f"📊 Unerkannte Kunden: {result.get('unrecognized_customers', 0)}")
            
            # Berechne Erkennungsrate
            total = result.get('total_customers', 0)
            recognized = result.get('recognized_customers', 0)
            if total > 0:
                rate = (recognized / total) * 100
                print(f"🎯 Erkennungsrate: {rate:.1f}%")
            
        else:
            print(f"❌ CSV-Verarbeitung fehlgeschlagen: {response.status_code}")
            print(f"Fehler: {response.text}")
            
    except Exception as e:
        print(f"❌ Fehler beim Testen: {e}")

if __name__ == "__main__":
    test_5_tourplans()
