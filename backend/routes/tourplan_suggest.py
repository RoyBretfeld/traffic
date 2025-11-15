"""
API-Route für Fuzzy-Vorschläge bei fehlenden Adressen
"""
from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import pandas as pd
from ingest.reader import read_tourplan
from repositories.geo_repo import bulk_get
from common.normalize import normalize_address # Importiere normalize_address
from services.fuzzy_suggest import suggest_for

router = APIRouter()

# Heuristik zur Erkennung der Adressspalte (aus tourplan_match.py)
def _addr_col(df: pd.DataFrame) -> tuple[int, int]:
    """Erkennt die Adressspalte und Header-Offset."""
    header = df.iloc[0].astype(str).str.lower().tolist()
    if any("adresse" in h for h in header):
        return next(i for i, h in enumerate(header) if "adresse" in h), 1
    return (2 if df.shape[1] > 2 else df.shape[1] - 1), 0

@router.get("/api/tourplan/suggest")
def api_tourplan_suggest(
    file: str = Query(..., description="Pfad zur Original-CSV unter ./Tourplaene"),
    topk: int = Query(3, ge=1, le=10, description="Maximale Anzahl Vorschläge pro Adresse"),
    threshold: int = Query(70, ge=0, le=100, description="Mindest-Score für Vorschläge (0-100)")
):
    """
    Ermittelt Fuzzy-Vorschläge für fehlende Adressen aus einem Tourplan.
    
    - Liest CSV über zentralen Ingest (CP850→UTF-8)
    - Identifiziert fehlende Adressen (nicht in geo_cache)
    - Führt Fuzzy-Search gegen bekannte Adressen durch
    - Gibt Vorschläge mit Scores zurück (nur lesend)
    """
    p = Path(file)
    if not p.exists():
        raise HTTPException(404, detail=f"Datei nicht gefunden: {p}")

    try:
        # 1) CSV lesen (zentraler Ingest erzeugt UTF-8-Kopie in STAGING)
        df = read_tourplan(p)

        # 2) Adressen extrahieren
        col, offset = _addr_col(df)
        data = df.iloc[offset:].reset_index(drop=True)

        # 3) Adressen normalisieren
        # def _norm(s: str) -> str: # Entfernt: Stattdessen normalize_address verwenden
        #     """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung."""
        #     import unicodedata
        #     import re
        #     s = unicodedata.normalize("NFC", (s or ""))
        #     s = re.sub(r"\s+", " ", s).strip()
        #     return s
        
        addrs = data.iloc[:, col].fillna("").astype(str).map(normalize_address).tolist() # Verwende normalize_address
        
        # Leere Adressen herausfiltern
        addrs = [a for a in addrs if a and a.strip()]

        # 4) Bereits vorhandene Geos herausfiltern
        geo = bulk_get(addrs)
        missing = [a for a in addrs if a and a not in geo]

        if not missing:
            return JSONResponse({
                "file": str(p),
                "missing": 0,
                "message": "Alle Adressen sind bereits im Cache vorhanden",
                "items": []
            }, media_type="application/json; charset=utf-8")

        # 5) Fuzzy-Vorschläge ermitteln
        suggestions = suggest_for(missing, topk=topk, threshold=threshold)

        # 6) Ergebnis zusammenstellen
        body = {
            "file": str(p),
            "missing": len(missing),
            "total_addresses": len(addrs),
            "cached_addresses": len(addrs) - len(missing),
            "parameters": {
                "topk": topk,
                "threshold": threshold
            },
            "items": suggestions
        }
        
        return JSONResponse(body, media_type="application/json; charset=utf-8")

    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Verarbeiten der CSV: {str(e)}")

@router.get("/api/tourplan/suggest/stats")
def api_tourplan_suggest_stats():
    """
    Gibt Statistiken über den Fuzzy-Suggest Service zurück.
    """
    try:
        from services.fuzzy_suggest import get_suggestions_stats
        stats = get_suggestions_stats()
        return JSONResponse(stats, media_type="application/json; charset=utf-8")
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Abrufen der Statistiken: {str(e)}")
