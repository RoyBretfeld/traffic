#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Repariert Encoding für alle 191 alten Kunden und geocoded neu
"""
import sys
import sqlite3
import time
import requests
from typing import Dict, Any, Optional

sys.path.insert(0, '.')
from backend.db.config import get_database_path

def fix_encoding(text: str) -> str:
    """Repariert kaputtes Encoding"""
    # Bekannte Encoding-Fehler
    replacements = {
        '\x81': 'ue',  # ü
        '\x84': 'ae',  # ä  
        '\x94': 'oe',  # ö
        '\x9a': 'ue',  # ü
        'á': 'ss',     # ß (manchmal)
        '�': 'ss',     # ß
    }
    
    result = text
    for bad, good in replacements.items():
        result = result.replace(bad, good)
    
    return result

def geocode_nominatim(address: str) -> Optional[Dict[str, Any]]:
    """Direktes Geocoding über Nominatim"""
    url = "https://nominatim.openstreetmap.org/search"
    params = {
        'q': address,
        'format': 'json',
        'limit': 1,
        'countrycodes': 'de'
    }
    headers = {'User-Agent': 'TrafficApp/1.0'}
    
    try:
        time.sleep(1.1)  # Rate limiting
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                result = data[0]
                return {
                    'lat': float(result['lat']),
                    'lon': float(result['lon'])
                }
    except Exception:
        pass
    
    return None

print("\n" + "="*80)
print("ENCODING-REPARATUR UND GEOCODING - 191 ALTE KUNDEN")
print("="*80 + "\n")

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Alle alten Kunden holen
cursor.execute("""
    SELECT id, name, adresse 
    FROM kunden 
    WHERE lat = 0 AND lon = 0
    ORDER BY name
""")

old_customers = cursor.fetchall()

print(f"[1/3] Zu reparieren: {len(old_customers)} Kunden\n")
print(f"[2/3] Starte Reparatur und Geocoding...\n")

stats = {
    'total': len(old_customers),
    'success': 0,
    'failed': 0
}

failed_list = []

for i, (cid, name, address) in enumerate(old_customers, 1):
    # Encoding reparieren
    fixed_address = fix_encoding(address)
    
    # Fortschritt anzeigen (nur Zahlen, keine Umlaute)
    if i % 20 == 0:
        print(f"[{i}/{stats['total']}] Bearbeitet... (Erfolg: {stats['success']}, Fehler: {stats['failed']})")
    
    # Geocoding
    result = geocode_nominatim(fixed_address)
    
    if result:
        # Update: Adresse UND Koordinaten
        cursor.execute("""
            UPDATE kunden 
            SET adresse = ?, lat = ?, lon = ? 
            WHERE id = ?
        """, (fixed_address, result['lat'], result['lon'], cid))
        
        stats['success'] += 1
    else:
        stats['failed'] += 1
        failed_list.append((cid, name, fixed_address))

# Änderungen speichern
conn.commit()
conn.close()

print(f"\n[3/3] FERTIG!")
print(f"\n{'='*80}")
print(f"ENDERGEBNIS")
print(f"{'='*80}")
print(f"Verarbeitet:         {stats['total']}")
print(f"  [OK] Erfolgreich:  {stats['success']} ({stats['success']/stats['total']*100:.1f}%)")
print(f"  [X] Fehlgeschlagen: {stats['failed']} ({stats['failed']/stats['total']*100:.1f}%)")
print(f"\n{'='*80}\n")

# Verbleibende exportieren
if failed_list:
    with open("remaining_failed.txt", "w", encoding="utf-8") as f:
        f.write(f"VERBLEIBENDE PROBLEMFAELLE: {len(failed_list)}\n")
        f.write("="*80 + "\n\n")
        for i, (cid, name, address) in enumerate(failed_list, 1):
            f.write(f"{i}. {name} (ID: {cid})\n")
            f.write(f"   Adresse: {address}\n\n")
    
    print(f"[INFO] {len(failed_list)} verbleibende Faelle in: remaining_failed.txt")
else:
    print(f"[SUCCESS] ALLE Kunden erfolgreich repariert und geocoded!")

print(f"\n{'='*80}\n")

