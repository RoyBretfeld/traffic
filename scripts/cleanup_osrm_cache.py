"""
OSRM-Cache Cleanup-Job für AR-06.
Löscht abgelaufene Einträge aus dem OSRM-Cache basierend auf TTL.
"""
import sys
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.cache.osrm_cache import OsrmCache
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Führt Cleanup des OSRM-Caches durch."""
    try:
        logger.info("Starte OSRM-Cache Cleanup...")
        deleted_count = OsrmCache.cleanup_old_entries()
        logger.info(f"✅ Cleanup abgeschlossen: {deleted_count} abgelaufene Einträge gelöscht")
        return 0
    except Exception as e:
        logger.error(f"❌ Fehler beim Cleanup: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

