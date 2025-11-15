#!/usr/bin/env python3
"""
Schnelle CSV-Analyse für FAMO TrafficApp
"""

import pandas as pd
from pathlib import Path
import re

def analyze_csv_files():
    print("📊 CSV-ANALYSE ERGEBNIS")
    print("=" * 50)
    
    # 1. Alle CSV-Dateien finden
    tourplaene_dir = Path("tourplaene")
    if not tourplaene_dir.exists():
        print("❌ tourplaene-Verzeichnis nicht gefunden!")
        return
    
    csv_files = list(tourplaene_dir.glob("*.csv"))
    print(f"📁 CSV-Dateien: {len(csv_files)}")
    print()
    
    total_lines = 0
    total_customers = 0
    total_tours = 0
    all_unique_customers = set()
    
    # 2. Jede Datei analysieren
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            file_lines = len(df)
            total_lines += file_lines
            
            # 3. Tour-Header finden
            tour_pattern = r'W-.*Uhr|PIR.*Uhr|PIR.*BAR|.*BAR|.*Tour'
            tour_headers = df[df['Name'].str.contains(tour_pattern, na=False, regex=True)]
            file_tours = len(tour_headers)
            total_tours += file_tours
            
            # 4. Kunden zählen
            customers = df[
                (df['Name'].notna()) & 
                (df['Straße'].notna()) & 
                (~df['Name'].str.contains(tour_pattern, na=False, regex=True)) &
                (df['Name'] != 'Name') &
                (df['Straße'] != 'Straße')
            ]
            
            file_customers = len(customers)
            total_customers += file_customers
            
            # Eindeutige Kunden sammeln
            for _, row in customers.iterrows():
                name = str(row['Name']).strip()
                address = str(row['Straße']).strip()
                if name and address:
                    customer_key = f"{name}|{address}"
                    all_unique_customers.add(customer_key)
            
            print(f"📄 {csv_file.name}: {file_lines} Zeilen, {file_tours} Touren, {file_customers} Kunden")
            
        except Exception as e:
            print(f"❌ Fehler bei {csv_file.name}: {e}")
    
    # 5. Ergebnisse ausgeben
    print()
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 50)
    print(f"📁 CSV-Dateien: {len(csv_files)}")
    print(f"📄 Gesamte Zeilen: {total_lines}")
    print(f"👥 Gesamte Kunden: {total_customers}")
    print(f"🔄 Eindeutige Kunden: {len(all_unique_customers)}")
    print(f"🚗 Touren: {total_tours}")
    print(f"📈 Durchschnitt: {total_customers // len(csv_files) if csv_files else 0} Kunden pro Datei")
    
    # 6. Vergleich mit aktueller DB
    print()
    print("🔍 VERGLEICH MIT DATENBANK")
    print("=" * 50)
    try:
        import sqlite3
        db_path = Path("data/traffic.db")
        if db_path.exists():
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Kunden in DB zählen
            cursor.execute("SELECT COUNT(*) FROM kunden")
            db_customers = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM touren")
            db_tours = cursor.fetchone()[0]
            
            conn.close()
            
            print(f"🗄️  DB Kunden: {db_customers}")
            print(f"🗄️  DB Touren: {db_tours}")
            print(f"📊 CSV vs DB Kunden: {total_customers} vs {db_customers}")
            print(f"📊 CSV vs DB Touren: {total_tours} vs {db_tours}")
            
            if db_customers < total_customers:
                print("⚠️  PROBLEM: DB hat weniger Kunden als CSV-Dateien!")
            else:
                print("✅ DB hat ausreichend Kunden")
        else:
            print("❌ Datenbank nicht gefunden")
    except Exception as e:
        print(f"❌ DB-Fehler: {e}")

if __name__ == "__main__":
    analyze_csv_files()
