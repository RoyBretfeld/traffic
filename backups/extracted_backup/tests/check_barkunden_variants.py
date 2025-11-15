#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft ob alle Varianten der Barkunden in DB sind
"""
import sys
import sqlite3
sys.path.insert(0, '.')

from backend.db.config import get_database_path

print("\n" + "="*80)
print("PRUEFUNG BARKUNDEN-VARIANTEN")
print("="*80 + "\n")

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Prüfe die Varianten
variants = {
    'Sven/Blumentritt': ['Sven - PF', 'Blumentritt', 'Sven - PF (Blumentritt)'],
    'MSM/MFH/Hubraum': ['MSM', 'MFH', 'Hubraum', 'MSM by HUBraum GmbH', 'MFH - PF'],
    'Jochen': ['Jochen - PF'],
    'Motor Mafia': ['Motor Mafia'],
}

print("VARIANTEN-PRUEFUNG:")
print("="*80 + "\n")

for group_name, names in variants.items():
    print(f"{group_name}:")
    found_count = 0
    for name in names:
        cursor.execute("SELECT COUNT(*), lat, lon FROM kunden WHERE name LIKE ? GROUP BY lat, lon", (f'%{name}%',))
        results = cursor.fetchall()
        if results:
            for count, lat, lon in results:
                if lat and lon and lat != 0 and lon != 0:
                    found_count += count
                    print(f"  [OK] {name}: {count}x gefunden (Lat: {lat:.4f}, Lon: {lon:.4f})")
                else:
                    print(f"  [X] {name}: {count}x ohne Koordinaten")
        else:
            print(f"  [-] {name}: nicht gefunden")
    print(f"  GESAMT: {found_count} Eintraege\n")

# Finale Statistik
cursor.execute("SELECT COUNT(*) FROM kunden")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NOT NULL AND lon IS NOT NULL AND lat != 0 AND lon != 0")
with_coords = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat = 0 AND lon = 0")
old_import = cursor.fetchone()[0]

print("="*80)
print("FINALE STATISTIK")
print("="*80)
print(f"Total Kunden:            {total}")
print(f"  [OK] Mit Koordinaten:     {with_coords} ({with_coords/total*100:.1f}%)")
print(f"  [X] Alter Import (lat=0): {old_import} ({old_import/total*100:.1f}%)")
print()
print(f"ERFOLG: {with_coords} von {total - old_import} relevanten Kunden = {with_coords/(total-old_import)*100:.1f}%")
print("="*80 + "\n")

conn.close()

