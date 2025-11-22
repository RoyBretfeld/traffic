"""
AR-04 / AR-06: Scheduled Jobs Wrapper.
Führt alle geplanten Jobs aus (Stats-Aggregation, OSRM-Cache Cleanup, etc.).
"""
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_all_jobs():
    """Führt alle geplanten Jobs aus."""
    results = {}
    
    # AR-04: Stats-Daily Aggregation
    try:
        from backend.services.stats_daily_aggregator import aggregate_daily_stats
        from datetime import timedelta
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        result = aggregate_daily_stats(yesterday)
        results['stats_daily'] = {"success": "error" not in result, "result": result}
        logger.info(f"Stats-Daily Aggregation: {'✅' if 'error' not in result else '❌'}")
    except Exception as e:
        results['stats_daily'] = {"success": False, "error": str(e)}
        logger.error(f"Stats-Daily Aggregation fehlgeschlagen: {e}")
    
    # AR-06: OSRM-Cache Cleanup
    try:
        from backend.cache.osrm_cache import OsrmCache
        deleted = OsrmCache.cleanup_old_entries()
        results['osrm_cache_cleanup'] = {"success": True, "deleted": deleted}
        logger.info(f"OSRM-Cache Cleanup: ✅ {deleted} Einträge gelöscht")
    except Exception as e:
        results['osrm_cache_cleanup'] = {"success": False, "error": str(e)}
        logger.error(f"OSRM-Cache Cleanup fehlgeschlagen: {e}")
    
    return results


if __name__ == "__main__":
    results = run_all_jobs()
    
    # Exit-Code basierend auf Ergebnissen
    all_success = all(r.get("success", False) for r in results.values())
    sys.exit(0 if all_success else 1)

