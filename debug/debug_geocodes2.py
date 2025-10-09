#!/usr/bin/env python3
"""
Debug-Skript für Geocodes-Export - Detaillierte Analyse
"""

import sqlite3
from pathlib import Path

DB_PATH = Path("data/traffic.db")

def debug_detailed():
    """Debug die Datenbank-Abfrage detailliert."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Genau die gleiche Abfrage wie im Export-Skript
    query = """
    SELECT 
        id,
        name,
        adresse,
        lat,
        lon,
        created_at
    FROM kunden 
    WHERE lat IS NOT NULL AND lon IS NOT NULL
    ORDER BY name
    LIMIT 3
    """
    
    cursor.execute(query)
    columns = [description[0] for description in cursor.description]
    print(f"📋 Spalten: {columns}")
    
    customers = []
    for row in cursor.fetchall():
        customer = dict(zip(columns, row))
        print(f"👤 Kunde: {customer}")
        print(f"   Lat-Typ: {type(customer['lat'])} = {customer['lat']}")
        print(f"   Lon-Typ: {type(customer['lon'])} = {customer['lon']}")
        customers.append(customer)
    
    conn.close()
    return customers

if __name__ == "__main__":
    debug_detailed()
