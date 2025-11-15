#!/usr/bin/env python3
"""
DB-Audit: Prüft Tabellen und Stats-Aggregation
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from db.core import ENGINE
from sqlalchemy import text

print("=== DB-Tabellen-Audit ===\n")

with ENGINE.connect() as conn:
    # 1. Alle Tabellen auflisten
    tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")).fetchall()
    print(f"Verfuegbare Tabellen ({len(tables)}):")
    for t in tables:
        print(f"  - {t[0]}")
    
    print("\n=== Wichtige Tabellen ===")
    
    # 2. Prüfe touren-Tabelle
    if any(t[0] == 'touren' for t in tables):
        count = conn.execute(text("SELECT COUNT(*) FROM touren")).scalar()
        print(f"[OK] touren: {count} Eintraege")
        
        # Prüfe Spalten
        columns = conn.execute(text("PRAGMA table_info(touren)")).fetchall()
        print(f"   Spalten: {', '.join([c[1] for c in columns])}")
        
        # Prüfe Indizes
        indexes = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='touren'")).fetchall()
        print(f"   Indizes: {', '.join([i[0] for i in indexes]) if indexes else 'Keine'}")
        
        # Prüfe Beispiel-Daten
        if count > 0:
            sample = conn.execute(text("SELECT tour_id, datum, kunden_ids, distanz_km FROM touren LIMIT 1")).fetchone()
            if sample:
                print(f"   Beispiel: {sample[0]} am {sample[1]} ({sample[2] or 'keine IDs'})")
    else:
        print("[FEHLER] touren: Tabelle fehlt!")
    
    # 3. Prüfe kunden-Tabelle
    if any(t[0] == 'kunden' for t in tables):
        count = conn.execute(text("SELECT COUNT(*) FROM kunden")).scalar()
        print(f"[OK] kunden: {count} Eintraege")
        
        # Prüfe Spalten
        columns = conn.execute(text("PRAGMA table_info(kunden)")).fetchall()
        print(f"   Spalten: {', '.join([c[1] for c in columns])}")
        
        # Prüfe Indizes
        indexes = conn.execute(text("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='kunden'")).fetchall()
        print(f"   Indizes: {', '.join([i[0] for i in indexes]) if indexes else 'Keine'}")
    else:
        print("[FEHLER] kunden: Tabelle fehlt!")
    
    # 4. Prüfe geo_cache
    if any(t[0] == 'geo_cache' for t in tables):
        count = conn.execute(text("SELECT COUNT(*) FROM geo_cache")).scalar()
        print(f"[OK] geo_cache: {count} Eintraege")
    else:
        print("[FEHLER] geo_cache: Tabelle fehlt!")
    
    print("\n=== Stats-Aggregation-Test ===")
    try:
        from backend.services.stats_aggregator import get_overview_stats
        stats = get_overview_stats()
        print(f"[OK] Stats-Aggregation funktioniert:")
        print(f"   Touren (Monat): {stats['monthly_tours']}")
        print(f"   Stops Ø: {stats['avg_stops']}")
        print(f"   KM: {stats['km_osrm_month']}")
    except Exception as e:
        print(f"[FEHLER] Stats-Aggregation: {e}")
        import traceback
        traceback.print_exc()

