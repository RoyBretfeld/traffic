#!/usr/bin/env python3
import sqlite3

def test_naumann_search():
    conn = sqlite3.connect('data/traffic.db')
    
    # Suche nach Naumann-Adressen
    cur = conn.execute("SELECT adresse FROM geocache WHERE adresse LIKE '%Naumann%'")
    rows = cur.fetchall()
    
    print("Naumann-Adressen im Geocache:")
    for i, row in enumerate(rows):
        print(f"  {i+1}: '{row[0]}'")
        print(f"      Länge: {len(row[0])}")
        print(f"      Bytes: {row[0].encode('utf-8')}")
        print()
    
    # Teste exakte Suche
    test_address = "Naumannstraße 12, 01809 Heidenau"
    print(f"Teste exakte Suche für: '{test_address}'")
    print(f"Länge: {len(test_address)}")
    print(f"Bytes: {test_address.encode('utf-8')}")
    
    cur = conn.execute("SELECT lat, lon, provider FROM geocache WHERE adresse = ?", (test_address,))
    row = cur.fetchone()
    print(f"Ergebnis: {row}")
    
    conn.close()

if __name__ == "__main__":
    test_naumann_search()
