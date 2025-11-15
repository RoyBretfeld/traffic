#!/usr/bin/env python3
"""Bereinigt den Geo Fail Cache, um alle Adressen erneut zu versuchen"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[0]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT.parent) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT.parent))

from repositories.geo_fail_repo import cleanup_expired, get_fail_stats
from sqlalchemy import text
from db.core import ENGINE

print("=" * 70)
print("GEO FAIL CACHE BEREINIGUNG")
print("=" * 70)

# 1. Aktuelle Statistiken
print("\n[1] Aktueller Status:")
stats_before = get_fail_stats()
print(f"  Gesamt Einträge: {stats_before.get('total', 0)}")
print(f"  Aktive Einträge: {stats_before.get('active', 0)}")

# 2. Abgelaufene Einträge bereinigen
print("\n[2] Bereinige abgelaufene Einträge...")
cleaned = cleanup_expired()
print(f"  Bereinigt: {cleaned} abgelaufene Einträge")

# 3. ALLE Einträge löschen (für Neustart)
print("\n[3] Lösche ALLE Einträge aus Fail-Cache...")
print("  (Adressen werden jetzt alle erneut versucht)")
try:
    with ENGINE.begin() as c:
        result = c.execute(text("DELETE FROM geo_fail"))
        deleted = result.rowcount
        print(f"  Gelöscht: {deleted} Einträge")
except Exception as e:
    print(f"  [FEHLER] {e}")

# 4. Finale Statistiken
print("\n[4] Finaler Status:")
stats_after = get_fail_stats()
print(f"  Gesamt Einträge: {stats_after.get('total', 0)}")
print(f"  Aktive Einträge: {stats_after.get('active', 0)}")

print("\n" + "=" * 70)
print("FAZIT:")
print(f"  Der Fail-Cache wurde geleert.")
print(f"  Alle Adressen werden beim nächsten Workflow erneut versucht.")
print(f"  Ziel: 100% Abdeckung durch wiederholtes Versuchen")
print("=" * 70)

