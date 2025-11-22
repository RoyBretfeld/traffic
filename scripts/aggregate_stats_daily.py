"""
AR-04: Stats-Daily Aggregator Job (Cron-Job).
Füllt stats_daily Tabelle täglich mit aggregierten Statistiken.
"""
import sys
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.stats_daily_aggregator import aggregate_daily_stats, aggregate_date_range
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Führt tägliche Aggregation durch."""
    try:
        # Aggregiere gestern (Standard)
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        logger.info(f"Starte Aggregation für {yesterday}")
        
        result = aggregate_daily_stats(yesterday)
        
        if "error" in result:
            logger.error(f"Fehler bei Aggregation: {result['error']}")
            return 1
        
        logger.info(f"✅ Aggregation erfolgreich: {result.get('total_tours', 0)} Touren, {result.get('total_stops', 0)} Stops")
        
        # Optional: Aggregiere letzte 7 Tage (falls Lücken vorhanden)
        if len(sys.argv) > 1 and sys.argv[1] == "--backfill":
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            end_date = yesterday
            logger.info(f"Backfill: Aggregiere von {start_date} bis {end_date}")
            range_result = aggregate_date_range(start_date, end_date)
            logger.info(f"Backfill abgeschlossen: {range_result.get('days_processed', 0)} Tage verarbeitet")
        
        return 0
    except Exception as e:
        logger.error(f"❌ Fehler beim Aggregieren: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())

