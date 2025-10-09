#!/usr/bin/env python3
import sqlite3

def debug_geocache():
    conn = sqlite3.connect('data/traffic.db')
    
    # Suche nach Heidenau-Einträgen
    cur = conn.execute("SELECT adresse, lat, lon, provider FROM geocache WHERE adresse LIKE '%heidenau%' OR adresse LIKE '%naumann%'")
    rows = cur.fetchall()
    
    print("Geocache Einträge mit Heidenau/Naumann:")
    for row in rows:
        print(f"  Adresse: '{row[0]}'")
        print(f"  Lat: {row[1]} (Typ: {type(row[1])})")
        print(f"  Lon: {row[2]} (Typ: {type(row[2])})")
        print(f"  Provider: {row[3]}")
        print()
    
    # Teste exakte Suche
    test_address = "Naumannstraße 12, 01809 Heidenau"
    cur = conn.execute("SELECT lat, lon, provider FROM geocache WHERE adresse = ?", (test_address,))
    row = cur.fetchone()
    
    print(f"Exakte Suche für '{test_address}':")
    if row:
        print(f"  Gefunden: {row[0]}, {row[1]} via {row[2]}")
    else:
        print("  Nicht gefunden")
    
    conn.close()

if __name__ == "__main__":
    debug_geocache()
