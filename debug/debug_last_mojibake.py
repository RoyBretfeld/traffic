#!/usr/bin/env python3
"""
Debug des letzten Mojibake-Zeichens.
"""

from pathlib import Path
import pandas as pd
from canonicalize_csv_pipeline import repair_all_mojibake

def debug_last_mojibake():
    """Debug des letzten Mojibake-Zeichens."""
    
    print("🔍 Debug des letzten Mojibake-Zeichens")
    print("=" * 50)
    
    # Test-Plan
    test_file = "tourplaene/Tourenplan 15.08.2025.csv"
    
    # Original lesen
    df_orig = pd.read_csv(test_file, encoding='cp850', sep=';', header=None, dtype=str)
    
    # Zeile 241 finden (André Zerbst)
    print("📋 Zeile 241 (Original):")
    for col in df_orig.columns:
        text = str(df_orig.iloc[240, col])  # 0-basiert
        print(f"   Spalte {col}: {repr(text)}")
    
    # Reparatur testen
    print("\n🔧 Reparatur-Test:")
    for col in df_orig.columns:
        original = str(df_orig.iloc[240, col])
        repaired = repair_all_mojibake(original)
        if original != repaired:
            print(f"   Spalte {col}:")
            print(f"     Original: {repr(original)}")
            print(f"     Repariert: {repr(repaired)}")
        else:
            print(f"   Spalte {col}: Keine Änderung")
    
    # Zeichen-für-Zeichen analysieren
    print("\n🔬 Zeichen-für-Zeichen Analyse:")
    text = str(df_orig.iloc[240, 1])  # Name-Spalte
    print(f"   Text: {repr(text)}")
    print(f"   Länge: {len(text)}")
    
    for i, char in enumerate(text):
        print(f"   Position {i}: {repr(char)} (U+{ord(char):04X})")
    
    # UTF-8-Bytes analysieren
    print("\n🔬 UTF-8-Bytes Analyse:")
    text_bytes = text.encode('utf-8')
    print(f"   UTF-8 Bytes: {text_bytes}")
    for i, byte in enumerate(text_bytes):
        print(f"   Byte {i}: 0x{byte:02X}")

if __name__ == "__main__":
    debug_last_mojibake()
