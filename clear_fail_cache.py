#!/usr/bin/env python3
"""
Fail-Cache komplett leeren
"""
import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

from db.core import ENGINE
from sqlalchemy import text

def clear_fail_cache():
    """Leert den kompletten Fail-Cache"""
    try:
        with ENGINE.begin() as c:
            result = c.execute(text("DELETE FROM geo_fail"))
            count = result.rowcount
            print(f"✅ Fail-Cache geleert! {count} Einträge entfernt.")
            return count
    except Exception as e:
        print(f"❌ Fehler beim Leeren des Fail-Cache: {e}")
        return 0

if __name__ == "__main__":
    clear_fail_cache()
