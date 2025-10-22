from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import pandas as pd
import re
import unicodedata
import logging
from ingest.reader import read_tourplan
from repositories.geo_repo import bulk_get
from ingest.guards import BAD_MARKERS

router = APIRouter()

# Logger für Observability
logger = logging.getLogger(__name__)

# Adressspalte heuristisch bestimmen (wie in match)
def _addr_col(df: pd.DataFrame) -> tuple[int, int]:
    """Erkennt die Adressspalte und Header-Offset."""
    header = df.iloc[0].astype(str).str.lower().tolist()
    if any("adresse" in h for h in header):
        return next(i for i, h in enumerate(header) if "adresse" in h), 1
    return (2 if df.shape[1] > 2 else df.shape[1] - 1), 0

@router.get("/api/tourplan/status")
def api_tourplan_status(file: str = Query(..., description="Pfad zur Original-CSV unter ./Tourplaene")):
    """
    Liefert Status-Zähler für eine Tourplan-CSV-Datei.
    
    Returns:
        JSON mit total, cached, missing, marker_hits, examples_missing
    """
    p = Path(file)
    if not p.exists():
        raise HTTPException(404, detail=f"Datei nicht gefunden: {p}")

    # CSV lesen über zentralen Ingest
    df = read_tourplan(p)
    
    # Adressen extrahieren
    col, offset = _addr_col(df)
    data = df.iloc[offset:].reset_index(drop=True)

    def _norm(s: str) -> str:
        """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung."""
        s = unicodedata.normalize("NFC", (s or "")).strip()
        s = re.sub(r"\s+", " ", s)
        return s

    addrs = data.iloc[:, col].fillna("").astype(str).map(_norm).tolist()
    
    # DB-Lookup für bereits gecachte Adressen
    geo = bulk_get(addrs)

    # Zähler berechnen
    total = len(addrs)
    missing = [a for a in addrs if a and a not in geo]
    marks = 0
    for a in addrs:
        if any(m in a for m in BAD_MARKERS):
            marks += 1

    # Mini-Observability: Status-Log nach Berechnung der Zähler
    success_rate = (total - len(missing)) / max(1, total)
    logger.info(f"Tourplan Status: {p.name} - Total: {total}, Cached: {total - len(missing)}, Missing: {len(missing)}, Success Rate: {success_rate:.2%}, Mojibake: {marks}")

    body = {
        "file": str(p),
        "total": total,
        "cached": total - len(missing),
        "missing": len(missing),
        "marker_hits": marks,
        "examples_missing": missing[:5],  # Erste 5 fehlende Adressen als Beispiele
    }
    
    return JSONResponse(body, media_type="application/json; charset=utf-8")
