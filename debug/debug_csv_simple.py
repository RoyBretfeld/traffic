#!/usr/bin/env python3
"""
Einfaches CSV-Debug-Script
"""

import pandas as pd
from pathlib import Path

def debug_csv():
    print("🔍 CSV-DEBUG")
    print("=" * 30)
    
    # Test mit einer CSV-Datei
    csv_file = Path("tourplaene/Tourenplan 14.08.2025.csv")
    
    if not csv_file.exists():
        print("❌ CSV-Datei nicht gefunden!")
        return
    
    # CSV lesen
    df = pd.read_csv(csv_file, encoding='utf-8')
    print(f"📄 {csv_file.name}: {len(df)} Zeilen")
    print(f"📋 Spalten: {list(df.columns)}")
    print()
    
    # Erste 10 Zeilen anzeigen
    print("📝 Erste 10 Zeilen:")
    for i, row in df.head(10).iterrows():
        print(f"  {i+1}: {dict(row)}")
    print()
    
    # Kunden zählen
    customers = 0
    for i, row in df.iterrows():
        kdnr = str(row.get('Kdnr', '')).strip()
        name = str(row.get('Name', '')).strip()
        address = str(row.get('Straße', '')).strip()
        
        print(f"Zeile {i+1}: Kdnr='{kdnr}', Name='{name}', Straße='{address}'")
        
        # Prüfe Bedingungen
        has_kdnr = kdnr and kdnr.isdigit()
        has_name = name and name != 'Name'
        has_address = address and address != 'Straße'
        not_header = not name.startswith('W-') and not name.startswith('PIR')
        
        print(f"  -> has_kdnr: {has_kdnr}, has_name: {has_name}, has_address: {has_address}, not_header: {not_header}")
        
        if has_kdnr and has_name and has_address and not_header:
            customers += 1
            print(f"  ✅ KUNDE GEFUNDEN: {name} | {address}")
        else:
            print(f"  ❌ Kein Kunde")
        print()
        
        if i >= 20:  # Nur erste 20 Zeilen
            break
    
    print(f"📊 Gefundene Kunden: {customers}")

if __name__ == "__main__":
    debug_csv()
