#!/usr/bin/env python3
"""
Quick Test für CSV Bulk Processor
"""

import sys
from pathlib import Path

# Backend-Module importieren
sys.path.append('backend')

try:
    from services.csv_bulk_processor import CSVBulkProcessor
    
    print("🚀 Teste CSV Bulk Processor...")
    
    # Processor initialisieren
    processor = CSVBulkProcessor()
    
    # CSV-Dateien finden
    csv_files = processor.find_all_csv_files()
    print(f"📁 {len(csv_files)} CSV-Dateien gefunden")
    
    if csv_files:
        # Erste Datei testen
        print(f"\n🔄 Teste erste Datei: {csv_files[0].name}")
        result = processor.process_csv_file(csv_files[0])
        
        if 'error' in result:
            print(f"❌ Fehler: {result['error']}")
        else:
            print(f"✅ Erfolgreich verarbeitet:")
            print(f"   - Touren: {result['total_tours']}")
            print(f"   - Kunden: {result['total_customers']}")
            
            # Geocoding testen
            if result['customers']:
                print(f"\n🌍 Teste Geocoding...")
                customers_with_geo = processor.calculate_geopoints(result['customers'][:1])
                
                if customers_with_geo:
                    customer = customers_with_geo[0]
                    print(f"✅ Geocoding erfolgreich:")
                    print(f"   - Name: {customer.get('name', 'N/A')}")
                    print(f"   - Koordinaten: {customer.get('latitude', 'N/A')}, {customer.get('longitude', 'N/A')}")
    
    print("\n🎉 Test abgeschlossen!")
    
except Exception as e:
    print(f"❌ Fehler: {e}")
    import traceback
    traceback.print_exc()