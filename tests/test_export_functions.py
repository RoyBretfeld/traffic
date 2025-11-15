#!/usr/bin/env python3
"""
Test der Export-Funktionen einzeln
"""

import sqlite3
import json
import csv
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any

DB_PATH = Path("data/traffic.db")

def get_all_customers_with_coordinates() -> List[Dict[str, Any]]:
    """Liest alle Kunden mit Koordinaten aus der Datenbank."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
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
    LIMIT 5
    """
    
    cursor.execute(query)
    columns = [description[0] for description in cursor.description]
    customers = []
    
    for row in cursor.fetchall():
        customer = dict(zip(columns, row))
        customers.append(customer)
    
    conn.close()
    return customers

def test_geojson():
    """Test GeoJSON-Export."""
    print("🧪 Teste GeoJSON-Export...")
    customers = get_all_customers_with_coordinates()
    
    features = []
    for customer in customers:
        print(f"Verarbeite Kunde: {customer['name']}")
        print(f"  Lat: {customer['lat']} (Typ: {type(customer['lat'])})")
        print(f"  Lon: {customer['lon']} (Typ: {type(customer['lon'])})")
        
        lat = float(customer['lat']) if customer['lat'] is not None else 0.0
        lon = float(customer['lon']) if customer['lon'] is not None else 0.0
        created_at = str(customer['created_at']) if customer['created_at'] is not None else ""
        
        feature = {
            "type": "Feature",
            "properties": {
                "id": customer["id"],
                "name": customer["name"],
                "adresse": customer["adresse"],
                "created_at": created_at
            },
            "geometry": {
                "type": "Point",
                "coordinates": [lon, lat]
            }
        }
        features.append(feature)
    
    print(f"✅ GeoJSON-Test erfolgreich: {len(features)} Features")

def test_markdown():
    """Test Markdown-Export."""
    print("🧪 Teste Markdown-Export...")
    customers = get_all_customers_with_coordinates()
    
    for customer in customers:
        print(f"Verarbeite Kunde: {customer['name']}")
        lat = float(customer['lat']) if customer['lat'] is not None else 0.0
        lon = float(customer['lon']) if customer['lon'] is not None else 0.0
        created_at = str(customer['created_at']) if customer['created_at'] is not None else ""
        print(f"  Lat: {lat:.6f}, Lon: {lon:.6f}, Created: {created_at}")
    
    print("✅ Markdown-Test erfolgreich")

if __name__ == "__main__":
    test_geojson()
    print()
    test_markdown()
