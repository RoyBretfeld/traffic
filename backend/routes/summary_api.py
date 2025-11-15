"""Einfaches Summary-API für Basis-Gesundheitschecks."""

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from db.core import ENGINE


router = APIRouter()


@router.get("/summary")
async def summary() -> JSONResponse:
    """Liefert Grundzahlen zur App (Anzahl Kunden/Touren)."""

    kunden = 0
    touren = 0

    try:
        with ENGINE.begin() as conn:
            kunden = conn.execute(text("SELECT COUNT(*) FROM geo_cache")).scalar() or 0
            touren = conn.execute(text("SELECT COUNT(*) FROM manual_queue")).scalar() or 0
    except Exception:
        # Falls Tabellen fehlen oder die Verbindung scheitert → Default 0
        kunden = kunden or 0
        touren = touren or 0

    return JSONResponse({"kunden": kunden, "touren": touren}, status_code=200)

