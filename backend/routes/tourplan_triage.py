from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import pandas as pd
from ingest.reader import read_tourplan
from .tourplan_match import _addr_col
from common.normalize import normalize_address
from repositories.geo_alias_repo import resolve_aliases
from repositories.manual_repo import is_open as manual_is_open
from sqlalchemy import text
from db.core import ENGINE

router = APIRouter()

@router.get("/api/tourplan/triage")
def triage(file: str = Query(...), limit: int = Query(30, ge=1, le=200)):
    """
    E2E-Triage für Geo-Probleme: Zeigt raw/norm/cache/alias/fail/manual Status.
    Nur lesen, keine Writes - reine Diagnose.
    """
    p = Path(file)
    if not p.exists():
        raise HTTPException(404, detail=f"Datei nicht gefunden: {p}")
    
    # CSV lesen
    df = read_tourplan(p)
    col, offset = _addr_col(df)
    data = df.iloc[offset:].reset_index(drop=True)
    addrs_raw = data.iloc[:, col].fillna("").astype(str).tolist()[:limit]

    # Normierung + Aliasse
    addrs_norm = [normalize_addr(a) for a in addrs_raw]
    aliases = resolve_aliases(addrs_norm)

    # Cache-Lookup (inkl. Canonicals)
    geo = bulk_get(addrs_norm + list(aliases.values()))

    # Fail-Cache Treffer (Info) - vereinfacht für Tests
    fail = {}

    items = []
    for raw, norm in zip(addrs_raw, addrs_norm):
        canon = aliases.get(norm)
        rec = geo.get(norm) or (geo.get(canon) if canon else None)
        has_geo = rec is not None
        
        items.append({
            "raw": raw,
            "norm": norm,
            "alias_of": canon,
            "in_cache": norm in geo,
            "via_alias": (not norm in geo) and bool(canon and geo.get(canon)),
            "has_geo": has_geo,
            "geo": rec,
            "in_fail": fail.get(norm),
            "manual_needed": manual_is_open(norm),
        })

    return JSONResponse({
        "file": str(p),
        "count": len(items),
        "items": items
    }, media_type="application/json; charset=utf-8")
