# routes/audit_geocoding.py
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from pathlib import Path
from collections import Counter
from typing import List, Set, Optional
import os

from common.normalize import normalize_address
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import bulk_get
from db.core import ENGINE
from sqlalchemy import text

router = APIRouter()

@router.get("/api/audit/geocoding")
def audit_geocoding(file: Optional[str] = Query(None, description="Spezifische CSV-Datei für Audit (optional)")):
    """
    Audit-Endpoint für Geocoding-Vollständigkeit und Duplikate.
    
    Prüft:
    1. Alle eindeutigen Adressen aus CSV-Dateien sind geocodiert
    2. Keine Duplikate in geo_cache (address_norm)
    3. Coverage-Prozent und fehlende Adressen
    
    Args:
        file: Optional - spezifische CSV-Datei für Audit (z.B. "mixed.csv")
    """
    try:
        # CSV-Verzeichnis zur Laufzeit lesen (für Tests)
        tourplan_dir = Path(os.getenv("TOURPLAN_DIR", "./tourplaene")).resolve()
        
        # 1) Alle Kunden-Adressen aus CSV sammeln (normalisiert)
        unique_addrs: Set[str] = set()
        
        if file:
            # Spezifische Datei verwenden
            csv_file = tourplan_dir / file
            if not csv_file.exists():
                return JSONResponse({"error": f"Datei nicht gefunden: {csv_file}"}, status_code=404)
            files = [csv_file]
        else:
            # Alle Tourenplan-CSVs verwenden
            files = sorted(p for p in tourplan_dir.glob("Tourenplan *.csv"))
        
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
                    
                    if address and address.strip():
                        unique_addrs.add(normalize_address(address))
            except Exception as e:
                # Log error but continue with other files
                print(f"Warning: Could not parse {csv_file.name}: {e}")
                continue

        # 2) DB-Duplikate prüfen (sollte 0 sein wegen PRIMARY KEY)
        with ENGINE.begin() as c:
            rows = c.execute(text(
                "SELECT address_norm, COUNT(*) as n FROM geo_cache GROUP BY address_norm HAVING n>1"
            )).fetchall()
        duplicates = [{"address_norm": r[0], "count": r[1]} for r in rows]

        # 3) Coverage prüfen (welche fehlen im Cache?)
        cache = bulk_get(list(unique_addrs))
        missing = sorted(a for a in unique_addrs if a not in cache)

        # 4) Zusätzliche Statistiken
        total_cache_entries = 0
        with ENGINE.begin() as c:
            result = c.execute(text("SELECT COUNT(*) FROM geo_cache")).fetchone()
            total_cache_entries = result[0] if result else 0

        # 5) Coverage-Berechnung
        coverage_pct = 0.0
        if unique_addrs:
            coverage_pct = round(100.0 * (len(unique_addrs) - len(missing)) / len(unique_addrs), 2)

        report = {
            "csv_files": len(files),
            "unique_addresses_csv": len(unique_addrs),
            "total_cache_entries": total_cache_entries,
            "cache_hits": len(cache),
            "missing": missing[:50],  # Vorschau (max 50)
            "missing_count": len(missing),
            "duplicates": duplicates[:50],  # Vorschau (max 50)
            "duplicates_count": len(duplicates),
            "coverage_pct": coverage_pct,
            "ok": len(missing) == 0 and len(duplicates) == 0,
            "status": "PASS" if len(missing) == 0 and len(duplicates) == 0 else "FAIL"
        }
        
        return JSONResponse(report, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        error_report = {
            "error": str(e),
            "csv_files": 0,
            "unique_addresses_csv": 0,
            "total_cache_entries": 0,
            "cache_hits": 0,
            "missing": [],
            "missing_count": 0,
            "duplicates": [],
            "duplicates_count": 0,
            "coverage_pct": 0.0,
            "ok": False,
            "status": "ERROR"
        }
        return JSONResponse(error_report, status_code=500, media_type="application/json; charset=utf-8")
