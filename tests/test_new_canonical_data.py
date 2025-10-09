#!/usr/bin/env python3
"""
Test mit neuen kanonischen Daten - prüft ob Geocoding besser wird.
"""

import sys
import os
sys.path.append('backend')

from pathlib import Path
import pandas as pd
from backend.db.dao import _connect

def test_new_canonical_data():
    """Test mit neuen kanonischen Daten."""
    
    print("🧪 Test mit neuen kanonischen Daten")
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
        
        # 2. Adressen extrahieren
        address_col = 2  # Straße-Spalte
        addresses = df.iloc[:, address_col].astype(str)
        
        # Gültige Adressen
        valid_addresses = addresses[
            (addresses != 'nan') & 
            (addresses != '') & 
            (addresses.notna()) &
            (addresses.str.len() > 2)
        ]
        
        print(f"📍 Gültige Adressen: {len(valid_addresses)}")
        
        # 3. Mojibake-Zeichen prüfen
        mojibake_chars = ['┬', '├', 'á', '@', ']', 'é', 'Ã¤', 'Ã¶', 'Ã¼', 'ÃŸ']
        mojibake_addresses = []
        
        for addr in valid_addresses:
            if any(char in addr for char in mojibake_chars):
                mojibake_addresses.append(addr)
        
        print(f"🔍 Adressen mit Mojibake: {len(mojibake_addresses)}")
        
        if mojibake_addresses:
            print("   Beispiele:")
            for addr in mojibake_addresses[:5]:
                print(f"     {addr}")
        else:
            print("   ✅ Alle Adressen sind sauber!")
        
        # 4. Adressen-Qualität analysieren
        print(f"\n📊 Adressen-Qualität:")
        
        # Kurze Adressen
        short_addresses = valid_addresses[valid_addresses.str.len() < 5]
        print(f"   📏 Kurze Adressen (<5 Zeichen): {len(short_addresses)}")
        if len(short_addresses) > 0:
            print("     Beispiele:")
            for addr in short_addresses.head(3):
                print(f"       {addr}")
        
        # Adressen mit Zahlen
        numeric_addresses = valid_addresses[valid_addresses.str.isdigit()]
        print(f"   🔢 Nur Zahlen: {len(numeric_addresses)}")
        if len(numeric_addresses) > 0:
            print("     Beispiele:")
            for addr in numeric_addresses.head(3):
                print(f"       {addr}")
        
        # Adressen mit "Straße"
        strasse_addresses = valid_addresses[valid_addresses.str.contains('Straße', case=False, na=False)]
        print(f"   🛣️  Mit 'Straße': {len(strasse_addresses)}")
        
        # Adressen mit "Strasse" (ohne ß)
        strasse_alt_addresses = valid_addresses[valid_addresses.str.contains('Strasse', case=False, na=False)]
        print(f"   🛣️  Mit 'Strasse': {len(strasse_alt_addresses)}")
        
        # 5. Geocoding-Simulation
        print(f"\n🌍 Geocoding-Simulation:")
        
        # Simuliere Geocoding-Erfolg basierend auf Adressen-Qualität
        geocoding_success = 0
        geocoding_failures = []
        
        for addr in valid_addresses:
            # Einfache Heuristik für Geocoding-Erfolg
            if (len(addr) >= 5 and 
                not addr.isdigit() and 
                not any(char in addr for char in mojibake_chars) and
                ('Straße' in addr or 'Strasse' in addr or 'Str.' in addr)):
                geocoding_success += 1
            else:
                geocoding_failures.append(addr)
        
        success_rate = (geocoding_success / len(valid_addresses)) * 100 if len(valid_addresses) > 0 else 0
        
        print(f"   📈 Geschätzte Geocoding-Quote: {success_rate:.1f}%")
        print(f"   ✅ Erfolgreiche Adressen: {geocoding_success}")
        print(f"   ❌ Problematische Adressen: {len(geocoding_failures)}")
        
        if geocoding_failures:
            print("   Beispiele problematischer Adressen:")
            for addr in geocoding_failures[:5]:
                print(f"     {addr}")
        
        # 6. Fazit
        print(f"\n📋 Fazit:")
        if len(mojibake_addresses) == 0 and success_rate > 90:
            print("   🎉 Exzellent! Adressen sind sauber und geocoding-tauglich!")
        elif len(mojibake_addresses) == 0:
            print("   ✅ Adressen sind sauber, aber einige könnten Geocoding-Probleme haben")
        else:
            print("   ⚠️  Noch Mojibake-Probleme vorhanden")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_new_canonical_data()
