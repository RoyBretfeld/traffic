#!/usr/bin/env python3
"""
Debug-Script: CSV-Analyse für FAMO TrafficApp
Analysiert alle CSV-Dateien und zeigt detaillierte Statistiken
"""

import os
import pandas as pd
import sqlite3
from pathlib import Path
import json

def analyze_csv_files():
    """Analysiert alle CSV-Dateien im tourplaene-Verzeichnis"""
    print("🔍 CSV-DATEIEN ANALYSE")
    print("=" * 50)
    
    tourplaene_dir = Path("tourplaene")
    if not tourplaene_dir.exists():
        print("❌ tourplaene-Verzeichnis nicht gefunden!")
        return
    
    csv_files = list(tourplaene_dir.glob("*.csv"))
    print(f"📁 Gefundene CSV-Dateien: {len(csv_files)}")
    print()
    
    total_rows = 0
    total_unique_customers = set()
    file_stats = []
    
    for csv_file in csv_files:
        try:
            # CSV lesen
            df = pd.read_csv(csv_file, encoding='utf-8')
            row_count = len(df)
            total_rows += row_count
            
            # Eindeutige Kunden zählen (basierend auf Name + Adresse)
            if 'Name' in df.columns and 'Adresse' in df.columns:
                customers = set()
                for _, row in df.iterrows():
                    name = str(row.get('Name', '')).strip()
                    address = str(row.get('Adresse', '')).strip()
                    if name and address:
                        customer_key = f"{name}|{address}"
                        customers.add(customer_key)
                        total_unique_customers.add(customer_key)
                
                unique_customers = len(customers)
            else:
                unique_customers = 0
                print(f"⚠️  {csv_file.name}: Keine 'Name' oder 'Adresse' Spalten gefunden")
            
            file_stats.append({
                'file': csv_file.name,
                'rows': row_count,
                'unique_customers': unique_customers,
                'columns': list(df.columns)
            })
            
            print(f"📄 {csv_file.name}: {row_count} Zeilen, {unique_customers} eindeutige Kunden")
            
        except Exception as e:
            print(f"❌ Fehler bei {csv_file.name}: {e}")
            file_stats.append({
                'file': csv_file.name,
                'rows': 0,
                'unique_customers': 0,
                'error': str(e)
            })
    
    print()
    print("📊 ZUSAMMENFASSUNG")
    print("=" * 50)
    print(f"📁 CSV-Dateien: {len(csv_files)}")
    print(f"📄 Gesamte Zeilen: {total_rows}")
    print(f"👥 Eindeutige Kunden: {len(total_unique_customers)}")
    print(f"📈 Durchschnitt pro Datei: {total_rows // len(csv_files) if csv_files else 0} Zeilen")
    
    return file_stats, total_rows, len(total_unique_customers)

def analyze_database():
    """Analysiert die Datenbank-Inhalte"""
    print("\n🗄️  DATENBANK ANALYSE")
    print("=" * 50)
    
    db_path = Path("data/traffic.db")
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        print(f"📋 Tabellen: {[t[0] for t in tables]}")
        
        # Kunden zählen
        if ('kunden',) in tables:
            cursor.execute("SELECT COUNT(*) FROM kunden")
            kunden_count = cursor.fetchone()[0]
            print(f"👥 Kunden in 'kunden' Tabelle: {kunden_count}")
            
            # Beispiel-Kunden anzeigen
            cursor.execute("SELECT Name, Adresse, lat, lng FROM kunden LIMIT 5")
            sample_customers = cursor.fetchall()
            print("📝 Beispiel-Kunden:")
            for customer in sample_customers:
                print(f"   - {customer[0]} | {customer[1]} | {customer[2]}, {customer[3]}")
        
        if ('customers',) in tables:
            cursor.execute("SELECT COUNT(*) FROM customers")
            customers_count = cursor.fetchone()[0]
            print(f"👥 Kunden in 'customers' Tabelle: {customers_count}")
        
        # Touren zählen
        if ('touren',) in tables:
            cursor.execute("SELECT COUNT(*) FROM touren")
            touren_count = cursor.fetchone()[0]
            print(f"🚗 Touren: {touren_count}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Datenbank-Fehler: {e}")

def analyze_csv_processing():
    """Simuliert den CSV-Processing-Prozess"""
    print("\n⚙️  CSV-PROCESSING SIMULATION")
    print("=" * 50)
    
    tourplaene_dir = Path("tourplaene")
    csv_files = list(tourplaene_dir.glob("*.csv"))
    
    processed_customers = 0
    processed_tours = 0
    
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding='utf-8')
            
            # Simuliere Kunden-Verarbeitung
            customers_in_file = 0
            for _, row in df.iterrows():
                name = str(row.get('Name', '')).strip()
                address = str(row.get('Adresse', '')).strip()
                if name and address:
                    customers_in_file += 1
            
            processed_customers += customers_in_file
            processed_tours += 1
            
            print(f"📄 {csv_file.name}: {customers_in_file} Kunden verarbeitet")
            
        except Exception as e:
            print(f"❌ Fehler bei {csv_file.name}: {e}")
    
    print(f"\n📊 Verarbeitungsergebnis:")
    print(f"   - Kunden: {processed_customers}")
    print(f"   - Touren: {processed_tours}")

if __name__ == "__main__":
    print("🚀 FAMO TrafficApp - CSV Debug Analyse")
    print("=" * 60)
    
    # 1. CSV-Dateien analysieren
    file_stats, total_rows, unique_customers = analyze_csv_files()
    
    # 2. Datenbank analysieren
    analyze_database()
    
    # 3. Processing simulieren
    analyze_csv_processing()
    
    print("\n✅ Analyse abgeschlossen!")
