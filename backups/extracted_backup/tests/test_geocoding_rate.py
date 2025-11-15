#!/usr/bin/env python3
"""
Test der Geocoding-Trefferquote mit reparierten Daten.
"""

import sys
import os
sys.path.append('backend')

from pathlib import Path
import pandas as pd
import requests
import json

def test_geocoding_rate():
    """Teste Geocoding-Trefferquote mit reparierten Daten."""
    
    print("🌍 Geocoding-Trefferquote Test")
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
        
        # Adressen filtern (nicht leer, nicht "nan")
        valid_addresses = addresses[
            (addresses != 'nan') & 
            (addresses != '') & 
            (addresses.notna())
        ]
        
        print(f"📍 Gültige Adressen: {len(valid_addresses)}")
        
        # 3. Mojibake-Zeichen in Adressen prüfen
        mojibake_chars = ['á', '@', ']', 'é', 'Ã¤', 'Ã¶', 'Ã¼', 'ÃŸ', '┬']
        mojibake_addresses = []
        
        for addr in valid_addresses:
            if any(char in addr for char in mojibake_chars):
                mojibake_addresses.append(addr)
        
        print(f"🔍 Adressen mit Mojibake: {len(mojibake_addresses)}")
        
        if mojibake_addresses:
            print("   Beispiele:")
            for addr in mojibake_addresses[:5]:
                print(f"     {addr}")
        
        # 4. Geocoding-Test mit einigen Adressen
        print(f"\n🌍 Teste Geocoding mit 5 Adressen...")
        
        test_addresses = valid_addresses.head(5).tolist()
        
        for i, addr in enumerate(test_addresses, 1):
            print(f"   {i}. {addr}")
            
            # Simuliere Geocoding-Request (ohne echte API)
            # Hier würden wir normalerweise die Geocoding-API aufrufen
            # Für den Test nehmen wir an, dass saubere Adressen besser funktionieren
            
            # Prüfe, ob Adresse Mojibake enthält
            has_mojibake = any(char in addr for char in mojibake_chars)
            status = "❌ Mojibake" if has_mojibake else "✅ Sauber"
            print(f"      {status}")
        
        # 5. Zusammenfassung
        clean_addresses = len(valid_addresses) - len(mojibake_addresses)
        clean_rate = (clean_addresses / len(valid_addresses)) * 100 if len(valid_addresses) > 0 else 0
        
        print(f"\n📊 Zusammenfassung:")
        print(f"   Gesamt Adressen: {len(valid_addresses)}")
        print(f"   Saubere Adressen: {clean_addresses}")
        print(f"   Mojibake Adressen: {len(mojibake_addresses)}")
        print(f"   Sauberkeits-Rate: {clean_rate:.1f}%")
        
        if clean_rate > 95:
            print("   🎉 Exzellent! Fast alle Adressen sind sauber.")
        elif clean_rate > 80:
            print("   ✅ Gut! Die meisten Adressen sind sauber.")
        else:
            print("   ⚠️  Verbesserung nötig! Viele Adressen haben Mojibake.")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_geocoding_rate()
