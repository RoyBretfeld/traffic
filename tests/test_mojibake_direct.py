#!/usr/bin/env python3
"""
Direkter Test der Mojibake-Reparatur mit Backend-Logik.
"""

import sys
import os
sys.path.append('backend')

from pathlib import Path
import pandas as pd
from canonicalize_csv_pipeline import repair_all_mojibake

def test_mojibake_repair():
    """Teste Mojibake-Reparatur direkt."""
    
    print("🔍 Direkter Mojibake-Test")
    print("=" * 50)
    
    # Test mit einem kanonischen Plan
    test_file = "tourplaene_canonical/Tourenplan 15.08.2025.csv"
    
    if not Path(test_file).exists():
        print(f"❌ Datei nicht gefunden: {test_file}")
        return
    
    print(f"📁 Teste: {test_file}")
    
    # 1. Kanonische Datei lesen
    try:
        df = pd.read_csv(test_file, encoding='utf-8', sep=';', header=None, dtype=str)
        print(f"✅ Gelesen: {len(df)} Zeilen")
        
        # 2. Mojibake-Zeichen suchen
        mojibake_chars = ['á', '@', ']', 'é', 'Ã¤', 'Ã¶', 'Ã¼', 'ÃŸ']
        mojibake_found = []
        
        for i, row in df.iterrows():
            for col in df.columns:
                text = str(row[col])
                for char in mojibake_chars:
                    if char in text:
                        mojibake_found.append(f"Zeile {i+1}, Spalte {col}: {text[:50]}...")
        
        print(f"🔍 Mojibake-Zeichen gefunden: {len(mojibake_found)}")
        
        if mojibake_found:
            print("\n📋 Beispiele:")
            for example in mojibake_found[:5]:
                print(f"   {example}")
        
        # 3. Reparatur testen
        print(f"\n🔧 Teste Reparatur...")
        repaired_count = 0
        
        for i, row in df.iterrows():
            for col in df.columns:
                original = str(row[col])
                repaired = repair_all_mojibake(original)
                if original != repaired:
                    repaired_count += 1
                    if repaired_count <= 3:  # Erste 3 Beispiele zeigen
                        print(f"   {original[:30]}... → {repaired[:30]}...")
        
        print(f"✅ Repariert: {repaired_count} Felder")
        
        # 4. Geocoding-Test simulieren
        print(f"\n🌍 Simuliere Geocoding...")
        address_col = 2  # Straße-Spalte
        addresses = df.iloc[:, address_col].astype(str)
        
        # Adressen mit Mojibake filtern
        mojibake_addresses = []
        for addr in addresses:
            if any(char in addr for char in mojibake_chars):
                mojibake_addresses.append(addr)
        
        print(f"   Adressen mit Mojibake: {len(mojibake_addresses)}")
        
        if mojibake_addresses:
            print("   Beispiele:")
            for addr in mojibake_addresses[:3]:
                repaired = repair_all_mojibake(addr)
                print(f"     {addr} → {repaired}")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_mojibake_repair()
