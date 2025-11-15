"""
Stats-API für Statistik-Box (MVP - Mock-Daten)
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.config import cfg

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/overview")
async def overview():
    """
    Liefert Übersichts-Statistiken für die Stats-Box.
    
    MVP: Mock-Daten, später aus DB aggregieren.
    """
    # Prüfe Feature-Flag
    stats_enabled = cfg("app:feature_flags:stats_box_enabled", True)
    if not stats_enabled:
        return JSONResponse({"error": "Stats-Box deaktiviert"}, status_code=503)
    
    # TODO: Später aus DB aggregieren
    # Jetzt: Mock-Daten
    return JSONResponse({
        "monthly_tours": 29,
        "avg_stops": 14.2,
        "km_osrm_month": 812.4
    })

