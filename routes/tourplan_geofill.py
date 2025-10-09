from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from ingest.reader import read_tourplan
from routes.tourplan_match import _addr_col  # wiederverwenden
from repositories.geo_repo import bulk_get
from services.geocode_fill import fill_missing
import asyncio

router = APIRouter()

@router.get("/api/tourplan/geocode-missing")
async def api_geocode_missing(
    file: str = Query(..., description="Pfad zur Original-CSV unter ./Tourplaene"),
    limit: int = Query(20, ge=1, le=100, description="Maximale Anzahl zu geokodierender Adressen"),
    dry_run: bool = Query(False, description="Wenn True, keine DB-Updates")
):
    """
    Geokodiert fehlende Adressen aus einem Tourplan.
    
    - Liest CSV über zentralen Ingest
    - Filtert bereits gecachte Adressen heraus
    - Geokodiert max. `limit` fehlende Adressen mit Rate-Limiting
    - Schreibt nur bei `dry_run=false` in geo_cache
    """
    p = Path(file)
    if not p.exists():
        raise HTTPException(404, detail=f"Datei nicht gefunden: {p}")

    # CSV lesen über zentralen Ingest
    df = read_tourplan(p)
    
    # Adressen extrahieren
    col, offset = _addr_col(df)
    data = df.iloc[offset:].reset_index(drop=True)
    addrs = data.iloc[:, col].fillna("").astype(str).tolist()

    # Bereits vorhandene Geos ausschließen
    geo = bulk_get(addrs)
    missing = [a for a in addrs if a and a.strip() and a not in geo]

    print(f"[GEOCODE API] {len(addrs)} Adressen total, {len(missing)} fehlend, limit={limit}")

    # Fehlende Adressen geokodieren
    res = await fill_missing(missing, limit=limit, dry_run=dry_run)
    
    return JSONResponse({
        "file": str(p),
        "requested": len(missing),
        "processed": min(len(missing), limit),
        "dry_run": dry_run,
        "items": res,
    }, media_type="application/json; charset=utf-8")
