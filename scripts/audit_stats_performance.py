#!/usr/bin/env python3
"""
Performance-Audit: Stats-Aggregation Queries
"""
import sys
import time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.core import ENGINE
from sqlalchemy import text
from datetime import datetime, timedelta

print("=== Stats-Aggregation Performance-Audit ===\n")

with ENGINE.connect() as conn:
    # Prüfe ob Tabellen existieren
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('touren', 'kunden')")).fetchall()
    table_names = [t[0] for t in tables]
    
    if 'touren' not in table_names:
        print("[FEHLER] Tabelle 'touren' fehlt!")
        sys.exit(1)
    
    if 'kunden' not in table_names:
        print("[FEHLER] Tabelle 'kunden' fehlt!")
        sys.exit(1)
    
    # Test 1: Einfache COUNT-Query
    print("Test 1: COUNT-Query Performance")
    start = time.time()
    count = conn.execute(text("SELECT COUNT(*) FROM touren")).scalar()
    elapsed = (time.time() - start) * 1000
    print(f"  Touren: {count} (Dauer: {elapsed:.2f}ms)")
    
    # Test 2: Monatliche Filterung
    print("\nTest 2: Monatliche Filterung")
    month_start = datetime.now().replace(day=1).strftime("%Y-%m-%d")
    if datetime.now().month == 12:
        month_end_date = datetime.now().replace(year=datetime.now().year + 1, month=1, day=1) - timedelta(days=1)
    else:
        month_end_date = datetime.now().replace(month=datetime.now().month + 1, day=1) - timedelta(days=1)
    month_end = month_end_date.strftime("%Y-%m-%d")
    
    start = time.time()
    tour_count = conn.execute(text("""
        SELECT COUNT(*) FROM touren 
        WHERE datum >= :start AND datum <= :end
    """), {"start": month_start, "end": month_end}).scalar()
    elapsed = (time.time() - start) * 1000
    print(f"  Touren im aktuellen Monat: {tour_count} (Dauer: {elapsed:.2f}ms)")
    
    # Test 3: JSON-Parsing für kunden_ids
    print("\nTest 3: kunden_ids JSON-Parsing")
    start = time.time()
    stop_result = conn.execute(text("""
        SELECT SUM(
            CASE 
                WHEN kunden_ids IS NULL OR kunden_ids = '' THEN 0
                ELSE (LENGTH(kunden_ids) - LENGTH(REPLACE(kunden_ids, ',', '')) + 1)
            END
        ) FROM touren 
        WHERE datum >= :start AND datum <= :end
    """), {"start": month_start, "end": month_end}).scalar()
    elapsed = (time.time() - start) * 1000
    print(f"  Stops (vereinfacht): {stop_result or 0} (Dauer: {elapsed:.2f}ms)")
    
    # Test 4: Distanz-Summe
    print("\nTest 4: Distanz-Summe")
    start = time.time()
    km_result = conn.execute(text("""
        SELECT COALESCE(SUM(distanz_km), 0.0) FROM touren 
        WHERE datum >= :start AND datum <= :end AND distanz_km IS NOT NULL
    """), {"start": month_start, "end": month_end}).scalar()
    elapsed = (time.time() - start) * 1000
    print(f"  KM: {km_result or 0.0} (Dauer: {elapsed:.2f}ms)")
    
    # Test 5: Indizes prüfen
    print("\nTest 5: Indizes auf touren")
    indexes = conn.execute(text("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='touren'")).fetchall()
    if indexes:
        for idx in indexes:
            print(f"  - {idx[0]}")
    else:
        print("  [WARNUNG] Keine Indizes auf touren!")
    
    # Test 6: EXPLAIN QUERY PLAN
    print("\nTest 6: Query-Plan (EXPLAIN)")
    plan = conn.execute(text("""
        EXPLAIN QUERY PLAN
        SELECT COUNT(*) FROM touren 
        WHERE datum >= :start AND datum <= :end
    """), {"start": month_start, "end": month_end}).fetchall()
    for row in plan:
        print(f"  {row}")

