"""
Stats-Aggregator für echte DB-Daten (Phase 1)
KEINE Mock-Daten - nur echte DB-Aggregationen
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text
from db.core import ENGINE

logger = logging.getLogger(__name__)


def get_monthly_stats(months: int = 12) -> List[Dict]:
    """
    Aggregiert monatliche Statistiken aus der DB.
    
    Args:
        months: Anzahl der letzten Monate (Standard: 12)
    
    Returns:
        Liste von Dicts mit {month, tours, stops, km}
    
    Raises:
        ValueError: Wenn Tabellen nicht existieren oder DB-Fehler auftritt
    """
    with ENGINE.connect() as conn:
        # Prüfe ob Tabellen existieren
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('touren', 'kunden', 'geo_cache')
        """))
        tables = [row[0] for row in result.fetchall()]
        
        if 'touren' not in tables:
            raise ValueError(f"Tabelle 'touren' nicht gefunden. Verfügbare Tabellen: {tables}")
        
        if 'kunden' not in tables:
            raise ValueError(f"Tabelle 'kunden' nicht gefunden. Verfügbare Tabellen: {tables}")
        
        # Aggregiere aus bestehenden Tabellen - ECHTE DATEN
        stats = []
        for i in range(months):
            month_date = datetime.now() - timedelta(days=30 * i)
            month_str = month_date.strftime("%Y-%m")
            month_start = month_date.replace(day=1).strftime("%Y-%m-%d")
            # Monatsende berechnen
            if month_date.month == 12:
                month_end_date = month_date.replace(year=month_date.year + 1, month=1, day=1) - timedelta(days=1)
            else:
                month_end_date = month_date.replace(month=month_date.month + 1, day=1) - timedelta(days=1)
            month_end = month_end_date.strftime("%Y-%m-%d")
            
            # Zähle Touren für diesen Monat (nach Datum gefiltert)
            tour_count = conn.execute(text("""
                SELECT COUNT(*) FROM touren 
                WHERE datum >= :start AND datum <= :end
            """), {"start": month_start, "end": month_end}).scalar() or 0
            
            # Zähle Stops für Touren in diesem Monat
            # kunden_ids ist JSON-Array (z.B. ["5329", "40620"]), wir parsen es
            import json
            stop_count = 0
            tour_rows = conn.execute(text("""
                SELECT kunden_ids FROM touren 
                WHERE datum >= :start AND datum <= :end AND kunden_ids IS NOT NULL AND kunden_ids != ''
            """), {"start": month_start, "end": month_end}).fetchall()
            
            for row in tour_rows:
                try:
                    # Versuche JSON zu parsen
                    ids = json.loads(row[0])
                    if isinstance(ids, list):
                        stop_count += len(ids)
                except (json.JSONDecodeError, TypeError):
                    # Fallback: Zähle Kommas (wenn nicht JSON)
                    ids_str = str(row[0])
                    if ids_str:
                        stop_count += ids_str.count(',') + 1
            
            # Summiere Distanz für diesen Monat (aus touren.distanz_km)
            km_result = conn.execute(text("""
                SELECT COALESCE(SUM(distanz_km), 0.0) FROM touren 
                WHERE datum >= :start AND datum <= :end AND distanz_km IS NOT NULL
            """), {"start": month_start, "end": month_end}).scalar()
            km = float(km_result) if km_result else 0.0
            
            stats.append({
                "month": month_str,
                "tours": tour_count,
                "stops": stop_count,
                "km": round(km, 2)
            })
        
        return stats


def get_daily_stats(days: int = 30) -> List[Dict]:
    """
    Aggregiert tägliche Statistiken aus der DB.
    
    Args:
        days: Anzahl der letzten Tage (Standard: 30)
    
    Returns:
        Liste von Dicts mit {date, tours, stops, km}
    
    Raises:
        ValueError: Wenn Tabellen nicht existieren oder DB-Fehler auftritt
    """
    with ENGINE.connect() as conn:
        # Prüfe ob Tabellen existieren
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('touren', 'kunden')
        """))
        tables = [row[0] for row in result.fetchall()]
        
        if 'touren' not in tables:
            raise ValueError(f"Tabelle 'touren' nicht gefunden. Verfügbare Tabellen: {tables}")
        
        # Aggregiere aus bestehenden Tabellen - ECHTE DATEN
        stats = []
        for i in range(days):
            day_date = datetime.now() - timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            
            # Zähle Touren für diesen Tag
            tour_count = conn.execute(text("""
                SELECT COUNT(*) FROM touren 
                WHERE datum = :date
            """), {"date": day_str}).scalar() or 0
            
            # Zähle Stops für Touren an diesem Tag
            import json
            stop_count = 0
            tour_rows = conn.execute(text("""
                SELECT kunden_ids FROM touren 
                WHERE datum = :date AND kunden_ids IS NOT NULL AND kunden_ids != ''
            """), {"date": day_str}).fetchall()
            
            for row in tour_rows:
                try:
                    ids = json.loads(row[0])
                    if isinstance(ids, list):
                        stop_count += len(ids)
                except (json.JSONDecodeError, TypeError):
                    ids_str = str(row[0])
                    if ids_str:
                        stop_count += ids_str.count(',') + 1
            
            # Summiere Distanz für diesen Tag
            km_result = conn.execute(text("""
                SELECT COALESCE(SUM(distanz_km), 0.0) FROM touren 
                WHERE datum = :date AND distanz_km IS NOT NULL
            """), {"date": day_str}).scalar()
            km = float(km_result) if km_result else 0.0
            
            stats.append({
                "date": day_str,
                "tours": tour_count,
                "stops": stop_count,
                "km": round(km, 2)
            })
        
        return stats


def get_overview_stats() -> Dict:
    """
    Liefert Übersichts-Statistiken für die Stats-Box.
    
    Returns:
        Dict mit monthly_tours, avg_stops, km_osrm_month
    
    Raises:
        ValueError: Wenn DB-Fehler auftritt oder Tabellen fehlen
    """
    monthly = get_monthly_stats(1)  # Letzter Monat
    if not monthly:
        raise ValueError("Keine monatlichen Statistiken verfügbar")
    
    month_data = monthly[0]
    tours = month_data.get("tours", 0)
    stops = month_data.get("stops", 0)
    km = month_data.get("km", 0.0)
    
    # Berechne Durchschnittliche Stops pro Tour (nur wenn Touren vorhanden)
    avg_stops = stops / max(tours, 1) if tours > 0 else 0.0
    
    return {
        "monthly_tours": tours,
        "avg_stops": round(avg_stops, 1),
        "km_osrm_month": round(km, 1)
    }

