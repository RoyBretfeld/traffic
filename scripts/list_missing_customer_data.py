#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Listet alle Kundennummern auf, die noch keine vollständigen Adressen haben.
Für Recherche in externer Kundenstamm-Datenbank.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3

def list_missing_customer_data():
    """Listet Kundennummern ohne vollständige Adressdaten"""
    
    db_path = PROJECT_ROOT / "data" / "traffic.db"
    if not db_path.exists():
        print(f"[FEHLER] Datenbank nicht gefunden: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Hole alle Synonyme mit customer_id, aber ohne vollständige Adresse
    query = """
        SELECT DISTINCT 
            customer_id,
            customer_name,
            street,
            postal_code,
            city,
            lat,
            lon,
            alias
        FROM address_synonyms
        WHERE customer_id IS NOT NULL 
            AND customer_id != ''
            AND customer_id REGEXP '^[0-9]{4,}$'  -- Mindestens 4 Ziffern
        ORDER BY CAST(customer_id AS INTEGER)
    """
    
    cursor.execute("SELECT DISTINCT customer_id, customer_name, street, postal_code, city, lat, lon FROM address_synonyms WHERE customer_id IS NOT NULL AND customer_id != ''")
    rows = cursor.fetchall()
    
    # Analysiere jede Kundennummer
    customer_data = {}
    missing_addresses = []
    missing_coords = []
    complete = []
    
    for row in rows:
        cust_id = str(row[0]).strip()
        if not cust_id.isdigit() or len(cust_id) < 4:
            continue
        
        name = row[1] or ''
        street = row[2] or ''
        postal_code = row[3] or ''
        city = row[4] or ''
        lat = row[5]
        lon = row[6]
        
        # Prüfe Vollständigkeit
        has_address = bool(street and postal_code and city)
        has_coords = bool(lat and lon)
        
        if cust_id not in customer_data:
            customer_data[cust_id] = {
                'name': name,
                'street': street,
                'postal_code': postal_code,
                'city': city,
                'lat': lat,
                'lon': lon,
                'has_address': has_address,
                'has_coords': has_coords
            }
        else:
            # Update wenn mehr Daten vorhanden
            if not customer_data[cust_id]['has_address'] and has_address:
                customer_data[cust_id].update({
                    'name': name,
                    'street': street,
                    'postal_code': postal_code,
                    'city': city,
                    'has_address': True
                })
            if not customer_data[cust_id]['has_coords'] and has_coords:
                customer_data[cust_id].update({
                    'lat': lat,
                    'lon': lon,
                    'has_coords': True
                })
    
    # Kategorisiere
    for cust_id, data in sorted(customer_data.items(), key=lambda x: int(x[0])):
        if data['has_address'] and data['has_coords']:
            complete.append(cust_id)
        elif not data['has_address']:
            missing_addresses.append((cust_id, data['name']))
        elif not data['has_coords']:
            missing_coords.append((cust_id, data['name'], f"{data['street']}, {data['postal_code']} {data['city']}".strip(', ')))
    
    # Ausgabe
    print("="*70)
    print("KUNDENNUMMERN-ANALYSE")
    print("="*70)
    print(f"\n[INFO] Gesamt: {len(customer_data)} Kundennummern\n")
    
    print(f"[OK] Vollständig (Adresse + Koordinaten): {len(complete)}")
    if complete:
        print(f"  Nummern: {', '.join(complete)}\n")
    
    print(f"[WARN] Fehlende Adressdaten: {len(missing_addresses)}")
    if missing_addresses:
        print("\n  Diese Nummern sollten in der Kundenstamm-Datenbank recherchiert werden:")
        print("  " + "-"*68)
        for cust_id, name in missing_addresses:
            print(f"  | {cust_id:>6} | {name:<40} | Adresse fehlt")
        print("  " + "-"*68)
        print(f"\n  Nummern: {', '.join([str(c[0]) for c in missing_addresses])}")
    
    print(f"\n[WARN] Fehlende Koordinaten (Adresse vorhanden): {len(missing_coords)}")
    if missing_coords:
        print("\n  Diese Nummern haben Adressen, aber keine Koordinaten:")
        print("  " + "-"*68)
        for cust_id, name, address in missing_coords:
            print(f"  | {cust_id:>6} | {name:<30} | {address}")
        print("  " + "-"*68)
    
    print("\n" + "="*70)
    print("FUR EXTERNE RECHERCHE (Kundenstamm-Datenbank):")
    print("="*70)
    research_list = missing_addresses + [(c[0], c[1]) for c in missing_coords]
    if research_list:
        research_ids = sorted(set([int(c[0]) for c in research_list]))
        print(f"\nKundennummern zum Nachschlagen: {', '.join(map(str, research_ids))}")
        print(f"\nBitte Adressen und Koordinaten für diese Nummern recherchieren:\n")
        for cust_id in research_ids:
            print(f"  - KdNr {cust_id}")
    
    conn.close()

if __name__ == "__main__":
    list_missing_customer_data()

