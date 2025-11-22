"""
Stats-API für Statistik-Box (Phase 1 - Echte DB-Daten)
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.config import cfg
from backend.services.stats_aggregator import get_overview_stats, get_monthly_stats, get_daily_stats
from fastapi.responses import Response
import csv
import json
from io import StringIO

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
async def overview():
    """
    Liefert Übersichts-Statistiken für die Stats-Box.
    
    Phase 1: Echte DB-Daten (aus bestehenden Tabellen aggregiert).
    KEINE Mock-Daten - bei Fehler wird HTTP 500 zurückgegeben.
    """
    # Prüfe Feature-Flag
    stats_enabled = cfg("app:feature_flags:stats_box_enabled", True)
    if not stats_enabled:
        return JSONResponse({"error": "Stats-Box deaktiviert"}, status_code=503)
    
    try:
        stats = get_overview_stats()
        return JSONResponse(stats)
    except ValueError as e:
        # DB-Tabellen fehlen oder Daten nicht verfügbar
        return JSONResponse({
            "error": f"Stats-Aggregation fehlgeschlagen: {str(e)}",
            "detail": "Datenbank-Tabellen fehlen oder sind nicht verfügbar"
        }, status_code=500)
    except Exception as e:
        # Unerwarteter Fehler
        return JSONResponse({
            "error": f"Unerwarteter Fehler bei Stats-Aggregation: {str(e)}",
            "detail": "Bitte Server-Logs prüfen"
        }, status_code=500)


@router.get("/monthly")
async def monthly(months: int = 12):
    """
    Liefert monatliche Statistiken.
    
    Args:
        months: Anzahl der letzten Monate (Standard: 12)
    """
    stats_enabled = cfg("app:feature_flags:stats_box_enabled", True)
    if not stats_enabled:
        return JSONResponse({"error": "Stats-Box deaktiviert"}, status_code=503)
    
    try:
        stats = get_monthly_stats(months)
        return JSONResponse({"months": stats})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/daily")
async def daily(days: int = 30):
    """
    Liefert tägliche Statistiken.
    
    Args:
        days: Anzahl der letzten Tage (Standard: 30)
    """
    stats_enabled = cfg("app:feature_flags:stats_box_enabled", True)
    if not stats_enabled:
        return JSONResponse({"error": "Stats-Box deaktiviert"}, status_code=503)
    
    try:
        stats = get_daily_stats(days)
        return JSONResponse({"days": stats})
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/export/csv")
async def export_csv(period: str = "monthly", count: int = 12):
    """
    Exportiert Statistiken als CSV.
    
    Args:
        period: "daily" oder "monthly" (Standard: "monthly")
        count: Anzahl der Perioden (Standard: 12)
    """
    stats_enabled = cfg("app:feature_flags:stats_box_enabled", True)
    if not stats_enabled:
        return JSONResponse({"error": "Stats-Box deaktiviert"}, status_code=503)
    
    try:
        if period == "daily":
            data = get_daily_stats(count)
            filename = f"stats_daily_{count}days.csv"
            headers = ["date", "tours", "stops", "km"]
        else:
            data = get_monthly_stats(count)
            filename = f"stats_monthly_{count}months.csv"
            headers = ["month", "tours", "stops", "km"]
        
        # HT-05: Erstelle CSV mit CSV-Injection-Schutz
        from backend.utils.csv_export import export_to_csv_file
        csv_bytes = export_to_csv_file(data, fieldnames=headers)
        
        return Response(
            content=csv_bytes,
            media_type="text/csv; charset=utf-8",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/export/json")
async def export_json(period: str = "monthly", count: int = 12):
    """
    Exportiert Statistiken als JSON.
    
    Args:
        period: "daily" oder "monthly" (Standard: "monthly")
        count: Anzahl der Perioden (Standard: 12)
    """
    stats_enabled = cfg("app:feature_flags:stats_box_enabled", True)
    if not stats_enabled:
        return JSONResponse({"error": "Stats-Box deaktiviert"}, status_code=503)
    
    try:
        if period == "daily":
            data = get_daily_stats(count)
            filename = f"stats_daily_{count}days.json"
            key = "days"
        else:
            data = get_monthly_stats(count)
            filename = f"stats_monthly_{count}months.json"
            key = "months"
        
        return Response(
            content=json.dumps({key: data}, indent=2),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@router.get("/costs")
async def costs_stats(from_date: str = None, to_date: str = None, group: str = "day"):
    """
    Liefert Kosten-Statistiken für einen Zeitraum.
    
    Args:
        from_date: Start-Datum (YYYY-MM-DD), optional (Standard: heute - 30 Tage)
        to_date: End-Datum (YYYY-MM-DD), optional (Standard: heute)
        group: "day" oder "week" (Standard: "day")
    
    Returns:
        JSON mit Kosten-KPIs pro Tag/Woche
    """
    stats_enabled = cfg("app:feature_flags:stats_box_enabled", True)
    if not stats_enabled:
        return JSONResponse({"error": "Stats-Box deaktiviert"}, status_code=503)
    
    try:
        from datetime import datetime, timedelta
        
        if not to_date:
            to_date = datetime.now().strftime("%Y-%m-%d")
        if not from_date:
            from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Parse dates
        from_dt = datetime.strptime(from_date, "%Y-%m-%d")
        to_dt = datetime.strptime(to_date, "%Y-%m-%d")
        
        if group == "week":
            # Wochenweise Aggregation
            stats = []
            current = from_dt
            while current <= to_dt:
                week_start = current
                week_end = min(current + timedelta(days=6), to_dt)
                
                # Aggregiere Daten für diese Woche
                week_days = get_daily_stats((week_end - week_start).days + 1)
                week_days = [d for d in week_days if week_start.strftime("%Y-%m-%d") <= d["date"] <= week_end.strftime("%Y-%m-%d")]
                
                if week_days:
                    total_tours = sum(d.get("tours", 0) for d in week_days)
                    total_stops = sum(d.get("stops", 0) for d in week_days)
                    total_km = sum(d.get("km", 0) for d in week_days)
                    total_cost = sum(d.get("total_cost", 0) for d in week_days)
                    total_time = sum(d.get("total_time_min", 0) for d in week_days)
                    
                    stats.append({
                        "date": week_start.strftime("%Y-%m-%d"),
                        "week": f"{week_start.strftime('%Y-W%V')}",
                        "total_tours": total_tours,
                        "total_stops": total_stops,
                        "total_distance_km": round(total_km, 2),
                        "total_time_min": round(total_time, 1),
                        "total_cost": round(total_cost, 2),
                        "avg_stops_per_tour": round(total_stops / total_tours, 2) if total_tours > 0 else 0.0,
                        "avg_distance_per_tour_km": round(total_km / total_tours, 2) if total_tours > 0 else 0.0,
                        "avg_cost_per_tour": round(total_cost / total_tours, 2) if total_tours > 0 else 0.0,
                        "avg_cost_per_stop": round(total_cost / total_stops, 2) if total_stops > 0 else 0.0,
                        "avg_cost_per_km": round(total_cost / total_km, 2) if total_km > 0 else 0.0
                    })
                
                current = week_end + timedelta(days=1)
            
            return JSONResponse(stats)
        else:
            # Tagesweise Aggregation
            days = (to_dt - from_dt).days + 1
            stats = get_daily_stats(days)
            
            # Filtere nach Datumsbereich
            filtered_stats = [
                s for s in stats 
                if from_date <= s["date"] <= to_date
            ]
            
            # Formatiere für API-Response
            result = []
            for s in filtered_stats:
                result.append({
                    "date": s["date"],
                    "total_tours": s.get("tours", 0),
                    "total_stops": s.get("stops", 0),
                    "total_distance_km": s.get("km", 0.0),
                    "total_time_min": s.get("total_time_min", 0.0),
                    "total_cost": s.get("total_cost", 0.0),
                    "avg_stops_per_tour": s.get("avg_stops_per_tour", 0.0),
                    "avg_distance_per_tour_km": s.get("avg_distance_per_tour_km", 0.0),
                    "avg_cost_per_tour": s.get("avg_cost_per_tour", 0.0),
                    "avg_cost_per_stop": s.get("avg_cost_per_stop", 0.0),
                    "avg_cost_per_km": s.get("avg_cost_per_km", 0.0)
                })
            
            return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)
