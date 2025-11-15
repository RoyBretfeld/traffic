#!/usr/bin/env python3
"""
Analysiert die Adressen in der DB ohne Koordinaten
"""
import sys
import sqlite3
sys.path.insert(0, '.')

from backend.db.config import get_database_path

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("""
    SELECT id, name, adresse 
    FROM kunden 
    WHERE (lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0)
      AND adresse IS NOT NULL 
      AND adresse != ''
    LIMIT 10
""")

print("\n" + "="*80)
print("BEISPIEL ADRESSEN (Erste 10)")
print("="*80 + "\n")

for cid, name, address in cursor.fetchall():
    print(f"ID: {cid}")
    print(f"Name: {name}")
    print(f"Adresse: {address}")
    print(f"Adresse (repr): {repr(address)}")
    print()

# Prüfe auch Barkunden
cursor.execute("""
    SELECT COUNT(*) 
    FROM kunden 
    WHERE (lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0)
      AND (adresse IS NULL OR adresse = '')
""")

barkunden_count = cursor.fetchone()[0]

print("="*80)
print(f"STATISTIK")
print("="*80)
print(f"Kunden mit Adresse (kaputt): 191")
print(f"Kunden OHNE Adresse (Barkunden): {barkunden_count}")
print(f"Gesamt ohne Geocode: {191 + barkunden_count}")
print()

conn.close()

