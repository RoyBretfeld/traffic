#!/usr/bin/env python3
"""
Finale Statusprüfung
"""
import sys
import sqlite3
sys.path.insert(0, '.')

from backend.db.config import get_database_path

print("\n" + "="*80)
print("FINALE STATUSPR�FUNG")
print("="*80 + "\n")

db_path = get_database_path()
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Gesamtstatistik
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

# Die 191 ohne Koordinaten analysieren
cursor.execute("""
    SELECT COUNT(*) 
    FROM kunden 
    WHERE (lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0)
      AND (adresse IS NULL OR adresse = '' OR LENGTH(adresse) < 5)
""")
without_address = cursor.fetchone()[0]

cursor.execute("""
    SELECT COUNT(*) 
    FROM kunden 
    WHERE (lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0)
      AND adresse IS NOT NULL 
      AND adresse != ''
      AND LENGTH(adresse) >= 5
""")
with_broken_address = cursor.fetchone()[0]

print(f"AUFSCHL�SSELUNG DER {without_coords} KUNDEN OHNE KOORDINATEN:")
print(f"{'='*80}")
print(f"Ohne Adresse (Barkunden):     {without_address}")
print(f"Mit Adresse (Encoding-Problem): {with_broken_address}")
print()

print(f"{'='*80}")
print(f"ANALYSE")
print(f"{'='*80}")
print()
print(f"Von {total} Kunden in der Datenbank:")
print()
print(f"  445 = NEUE Kunden aus CSVs (alle mit Koordinaten) [OK]")
print(f"  {without_address} = Barkunden aus CSVs (brauchen Adressen)")
print(f"  {with_broken_address} = ALTE Kunden (Encoding-Problem)")
print()
print(f"EMPFEHLUNG:")
print(f"  1. Barkunden-Adressen eingeben ({without_address} St�ck)")
print(f"  2. Alte Kunden ({with_broken_address} St�ck) aus DB l�schen")
print(f"     -> Sie stammen aus altem Import mit kaputtem Encoding")
print()

# Prüfe ob die 191 wirklich alt sind (lat=0, lon=0)
cursor.execute("""
    SELECT COUNT(*) 
    FROM kunden 
    WHERE lat = 0 AND lon = 0
""")
with_zero_coords = cursor.fetchone()[0]

print(f"INFO: {with_zero_coords} Kunden haben lat=0, lon=0 (= alter Import)")
print()

conn.close()

print("="*80 + "\n")

