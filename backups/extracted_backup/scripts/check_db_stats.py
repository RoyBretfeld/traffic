#!/usr/bin/env python3
"""Datenbank-Statistiken Check"""
import sqlite3
from pathlib import Path

db_path = Path("data/traffic.db")
if not db_path.exists():
    print(f"FEHLER: Datenbank nicht gefunden: {db_path}")
    exit(1)

conn = sqlite3.connect(str(db_path))
cur = conn.cursor()

print("=== Datenbank-Statistiken ===")
print()

# Tabellen auflisten
tables = [row[0] for row in cur.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name").fetchall()]
print(f"Tabellen gefunden: {len(tables)}")
print()

# Wichtige Tabellen prüfen
important_tables = ['kunden', 'touren', 'geo_cache', 'manual_queue', 'geo_fail']

print("Wichtige Tabellen:")
for table in important_tables:
    if table in tables:
        try:
            count = cur.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            print(f"  {table}: {count} Eintraege")
        except Exception as e:
            print(f"  {table}: Fehler beim Zaehlen - {e}")
    else:
        print(f"  {table}: NICHT GEFUNDEN")

print()

# Integrity Check
try:
    result = cur.execute("PRAGMA integrity_check").fetchone()[0]
    if result == "ok":
        print("Integrity Check: OK")
    else:
        print(f"Integrity Check: {result}")
except Exception as e:
    print(f"Integrity Check Fehler: {e}")

conn.close()

