from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import unicodedata
import re
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import bulk_get
from services.geocode_persist import write_result
import asyncio

def _norm(s: str) -> str:
    """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung (wie Bulk-Process)."""
    s = unicodedata.normalize("NFC", (s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s

router = APIRouter()

@router.get("/api/tourplan/geocode-missing")
async def api_geocode_missing(
    file: str = Query(..., description="Pfad zur Original-CSV unter ./Tourplaene"),
    limit: int = Query(20, ge=1, le=100, description="Maximale Anzahl zu geokodierender Adressen"),
    dry_run: bool = Query(False, description="Wenn True, keine DB-Updates")
):
    """
    Geokodiert fehlende Adressen aus einem Tourplan.
    
    - Verwendet modernen Tourplan-Parser
    - Filtert bereits gecachte Adressen heraus
    - Geokodiert max. `limit` fehlende Adressen mit Rate-Limiting
    - Schreibt nur bei `dry_run=false` in geo_cache über neuen Persist-Writer
    """
    p = Path(file)
    if not p.exists():
        raise HTTPException(404, detail=f"Datei nicht gefunden: {p}")

    # CSV mit modernem Parser lesen
    tour_data = parse_tour_plan_to_dict(str(p))
    
    # Vollständige Adressen extrahieren
    addrs = []
    for customer in tour_data["customers"]:
        if 'address' in customer and customer['address']:
            full_address = customer['address']
        else:
            full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
        
        # Synonym-Check
        customer_name = customer.get('name', '')
        if customer_name:
            from common.synonyms import resolve_synonym
            synonym_hit = resolve_synonym(customer_name)
            if synonym_hit:
                addrs.append(synonym_hit.resolved_address)
                continue
        
        addrs.append(_norm(full_address))

    # Bereits vorhandene Geos ausschließen
    geo = bulk_get(addrs)
    missing = [a for a in addrs if a and a.strip() and a not in geo]

    print(f"[GEOCODE API] {len(addrs)} Adressen total, {len(missing)} fehlend, limit={limit}")

    # Fehlende Adressen geokodieren (mit neuem System)
    res = await _geocode_missing_new(missing[:limit], dry_run=dry_run)
    
    return JSONResponse({
        "file": str(p),
        "requested": len(missing),
        "processed": min(len(missing), limit),
        "dry_run": dry_run,
        "items": res,
    }, media_type="application/json; charset=utf-8")

async def _geocode_missing_new(addresses: list[str], dry_run: bool = False) -> list[dict]:
    """
    Geokodiert fehlende Adressen mit dem neuen System.
    
    - Verwendet services.geocode_fill._geocode_one für einzelne Adressen
    - Schreibt über services.geocode_persist.write_result
    - Rate-Limiting: 1 Sekunde zwischen Requests
    """
    import httpx
    from services.geocode_fill import _geocode_one
    
    results = []
    
    async with httpx.AsyncClient() as client:
        for i, addr in enumerate(addresses):
            try:
                print(f"[GEOCODE NEW] {i+1}/{len(addresses)}: {addr}")
                
                # Geocoding durchführen
                geo_result = await _geocode_one(addr, client)
                
                if geo_result:
                    # Erfolgreich geocodiert
                    results.append({
                        "address": addr,
                        "result": {
                            "lat": float(geo_result.get("lat", 0)),
                            "lon": float(geo_result.get("lon", 0))
                        }
                    })
                else:
                    # Fehlgeschlagen
                    results.append({
                        "address": addr,
                        "result": None
                    })
                
                # Rate-Limiting: 1 Sekunde zwischen Requests
                if i < len(addresses) - 1:
                    await asyncio.sleep(1.0)
                    
            except Exception as e:
                print(f"[GEOCODE NEW] Fehler bei {addr}: {e}")
                results.append({
                    "address": addr,
                    "result": None,
                    "error": str(e)
                })
    
    return results
