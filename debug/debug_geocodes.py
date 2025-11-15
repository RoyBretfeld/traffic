#!/usr/bin/env python3
"""
Debug-Skript für Geocodes-Export
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/traffic.db")

def debug_database():
    """Debug die Datenbank-Struktur."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabellen auflisten
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("📋 Tabellen in der Datenbank:")
    for table in tables:
        print(f"  - {table[0]}")
    
    # Kunden-Tabelle Schema
    cursor.execute("PRAGMA table_info(kunden);")
    columns = cursor.fetchall()
    print(f"\n📊 Schema der 'kunden' Tabelle:")
    for col in columns:
        print(f"  - {col[1]} ({col[2]})")
    
    # Erste 5 Kunden
    cursor.execute("SELECT * FROM kunden LIMIT 5;")
    customers = cursor.fetchall()
    print(f"\n👥 Erste 5 Kunden:")
    for customer in customers:
        print(f"  - {customer}")
    
    # Kunden mit Koordinaten
    cursor.execute("""
    SELECT id, name, adresse, lat, lon, created_at
    FROM kunden 
    WHERE lat IS NOT NULL AND lon IS NOT NULL
    LIMIT 3
    """)
    with_coords = cursor.fetchall()
    print(f"\n🗺️ Kunden mit Koordinaten (erste 3):")
    for customer in with_coords:
        print(f"  - ID: {customer[0]}, Name: {customer[1]}")
        print(f"    Adresse: {customer[2]}")
        print(f"    Lat: {customer[3]} (Typ: {type(customer[3])})")
        print(f"    Lon: {customer[4]} (Typ: {type(customer[4])})")
        print(f"    Created: {customer[5]} (Typ: {type(customer[5])})")
        print()
    
    conn.close()

if __name__ == "__main__":
    debug_database()
