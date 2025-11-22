#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft ob Hindernisse in der Datenbank vorhanden sind
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3
from backend.db.config import get_database_path

db_path = get_database_path()
print(f"\n{'='*80}")
print(f"HINDERNISSE & BLITZER CHECK")
print(f"{'='*80}\n")
print(f"Datenbank: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Prüfe ob Tabellen existieren
cursor.execute("""
    SELECT name FROM sqlite_master 
    WHERE type='table' AND name IN ('traffic_incidents', 'speed_cameras')
""")
tables = [row[0] for row in cursor.fetchall()]

print("TABELLEN:")
print(f"  traffic_incidents: {'[OK] Vorhanden' if 'traffic_incidents' in tables else '[FEHLT] Nicht vorhanden'}")
print(f"  speed_cameras: {'[OK] Vorhanden' if 'speed_cameras' in tables else '[FEHLT] Nicht vorhanden'}")
print()

# Prüfe Hindernisse
if 'traffic_incidents' in tables:
    cursor.execute("SELECT COUNT(*) FROM traffic_incidents")
    count = cursor.fetchone()[0]
    print(f"HINDERNISSE: {count} Eintraege")
    
    if count > 0:
        cursor.execute("""
            SELECT incident_id, type, lat, lon, severity, description, delay_minutes, radius_km
            FROM traffic_incidents
            LIMIT 10
        """)
        print("\nErste 10 Hindernisse:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} @ [{row[2]:.6f}, {row[3]:.6f}] | Severity: {row[4]} | Delay: {row[6]}min | Radius: {row[7]}km")
            if row[5]:
                print(f"    Beschreibung: {row[5]}")
    else:
        print("  [WARN] Keine Hindernisse in der Datenbank!")
        print("  -> Verwende POST /api/traffic/incidents um Hindernisse hinzuzufuegen")
else:
    print("HINDERNISSE: Tabelle existiert nicht")
    print("  -> Wird automatisch erstellt beim ersten API-Call")

print()

# Prüfe Blitzer
if 'speed_cameras' in tables:
    cursor.execute("SELECT COUNT(*) FROM speed_cameras")
    count = cursor.fetchone()[0]
    print(f"BLITZER: {count} Eintraege")
    
    if count > 0:
        cursor.execute("""
            SELECT camera_id, type, lat, lon, direction, speed_limit, description, verified
            FROM speed_cameras
            LIMIT 10
        """)
        print("\nErste 10 Blitzer:")
        for row in cursor.fetchall():
            print(f"  - {row[0]}: {row[1]} @ [{row[2]:.6f}, {row[3]:.6f}] | Direction: {row[4] or 'N/A'} | Limit: {row[5] or 'N/A'} km/h | Verified: {bool(row[7])}")
            if row[6]:
                print(f"    Beschreibung: {row[6]}")
    else:
        print("  [WARN] Keine Blitzer in der Datenbank!")
        print("  -> Verwende POST /api/traffic/cameras um Blitzer hinzuzufuegen")
else:
    print("BLITZER: Tabelle existiert nicht")
    print("  -> Wird automatisch erstellt beim ersten API-Call")

print(f"\n{'='*80}\n")

conn.close()

