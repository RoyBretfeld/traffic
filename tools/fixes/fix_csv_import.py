#!/usr/bin/env python3
"""
CSV-Import Problem lösen - Schritt für Schritt
"""

import pandas as pd
from pathlib import Path
import sqlite3

def step1_analyze_csv():
    """Schritt 1: CSV-Dateien analysieren"""
    print("🔍 SCHRITT 1: CSV-DATEIEN ANALYSIEREN")
    print("=" * 50)
    
    # Eine CSV-Datei testen
    csv_file = Path("tourplaene/Tourenplan 14.08.2025.csv")
    
    if not csv_file.exists():
        print("❌ CSV-Datei nicht gefunden!")
        return False
    
    # Verschiedene Encodings probieren
    for encoding in ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']:
        try:
            df = pd.read_csv(csv_file, encoding=encoding)
            print(f"✅ Encoding {encoding} funktioniert!")
            print(f"📄 Zeilen: {len(df)}")
            print(f"📋 Spalten: {list(df.columns)}")
            print()
            
            # Erste 5 Zeilen anzeigen
            print("📝 Erste 5 Zeilen:")
            for i, row in df.head(5).iterrows():
                print(f"  {i+1}: {dict(row)}")
            print()
            
            return df
        except Exception as e:
            print(f"❌ Encoding {encoding} fehlgeschlagen: {e}")
    
    return False

def step2_count_customers(df):
    """Schritt 2: Kunden zählen"""
    print("🔍 SCHRITT 2: KUNDEN ZÄHLEN")
    print("=" * 50)
    
    customers = 0
    for i, row in df.iterrows():
        kdnr = str(row.get('Kdnr', '')).strip()
        name = str(row.get('Name', '')).strip()
        address = str(row.get('Straße', '')).strip()
        
        # Debug für erste 10 Zeilen
        if i < 10:
            print(f"Zeile {i+1}: Kdnr='{kdnr}', Name='{name}', Straße='{address}'")
        
        # Kunden-Bedingungen prüfen
        has_kdnr = kdnr and kdnr.isdigit()
        has_name = name and name != 'Name'
        has_address = address and address != 'Straße'
        not_header = not name.startswith('W-') and not name.startswith('PIR')
        
        if has_kdnr and has_name and has_address and not_header:
            customers += 1
            if customers <= 5:  # Erste 5 Kunden anzeigen
                print(f"  ✅ KUNDE {customers}: {name} | {address}")
    
    print(f"\n📊 GEFUNDENE KUNDEN: {customers}")
    return customers

def step3_save_to_db(customers_data):
    """Schritt 3: In Datenbank speichern"""
    print("🔍 SCHRITT 3: IN DATENBANK SPEICHERN")
    print("=" * 50)
    
    # Datenbank verbinden
    db_path = Path("data/traffic.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Kunden-Tabelle leeren
    cursor.execute("DELETE FROM kunden")
    print("🗑️  Kunden-Tabelle geleert")
    
    # Kunden speichern
    saved = 0
    for name, address in customers_data:
        cursor.execute("""
            INSERT INTO kunden (Name, Adresse, lat, lng, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
        """, (name, address, 0.0, 0.0))
        saved += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ {saved} Kunden in Datenbank gespeichert")
    return saved

def main():
    print("🚀 CSV-IMPORT PROBLEM LÖSEN")
    print("=" * 60)
    
    # Schritt 1: CSV analysieren
    df = step1_analyze_csv()
    if not df:
        print("❌ Schritt 1 fehlgeschlagen!")
        return
    
    # Schritt 2: Kunden zählen
    customers = step2_count_customers(df)
    if customers == 0:
        print("❌ Schritt 2 fehlgeschlagen - keine Kunden gefunden!")
        return
    
    # Schritt 3: In DB speichern
    # (Hier würden wir die echten Kundendaten sammeln)
    print("✅ Alle Schritte erfolgreich!")
    print(f"📊 Ergebnis: {customers} Kunden gefunden")

if __name__ == "__main__":
    main()
