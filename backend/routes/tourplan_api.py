"""
API-Endpunkte für Tourplan-Übersicht
Zeigt Gesamtdaten von Tourplänen (gruppiert nach Datum)
Kombiniert Daten aus DB und tourplaene Verzeichnis
"""
from fastapi import APIRouter, HTTPException, Query, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy import text
from db.core import ENGINE
import json
import logging
import os
import re
from backend.routes.auth_api import require_admin

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/tourplan", tags=["tourplan"])

# Tourplaene-Verzeichnis
TOURPLAENE_DIR = Path(os.getenv("ORIG_DIR", "./tourplaene")).resolve()
if not TOURPLAENE_DIR.exists():
    # Fallback-Verzeichnisse
    possible_dirs = [Path("./Tourplaene"), Path("./data/tourplaene"), Path("./tourplaene")]
    for dir_path in possible_dirs:
        if dir_path.exists():
            TOURPLAENE_DIR = dir_path.resolve()
            break


@router.get("/list")
async def list_tourplans():
    """
    Listet alle verfügbaren Tourpläne auf.
    Kombiniert:
    1. CSV-Dateien aus tourplaene Verzeichnis (mit Dateinamen)
    2. Daten aus DB (gruppiert nach Datum)
    """
    try:
        tourplans = []
        
        # 1. CSV-Dateien aus tourplaene Verzeichnis
        csv_files = {}
        if TOURPLAENE_DIR.exists():
            for csv_file in TOURPLAENE_DIR.glob("*.csv"):
                try:
                    # Versuche Datum aus Dateinamen zu extrahieren
                    filename = csv_file.name
                    # Dateinamen-Format: z.B. "Tourenplan 18.08.2025.csv" oder "2025-08-18.csv"
                    date_match = re.search(r'(\d{2})\.(\d{2})\.(\d{2,4})', filename)
                    if date_match:
                        day, month, year = date_match.groups()
                        if len(year) == 2:
                            year = "20" + year
                        datum = f"{year}-{month}-{day}"
                    else:
                        # Fallback: Verwende Datei-Modifikationsdatum
                        stat = csv_file.stat()
                        mod_date = datetime.fromtimestamp(stat.st_mtime)
                        datum = mod_date.strftime("%Y-%m-%d")
                    
                    csv_files[datum] = {
                        "filename": filename,
                        "file_path": str(csv_file),
                        "size": stat.st_size if 'stat' in locals() else csv_file.stat().st_size,
                        "modified": stat.st_mtime if 'stat' in locals() else csv_file.stat().st_mtime
                    }
                except Exception as e:
                    logger.warning(f"Fehler beim Lesen von {csv_file.name}: {e}")
                    continue
        
        # 2. Daten aus DB (gruppiert nach Datum)
        db_tourplans = {}
        try:
            with ENGINE.begin() as conn:
                # Prüfe ob gesamtzeit_min Spalte existiert (wie in /overview und /tours)
                column_check = conn.execute(text("PRAGMA table_info(touren)")).fetchall()
                has_gesamtzeit_min = any(col[1] == 'gesamtzeit_min' for col in column_check)
                has_dauer_min = any(col[1] == 'dauer_min' for col in column_check)
                
                # Verwende gesamtzeit_min falls vorhanden, sonst dauer_min
                time_column = "gesamtzeit_min" if has_gesamtzeit_min else ("dauer_min" if has_dauer_min else "NULL")
                
                result = conn.execute(text(f"""
                    SELECT 
                        datum,
                        COUNT(*) as tour_count,
                        SUM(
                            CASE 
                                WHEN kunden_ids IS NOT NULL AND kunden_ids != '' 
                                THEN (LENGTH(kunden_ids) - LENGTH(REPLACE(kunden_ids, ',', '')) + 1)
                                ELSE 0
                            END
                        ) as total_stops,
                        COALESCE(SUM(distanz_km), 0.0) as total_km,
                        COALESCE(SUM({time_column}), 0.0) as total_time_min
                    FROM touren
                    GROUP BY datum
                    ORDER BY datum DESC
                    LIMIT 100
                """))
                
                for row in result:
                    datum, tour_count, total_stops, total_km, total_time_min = row
                    db_tourplans[datum] = {
                        "tour_count": tour_count,
                        "total_stops": total_stops or 0,
                        "total_km": round(float(total_km or 0), 2),
                        "total_time_min": int(total_time_min or 0)
                    }
        except Exception as e:
            logger.warning(f"Fehler beim Lesen aus DB: {e}")
        
        # 3. Kombiniere beide Quellen
        all_dates = set(list(csv_files.keys()) + list(db_tourplans.keys()))
        
        for datum in sorted(all_dates, reverse=True):
            csv_info = csv_files.get(datum, {})
            db_info = db_tourplans.get(datum, {})
            
            tourplans.append({
                "datum": datum,
                "filename": csv_info.get("filename"),
                "file_path": csv_info.get("file_path"),
                "file_size": csv_info.get("size"),
                "file_modified": csv_info.get("modified"),
                "tour_count": db_info.get("tour_count", 0),
                "total_stops": db_info.get("total_stops", 0),
                "total_km": db_info.get("total_km", 0.0),
                "total_time_min": db_info.get("total_time_min", 0),
                "has_file": datum in csv_files,
                "has_db_data": datum in db_tourplans
            })
        
        return JSONResponse({
            "success": True,
            "tourplans": tourplans,
            "tourplaene_dir": str(TOURPLAENE_DIR),
            "tourplaene_dir_exists": TOURPLAENE_DIR.exists()
        })
    except Exception as e:
        logger.error(f"Fehler beim Auflisten der Tourpläne: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "tourplans": []
        }, status_code=500)


@router.get("/overview")
async def get_tourplan_overview(
    datum: str = Query(..., description="Tourplan-Datum (YYYY-MM-DD)"),
    include_all: bool = Query(True, description="Alle Touren einbeziehen (inkl. Ignor-Touren) für statistische Zwecke. Standard: True (alle Touren werden gezählt)")
):
    """
    Gibt Gesamt-KPIs für einen Tourplan zurück.
    
    Standardmäßig werden alle Touren gezählt (include_all=True).
    Dies beinhaltet auch Touren, die normalerweise in der Ignore-Liste stehen,
    da diese für statistische Zwecke (Kosten, KM, Zeit) relevant sind.
    """
    # Validiere Datum-Format
    import re
    if not datum or datum == 'undefined' or not re.match(r'^\d{4}-\d{2}-\d{2}$', datum):
        return JSONResponse({
            "success": False,
            "error": f"Ungültiges Datum-Format: {datum}. Erwartet: YYYY-MM-DD"
        }, status_code=400)
    
    try:
        with ENGINE.begin() as conn:
            # Prüfe ob gesamtzeit_min Spalte existiert
            column_check = conn.execute(text("PRAGMA table_info(touren)")).fetchall()
            has_gesamtzeit_min = any(col[1] == 'gesamtzeit_min' for col in column_check)
            has_dauer_min = any(col[1] == 'dauer_min' for col in column_check)
            
            # Verwende gesamtzeit_min falls vorhanden, sonst dauer_min
            time_column = "gesamtzeit_min" if has_gesamtzeit_min else "dauer_min"
            
            # Gesamt-KPIs für diesen Tag
            stats = conn.execute(text(f"""
                SELECT 
                    COUNT(*) as tour_count,
                    SUM(
                        CASE 
                            WHEN kunden_ids IS NOT NULL AND kunden_ids != '' 
                            THEN (LENGTH(kunden_ids) - LENGTH(REPLACE(kunden_ids, ',', '')) + 1)
                            ELSE 0
                        END
                    ) as total_stops,
                    COALESCE(SUM(distanz_km), 0.0) as total_km,
                    COALESCE(SUM({time_column}), 0.0) as total_time_min,
                    COUNT(CASE WHEN distanz_km IS NOT NULL THEN 1 END) as tours_with_distance,
                    COUNT(CASE WHEN {time_column} IS NOT NULL THEN 1 END) as tours_with_time
                FROM touren
                WHERE datum = :datum
            """), {"datum": datum}).fetchone()
            
            # Auch bei 0 Touren Daten zurückgeben (mit 0-Werten)
            if not stats:
                # Fallback: Alle Werte auf 0 setzen
                tour_count, total_stops, total_km, total_time_min, tours_with_distance, tours_with_time = 0, 0, 0.0, 0, 0, 0
            else:
                tour_count, total_stops, total_km, total_time_min, tours_with_distance, tours_with_time = stats
                # Wenn tour_count 0 ist, setze alle Werte auf 0
                if tour_count == 0:
                    total_stops, total_km, total_time_min, tours_with_distance, tours_with_time = 0, 0.0, 0, 0, 0
            
            # Berechne Kosten (falls Konfiguration vorhanden)
            from backend.services.stats_aggregator import get_cost_config, calculate_tour_cost
            
            cost_config = get_cost_config()
            total_cost = 0.0
            
            # Berechne Kosten für jede Tour mit Distanz und Zeit (nur wenn Touren vorhanden)
            if tour_count > 0:
                # Prüfe ob fahrzeug_typ Spalte existiert
                column_check = conn.execute(text("PRAGMA table_info(touren)")).fetchall()
                has_vehicle_type = any(col[1] == 'fahrzeug_typ' for col in column_check)
                vehicle_type_column = "fahrzeug_typ" if has_vehicle_type else "NULL"
                
                tour_rows = conn.execute(text(f"""
                    SELECT 
                        COALESCE(distanz_km, 0) as distanz,
                        COALESCE({time_column}, 0) as zeit,
                        CASE 
                            WHEN kunden_ids IS NOT NULL AND kunden_ids != '' 
                            THEN (LENGTH(kunden_ids) - LENGTH(REPLACE(kunden_ids, ',', '')) + 1)
                            ELSE 0
                        END as stops,
                        COALESCE({vehicle_type_column}, 'diesel') as fahrzeug_typ
                    FROM touren
                    WHERE datum = :datum
                """), {"datum": datum}).fetchall()
                
                for row in tour_rows:
                    dist, time_min, stops, vehicle_type = row[0] or 0, row[1] or 0, row[2] or 0, (row[3] or 'diesel') if len(row) > 3 else 'diesel'
                    if dist > 0 and time_min > 0 and stops > 0:
                        tour_cost = calculate_tour_cost(dist, time_min, stops, cost_config, vehicle_type=vehicle_type)
                        total_cost += tour_cost["tour_cost_total"]
                    elif dist > 0:
                        # Fallback: Schätze Zeit basierend auf Distanz
                        estimated_time = (dist / 50.0) * 60
                        estimated_stops = max(stops, 1) if stops > 0 else 1
                        tour_cost = calculate_tour_cost(dist, estimated_time, estimated_stops, cost_config, vehicle_type=vehicle_type)
                        total_cost += tour_cost["tour_cost_total"]
            
            return JSONResponse({
                "success": True,
                "datum": datum,
                "tour_count": tour_count,
                "total_stops": total_stops or 0,
                "total_km": round(float(total_km or 0), 2),
                "total_time_min": int(total_time_min or 0),
                "total_cost": round(total_cost, 2),
                "avg_km_per_tour": round(float(total_km or 0) / tour_count, 2) if tour_count > 0 else 0.0,
                "avg_stops_per_tour": round((total_stops or 0) / tour_count, 1) if tour_count > 0 else 0.0,
                "avg_time_per_tour": round((total_time_min or 0) / tour_count, 1) if tour_count > 0 else 0.0,
                "tours_with_distance": tours_with_distance or 0,
                "tours_with_time": tours_with_time or 0
            })
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tourplan-Übersicht: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)


@router.get("/tours")
async def get_tourplan_tours(
    datum: str = Query(..., description="Tourplan-Datum (YYYY-MM-DD)"),
    include_all: bool = Query(True, description="Alle Touren einbeziehen (inkl. Ignor-Touren) für statistische Zwecke. Standard: True (alle Touren werden zurückgegeben)")
):
    """
    Gibt alle Touren eines Tourplans zurück.
    
    Standardmäßig werden alle Touren zurückgegeben (include_all=True).
    Dies beinhaltet auch Touren, die normalerweise in der Ignore-Liste stehen,
    da diese für statistische Zwecke (Kosten, KM, Zeit) relevant sind.
    """
    # Validiere Datum-Format
    import re
    if not datum or datum == 'undefined' or not re.match(r'^\d{4}-\d{2}-\d{2}$', datum):
        return JSONResponse({
            "success": False,
            "error": f"Ungültiges Datum-Format: {datum}. Erwartet: YYYY-MM-DD",
            "tours": []
        }, status_code=400)
    
    try:
        with ENGINE.begin() as conn:
            # Prüfe welche Zeit-Spalte existiert
            column_check = conn.execute(text("PRAGMA table_info(touren)")).fetchall()
            has_gesamtzeit_min = any(col[1] == 'gesamtzeit_min' for col in column_check)
            time_column = "gesamtzeit_min" if has_gesamtzeit_min else "dauer_min"
            
            # Prüfe ob fahrzeug_typ Spalte existiert
            column_check = conn.execute(text("PRAGMA table_info(touren)")).fetchall()
            has_vehicle_type = any(col[1] == 'fahrzeug_typ' for col in column_check)
            vehicle_type_column = "COALESCE(fahrzeug_typ, 'diesel')" if has_vehicle_type else "'diesel'"
            
            tours = conn.execute(text(f"""
                SELECT 
                    tour_id,
                    kunden_ids,
                    dauer_min,
                    distanz_km,
                    {time_column} as gesamtzeit_min,
                    fahrer,
                    {vehicle_type_column} as fahrzeug_typ,
                    created_at
                FROM touren
                WHERE datum = :datum
                ORDER BY tour_id
            """), {"datum": datum}).fetchall()
            
            tour_list = []
            for row in tours:
                # SQL gibt immer fahrzeug_typ zurück (entweder aus Spalte oder als 'diesel' String)
                # Daher immer 8 Werte entpacken
                tour_id, kunden_ids, dauer_min, distanz_km, gesamtzeit_min, fahrer, vehicle_type, created_at = row
                
                # Falls vehicle_type None ist (sollte nicht passieren, aber sicherheitshalber)
                if not vehicle_type:
                    vehicle_type = 'diesel'
                
                # Berechne Anzahl Stops aus kunden_ids
                stops_count = 0
                if kunden_ids:
                    try:
                        ids = json.loads(kunden_ids)
                        if isinstance(ids, list):
                            stops_count = len(ids)
                    except (json.JSONDecodeError, TypeError):
                        # Fallback: Zähle Kommas
                        stops_count = kunden_ids.count(',') + 1 if kunden_ids else 0
                
                # Berechne Kosten (falls vorhanden) - mit Fahrzeugtyp
                cost = None
                if distanz_km and gesamtzeit_min and stops_count > 0:
                    from backend.services.stats_aggregator import get_cost_config, calculate_tour_cost
                    cost_config = get_cost_config()
                    cost_data = calculate_tour_cost(distanz_km, gesamtzeit_min, stops_count, cost_config, vehicle_type=vehicle_type)
                    cost = cost_data["tour_cost_total"]
                
                tour_list.append({
                    "tour_id": tour_id,
                    "stops_count": stops_count,
                    "distance_km": round(float(distanz_km or 0), 2) if distanz_km else None,
                    "time_min": int(gesamtzeit_min or dauer_min or 0) if (gesamtzeit_min or dauer_min) else None,
                    "cost": round(cost, 2) if cost else None,
                    "fahrer": fahrer,
                    "created_at": created_at,
                    "has_distance": distanz_km is not None,
                    "has_time": (gesamtzeit_min or dauer_min) is not None
                })
            
            return JSONResponse({
                "success": True,
                "datum": datum,
                "tours": tour_list,
                "count": len(tour_list)
            })
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Touren: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "tours": []
        }, status_code=500)


@router.post("/upload")
async def upload_tourplan(file: UploadFile = File(...), session: dict = Depends(require_admin)):
    """
    Lädt einen Tourplan hoch und speichert ihn im tourplaene Verzeichnis.
    """
    try:
        # SC-07: Validierung
        if not file.filename:
            raise HTTPException(400, detail="Kein Dateiname angegeben")
        
        # SC-07: Filename-Whitelist (Path Traversal verhindern)
        SAFE_FILENAME = re.compile(r"^[A-Za-z0-9_.\-]+$")
        if not SAFE_FILENAME.match(file.filename):
            raise HTTPException(400, detail="Ungültiger Dateiname. Nur A-Z, a-z, 0-9, _, ., - erlaubt")
        
        # Prüfe Dateityp
        if not file.filename.lower().endswith('.csv'):
            return JSONResponse({
                "success": False,
                "error": "Nur CSV-Dateien sind erlaubt"
            }, status_code=400)
        
        # SC-07: Größen-Limit
        MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10MB
        content_preview = await file.read(MAX_UPLOAD_BYTES + 1)
        if len(content_preview) > MAX_UPLOAD_BYTES:
            raise HTTPException(413, detail=f"Datei zu groß (max {MAX_UPLOAD_BYTES} Bytes)")
        await file.seek(0)  # Zurück zum Anfang
        
        # Stelle sicher, dass Verzeichnis existiert
        TOURPLAENE_DIR.mkdir(parents=True, exist_ok=True)
        
        # SC-07: Pfad-Check mit resolve() (Path Traversal verhindern)
        file_path = (TOURPLAENE_DIR / file.filename).resolve()
        if not str(file_path).startswith(str(TOURPLAENE_DIR.resolve())):
            raise HTTPException(400, detail="Pfad außerhalb des erlaubten Verzeichnisses")
        
        # Prüfe ob Datei bereits existiert
        if file_path.exists():
            return JSONResponse({
                "success": False,
                "error": f"Datei '{file.filename}' existiert bereits"
            }, status_code=409)
        
        # Lese Dateiinhalt
        content = await file.read()
        
        # Speichere Datei
        file_path.write_bytes(content)
        
        logger.info(f"Tourplan hochgeladen: {file.filename} ({len(content)} Bytes)")
        
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "file_path": str(file_path),
            "size": len(content),
            "message": f"Tourplan '{file.filename}' erfolgreich hochgeladen"
        })
        
    except Exception as e:
        logger.error(f"Fehler beim Hochladen des Tourplans: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e)
        }, status_code=500)

