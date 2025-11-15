#!/usr/bin/env python3
"""Test Datenbank direkt"""
import sqlite3
from pathlib import Path

db_path = Path("data/traffic.db")
print(f"Datenbank-Pfad: {db_path}")
print(f"Existiert: {db_path.exists()}")

try:
    conn = sqlite3.connect(str(db_path), timeout=10)
    cur = conn.cursor()
    result = cur.execute("SELECT name FROM sqlite_master WHERE type='table' LIMIT 5").fetchall()
    print(f"Tabellen gefunden: {len(result)}")
    print(f"Erste 5: {[r[0] for r in result]}")
    conn.close()
    print("✓ Datenbank-Zugriff erfolgreich")
except Exception as e:
    print(f"✗ Fehler: {e}")

