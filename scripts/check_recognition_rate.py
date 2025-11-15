#!/usr/bin/env python3
"""Aktuelle Erkennungsrate prüfen"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

import sqlite3

print("=" * 70)
print("ADDRESS RECOGNITION RATE - STATUS")
print("=" * 70)

try:
    conn = sqlite3.connect('data/traffic.db')
    cursor = conn.cursor()
    
    # Gesamt-Statistik
    total = cursor.execute('SELECT COUNT(*) FROM geo_cache').fetchone()[0]
    with_coords = cursor.execute('SELECT COUNT(*) FROM geo_cache WHERE lat IS NOT NULL AND lon IS NOT NULL').fetchone()[0]
    without_coords = total - with_coords
    
    rate = (with_coords / total * 100) if total > 0 else 0
    
    print(f"\n[GEO_CACHE STATISTIK]")
    print(f"  Gesamt Einträge: {total}")
    print(f"  Mit Koordinaten: {with_coords}")
    print(f"  Ohne Koordinaten: {without_coords}")
    print(f"  Erkennungsrate: {rate:.2f}%")
    
    # Nach Quelle
    print(f"\n[NACH QUELLE]")
    sources = cursor.execute('SELECT source, COUNT(*) FROM geo_cache WHERE lat IS NOT NULL GROUP BY source ORDER BY COUNT(*) DESC').fetchall()
    for src, count in sources:
        percentage = (count / with_coords * 100) if with_coords > 0 else 0
        print(f"  {src}: {count} ({percentage:.1f}%)")
    
    # Manual Queue
    print(f"\n[MANUAL QUEUE]")
    open_queue = cursor.execute('SELECT COUNT(*) FROM manual_queue WHERE status = "open" OR status IS NULL').fetchone()[0]
    closed_queue = cursor.execute('SELECT COUNT(*) FROM manual_queue WHERE status = "closed"').fetchone()[0]
    total_queue = cursor.execute('SELECT COUNT(*) FROM manual_queue').fetchone()[0]
    print(f"  Offen: {open_queue}")
    print(f"  Geschlossen: {closed_queue}")
    print(f"  Gesamt: {total_queue}")
    
    # Geo Fail Cache
    print(f"\n[GEO FAIL CACHE]")
    failed = cursor.execute('SELECT COUNT(*) FROM geo_fail').fetchone()[0]
    print(f"  Fehlgeschlagene Adressen: {failed}")
    
    # Zusammenfassung
    print(f"\n" + "=" * 70)
    print(f"ZUSAMMENFASSUNG:")
    print(f"  Erkennungsrate: {rate:.2f}% ({with_coords}/{total})")
    if open_queue > 0:
        print(f"  [WARN] {open_queue} Adressen in Manual Queue (benötigen manuelle Bearbeitung)")
    if failed > 0:
        print(f"  [INFO] {failed} Adressen im Fail-Cache (werden nicht erneut versucht)")
    if rate >= 90:
        print(f"  [OK] Ziel von 90%+ erreicht!")
    else:
        print(f"  [WARN] Ziel von 90%+ noch nicht erreicht")
    print("=" * 70)
    
    conn.close()
    
except Exception as e:
    print(f"[FEHLER] {e}")
    import traceback
    traceback.print_exc()

