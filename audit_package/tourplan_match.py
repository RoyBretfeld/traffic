from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import pandas as pd
import io
import re
import unicodedata
import os
import asyncio
from ingest.reader import read_tourplan
from repositories.geo_repo import bulk_get
from repositories.geo_alias_repo import resolve_aliases
import unicodedata
import re

def _norm(s: str) -> str:
    """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung (wie Bulk-Process)."""
    s = unicodedata.normalize("NFC", (s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s
from repositories.manual_repo import is_open as manual_is_open
from services.geocode_fill import fill_missing
from ingest.guards import BAD_MARKERS
from services.stop_dto import build_stop_dto

router = APIRouter()

# Geocoding-Erzwingung Konfiguration
ENFORCE = os.getenv("GEOCODE_ENFORCE", "1") not in ("0","false","False")
BATCH_LIMIT = int(os.getenv("GEOCODE_BATCH_LIMIT", "25"))

# Heuristik zur Erkennung der Adressspalte
def _addr_col(df: pd.DataFrame) -> tuple[int, int]:
    """Erkennt die Adressspalte und Header-Offset."""
    header = df.iloc[0].astype(str).str.lower().tolist()
    if any("adresse" in h for h in header):
        return next(i for i,h in enumerate(header) if "adresse" in h), 1
    return (2 if df.shape[1] > 2 else df.shape[1]-1), 0

@router.get("/api/tourplan/match")
async def api_tourplan_match(file: str = Query(..., description="Pfad zur Original-CSV unter ./Tourplaene")):
    """
    Matcht Adressen aus einem Tourplan gegen die geo_cache Datenbank.
    
    - Verwendet modernen Tourplan-Parser für vollständige Adressen
    - Normalisiert Adressen mit PLZ und Stadt
    - Führt bulk_get gegen geo_cache aus
    - Gibt Status je Zeile zurück (ok/warn/bad)
    """
    p = Path(file)
    if not p.exists():
        raise HTTPException(404, detail=f"Datei nicht gefunden: {p}")

    # 1) CSV mit modernem Parser lesen (vollständige Adressen mit PLZ und Stadt)
    from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
    tour_data = parse_tour_plan_to_dict(str(p))

    # 2) Vollständige Adressen zusammenbauen
    
    # Vollständige Adressen aus Kunden-Daten extrahieren
    addrs = []
    for customer in tour_data["customers"]:
        # Verwende die bereits normalisierte Adresse aus dem Parser
        if 'address' in customer and customer['address']:
            full_address = customer['address']
        else:
            # Fallback: Vollständige Adresse zusammenbauen: Straße, PLZ Stadt
            full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
        
        # KRITISCH: Synonym-Check VOR Normalisierung
        customer_name = customer.get('name', '')
        synonym_hit = None
        if customer_name:
            from common.synonyms import resolve_synonym
            synonym_hit = resolve_synonym(customer_name)
        
        if synonym_hit:
            # Synonym gefunden - verwende die Synonym-Adresse
            addrs.append(synonym_hit.resolved_address)
        else:
            # Normale Normalisierung
            addrs.append(_norm(full_address))

    # 4) Alias-Auflösung und DB-Lookup (bulk)
    aliases = resolve_aliases(addrs)  # map: query_norm -> canonical_norm
    geo = bulk_get(addrs + list(aliases.values()))  # beide Mengen laden
    
    # 5) Geocoding-Erzwingung (wenn aktiviert)
    if ENFORCE:
        missing = [a for a in addrs if a and a not in geo]
        if missing:
            print(f"[MATCH ENFORCE] {len(missing)} fehlende Adressen, geokodiere max. {BATCH_LIMIT}")
            await fill_missing(missing, limit=min(BATCH_LIMIT, len(missing)), dry_run=False)
            geo = bulk_get(addrs + list(aliases.values()))  # erneut laden

    # 6) Ergebnis bauen (ok/warn + optional Marker-Hinweis)
    out = []
    for i, customer in enumerate(tour_data["customers"]):
        # Verwende die bereits normalisierte Adresse aus dem Parser
        if 'address' in customer and customer['address']:
            full_address = customer['address']
        else:
            # Fallback: Vollständige Adresse für Anzeige
            full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
        
        # KRITISCH: Synonym-Check für DTO-Erstellung - IMMER für PF-Kunden
        customer_name = customer.get('name', '')
        synonym_hit = None
        
        # Vereinfachter Check: Rufe resolve_synonym immer auf
        from common.synonyms import resolve_synonym
        synonym_hit = resolve_synonym(customer_name)
        
        if synonym_hit:
            # Synonym gefunden - verwende Synonym-Adresse und Koordinaten
            addr_norm = synonym_hit.resolved_address
            marks = []  # Synonyme haben keine Mojibake-Marker
            rec = {
                'lat': synonym_hit.lat,
                'lon': synonym_hit.lon,
                '_note': 'synonym',
                'address': {'road': synonym_hit.resolved_address}
            }
            has_geo = True
            status = "ok"
        else:
            # Normale Verarbeitung
            addr_norm = _norm(full_address)
            marks = [m for m in BAD_MARKERS if m in addr_norm]
            
            # Alias-Auflösung
            canon = aliases.get(addr_norm)
            rec = geo.get(addr_norm) or (geo.get(canon) if canon else None)
            
            # KRITISCHE VALIDIERUNG: Nur gültige Adressen mit deutschen Koordinaten akzeptieren
            has_geo = False
            if rec is not None:
                # Prüfe ob Adresse nicht leer ist
                if full_address and full_address.strip() and full_address != "nan, nan nan":
                    # Prüfe ob Koordinaten in Deutschland liegen (grobe Bounding Box)
                    lat, lon = rec.get('lat', 0), rec.get('lon', 0)
                    if lat and lon and 47.0 <= lat <= 55.0 and 5.0 <= lon <= 15.0:
                        has_geo = True
            
            # Status-Logik:
            # ok: hat VALIDE Geo-Daten UND keine Mojibake-Marker UND gültige Adresse
            # warn: keine Geo-Daten ABER keine Mojibake-Marker  
            # bad: Mojibake-Marker vorhanden ODER ungültige Adresse
            if not full_address or not full_address.strip() or full_address == "nan, nan nan":
                status = "bad"  # Ungültige Adresse = immer bad
            elif has_geo:
                status = "ok" if not marks else "bad"
            else:
                status = "warn" if not marks else "bad"
        
        # Bestimme resolved_address und geo_source
        if synonym_hit:
            # Synonym gefunden - verwende die Synonym-Adresse
            resolved_address = synonym_hit.resolved_address
            geo_source = "synonym"
        else:
            # Normale Verarbeitung
            resolved_address = addr_norm
            geo_source = "cache"
        
        # Extra-Daten für das DTO
        extra = {
            "row": int(i + 1),
            "alias_of": canon,  # zeigt, wenn Alias greift
            "markers": marks,
            "status": status,
            "manual_needed": manual_is_open(addr_norm),
        }
        
        # DTO mit build_stop_dto erstellen
        stop_dto = build_stop_dto(
            stop_id=str(i + 1),
            display_name=customer.get('name', ''),
            resolved_address=resolved_address,
            lat=rec.get('lat') if rec else None,
            lon=rec.get('lon') if rec else None,
            geo_source=geo_source,
            extra=extra
        )
        
        out.append(stop_dto)

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
