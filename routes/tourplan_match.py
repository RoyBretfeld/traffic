from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import pandas as pd
import io
import re
import unicodedata
import os
from ingest.reader import read_tourplan
from repositories.geo_repo import bulk_get, normalize_addr
from ingest.guards import BAD_MARKERS

router = APIRouter()

# Heuristik zur Erkennung der Adressspalte
def _addr_col(df: pd.DataFrame) -> tuple[int, int]:
    """Erkennt die Adressspalte und Header-Offset."""
    header = df.iloc[0].astype(str).str.lower().tolist()
    if any("adresse" in h for h in header):
        return next(i for i,h in enumerate(header) if "adresse" in h), 1
    return (2 if df.shape[1] > 2 else df.shape[1]-1), 0

@router.get("/api/tourplan/match")
def api_tourplan_match(file: str = Query(..., description="Pfad zur Original-CSV unter ./Tourplaene")):
    """
    Matcht Adressen aus einem Tourplan gegen die geo_cache Datenbank.
    
    - Liest CSV über zentralen Ingest (CP850→UTF-8)
    - Normalisiert Adressen
    - Führt bulk_get gegen geo_cache aus
    - Gibt Status je Zeile zurück (ok/warn/bad)
    """
    p = Path(file)
    if not p.exists():
        raise HTTPException(404, detail=f"Datei nicht gefunden: {p}")

    # 1) CSV lesen (zentraler Ingest erzeugt UTF-8-Kopie in STAGING)
    df = read_tourplan(p)

    # 2) Adressen extrahieren
    col, offset = _addr_col(df)
    data = df.iloc[offset:].reset_index(drop=True)

    # 3) Normalisieren + Marker einsammeln
    def _norm(s: str) -> str:
        """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung."""
        s = unicodedata.normalize("NFC", (s or ""))
        s = re.sub(r"\s+", " ", s).strip()
        return s
    
    addrs = data.iloc[:, col].fillna("").astype(str).map(_norm).tolist()

    # 4) DB-Lookup (bulk)
    geo = bulk_get(addrs)

    # 5) Ergebnis bauen (ok/warn + optional Marker-Hinweis)
    out = []
    for i, row in data.iterrows():
        addr_raw = str(row.iloc[col] or "")
        addr_norm = _norm(addr_raw)
        has_geo = addr_norm in geo
        marks = [m for m in BAD_MARKERS if m in addr_norm]
        
        # Status-Logik:
        # ok: hat Geo-Daten UND keine Mojibake-Marker
        # warn: keine Geo-Daten ABER keine Mojibake-Marker  
        # bad: Mojibake-Marker vorhanden
        status = "ok" if (has_geo and not marks) else ("warn" if (not marks and not has_geo) else "bad")
        
        out.append({
            "row": int(i + 1),
            "address": addr_norm,
            "has_geo": bool(has_geo),
            "geo": geo.get(addr_norm),
            "markers": marks,
            "status": status,
        })

    # Zusammenfassung
    body = {
        "file": str(p), 
        "rows": len(out), 
        "ok": sum(1 for r in out if r["status"]=="ok"), 
        "warn": sum(1 for r in out if r["status"]=="warn"), 
        "bad": sum(1 for r in out if r["status"]=="bad"), 
        "items": out
    }
    
    return JSONResponse(body, media_type="application/json; charset=utf-8")
