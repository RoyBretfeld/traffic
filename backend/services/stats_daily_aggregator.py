"""
HT-10 / AR-04: Stats-Daily Aggregator Job.
Füllt stats_daily Tabelle mit aggregierten Tagesstatistiken.
"""
import logging
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import text
from db.core import ENGINE

logger = logging.getLogger(__name__)


def aggregate_daily_stats(date: Optional[str] = None) -> dict:
    """
    Aggregiert Tagesstatistiken und speichert sie in stats_daily (HT-10 / AR-04).
    
    Args:
        date: Datum im Format YYYY-MM-DD (Standard: heute)
    
    Returns:
        Dict mit aggregierten Statistiken
    """
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    
    logger.info(f"Aggregiere Tagesstatistiken für {date}")
    
    with ENGINE.begin() as conn:
        # Prüfe ob stats_daily Tabelle existiert
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='stats_daily'
        """))
        if not result.fetchone():
            logger.warning("Tabelle stats_daily existiert nicht. Migration ausführen?")
            return {"error": "stats_daily table not found"}
        
        # Aggregiere aus tours/tour_stops
        # Hinweis: Nutzt bestehende Tabellen (touren, kunden)
        stats = conn.execute(text("""
            SELECT 
                COUNT(DISTINCT t.id) as total_tours,
                COUNT(DISTINCT CASE WHEN t.status = 'completed' THEN t.id END) as completed_tours,
                COUNT(DISTINCT CASE WHEN t.status = 'aborted' THEN t.id END) as aborted_tours,
                COALESCE(SUM(t.stops_count), 0) as total_stops,
                COALESCE(SUM(t.distanz_km), 0.0) as total_km_planned,
                COALESCE(SUM(t.distanz_km), 0.0) as total_km_real,  -- TODO: Unterscheidung planned/real
                COALESCE(SUM(t.gesamtzeit_min), 0.0) as total_time_min,
                0.0 as total_cost,  -- TODO: Kostenberechnung
                0.0 as avg_delay_minutes,  -- TODO: Delay-Berechnung
                0.0 as avg_success_score  -- TODO: Success-Score
            FROM touren t
            WHERE t.datum = :date
        """), {"date": date}).fetchone()
        
        if not stats:
            logger.warning(f"Keine Daten für {date} gefunden")
            return {"error": "No data found"}
        
        # Upsert in stats_daily
        conn.execute(text("""
            INSERT INTO stats_daily (
                date, region, total_tours, completed_tours, aborted_tours,
                total_stops, total_km_planned, total_km_real, total_time_min,
                total_cost, avg_delay_minutes, avg_success_score, updated_at
            ) VALUES (
                :date, NULL, :total_tours, :completed_tours, :aborted_tours,
                :total_stops, :total_km_planned, :total_km_real, :total_time_min,
                :total_cost, :avg_delay_minutes, :avg_success_score, CURRENT_TIMESTAMP
            )
            ON CONFLICT(date, region) DO UPDATE SET
                total_tours = excluded.total_tours,
                completed_tours = excluded.completed_tours,
                aborted_tours = excluded.aborted_tours,
                total_stops = excluded.total_stops,
                total_km_planned = excluded.total_km_planned,
                total_km_real = excluded.total_km_real,
                total_time_min = excluded.total_time_min,
                total_cost = excluded.total_cost,
                avg_delay_minutes = excluded.avg_delay_minutes,
                avg_success_score = excluded.avg_success_score,
                updated_at = CURRENT_TIMESTAMP
        """), {
            "date": date,
            "total_tours": stats[0] or 0,
            "completed_tours": stats[1] or 0,
            "aborted_tours": stats[2] or 0,
            "total_stops": stats[3] or 0,
            "total_km_planned": stats[4] or 0.0,
            "total_km_real": stats[5] or 0.0,
            "total_time_min": stats[6] or 0.0,
            "total_cost": stats[7] or 0.0,
            "avg_delay_minutes": stats[8] or 0.0,
            "avg_success_score": stats[9] or 0.0
        })
        
        logger.info(f"Stats für {date} aggregiert: {stats[0]} Touren, {stats[3]} Stops")
        
        return {
            "date": date,
            "total_tours": stats[0] or 0,
            "total_stops": stats[3] or 0,
            "total_km": stats[4] or 0.0
        }


def aggregate_date_range(start_date: str, end_date: str) -> dict:
    """
    Aggregiert Statistiken für einen Datumsbereich.
    
    Args:
        start_date: Start-Datum (YYYY-MM-DD)
        end_date: End-Datum (YYYY-MM-DD)
    
    Returns:
        Dict mit Zusammenfassung
    """
    logger.info(f"Aggregiere Statistiken von {start_date} bis {end_date}")
    
    results = []
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_dt = datetime.strptime(end_date, "%Y-%m-%d")
    
    while current_date <= end_dt:
        date_str = current_date.strftime("%Y-%m-%d")
        result = aggregate_daily_stats(date_str)
        if "error" not in result:
            results.append(result)
        current_date += timedelta(days=1)
    
    return {
        "start_date": start_date,
        "end_date": end_date,
        "days_processed": len(results),
        "results": results
    }

