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
        
        # Erstelle CSV
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()
        writer.writerows(data)
        
        return Response(
            content=output.getvalue(),
            media_type="text/csv",
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

