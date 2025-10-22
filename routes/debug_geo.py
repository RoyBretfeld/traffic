from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from db.core import ENGINE
from common.normalize import normalize_address

router = APIRouter()

@router.get("/debug/geo/peek")
def debug_geo_peek(addr: str = Query(..., description="Adresse im Klartext")):
    """
    Mini-Diagnose-Route für Geocoding-Debugging.
    
    Prüft ob eine Adresse im geo_cache vorhanden ist und gibt Details zurück.
    """
    key = normalize_address(addr)
    
    with ENGINE.begin() as c:
        row = c.execute(text(
            "SELECT address_norm, lat, lon, source, by_user, updated_at FROM geo_cache WHERE address_norm=:a"
        ), {"a": key}).mappings().first()
    
    return JSONResponse({
        "query": addr,
        "norm": key,
        "hit": bool(row),
        "row": dict(row) if row else None
    }, media_type="application/json; charset=utf-8")

@router.get("/debug/geo/stats")
def debug_geo_stats():
    """
    Statistik über den geo_cache für Debugging.
    """
    with ENGINE.begin() as c:
        # Gesamtanzahl Einträge
        total = c.execute(text("SELECT COUNT(*) as count FROM geo_cache")).scalar()
        
        # Einträge nach Source gruppiert
        sources = c.execute(text(
            "SELECT source, COUNT(*) as count FROM geo_cache GROUP BY source"
        )).mappings().all()
        
        # Letzte Updates
        recent = c.execute(text(
            "SELECT address_norm, updated_at FROM geo_cache ORDER BY updated_at DESC LIMIT 5"
        )).mappings().all()
    
    return JSONResponse({
        "total_entries": total,
        "by_source": [dict(s) for s in sources],
        "recent_updates": [dict(r) for r in recent]
    }, media_type="application/json; charset=utf-8")
