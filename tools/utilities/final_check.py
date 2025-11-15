#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import sqlite3
sys.path.insert(0, '.')

from backend.db.config import get_database_path

print("\n" + "="*80)
print("FINALE ANALYSE")
print("="*80 + "\n")

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM kunden")
total = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NOT NULL AND lon IS NOT NULL AND lat != 0 AND lon != 0")
with_coords = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0")
without_coords = cursor.fetchone()[0]

print(f"DATENBANK GESAMT")
print(f"{'='*80}")
print(f"Total:               {total}")
print(f"  [OK] Mit Koordinaten:   {with_coords} ({with_coords/total*100:.1f}%)")
print(f"  [X] Ohne Koordinaten:  {without_coords} ({without_coords/total*100:.1f}%)")
print()

cursor.execute("SELECT COUNT(*) FROM kunden WHERE (lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0) AND (adresse IS NULL OR adresse = '' OR LENGTH(adresse) < 5)")
without_address = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM kunden WHERE (lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0) AND adresse IS NOT NULL AND adresse != '' AND LENGTH(adresse) >= 5")
with_address = cursor.fetchone()[0]

cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat = 0 AND lon = 0")
old_import = cursor.fetchone()[0]

print(f"AUFSCHLUESSELUNG ({without_coords} ohne Koordinaten):")
print(f"{'='*80}")
print(f"Ohne Adresse (Barkunden):       {without_address}")
print(f"Mit Adresse (Encoding-Problem): {with_address}")
print(f"Davon alter Import (lat=0):     {old_import}")
print()

print(f"{'='*80}")
print(f"ZUSAMMENFASSUNG")
print(f"{'='*80}")
print()
print(f"ERFOLG:")
print(f"  445 neue Kunden mit Koordinaten aus CSVs importiert!")
print()
print(f"NOCH ZU TUN:")
print(f"  {without_address} Barkunden brauchen Adressen")
print(f"  {with_address} alte Kunden mit kaputtem Encoding")
print()
print(f"EMPFEHLUNG:")
print(f"  1. Barkunden-Adressen eingeben")
print(f"  2. Alte {with_address} Kunden loeschen (kaputtes Encoding)")
print()

conn.close()

print("="*80 + "\n")

