#!/usr/bin/env python3
"""Prüft welche Tabellen in der DB existieren"""
from db.core import ENGINE
from sqlalchemy import text

with ENGINE.connect() as conn:
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
    print("Verfuegbare Tabellen:")
    for t in tables:
        print(f"  - {t[0]}")

