#!/usr/bin/env python3
"""
Finaler Test mit einem Plan - was bleibt an Fehlern übrig?
"""

import sys
import os
sys.path.append('backend')

from pathlib import Path
import pandas as pd
from tools.utilities.canonicalize_csv_pipeline import canonicalize_csv, repair_all_mojibake

def assert_utf8(s: str):
    """Wächter-Funktion: Fängt Doppel-Decode sofort ab."""
    if s.encode("utf-8", errors="strict").decode("utf-8", errors="strict") != s:
        raise ValueError("Nicht-stabile UTF-8-Roundtrip – Zeichen wurden schon verhunzt.")

def test_single_plan_final():
    """Teste einen Plan endgültig - was bleibt an Fehlern übrig?"""
    
    print("🧪 Finaler Test mit einem Plan")
    print("=" * 50)
    
    # Test-Plan auswählen
    test_file = "tourplaene/Tourenplan 15.08.2025.csv"
    
    print(f"📁 Test-Datei: {test_file}")
    
    # 1. Original lesen (CP850)
    print("\n1️⃣ Original-Datei (CP850)...")
    try:
        df_orig = pd.read_csv(test_file, encoding='cp850', sep=';', header=None, dtype=str)
        print(f"   ✅ Original gelesen: {len(df_orig)} Zeilen")
        
        # Mojibake-Zeichen zählen
        mojibake_chars = ['á', '@', ']', 'é', 'Ã¤', 'Ã¶', 'Ã¼', 'ÃŸ', '┬', '├']
        mojibake_count = 0
        mojibake_examples = []
        
        for i, row in df_orig.iterrows():
            for col in df_orig.columns:
                text = str(row[col])
                for char in mojibake_chars:
                    if char in text:
                        mojibake_count += 1
                        if len(mojibake_examples) < 5:
                            mojibake_examples.append(f"Zeile {i+1}: {text[:50]}...")
        
        print(f"   🔍 Mojibake-Zeichen: {mojibake_count}")
        if mojibake_examples:
            print("   Beispiele:")
            for ex in mojibake_examples:
                print(f"     {ex}")
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return
    
    # 2. Kanonische Version erstellen
    print("\n2️⃣ Kanonische Version erstellen...")
    try:
        canonical_file = "test_canonical_final.csv"
        excel_file = "test_excel_final.csv"
        
        info = canonicalize_csv(test_file, canonical_file, excel_file)
        print(f"   ✅ Kanonisiert: {info}")
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return
    
    # 3. Kanonische Version lesen (UTF-8)
    print("\n3️⃣ Kanonische Version (UTF-8)...")
    try:
        df_canonical = pd.read_csv(canonical_file, encoding='utf-8', sep=';', header=None, dtype=str)
        print(f"   ✅ Kanonisch gelesen: {len(df_canonical)} Zeilen")
        
        # Mojibake-Zeichen nach Reparatur zählen
        mojibake_count_after = 0
        mojibake_examples_after = []
        
        for i, row in df_canonical.iterrows():
            for col in df_canonical.columns:
                text = str(row[col])
                for char in mojibake_chars:
                    if char in text:
                        mojibake_count_after += 1
                        if len(mojibake_examples_after) < 5:
                            mojibake_examples_after.append(f"Zeile {i+1}: {text[:50]}...")
        
        print(f"   🔍 Mojibake-Zeichen nach Reparatur: {mojibake_count_after}")
        if mojibake_examples_after:
            print("   Beispiele:")
            for ex in mojibake_examples_after:
                print(f"     {ex}")
        
        # 4. UTF-8-Wächter testen
        print("\n4️⃣ UTF-8-Wächter testen...")
        utf8_errors = 0
        for i, row in df_canonical.iterrows():
            for col in df_canonical.columns:
                text = str(row[col])
                try:
                    assert_utf8(text)
                except ValueError as e:
                    utf8_errors += 1
                    if utf8_errors <= 3:
                        print(f"   ❌ UTF-8-Fehler Zeile {i+1}: {text[:30]}...")
        
        print(f"   🔍 UTF-8-Fehler: {utf8_errors}")
        
        # 5. Adressen analysieren
        print("\n5️⃣ Adressen analysieren...")
        address_col = 2  # Straße-Spalte
        addresses = df_canonical.iloc[:, address_col].astype(str)
        
        # Gültige Adressen
        valid_addresses = addresses[
            (addresses != 'nan') & 
            (addresses != '') & 
            (addresses.notna())
        ]
        
        print(f"   📍 Gültige Adressen: {len(valid_addresses)}")
        
        # Adressen mit Problemen
        problem_addresses = []
        for addr in valid_addresses:
            # Mojibake-Zeichen
            if any(char in addr for char in mojibake_chars):
                problem_addresses.append(("Mojibake", addr))
            # Leere oder sehr kurze Adressen
            elif len(addr.strip()) < 3:
                problem_addresses.append(("Zu kurz", addr))
            # Nur Zahlen
            elif addr.strip().isdigit():
                problem_addresses.append(("Nur Zahlen", addr))
        
        print(f"   ⚠️  Problematische Adressen: {len(problem_addresses)}")
        
        if problem_addresses:
            print("   Beispiele:")
            for problem_type, addr in problem_addresses[:5]:
                print(f"     {problem_type}: {addr}")
        
        # 6. Zusammenfassung
        print(f"\n📊 Zusammenfassung:")
        print(f"   Original Mojibake: {mojibake_count}")
        print(f"   Nach Reparatur: {mojibake_count_after}")
        print(f"   UTF-8-Fehler: {utf8_errors}")
        print(f"   Problematische Adressen: {len(problem_addresses)}")
        
        if mojibake_count_after == 0 and utf8_errors == 0:
            print("   🎉 Perfekt! Keine Mojibake oder UTF-8-Fehler!")
        elif mojibake_count_after == 0:
            print("   ✅ Mojibake behoben, aber UTF-8-Probleme!")
        else:
            print("   ⚠️  Noch Mojibake-Probleme vorhanden!")
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 7. Aufräumen
    print("\n6️⃣ Aufräumen...")
    try:
        Path(canonical_file).unlink()
        Path(excel_file).unlink()
        print("   ✅ Test-Dateien gelöscht")
    except:
        pass
    
    print("\n✅ Test abgeschlossen!")

if __name__ == "__main__":
    test_single_plan_final()
