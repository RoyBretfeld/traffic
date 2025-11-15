# routes/audit_status.py
from __future__ import annotations
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import Set, Dict, Any
import os

from common.normalize import normalize_address

import unicodedata
import re

# def _norm(s: str) -> str:
#     """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung (wie Bulk-Process)."""
#     s = unicodedata.normalize("NFC", (s or ""))
#     s = re.sub(r"\s+", " ", s).strip()
#     return s
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
import repositories.geo_repo as repo

router = APIRouter()
TOURPLAN_DIR = Path(os.getenv("TOURPLAN_DIR", "./tourplaene")).resolve()

@router.get("/api/audit/status")
def audit_status(limit: int = Query(50, ge=1, le=1000)):
    """
    Abschlussreport für Geocoding-Vollständigkeit und Statistiken.
    
    Liefert:
    - Coverage-Prozent aller Adressen
    - Fehlende Adressen (Preview)
    - Statistiken nach Quelle, Präzision und Region
    - Manual-Queue Status
    
    Args:
        limit: Maximale Anzahl fehlender Adressen in Preview
        
    Returns:
        JSON mit vollständigem Geocoding-Report
    """
    try:
        # 1) Alle CSV-Dateien finden und verarbeiten
        files = sorted(p for p in TOURPLAN_DIR.glob("*.csv"))
        unique: Set[str] = set()
        
        for csv_file in files:
            try:
                tour_data = parse_tour_plan_to_dict(str(csv_file))
                for customer in tour_data.get('customers', []):
                    # Verwende das 'address' Feld falls vorhanden, sonst baue es aus den Einzelfeldern
                    address = customer.get('address')
                    if not address or not address.strip():
                        # Fallback: Adresse aus Einzelfeldern zusammenbauen
                        street = customer.get('street', '').strip()
                        postal_code = customer.get('postal_code', '').strip()
                        city = customer.get('city', '').strip()
                        if street and postal_code and city:
                            address = f"{street}, {postal_code} {city}"
                    
                    if address and address.strip() and address != "nan, nan nan":
                        unique.add(normalize_address(address))
            except Exception as e:
                print(f"Warning: Could not parse {csv_file.name}: {e}")
                continue

        # 2) Cache-Lookup für alle Adressen
        cache = repo.bulk_get(list(unique))
        missing = sorted(a for a in unique if a not in cache)

        # 3) Statistiken sammeln
        src_cnt = {"synonym": 0, "geocoder": 0, "cache": 0, "unknown": 0}
        prec_cnt = {"full": 0, "zip_centroid": 0, "none": 0}
        region_stats = {"ok": 0, "bad": 0, "unknown": 0}
        
        for v in cache.values():
            # Quelle-Statistiken
            s = v.get('source') or 'unknown'
            if s in src_cnt:
                src_cnt[s] += 1
            else:
                src_cnt["unknown"] += 1
            
            # Präzisions-Statistiken
            p = v.get('precision') or 'none'
            if p in prec_cnt:
                prec_cnt[p] += 1
            else:
                prec_cnt["none"] += 1
            
            # Region-Statistiken
            region_ok = v.get('region_ok')
            if region_ok == 1:
                region_stats["ok"] += 1
            elif region_ok == 0:
                region_stats["bad"] += 1
            else:
                region_stats["unknown"] += 1

        # 4) Manual-Queue Status
        from repositories.manual_repo import list_open
        manual_queue = list_open(limit=100)
        
        # 5) Coverage berechnen
        coverage_pct = 0
        if unique:
            coverage_pct = round(100 * (len(unique) - len(missing)) / len(unique), 2)

        # 6) Report zusammenstellen
        report = {
            "csv_files": len(files),
            "unique_addresses_csv": len(unique),
            "coverage_pct": coverage_pct,
            "missing_count": len(missing),
            "missing_preview": missing[:limit],
            "sources": src_cnt,
            "precision": prec_cnt,
            "region_stats": region_stats,
            "manual_queue_count": len(manual_queue),
            "manual_queue_preview": manual_queue[:10],  # Erste 10 Einträge
            "ok": len(missing) == 0,
            "timestamp": "2025-01-15T10:30:00Z"  # TODO: Echte Timestamp
        }
        
        return JSONResponse(report, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Audit-Status konnte nicht erstellt werden: {str(e)}"}, 
            status_code=500
        )

@router.get("/api/audit/manual-queue")
def get_manual_queue(limit: int = Query(100, ge=1, le=1000)):
    """
    Liefert alle Einträge aus der Manual-Queue.
    
    Args:
        limit: Maximale Anzahl der zurückzugebenden Einträge
        
    Returns:
        JSON mit Manual-Queue Einträgen
    """
    try:
        from repositories.manual_repo import list_open
        items = list_open(limit=limit)
        
        return JSONResponse({
            "count": len(items),
            "items": items
        }, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Manual-Queue konnte nicht abgerufen werden: {str(e)}"}, 
            status_code=500
        )

@router.post("/api/audit/export-manual-queue")
def export_manual_queue():
    """
    Exportiert die Manual-Queue als CSV-Datei.
    
    Returns:
        JSON mit Export-Status und Dateipfad
    """
    try:
        from repositories.manual_repo import export_csv
        from datetime import datetime
        
        # Export-Pfad generieren
        timestamp = datetime.now().strftime("%Y%m%d_%H%M")
        export_path = f"./var/manual_queue/pending_{timestamp}.csv"
        
        # Verzeichnis erstellen falls nicht vorhanden
        Path(export_path).parent.mkdir(parents=True, exist_ok=True)
        
        # CSV exportieren
        count = export_csv(export_path)
        
        return JSONResponse({
            "success": True,
            "export_path": export_path,
            "exported_count": count,
            "message": f"{count} Einträge nach {export_path} exportiert"
        }, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        return JSONResponse(
            {"error": f"Manual-Queue Export fehlgeschlagen: {str(e)}"}, 
            status_code=500
        )
