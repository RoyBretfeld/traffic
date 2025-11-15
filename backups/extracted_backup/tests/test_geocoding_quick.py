#!/usr/bin/env python3
"""
Schneller Geocoding-Test mit nur 5 Plänen - ohne Webseite!
"""

import sys
import os
sys.path.append('backend')

from pathlib import Path
import pandas as pd
import sqlite3
from backend.db.dao import _connect, upsert_kunden, get_kunde_id_by_name_adresse, Kunde

def test_geocoding_quick():
    """Schneller Geocoding-Test mit 5 Plänen."""
    
    print("🚀 Schneller Geocoding-Test")
    print("=" * 50)
    
    # 5 kanonische Pläne auswählen
    test_plans = [
        "tourplaene_canonical/Tourenplan 15.08.2025.csv",
        "tourplaene_canonical/Tourenplan 01.09.2025.csv", 
        "tourplaene_canonical/Tourenplan 02.09.2025.csv",
        "tourplaene_canonical/Tourenplan 03.09.2025.csv",
        "tourplaene_canonical/Tourenplan 04.09.2025.csv"
    ]
    
    print(f"📁 Teste 5 Pläne:")
    for plan in test_plans:
        print(f"   - {Path(plan).name}")
    
    # Datenbank vorher prüfen
    print(f"\n1️⃣ Datenbank-Status vorher...")
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM kunden")
        kunden_vorher = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NOT NULL AND lon IS NOT NULL")
        geocoded_vorher = cursor.fetchone()[0]
        conn.close()
        
        print(f"   📊 Kunden vorher: {kunden_vorher}")
        print(f"   📍 Geocoded vorher: {geocoded_vorher}")
        print(f"   📈 Quote vorher: {(geocoded_vorher/kunden_vorher*100):.1f}%" if kunden_vorher > 0 else "0%")
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return
    
    # 5 Pläne verarbeiten
    print(f"\n2️⃣ Verarbeite 5 Pläne...")
    total_customers = 0
    processed_customers = 0
    
    for i, plan_file in enumerate(test_plans, 1):
        if not Path(plan_file).exists():
            print(f"   ⚠️  {Path(plan_file).name} nicht gefunden")
            continue
            
        print(f"   📄 [{i}/5] {Path(plan_file).name}")
        
        try:
            # CSV lesen
            df = pd.read_csv(plan_file, encoding='utf-8', sep=';', header=None, dtype=str)
            print(f"      ✅ Gelesen: {len(df)} Zeilen")
            
            # Kunden extrahieren (Spalten: Kdnr, Name, Straße, PLZ, Ort, Gedruckt)
            customers = []
            for _, row in df.iterrows():
                kdnr = str(row[0]).strip()
                name = str(row[1]).strip()
                strasse = str(row[2]).strip()
                plz = str(row[3]).strip()
                ort = str(row[4]).strip()
                
                # Gültige Kunden filtern
                if (kdnr and kdnr != 'nan' and 
                    name and name != 'nan' and 
                    strasse and strasse != 'nan' and
                    plz and plz != 'nan' and
                    ort and ort != 'nan'):
                    
                    # Adresse zusammenbauen
                    adresse = f"{strasse}, {plz} {ort}"
                    
                    customers.append(Kunde(
                        name=name,
                        adresse=adresse,
                        lat=None,
                        lon=None
                    ))
            
            print(f"      📍 Gültige Kunden: {len(customers)}")
            
            # Kunden in DB speichern
            if customers:
                try:
                    upsert_kunden(customers)
                    print(f"      ✅ In DB gespeichert")
                    processed_customers += len(customers)
                except Exception as e:
                    print(f"      ❌ DB-Fehler: {e}")
            
            total_customers += len(customers)
            
        except Exception as e:
            print(f"      ❌ Fehler: {e}")
            continue
    
    print(f"\n3️⃣ Verarbeitung abgeschlossen:")
    print(f"   📊 Gesamt Kunden: {total_customers}")
    print(f"   ✅ Verarbeitet: {processed_customers}")
    
    # Datenbank nachher prüfen
    print(f"\n4️⃣ Datenbank-Status nachher...")
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM kunden")
        kunden_nachher = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NOT NULL AND lon IS NOT NULL")
        geocoded_nachher = cursor.fetchone()[0]
        conn.close()
        
        print(f"   📊 Kunden nachher: {kunden_nachher}")
        print(f"   📍 Geocoded nachher: {geocoded_nachher}")
        print(f"   📈 Quote nachher: {(geocoded_nachher/kunden_nachher*100):.1f}%" if kunden_nachher > 0 else "0%")
        
        # Verbesserung berechnen
        if kunden_vorher > 0:
            verbesserung = ((geocoded_nachher - geocoded_vorher) / kunden_vorher) * 100
            print(f"   🎯 Verbesserung: +{verbesserung:.1f}%")
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
        return
    
    # 5. Unerkannte Kunden analysieren
    print(f"\n5️⃣ Unerkannte Kunden analysieren...")
    try:
        conn = _connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name, adresse, lat, lon 
            FROM kunden 
            WHERE lat IS NULL OR lon IS NULL 
            ORDER BY name
            LIMIT 10
        """)
        unerkannte = cursor.fetchall()
        conn.close()
        
        print(f"   🔍 Erste 10 unerkannte Kunden:")
        for name, adresse, lat, lon in unerkannte:
            status = "❌ Keine Koordinaten" if lat is None or lon is None else "✅ Geocoded"
            print(f"     {name} | {adresse} | {status}")
        
    except Exception as e:
        print(f"   ❌ Fehler: {e}")
    
    print(f"\n✅ Schneller Test abgeschlossen!")

if __name__ == "__main__":
    test_geocoding_quick()
