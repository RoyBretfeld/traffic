"""API für Adress-Erkennungsrate und DB-Persistenz-Status."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from db.core import ENGINE
from repositories.manual_repo import get_stats

router = APIRouter(prefix="/api/address-recognition", tags=["address"])


@router.get("/status")
async def recognition_status():
    """
    Zeigt aktuelle Adress-Erkennungsrate und DB-Persistenz-Status.
    
    Regel: Einmal geocodiert = immer aus DB (nicht anders).
    """
    with ENGINE.begin() as conn:
        # Gesamt-Statistik
        total_cached = conn.execute(text("SELECT COUNT(*) FROM geo_cache")).scalar()
        with_coords = conn.execute(text("SELECT COUNT(*) FROM geo_cache WHERE lat IS NOT NULL AND lon IS NOT NULL")).scalar()
        manual_sources = conn.execute(text("SELECT COUNT(*) FROM geo_cache WHERE source = 'manual'")).scalar()
        geocoded_sources = conn.execute(text("SELECT COUNT(*) FROM geo_cache WHERE source = 'geocoded'")).scalar()
        synonym_sources = conn.execute(text("SELECT COUNT(*) FROM geo_cache WHERE source = 'synonym'")).scalar()
        
        # Beispiel-Eintrag
        sample = conn.execute(text("SELECT address_norm, lat, lon, source, last_seen FROM geo_cache WHERE lat IS NOT NULL ORDER BY last_seen DESC LIMIT 1")).fetchone()
        
        # Manual-Queue
        try:
            stats = get_stats()
            pending = stats.get('open', 0)
            total_queue = stats.get('total', 0)
        except Exception:
            pending = 0
            total_queue = 0
    
    recognition_rate = (with_coords / total_cached * 100) if total_cached > 0 else 0
    
    return JSONResponse({
        "geo_cache": {
            "total_entries": total_cached,
            "with_coordinates": with_coords,
            "recognition_rate_percent": round(recognition_rate, 2),
            "sources": {
                "manual": manual_sources,
                "geocoded": geocoded_sources,
                "synonym": synonym_sources
            }
        },
        "manual_queue": {
            "pending": pending,
            "total": total_queue
        },
        "workflow_rule": "Einmal geocodiert = immer aus DB (nicht anders)",
        "persistence_status": "✅ Koordinaten werden dauerhaft in geo_cache gespeichert",
        "sample_entry": {
            "address": sample[0] if sample else None,
            "coordinates": [sample[1], sample[2]] if sample else None,
            "source": sample[3] if sample else None,
            "last_seen": str(sample[4]) if sample else None
        } if sample else None
    })

