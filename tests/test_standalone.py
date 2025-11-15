#!/usr/bin/env python3
"""
Standalone Test für CSV Bulk Processor - ohne Server
"""

import sys
import os
from pathlib import Path

# Arbeitsverzeichnis setzen
os.chdir(Path(__file__).parent)

# Backend-Module importieren
sys.path.append('backend')
sys.path.append('docs')

def test_csv_bulk():
    try:
        print("🚀 Teste CSV Bulk Processor (Standalone)...")
        
        from csv_bulk_processor import CSVBulkProcessor
        
        # Processor initialisieren
        processor = CSVBulkProcessor()
        print("✅ CSVBulkProcessor initialisiert")
        
        # CSV-Dateien finden
        csv_files = processor.find_all_csv_files()
        print(f"📁 {len(csv_files)} CSV-Dateien gefunden")
        
        if not csv_files:
            print("❌ Keine CSV-Dateien im tourplaene/ Verzeichnis gefunden!")
            return
        
        # Erste CSV-Datei testen
        print(f"\n🔄 Teste erste Datei: {csv_files[0].name}")
        result = processor.process_csv_file(csv_files[0])
        
        if 'error' in result:
            print(f"❌ Fehler: {result['error']}")
            return
        
        print(f"✅ Erfolgreich verarbeitet:")
        print(f"   - Touren: {result['total_tours']}")
        print(f"   - Kunden: {result['total_customers']}")
        
        # Geocoding testen
        if result['customers']:
            print(f"\n🌍 Teste Geocoding für ersten Kunden...")
            customers_with_geo = processor.calculate_geopoints(result['customers'][:1])
            
            if customers_with_geo:
                customer = customers_with_geo[0]
                print(f"✅ Geocoding erfolgreich:")
                print(f"   - Name: {customer.get('name', 'N/A')}")
                print(f"   - Adresse: {customer.get('street', 'N/A')}, {customer.get('postal_code', 'N/A')} {customer.get('city', 'N/A')}")
                print(f"   - Koordinaten: {customer.get('latitude', 'N/A')}, {customer.get('longitude', 'N/A')}")
            else:
                print("❌ Geocoding fehlgeschlagen")
        
        print("\n🎉 Test abgeschlossen!")
        
    except Exception as e:
        print(f"❌ Fehler beim Test: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_csv_bulk()
