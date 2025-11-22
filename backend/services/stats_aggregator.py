"""
Stats-Aggregator für echte DB-Daten (Phase 1)
KEINE Mock-Daten - nur echte DB-Aggregationen
Erweitert: Kosten-KPIs gemäß STATISTIK_KOSTEN_KPIS.md
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from sqlalchemy import text
from db.core import ENGINE
from backend.config import cfg

logger = logging.getLogger(__name__)


def get_cost_config() -> Dict[str, float]:
    """
    Lädt Kosten-Konfiguration aus app_settings oder verwendet Defaults.
    
    Returns:
        Dict mit cost_per_km, cost_driver_per_hour, cost_vehicle_per_hour
    """
    # Versuche aus app_settings zu laden
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(text("""
                SELECT name FROM sqlite_master 
                WHERE type='table' AND name='app_settings'
            """))
            if result.fetchone():
                # Lade Kosten-Parameter
                cost_per_km = conn.execute(text("""
                    SELECT value FROM app_settings 
                    WHERE key = 'cost_per_km'
                """)).scalar()
                cost_driver = conn.execute(text("""
                    SELECT value FROM app_settings 
                    WHERE key = 'cost_driver_per_hour'
                """)).scalar()
                cost_vehicle = conn.execute(text("""
                    SELECT value FROM app_settings 
                    WHERE key = 'cost_vehicle_per_hour'
                """)).scalar()
                
                return {
                    "cost_per_km": float(cost_per_km) if cost_per_km else 0.50,
                    "cost_driver_per_hour": float(cost_driver) if cost_driver else 25.0,
                    "cost_vehicle_per_hour": float(cost_vehicle) if cost_vehicle else 0.0
                }
    except Exception as e:
        logger.debug(f"Fehler beim Laden der Kosten-Konfiguration: {e}")
    
    # Defaults (können auch aus config/app.yaml kommen)
    return {
        "cost_per_km": cfg("costs:cost_per_km", 0.50),
        "cost_driver_per_hour": cfg("costs:cost_driver_per_hour", 25.0),
        "cost_vehicle_per_hour": cfg("costs:cost_vehicle_per_hour", 0.0)
    }


def get_vehicle_cost_config(vehicle_type: str = "diesel") -> Dict[str, float]:
    """
    Gibt Kosten-Konfiguration für spezifischen Fahrzeugtyp zurück.
    
    Args:
        vehicle_type: 'diesel', 'e_auto', 'benzin'
    
    Returns:
        Dict mit fuel_cost_per_km, adblue_cost_per_km (nur Diesel), etc.
    """
    # Standard-Werte (können später aus app_settings geladen werden)
    configs = {
        "diesel": {
            "fuel_consumption_per_100km": 8.5,  # Liter pro 100km
            "fuel_price_per_liter": 1.45,  # Euro pro Liter Diesel
            "adblue_consumption_per_100km": 1.5,  # Liter AdBlue pro 100km
            "adblue_price_per_liter": 0.80,  # Euro pro Liter AdBlue
            "fuel_cost_per_km": (8.5 / 100) * 1.45,  # ~0.123 €/km
            "adblue_cost_per_km": (1.5 / 100) * 0.80,  # ~0.012 €/km
            "total_fuel_cost_per_km": (8.5 / 100) * 1.45 + (1.5 / 100) * 0.80  # ~0.135 €/km
        },
        "e_auto": {
            "power_consumption_per_100km": 20.0,  # kWh pro 100km
            "power_price_per_kwh": 0.30,  # Euro pro kWh (Ladestation)
            "fuel_cost_per_km": (20.0 / 100) * 0.30,  # ~0.06 €/km
            "adblue_cost_per_km": 0.0,  # Kein AdBlue
            "total_fuel_cost_per_km": (20.0 / 100) * 0.30  # ~0.06 €/km
        },
        "benzin": {
            "fuel_consumption_per_100km": 9.0,  # Liter pro 100km
            "fuel_price_per_liter": 1.55,  # Euro pro Liter Benzin
            "fuel_cost_per_km": (9.0 / 100) * 1.55,  # ~0.140 €/km
            "adblue_cost_per_km": 0.0,  # Kein AdBlue
            "total_fuel_cost_per_km": (9.0 / 100) * 1.55  # ~0.140 €/km
        }
    }
    
    return configs.get(vehicle_type.lower(), configs["diesel"])


def calculate_tour_cost(
    distance_km: float,
    total_time_min: float,
    stops_count: int,
    cost_config: Optional[Dict[str, float]] = None,
    vehicle_type: str = "diesel"
) -> Dict[str, float]:
    """
    Berechnet Kosten für eine einzelne Tour.
    
    Args:
        distance_km: Gesamtstrecke in km (inkl. Rückfahrt)
        total_time_min: Gesamtzeit in Minuten (Fahren + Service)
        stops_count: Anzahl Stops
        cost_config: Optional, sonst wird get_cost_config() verwendet
        vehicle_type: 'diesel', 'e_auto', 'benzin' (Standard: 'diesel')
    
    Returns:
        Dict mit tour_cost_total, cost_per_stop, cost_per_km, fuel_cost, adblue_cost (nur Diesel)
    """
    if cost_config is None:
        cost_config = get_cost_config()
    
    # Fahrzeugtyp-spezifische Kosten
    vehicle_cost_config = get_vehicle_cost_config(vehicle_type)
    
    hours_total = total_time_min / 60.0
    
    # Treibstoff-Kosten (Diesel + AdBlue, E-Auto, oder Benzin)
    fuel_cost = distance_km * vehicle_cost_config["total_fuel_cost_per_km"]
    adblue_cost = distance_km * vehicle_cost_config.get("adblue_cost_per_km", 0.0) if vehicle_type.lower() == "diesel" else 0.0
    
    # Fahrer-Kosten
    driver_cost = hours_total * cost_config["cost_driver_per_hour"]
    
    # Fahrzeug-Abschreibung/Stundenkosten
    vehicle_hour_cost = hours_total * cost_config["cost_vehicle_per_hour"]
    vehicle_depreciation_km = distance_km * cost_config.get("cost_per_km", 0.50)  # Abschreibung pro km
    
    # Gesamtkosten
    tour_cost_total = fuel_cost + driver_cost + vehicle_hour_cost + vehicle_depreciation_km
    
    result = {
        "tour_cost_total": round(tour_cost_total, 2),
        "cost_per_stop": round(tour_cost_total / stops_count, 2) if stops_count > 0 else 0.0,
        "cost_per_km": round(tour_cost_total / distance_km, 2) if distance_km > 0 else 0.0,
        "fuel_cost": round(fuel_cost, 2),
        "driver_cost": round(driver_cost, 2),
        "vehicle_cost": round(vehicle_hour_cost + vehicle_depreciation_km, 2),
        "vehicle_type": vehicle_type
    }
    
    # AdBlue-Kosten nur für Diesel
    if vehicle_type.lower() == "diesel":
        result["adblue_cost"] = round(adblue_cost, 2)
        result["diesel_cost"] = round(fuel_cost - adblue_cost, 2)
    
    return result


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
            
            # Berechne Kosten-KPIs (analog zu get_daily_stats)
            cost_config = get_cost_config()
            total_cost = 0.0
            total_time_min = 0.0
            
            try:
                # Prüfe ob gesamtzeit_min Spalte existiert (dynamische Spaltenprüfung)
                column_check = conn.execute(text("PRAGMA table_info(touren)")).fetchall()
                has_gesamtzeit_min = any(col[1] == 'gesamtzeit_min' for col in column_check)
                has_dauer_min = any(col[1] == 'dauer_min' for col in column_check)
                time_column = "gesamtzeit_min" if has_gesamtzeit_min else ("dauer_min" if has_dauer_min else "NULL")
                
                tour_rows_with_data = conn.execute(text(f"""
                    SELECT 
                        COALESCE(distanz_km, 0) as distanz,
                        COALESCE({time_column}, 0) as zeit,
                        COALESCE(stops_count, 0) as stops
                    FROM touren 
                    WHERE datum >= :start AND datum <= :end
                """), {"start": month_start, "end": month_end}).fetchall()
                
                for row in tour_rows_with_data:
                    dist, time_min, stops = row[0] or 0, row[1] or 0, row[2] or 0
                    if dist > 0 and time_min > 0 and stops > 0:
                        tour_cost = calculate_tour_cost(dist, time_min, stops, cost_config)
                        total_cost += tour_cost["tour_cost_total"]
                        total_time_min += time_min
                    elif dist > 0:
                        estimated_time = (dist / 50.0) * 60
                        estimated_stops = max(stops, 1) if stops > 0 else 1
                        tour_cost = calculate_tour_cost(dist, estimated_time, estimated_stops, cost_config)
                        total_cost += tour_cost["tour_cost_total"]
                        total_time_min += estimated_time
            except Exception as e:
                logger.debug(f"Kostenberechnung für {month_str} fehlgeschlagen: {e}")
                if km > 0:
                    estimated_time = (km / 50.0) * 60
                    estimated_stops = max(stop_count, 1) if stop_count > 0 else 1
                    tour_cost = calculate_tour_cost(km, estimated_time, estimated_stops, cost_config)
                    total_cost = tour_cost["tour_cost_total"] * tour_count if tour_count > 0 else 0.0
                    total_time_min = estimated_time * tour_count if tour_count > 0 else 0.0
            
            stats.append({
                "month": month_str,
                "tours": tour_count,
                "stops": stop_count,
                "km": round(km, 2),
                "total_time_min": round(total_time_min, 1),
                "total_cost": round(total_cost, 2),
                "avg_cost_per_tour": round(total_cost / tour_count, 2) if tour_count > 0 else 0.0,
                "avg_cost_per_stop": round(total_cost / stop_count, 2) if stop_count > 0 else 0.0,
                "avg_cost_per_km": round(total_cost / km, 2) if km > 0 else 0.0,
                "avg_stops_per_tour": round(stop_count / tour_count, 2) if tour_count > 0 else 0.0,
                "avg_distance_per_tour_km": round(km / tour_count, 2) if tour_count > 0 else 0.0
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
            
            # Berechne Kosten-KPIs (falls distanz_km vorhanden)
            cost_config = get_cost_config()
            total_cost = 0.0
            total_time_min = 0.0
            
            # Versuche Zeit- und Kosten-Daten aus touren zu holen
            # Falls Felder nicht existieren, verwende Schätzungen
            try:
                # Prüfe ob Zeit-Felder existieren (dynamische Spaltenprüfung)
                column_check = conn.execute(text("PRAGMA table_info(touren)")).fetchall()
                has_gesamtzeit_min = any(col[1] == 'gesamtzeit_min' for col in column_check)
                has_dauer_min = any(col[1] == 'dauer_min' for col in column_check)
                time_column = "gesamtzeit_min" if has_gesamtzeit_min else ("dauer_min" if has_dauer_min else "NULL")
                
                tour_rows_with_data = conn.execute(text(f"""
                    SELECT 
                        COALESCE(distanz_km, 0) as distanz,
                        COALESCE({time_column}, 0) as zeit,
                        COALESCE(stops_count, 0) as stops
                    FROM touren 
                    WHERE datum = :date
                """), {"date": day_str}).fetchall()
                
                for row in tour_rows_with_data:
                    dist, time_min, stops = row[0] or 0, row[1] or 0, row[2] or 0
                    if dist > 0 and time_min > 0 and stops > 0:
                        tour_cost = calculate_tour_cost(dist, time_min, stops, cost_config)
                        total_cost += tour_cost["tour_cost_total"]
                        total_time_min += time_min
                    elif dist > 0:
                        # Fallback: Schätze Zeit basierend auf Distanz (50 km/h Durchschnitt)
                        estimated_time = (dist / 50.0) * 60  # Minuten
                        estimated_stops = max(stops, 1) if stops > 0 else 1
                        tour_cost = calculate_tour_cost(dist, estimated_time, estimated_stops, cost_config)
                        total_cost += tour_cost["tour_cost_total"]
                        total_time_min += estimated_time
            except Exception as e:
                logger.debug(f"Kostenberechnung für {day_str} fehlgeschlagen (Felder fehlen?): {e}")
                # Fallback: Schätze basierend auf km
                if km > 0:
                    estimated_time = (km / 50.0) * 60  # Minuten bei 50 km/h
                    estimated_stops = max(stop_count, 1) if stop_count > 0 else 1
                    tour_cost = calculate_tour_cost(km, estimated_time, estimated_stops, cost_config)
                    total_cost = tour_cost["tour_cost_total"] * tour_count if tour_count > 0 else 0.0
                    total_time_min = estimated_time * tour_count if tour_count > 0 else 0.0
            
            stats.append({
                "date": day_str,
                "tours": tour_count,
                "stops": stop_count,
                "km": round(km, 2),
                "total_time_min": round(total_time_min, 1),
                "total_cost": round(total_cost, 2),
                "avg_cost_per_tour": round(total_cost / tour_count, 2) if tour_count > 0 else 0.0,
                "avg_cost_per_stop": round(total_cost / stop_count, 2) if stop_count > 0 else 0.0,
                "avg_cost_per_km": round(total_cost / km, 2) if km > 0 else 0.0,
                "avg_stops_per_tour": round(stop_count / tour_count, 2) if tour_count > 0 else 0.0,
                "avg_distance_per_tour_km": round(km / tour_count, 2) if tour_count > 0 else 0.0
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

