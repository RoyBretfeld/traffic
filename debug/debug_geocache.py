#!/usr/bin/env python3
import sqlite3

def debug_geocache():
    conn = sqlite3.connect('data/traffic.db')
    
    # Prüfe ob Tabelle existiert
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='geocache'")
    result = cur.fetchone()
    print(f"Geocache-Tabelle existiert: {result is not None}")
    
    if result:
        # Prüfe Schema
        cur = conn.execute("PRAGMA table_info(geocache)")
        columns = cur.fetchall()
        print("Geocache-Schema:")
        for col in columns:
            print(f"  {col}")
        
        # Prüfe erste Zeilen
        cur = conn.execute("SELECT * FROM geocache LIMIT 3")
        rows = cur.fetchall()
        print("\nErste 3 Zeilen:")
        for row in rows:
            print(f"  {row}")
            
        # Prüfe spezifische Adresse
        test_address = "Schulstraße 25, 01468 Moritzburg (OT Boxdorf)"
        cur = conn.execute("SELECT lat, lon, provider FROM geocache WHERE adresse = ?", (test_address,))
        row = cur.fetchone()
        print(f"\nTest für Adresse '{test_address}':")
        print(f"  Gefunden: {row}")
        if row:
            print(f"  lat: {row[0]} (type: {type(row[0])})")
            print(f"  lon: {row[1]} (type: {type(row[1])})")
            print(f"  provider: {row[2]} (type: {type(row[2])})")
    
    conn.close()

if __name__ == "__main__":
    debug_geocache()
