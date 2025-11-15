#!/usr/bin/env python3
"""
Zeigt aktuelle Datenbankstatistik
"""
import sys
import sqlite3
sys.path.insert(0, '.')

from pathlib import Path
from backend.db.config import get_database_path

db_path = get_database_path()

print(f"\n{'='*80}")
print(f"DATENBANK-STATISTIK")
print(f"{'='*80}\n")
print(f"Datenbank: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Gesamtanzahl Kunden
cursor.execute("SELECT COUNT(*) FROM kunden")
total = cursor.fetchone()[0]

# Mit Koordinaten
cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NOT NULL AND lon IS NOT NULL AND lat != 0 AND lon != 0")
with_coords = cursor.fetchone()[0]

# Ohne Koordinaten
cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0")
without_coords = cursor.fetchone()[0]

# Statistiken
success_rate = (with_coords / total * 100) if total > 0 else 0

print(f"KUNDEN IN DATENBANK:")
print(f"{'='*80}")
print(f"Gesamt:              {total:,} Kunden")
print(f"  [OK] Mit Koordinaten:   {with_coords:,} ({success_rate:.1f}%)")
print(f"  [X] Ohne Koordinaten:  {without_coords:,} ({100-success_rate:.1f}%)")
print(f"\n{'='*80}")

# Vorher/Nachher Vergleich
print(f"\nVORHER/NACHHER VERGLEICH:")
print(f"{'='*80}")
print(f"Vorher (aus letzter Analyse): 382 Kunden (16 mit Koordinaten)")
print(f"Jetzt:                        {total:,} Kunden ({with_coords:,} mit Koordinaten)")
print(f"\n  -> NEU HINZUGEFUEGT:        {total - 382:,} Kunden")
print(f"  -> Neue mit Koordinaten:    {with_coords - 16:,} Kunden")
print(f"\n{'='*80}\n")

conn.close()

