#!/usr/bin/env python3
"""
Direkte CSV-Analyse
"""

import pandas as pd
from pathlib import Path

def analyze_csv():
    print("🔍 DIREKTE CSV-ANALYSE")
    print("=" * 40)
    
    # Eine CSV-Datei analysieren
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
    
    # Tour-Header suchen
    print("🔍 Suche Tour-Header...")
    tour_headers = df[df['Name'].str.contains('W-.*Uhr', na=False, regex=True)]
    print(f"Gefundene Tour-Header: {len(tour_headers)}")
    for header in tour_headers['Name'].values:
        print(f"  - {header}")
    print()
    
    # Kunden zählen
    print("👥 Zähle Kunden...")
    customers = 0
    for _, row in df.iterrows():
        name = str(row.get('Name', '')).strip()
        address = str(row.get('Straße', '')).strip()
        
        if name and address and name != 'Name' and address != 'Straße':
            customers += 1
            if customers <= 5:  # Erste 5 Kunden anzeigen
                print(f"  {customers}: {name} | {address}")
    
    print(f"Gesamte Kunden: {customers}")

if __name__ == "__main__":
    analyze_csv()
