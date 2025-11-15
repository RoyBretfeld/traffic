#!/usr/bin/env python3
"""
CI-SLO-Check für TrafficApp
Überprüft Service Level Objectives (SLOs) für Encoding und Erkennungsquote
"""

from __future__ import annotations
import os
import json
import sys
from pathlib import Path
import requests
import tempfile

# Schwellen (überschreibbar per ENV)
SLO_OK_RATE = float(os.getenv("SLO_OK_RATE", "0.95"))

def create_test_csv():
    """Erstelle Test-CSV mit Umlauten"""
    csv_content = "Kunde;Adresse\nX;Fröbelstraße 1, Dresden\nY;A zu B, Teststadt\n"
    
    # Erstelle temporäre Datei
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='cp850')
    temp_file.write(csv_content)
    temp_file.close()
    
    return Path(temp_file.name)

def check_api_endpoints():
    """Überprüfe API-Endpoints direkt"""
    base_url = "http://127.0.0.1:8111"
    
    # Teste ob Server läuft
    try:
        response = requests.get(f"{base_url}/api/db-status", timeout=5)
        if response.status_code != 200:
            print(f"FEHLER: Server nicht erreichbar (Status {response.status_code})")
            return False, {}
    except requests.exceptions.RequestException as e:
        print(f"FEHLER: Server nicht erreichbar: {e}")
        return False, {}
    
    # Teste mit bestehender CSV-Datei
    test_file = Path("tourplaene/Tourenplan 04.09.2025.csv")
    if not test_file.exists():
        print(f"WARNUNG: Test-Datei {test_file} nicht gefunden")
        return False, {}
    
    try:
        # Teste parse-csv-tourplan Endpoint
        with open(test_file, 'rb') as f:
            files = {'file': f}
            response = requests.post(f"{base_url}/api/parse-csv-tourplan", files=files, timeout=30)
        
        if response.status_code != 200:
            print(f"FEHLER: parse-csv-tourplan gibt Status {response.status_code}: {response.text}")
            return False, {}
        
        data = response.json()
        
        # Überprüfe Geocoding-Statistiken
        geocoding = data.get("geocoding", {})
        total = geocoding.get("total", 0)
        from_db = geocoding.get("from_db", 0)
        from_geocoding = geocoding.get("from_geocoding", 0)
        failed = geocoding.get("failed", 0)
        
        # Berechne Erfolgsquote
        success_count = from_db + from_geocoding
        success_rate = success_count / max(1, total)
        
        print(f"Geocoding-Statistiken:")
        print(f"  Total: {total}")
        print(f"  Aus DB: {from_db}")
        print(f"  Neu geocodiert: {from_geocoding}")
        print(f"  Fehlgeschlagen: {failed}")
        print(f"  Erfolgsquote: {success_rate:.2%}")
        
        # SLO-Check
        if success_rate < SLO_OK_RATE:
            print(f"SLO VERFEHLT: success_rate={success_rate:.2%} < {SLO_OK_RATE:.0%}")
            return False, data
        
        print(f"SLO ERFÜLLT: success_rate={success_rate:.2%} >= {SLO_OK_RATE:.0%}")
        
        # Mojibake-Check
        response_text = response.text
        BAD_MARKERS = ["Ã", "┬", "├", "�"]
        found_markers = [marker for marker in BAD_MARKERS if marker in response_text]
        
        if found_markers:
            print(f"MOJIBAKE GEFUNDEN: {found_markers}")
            return False, data
        
        print("MOJIBAKE-CHECK: OK")
        
        return True, data
        
    except Exception as e:
        print(f"FEHLER beim API-Test: {e}")
        return False, {}

def main():
    """Hauptfunktion"""
    print("=== CI-SLO-Check für TrafficApp ===")
    print(f"SLO-Schwelle: {SLO_OK_RATE:.0%}")
    
    # API-Check
    api_ok, api_data = check_api_endpoints()
    
    # Ergebnis
    result = {
        "success": api_ok,
        "slo_ok_rate": api_ok,
        "mojibake_ok": api_ok,
        "api_data": api_data,
        "message": "API-Tests erfolgreich" if api_ok else "API-Tests fehlgeschlagen"
    }
    
    print("\n=== ERGEBNIS ===")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    # Exit-Code
    sys.exit(0 if api_ok else 1)

if __name__ == "__main__":
    main()
