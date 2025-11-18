#!/usr/bin/env python3
"""Fügt fehlende Spalten first_seen und last_seen zur geo_cache Tabelle hinzu."""
import sqlite3
from pathlib import Path

db_path = Path("data/traffic.db")
if not db_path.exists():
    print(f"❌ Datenbank nicht gefunden: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Prüfe vorhandene Spalten
cursor.execute("PRAGMA table_info(geo_cache)")
cols = [row[1] for row in cursor.fetchall()]
print(f"Vorhandene Spalten: {cols}")

# Füge first_seen hinzu, falls fehlt
if "first_seen" not in cols:
    try:
        cursor.execute("ALTER TABLE geo_cache ADD COLUMN first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ Spalte 'first_seen' hinzugefügt")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Fehler beim Hinzufügen von 'first_seen': {e}")
else:
    print("ℹ️ Spalte 'first_seen' bereits vorhanden")

# Füge last_seen hinzu, falls fehlt
if "last_seen" not in cols:
    try:
        cursor.execute("ALTER TABLE geo_cache ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        print("✅ Spalte 'last_seen' hinzugefügt")
    except sqlite3.OperationalError as e:
        print(f"⚠️ Fehler beim Hinzufügen von 'last_seen': {e}")
else:
    print("ℹ️ Spalte 'last_seen' bereits vorhanden")

conn.commit()

# Prüfe erneut
cursor.execute("PRAGMA table_info(geo_cache)")
cols_after = [row[1] for row in cursor.fetchall()]
print(f"\nSpalten nach Migration: {cols_after}")
print(f"✅ first_seen vorhanden: {'first_seen' in cols_after}")
print(f"✅ last_seen vorhanden: {'last_seen' in cols_after}")

conn.close()
print("\n✅ Migration abgeschlossen")

