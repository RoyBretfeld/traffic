#!/usr/bin/env python3
"""
Test der Mojibake-Reparatur mit einem einzelnen Tourplan.
"""

from pathlib import Path
from canonicalize_csv_pipeline import canonicalize_csv, repair_all_mojibake
import pandas as pd

def test_single_plan():
    """Teste Mojibake-Reparatur mit einem Plan."""
    
    # Test-Plan auswählen
    test_file = "tourplaene/Tourenplan 15.08.2025.csv"
    
    print("🔍 Mojibake-Reparatur Test")
    print("=" * 50)
    print(f"📁 Test-Datei: {test_file}")
    
    # 1. Original lesen und analysieren
    print("\n1️⃣ Original-Datei analysieren...")
    try:
        df_orig = pd.read_csv(test_file, encoding='cp850', sep=';', header=None, dtype=str)
        print(f"   ✅ Original gelesen: {len(df_orig)} Zeilen")
        
        # Mojibake-Zeichen zählen
        mojibake_chars = ['á', '@', ']', 'é', 'Ã¤', 'Ã¶', 'Ã¼', 'ÃŸ']
        mojibake_count = 0
        for col in df_orig.columns:
            if df_orig[col].dtype == 'object':
                for char in mojibake_chars:
                    mojibake_count += df_orig[col].astype(str).str.contains(char, na=False).sum()
        
        print(f"   🔍 Mojibake-Zeichen gefunden: {mojibake_count}")
        
    except Exception as e:
        print(f"   ❌ Fehler beim Lesen: {e}")
        return
    
    # 2. Kanonische Version erstellen
    print("\n2️⃣ Kanonische Version erstellen...")
    try:
        canonical_file = "test_canonical.csv"
        excel_file = "test_excel.csv"
        
        info = canonicalize_csv(test_file, canonical_file, excel_file)
        print(f"   ✅ Kanonisiert: {info}")
        
    except Exception as e:
        print(f"   ❌ Fehler beim Kanonisieren: {e}")
        return
    
    # 3. Kanonische Version lesen und vergleichen
    print("\n3️⃣ Kanonische Version analysieren...")
    try:
        df_canonical = pd.read_csv(canonical_file, encoding='utf-8', sep=';', header=None, dtype=str)
        print(f"   ✅ Kanonisch gelesen: {len(df_canonical)} Zeilen")
        
        # Mojibake-Zeichen nach Reparatur zählen
        mojibake_count_after = 0
        for col in df_canonical.columns:
            if df_canonical[col].dtype == 'object':
                for char in mojibake_chars:
                    mojibake_count_after += df_canonical[col].astype(str).str.contains(char, na=False).sum()
        
        print(f"   🔍 Mojibake-Zeichen nach Reparatur: {mojibake_count_after}")
        print(f"   📊 Reparatur-Erfolg: {mojibake_count - mojibake_count_after} Zeichen repariert")
        
    except Exception as e:
        print(f"   ❌ Fehler beim Lesen der kanonischen Version: {e}")
        return
    
    # 4. Beispiele der Reparatur zeigen
    print("\n4️⃣ Reparatur-Beispiele:")
    print("   Vorher → Nachher")
    print("   " + "-" * 40)
    
    # Einige Beispiele aus den Daten zeigen
    for i in range(min(5, len(df_orig))):
        for col in df_orig.columns:
            if df_orig[col].dtype == 'object':
                orig_text = str(df_orig.iloc[i, col])
                if any(char in orig_text for char in mojibake_chars):
                    canonical_text = str(df_canonical.iloc[i, col])
                    if orig_text != canonical_text:
                        print(f"   {orig_text[:30]}... → {canonical_text[:30]}...")
                        break
    
    # 5. Aufräumen
    print("\n5️⃣ Aufräumen...")
    try:
        Path(canonical_file).unlink()
        Path(excel_file).unlink()
        print("   ✅ Test-Dateien gelöscht")
    except:
        pass
    
    print("\n✅ Test abgeschlossen!")

if __name__ == "__main__":
    test_single_plan()
