"""
Bulk Processing aller CSV-Tourpläne mit DB-First Strategie
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import asyncio
import uuid
from typing import Dict, Any, List
from repositories.geo_repo import get as geo_get, upsert as geo_upsert, bulk_get
from backend.services.geocode import geocode_address
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from common.normalize import normalize_address

router = APIRouter()

# Progress-Tracker für Bulk-Processing (Session-basiert, wie bei workflow_upload)
_bulk_progress: Dict[str, Dict[str, Any]] = {}


@router.get("/api/tourplan/bulk-progress/{session_id}")
async def get_bulk_progress(session_id: str):
    """Liefert den aktuellen Bulk-Processing-Progress für eine Session."""
    progress = _bulk_progress.get(session_id, {
        "total_files": 0,
        "processed_files": 0,
        "current_file": "",
        "total_customers": 0,
        "processed_customers": 0,
        "db_hits": 0,
        "geoapify_calls": 0,
        "errors": 0,
        "status": "idle"
    })
    return JSONResponse(progress)


@router.post("/api/tourplan/bulk-process-all")
async def bulk_process_all_csv():
    """
    Verarbeitet ALLE CSV-Dateien aus dem tourplaene Verzeichnis.
    
    DB-First Strategie:
    1. Lädt alle CSV-Dateien
    2. Für jede Datei: Parse alle Kunden
    3. Für jeden Kunden:
       - Prüfe DB (geo_get) → Wenn vorhanden: Überspringen
       - Wenn nicht in DB: Geocode mit Geoapify
       - Speichere in DB (geo_upsert)
    4. Live-Progress-Tracking
    
    Returns:
        JSON mit Statistiken (Dateien, Kunden, DB-Hits, Geoapify-Calls, etc.)
    """
    session_id = str(uuid.uuid4())
    _bulk_progress[session_id] = {
        "total_files": 0,
        "processed_files": 0,
        "current_file": "",
        "total_customers": 0,
        "processed_customers": 0,
        "current_customer": "",
        "db_hits": 0,
        "geoapify_calls": 0,
        "errors": 0,
        "status": "starting"
    }
    
    try:
        # 1. Finde tourplaene Verzeichnis
        tourplaene_dir = Path("./tourplaene")
        if not tourplaene_dir.exists():
            # Fallback: Versuche verschiedene Verzeichnisse
            possible_dirs = [Path("./Tourplaene"), Path("./data/tourplaene"), Path("tourplaene")]
            for dir_path in possible_dirs:
                if dir_path.exists():
                    tourplaene_dir = dir_path
                    break
            else:
                raise HTTPException(404, detail="Tourplaene-Verzeichnis nicht gefunden")
        
        # 2. Finde alle CSV-Dateien
        csv_files = list(tourplaene_dir.glob("*.csv"))
        if not csv_files:
            raise HTTPException(404, detail="Keine CSV-Dateien im tourplaene Verzeichnis gefunden")
        
        # Sortiere nach Name
        csv_files.sort(key=lambda x: x.name)
        
        _bulk_progress[session_id]["total_files"] = len(csv_files)
        _bulk_progress[session_id]["status"] = "processing"
        
        # 3. Statistiken
        stats = {
            "files_processed": 0,
            "total_customers": 0,
            "unique_addresses": set(),  # Für eindeutige Adressen
            "initially_cached": 0,  # Bereits in DB
            "newly_geocoded": 0,  # Neu geocodiert
            "errors": [],
            "file_stats": []  # Statistiken pro Datei
        }
        
        # 4. Verarbeite jede CSV-Datei
        for file_idx, csv_file in enumerate(csv_files):
            file_stats = {
                "file": csv_file.name,
                "customers_total": 0,
                "db_hits": 0,
                "geoapify_calls": 0,
                "errors": 0
            }
            
            _bulk_progress[session_id]["processed_files"] = file_idx
            _bulk_progress[session_id]["current_file"] = csv_file.name
            
            try:
                # Parse CSV-Datei
                tour_data = parse_tour_plan_to_dict(str(csv_file))
                customers = tour_data.get("customers", [])
                
                if not customers:
                    # Verwende Standard-Logging (enhanced_logger könnte zu viel sein für Bulk-Processing)
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"[BULK] Keine Kunden in {csv_file.name}")
                    continue
                
                stats["total_customers"] += len(customers)
                file_stats["customers_total"] = len(customers)
                
                # Zähle Kunden für Progress
                total_customers_in_file = len(customers)
                _bulk_progress[session_id]["total_customers"] += total_customers_in_file
                
                # 5. Verarbeite jeden Kunden (DB-First)
                for customer_idx, customer in enumerate(customers):
                    processed_count = _bulk_progress[session_id]["processed_customers"]
                    _bulk_progress[session_id]["processed_customers"] = processed_count + 1
                    _bulk_progress[session_id]["current_customer"] = f"{customer.get('name', 'Unbekannt')} ({processed_count + 1}/{_bulk_progress[session_id]['total_customers']})"
                    
                    # Baue Adresse
                    address = customer.get('address') or ", ".join(filter(None, [
                        customer.get('street', '').strip(),
                        f"{customer.get('postal_code', '')} {customer.get('city', '')}".strip()
                    ]))
                    
                    if not address:
                        file_stats["errors"] += 1
                        stats["errors"].append(f"{csv_file.name}: Keine Adresse für {customer.get('name', 'Unbekannt')}")
                        continue
                    
                    # Normalisiere Adresse für DB-Lookup
                    addr_norm = normalize_address(address)
                    stats["unique_addresses"].add(addr_norm)
                    
                    # DB-First: Prüfe geo_cache
                    geo_result = geo_get(addr_norm)
                    
                    if geo_result:
                        # Bereits in DB → Überspringen
                        stats["initially_cached"] += 1
                        file_stats["db_hits"] += 1
                        _bulk_progress[session_id]["db_hits"] += 1
                        print(f"[BULK] DB-Hit: {address[:50]}...")
                    else:
                        # Nicht in DB → Geocode mit Geoapify
                        _bulk_progress[session_id]["current_customer"] = f"Geoapify: {customer.get('name', 'Unbekannt')} ({processed_count + 1}/{_bulk_progress[session_id]['total_customers']})"
                        print(f"[BULK] DB-Miss: {address[:50]}..., rufe Geoapify auf...")
                        
                        try:
                            geo_result = geocode_address(address)
                            _bulk_progress[session_id]["geoapify_calls"] += 1
                            file_stats["geoapify_calls"] += 1
                            
                            if geo_result and geo_result.get('lat') and geo_result.get('lon'):
                                # Geoapify erfolgreich → Speichere in DB
                                lat = float(geo_result['lat'])
                                lon = float(geo_result['lon'])
                                
                                geo_upsert(
                                    address=addr_norm,
                                    lat=lat,
                                    lon=lon,
                                    source="geoapify",
                                    company_name=customer.get('name')
                                )
                                
                                stats["newly_geocoded"] += 1
                                print(f"[BULK] OK Geoapify + DB-Save: {address[:50]}... -> ({lat}, {lon})")
                                
                                # Rate Limiting: 200ms zwischen Geoapify-Calls
                                await asyncio.sleep(0.2)
                            else:
                                # Geoapify fehlgeschlagen
                                file_stats["errors"] += 1
                                stats["errors"].append(f"{csv_file.name}: Geocoding fehlgeschlagen für {address[:50]}...")
                                _bulk_progress[session_id]["errors"] += 1
                        except Exception as geo_error:
                            file_stats["errors"] += 1
                            stats["errors"].append(f"{csv_file.name}: Geocoding-Fehler für {address[:50]}...: {str(geo_error)}")
                            _bulk_progress[session_id]["errors"] += 1
                            print(f"[BULK] ERROR Geocoding: {geo_error}")
                
                # Datei-Statistik speichern
                stats["file_stats"].append(file_stats)
                stats["files_processed"] += 1
                
            except Exception as file_error:
                print(f"[BULK] ERROR bei {csv_file.name}: {file_error}")
                stats["errors"].append(f"{csv_file.name}: Parse-Fehler: {str(file_error)}")
                file_stats["errors"] += 1
                stats["file_stats"].append(file_stats)
        
        # 6. Finale Statistiken
        unique_addresses_count = len(stats["unique_addresses"])
        success_rate = 0.0
        if stats["total_customers"] > 0:
            success_rate = ((stats["initially_cached"] + stats["newly_geocoded"]) / stats["total_customers"]) * 100
        
        _bulk_progress[session_id]["status"] = "completed"
        _bulk_progress[session_id]["current_file"] = "Abgeschlossen"
        _bulk_progress[session_id]["current_customer"] = f"Fertig! {stats['initially_cached']} DB, {stats['newly_geocoded']} neu geocodiert"
        
        return JSONResponse({
            "success": True,
            "session_id": session_id,
            "files_processed": stats["files_processed"],
            "total_customers": stats["total_customers"],
            "unique_addresses": unique_addresses_count,
            "initially_cached": stats["initially_cached"],
            "newly_geocoded": stats["newly_geocoded"],
            "db_hits": _bulk_progress[session_id]["db_hits"],
            "geoapify_calls": _bulk_progress[session_id]["geoapify_calls"],
            "errors_count": len(stats["errors"]),
            "errors": stats["errors"][:50],  # Max. 50 Fehler
            "success_rate": round(success_rate, 2),
            "file_stats": stats["file_stats"]
        }, media_type="application/json; charset=utf-8")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"[BULK ERROR] {e}")
        import traceback
        error_trace = traceback.format_exc()
        print(f"[BULK ERROR TRACE] {error_trace}")
        _bulk_progress[session_id]["status"] = "error"
        _bulk_progress[session_id]["current_file"] = f"Fehler: {str(e)}"
        # Return error details instead of raising (für besseres Frontend-Feedback)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "error_detail": error_trace.split('\n')[-5:],  # Letzte 5 Zeilen
            "session_id": session_id
        }, status_code=500, media_type="application/json; charset=utf-8")
