#!/usr/bin/env python3
"""
Schneller Test mit 5 Plänen für Encoding-Fixes
Testet die neuen Mojibake-Guards und UTF-8-Fixes
"""

import sys
from pathlib import Path
import asyncio

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from backend.utils.encoding_guards import trace_text, assert_no_mojibake, smoke_test_encoding
from backend.app import read_tourplan_csv

def test_5_plans():
    """Testet 5 Tourpläne auf Encoding-Probleme"""
    
    print("🚀 Starte Encoding-Test mit 5 Plänen...")
    print("=" * 60)
    
    # 1. Smoke Test
    print("\n1️⃣ Smoke Test...")
    try:
        smoke_test_encoding()
        print("✅ Smoke Test erfolgreich")
    except Exception as e:
        print(f"❌ Smoke Test fehlgeschlagen: {e}")
        return False
    
    # 2. Finde 5 CSV-Dateien
    tourplaene_dir = Path("tourplaene")
    if not tourplaene_dir.exists():
        print("❌ tourplaene Verzeichnis nicht gefunden")
        return False
    
    csv_files = list(tourplaene_dir.glob("*.csv"))[:5]  # Nur 5 Dateien
    print(f"\n2️⃣ Gefundene CSV-Dateien: {len(csv_files)}")
    for i, file in enumerate(csv_files, 1):
        print(f"   {i}. {file.name}")
    
    if not csv_files:
        print("❌ Keine CSV-Dateien gefunden")
        return False
    
    # 3. Teste jede Datei
    print(f"\n3️⃣ Teste {len(csv_files)} Dateien...")
    
    total_customers = 0
    recognized_customers = 0
    mojibake_errors = 0
    
    for i, csv_file in enumerate(csv_files, 1):
        print(f"\n📄 Datei {i}/{len(csv_files)}: {csv_file.name}")
        print("-" * 40)
        
        try:
            # CSV lesen mit neuen Guards
            df = read_tourplan_csv(csv_file)
            print(f"   ✅ CSV erfolgreich gelesen: {len(df)} Zeilen")
            
            # Teste erste paar Zeilen auf Mojibake
            for idx, row in df.head(3).iterrows():
                for col in df.columns:
                    if pd.notna(row[col]) and isinstance(row[col], str):
                        try:
                            assert_no_mojibake(str(row[col]))
                        except ValueError as e:
                            print(f"   ❌ Mojibake in Zeile {idx}, Spalte {col}: {e}")
                            mojibake_errors += 1
                        else:
                            # Trace erste 50 Zeichen
                            trace_text(f"ROW_{idx}_{col}", str(row[col])[:50])
            
            # Simuliere Kunden-Erkennung
            customers_in_file = 0
            for idx, row in df.iterrows():
                if len(row) >= 6:  # Mindestens 6 Spalten erwartet
                    customer = {
                        'name': str(row.iloc[1]) if len(row) > 1 else '',
                        'street': str(row.iloc[2]) if len(row) > 2 else '',
                        'postal_code': str(row.iloc[3]) if len(row) > 3 else '',
                        'city': str(row.iloc[4]) if len(row) > 4 else '',
                    }
                    
                    # Prüfe auf leere Kunden
                    if customer['name'].strip() and customer['name'] != 'nan':
                        customers_in_file += 1
                        total_customers += 1
                        
                        # Simuliere Erkennung (vereinfacht)
                        if customer.get('street') and customer.get('city'):
                            recognized_customers += 1
            
            print(f"   📊 Kunden in Datei: {customers_in_file}")
            
        except Exception as e:
            print(f"   ❌ Fehler bei {csv_file.name}: {e}")
            continue
    
    # 4. Ergebnisse
    print(f"\n4️⃣ Test-Ergebnisse:")
    print("=" * 60)
    print(f"📁 Dateien getestet: {len(csv_files)}")
    print(f"👥 Gesamt Kunden: {total_customers}")
    print(f"✅ Erkannte Kunden: {recognized_customers}")
    print(f"❌ Mojibake-Fehler: {mojibake_errors}")
    
    if total_customers > 0:
        success_rate = (recognized_customers / total_customers) * 100
        print(f"📈 Erkennungsrate: {success_rate:.1f}%")
        
        if success_rate >= 90:
            print("🎉 EXCELLENT! Erkennungsrate über 90%")
        elif success_rate >= 80:
            print("👍 GUT! Erkennungsrate über 80%")
        else:
            print("⚠️  Verbesserung nötig")
    
    if mojibake_errors == 0:
        print("🎯 PERFEKT! Keine Mojibake-Fehler gefunden")
    else:
        print(f"⚠️  {mojibake_errors} Mojibake-Fehler gefunden")
    
    print("\n" + "=" * 60)
    return mojibake_errors == 0

if __name__ == "__main__":
    import pandas as pd
    
    try:
        success = test_5_plans()
        if success:
            print("🎉 Test erfolgreich abgeschlossen!")
        else:
            print("❌ Test mit Problemen abgeschlossen")
    except Exception as e:
        print(f"💥 Test fehlgeschlagen: {e}")
        import traceback
        traceback.print_exc()
