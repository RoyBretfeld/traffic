#!/usr/bin/env python3
"""
DB-Verwaltungs-API für den Admin-Bereich
Ermöglicht Batch-Geocoding und DB-Statistiken
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
from typing import List, Dict, Any
import pandas as pd
import sqlite3
import logging
from pydantic import BaseModel

from backend.services.geocode import geocode_address
from repositories.geo_repo import upsert as geo_upsert
from backend.utils.safe_print import safe_print

router = APIRouter()
logger = logging.getLogger(__name__)

# Tourenpläne-Verzeichnis
TOURPLAENE_DIR = Path("Tourplaene")
TOURPLAENE_DIR.mkdir(exist_ok=True)


class GeocodeFileRequest(BaseModel):
    filename: str


@router.post("/api/tourplan/batch-geocode")
async def batch_geocode_tourplan(file: UploadFile = File(...)):
    """
    Lädt einen Tourplan hoch, geocodiert alle Adressen und speichert sie in die DB.
    """
    safe_print(f"[DB-API] Batch-Geocode Upload: {file.filename}")
    
    try:
        # Speichere Datei
        file_path = TOURPLAENE_DIR / file.filename
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Lese CSV
        df = pd.read_csv(file_path, sep=';', encoding='cp850', on_bad_lines='skip')
        
        # Prüfe Spalten
        required_cols = ['Name', 'Straße', 'PLZ', 'Ort']
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            return JSONResponse({
                "success": False,
                "error": f"Fehlende Spalten: {', '.join(missing_cols)}",
                "total_customers": 0,
                "geocoded_count": 0,
                "skipped_count": 0,
                "error_count": 0
            }, status_code=400)
        
        # Statistiken
        stats = {
            "total_customers": len(df),
            "geocoded_count": 0,
            "skipped_count": 0,
            "error_count": 0
        }
        
        # Geocodiere jede Adresse
        for idx, row in df.iterrows():
            try:
                name = str(row.get('Name', '')).strip()
                street = str(row.get('Straße', '')).strip()
                plz = str(row.get('PLZ', '')).strip()
                ort = str(row.get('Ort', '')).strip()
                
                if not all([name, street, plz, ort]):
                    stats["skipped_count"] += 1
                    continue
                
                # Prüfe ob bereits gecoded
                address = f"{street}, {plz} {ort}"
                
                # Versuche Geocodierung
                result = geocode_address(address)
                
                if result and result.get('lat') and result.get('lon'):
                    # Speichere in DB
                    geo_upsert(address, result['lat'], result['lon'])
                    stats["geocoded_count"] += 1
                    safe_print(f"[DB-API] Geocoded: {name} @ {address} -> ({result['lat']}, {result['lon']})")
                else:
                    stats["error_count"] += 1
                    safe_print(f"[DB-API] Geocoding fehlgeschlagen: {address}")
                    
            except Exception as e:
                stats["error_count"] += 1
                safe_print(f"[DB-API] Fehler bei Zeile {idx}: {e}")
        
        safe_print(f"[DB-API] Batch-Geocode abgeschlossen: {stats}")
        
        return JSONResponse({
            "success": True,
            **stats
        })
        
    except Exception as e:
        logger.error(f"Fehler bei Batch-Geocoding: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "total_customers": 0,
            "geocoded_count": 0,
            "skipped_count": 0,
            "error_count": 0
        }, status_code=500)


@router.get("/api/tourplan/list")
async def list_tourplans():
    """
    Gibt eine Liste aller verfügbaren Tourenpläne zurück.
    """
    try:
        tourplans = []
        
        for file_path in TOURPLAENE_DIR.glob("*.csv"):
            try:
                # Lese CSV
                df = pd.read_csv(file_path, sep=';', encoding='cp850', on_bad_lines='skip')
                
                # Zähle Kunden
                customer_count = len(df)
                
                # Zähle geocodierte Kunden (grobe Schätzung)
                geocoded_count = 0
                if 'Latitude' in df.columns and 'Longitude' in df.columns:
                    geocoded_count = df[['Latitude', 'Longitude']].notna().all(axis=1).sum()
                
                geocode_rate = round((geocoded_count / customer_count * 100) if customer_count > 0 else 0, 1)
                
                tourplans.append({
                    "filename": file_path.name,
                    "customer_count": customer_count,
                    "geocoded_count": geocoded_count,
                    "geocode_rate": geocode_rate
                })
                
            except Exception as e:
                safe_print(f"[DB-API] Fehler beim Lesen von {file_path.name}: {e}")
        
        return JSONResponse({
            "success": True,
            "tourplans": sorted(tourplans, key=lambda x: x['filename'])
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Tourenpläne: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "tourplans": []
        }, status_code=500)


@router.post("/api/tourplan/geocode-file")
async def geocode_single_file(request: GeocodeFileRequest):
    """
    Geocodiert einen einzelnen Tourplan (aus dem Tourplaene-Verzeichnis).
    """
    filename = request.filename
    file_path = TOURPLAENE_DIR / filename
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail=f"Tourplan nicht gefunden: {filename}")
    
    safe_print(f"[DB-API] Geocode File: {filename}")
    
    try:
        # Lese CSV
        df = pd.read_csv(file_path, sep=';', encoding='cp850', on_bad_lines='skip')
        
        # Statistiken
        stats = {
            "total_customers": len(df),
            "geocoded_count": 0,
            "skipped_count": 0,
            "error_count": 0
        }
        
        # Geocodiere jede Adresse
        for idx, row in df.iterrows():
            try:
                name = str(row.get('Name', '')).strip()
                street = str(row.get('Straße', '')).strip()
                plz = str(row.get('PLZ', '')).strip()
                ort = str(row.get('Ort', '')).strip()
                
                if not all([name, street, plz, ort]):
                    stats["skipped_count"] += 1
                    continue
                
                # Adresse
                address = f"{street}, {plz} {ort}"
                
                # Versuche Geocodierung
                result = geocode_address(address)
                
                if result and result.get('lat') and result.get('lon'):
                    # Speichere in DB
                    geo_upsert(address, result['lat'], result['lon'])
                    stats["geocoded_count"] += 1
                else:
                    stats["error_count"] += 1
                    
            except Exception as e:
                stats["error_count"] += 1
                safe_print(f"[DB-API] Fehler bei Zeile {idx}: {e}")
        
        safe_print(f"[DB-API] Geocode File abgeschlossen: {stats}")
        
        return JSONResponse({
            "success": True,
            **stats
        })
        
    except Exception as e:
        logger.error(f"Fehler bei File-Geocoding: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/db/stats")
async def get_db_stats():
    """
    Gibt DB-Statistiken zurück (Geocodes aus geo_cache).
    """
    try:
        from sqlalchemy import text
        from db.core import ENGINE
        
        stats = {
            "total_customers": 0,
            "geocoded_customers": 0,
            "missing_geocodes": 0,
            "geocode_rate": 0
        }
        
        try:
            with ENGINE.connect() as conn:
                # Zähle Einträge in geo_cache (gecachte Geocodes)
                result = conn.execute(text("SELECT COUNT(*) FROM geo_cache"))
                stats["geocoded_customers"] = result.scalar() or 0
                
                # Zähle fehlgeschlagene Geocodes in geo_fail
                try:
                    result = conn.execute(text("SELECT COUNT(*) FROM geo_fail"))
                    failed_count = result.scalar() or 0
                except Exception:
                    failed_count = 0
                
                # Total = Erfolgreiche + Fehlgeschlagene
                stats["total_customers"] = stats["geocoded_customers"] + failed_count
                stats["missing_geocodes"] = failed_count
                
                # Berechne Rate
                if stats["total_customers"] > 0:
                    stats["geocode_rate"] = round((stats["geocoded_customers"] / stats["total_customers"]) * 100, 1)
                
        except Exception as db_error:
            safe_print(f"[DB-API] DB-Fehler: {db_error}")
            # Versuche alternatives Schema (traffic.db customers)
            try:
                import sqlite3
                db_path = Path("traffic.db")
                if db_path.exists():
                    conn_sqlite = sqlite3.connect(db_path)
                    cursor = conn_sqlite.cursor()
                    
                    # Zähle Kunden in traffic.db
                    cursor.execute("SELECT COUNT(*) FROM customers")
                    stats["total_customers"] = cursor.fetchone()[0]
                    
                    # Zähle mit Koordinaten
                    cursor.execute("SELECT COUNT(*) FROM customers WHERE latitude IS NOT NULL AND longitude IS NOT NULL")
                    stats["geocoded_customers"] = cursor.fetchone()[0]
                    
                    stats["missing_geocodes"] = stats["total_customers"] - stats["geocoded_customers"]
                    
                    if stats["total_customers"] > 0:
                        stats["geocode_rate"] = round((stats["geocoded_customers"] / stats["total_customers"]) * 100, 1)
                    
                    conn_sqlite.close()
            except Exception as fallback_error:
                safe_print(f"[DB-API] Fallback-Fehler: {fallback_error}")
        
        return JSONResponse({
            "success": True,
            **stats
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der DB-Statistiken: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "total_customers": 0,
            "geocoded_customers": 0,
            "missing_geocodes": 0,
            "geocode_rate": 0
        }, status_code=500)

