"""
API für Tour-Filter-Verwaltung (Ignore/Allow-Listen)
Ermöglicht CRUD-Operationen auf config/tour_ignore_list.json
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import json
import logging
from datetime import datetime

router = APIRouter()
logger = logging.getLogger(__name__)


class TourFilterUpdate(BaseModel):
    """Request-Model für Tour-Filter-Update"""
    ignore_tours: List[str]
    allow_tours: List[str]
    description: Optional[str] = None
    allow_description: Optional[str] = None
    reason: Optional[str] = None
    allow_reason: Optional[str] = None


def get_filter_file_path() -> Path:
    """Gibt den Pfad zur Tour-Filter-Datei zurück."""
    project_root = Path(__file__).parent.parent.parent
    return project_root / "config" / "tour_ignore_list.json"


def load_filter_data() -> dict:
    """Lädt die Tour-Filter-Datei."""
    filter_file = get_filter_file_path()
    
    if not filter_file.exists():
        # Erstelle Standard-Struktur
        default_data = {
            "ignore_tours": ["DBD", "DPD", "DVD"],
            "allow_tours": [],
            "description": "Touren die nicht in die Routenplanung einbezogen werden sollen",
            "allow_description": "Touren die VERARBEITET werden sollen (wenn Liste vorhanden, werden NUR diese Touren verarbeitet)",
            "reason": "Pickup/Nachtlieferung - werden separat gehandhabt",
            "allow_reason": "Alle Touren werden verarbeitet",
            "last_updated": datetime.now().strftime("%Y-%m-%d"),
            "usage": {
                "ignore_tours": "Touren mit diesen Patterns werden übersprungen",
                "allow_tours": "Wenn diese Liste vorhanden ist und nicht leer, werden NUR Touren verarbeitet die hier stehen. Ignore-Liste hat Vorrang."
            }
        }
        return default_data
    
    try:
        with open(filter_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Fehler beim Laden der Tour-Filter-Datei: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Filter-Datei: {e}")


def save_filter_data(data: dict) -> None:
    """Speichert die Tour-Filter-Datei."""
    filter_file = get_filter_file_path()
    
    # Erstelle config-Verzeichnis falls nicht vorhanden
    filter_file.parent.mkdir(parents=True, exist_ok=True)
    
    # Aktualisiere last_updated
    data["last_updated"] = datetime.now().strftime("%Y-%m-%d")
    
    try:
        with open(filter_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Tour-Filter-Datei gespeichert: {filter_file}")
    except Exception as e:
        logger.error(f"Fehler beim Speichern der Tour-Filter-Datei: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Filter-Datei: {e}")


@router.get("/api/tour-filter")
async def get_tour_filters():
    """
    Gibt die aktuellen Tour-Filter (Ignore/Allow-Listen) zurück.
    """
    try:
        data = load_filter_data()
        return JSONResponse({
            "success": True,
            "ignore_tours": data.get("ignore_tours", []),
            "allow_tours": data.get("allow_tours", []),
            "description": data.get("description", ""),
            "allow_description": data.get("allow_description", ""),
            "reason": data.get("reason", ""),
            "allow_reason": data.get("allow_reason", ""),
            "last_updated": data.get("last_updated", ""),
            "usage": data.get("usage", {})
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tour-Filter: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Filter: {e}")


@router.get("/api/tour-filter/allowed")
async def get_allowed_tours():
    """
    Gibt alle erlaubten Touren zurück (alle, die nicht in der Ignore-Liste stehen).
    Holt Touren aus der Datenbank.
    """
    try:
        from db.core import ENGINE
        from sqlalchemy import text
        
        # Lade Ignore-Liste
        filter_data = load_filter_data()
        ignore_patterns = filter_data.get("ignore_tours", [])
        
        # Hole alle Touren aus der DB
        allowed_tours = []
        try:
            with ENGINE.connect() as conn:
                # Prüfe ob touren-Tabelle existiert
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='touren'
                """))
                if not result.fetchone():
                    # Keine Touren-Tabelle vorhanden
                    return JSONResponse({
                        "success": True,
                        "allowed_tours": [],
                        "message": "Keine Touren-Tabelle in der Datenbank gefunden"
                    })
                
                # Hole alle Tour-IDs (NICHT DISTINCT, da wir Duplikate zusammenführen wollen)
                result = conn.execute(text("""
                    SELECT tour_id, kunden_ids
                    FROM touren 
                    WHERE tour_id IS NOT NULL AND tour_id != ''
                    ORDER BY tour_id
                """))
                
                all_tours = []
                for row in result.fetchall():
                    tour_id = row[0]
                    kunden_ids_str = row[1] or '[]'
                    
                    # Zähle Stops (kunden_ids ist JSON-Array)
                    import json
                    try:
                        kunden_ids = json.loads(kunden_ids_str) if kunden_ids_str else []
                        stop_count = len(kunden_ids) if isinstance(kunden_ids, list) else 0
                    except (json.JSONDecodeError, TypeError):
                        # Fallback: Zähle Kommas
                        stop_count = kunden_ids_str.count(',') + 1 if kunden_ids_str and kunden_ids_str != '[]' else 0
                    
                    all_tours.append({
                        'tour_id': tour_id,
                        'stop_count': stop_count
                    })
                
                # Normalisiere Tour-IDs (entferne "Uhr Tour", "Uhr BAR", "Uhr", etc. für Gruppierung)
                import re
                def normalize_tour_id(tour_id: str) -> str:
                    """Normalisiert Tour-ID für Duplikat-Erkennung"""
                    # Entferne "Uhr Tour", "Uhr BAR", "Tour", "BAR", "Uhr" am Ende
                    # Reihenfolge wichtig: zuerst "Uhr Tour", dann "Uhr", dann "Tour"
                    normalized = tour_id
                    normalized = re.sub(r'\s*Uhr\s*(Tour|BAR)$', '', normalized, flags=re.IGNORECASE).strip()
                    normalized = re.sub(r'\s*Uhr$', '', normalized, flags=re.IGNORECASE).strip()
                    normalized = re.sub(r'\s*(Tour|BAR)$', '', normalized, flags=re.IGNORECASE).strip()
                    # Entferne führende/abschließende Leerzeichen
                    return normalized.strip()
                
                # Sammle Touren mit normalisierten IDs (für Duplikat-Erkennung)
                tour_map = {}  # normalized_id -> tour_id (bevorzuge kürzere Version)
                
                # Importiere Filter-Logik aus workflow_api
                from backend.routes.workflow_api import should_process_tour_admin
                
                # Filtere gegen Ignore-Liste und ungültige Touren
                for tour_info in all_tours:
                    tour_id = tour_info['tour_id']
                    stop_count = tour_info['stop_count']
                    
                    # Ignoriere "Unknown" und Touren ohne Stops
                    if tour_id.upper() == 'UNKNOWN' or stop_count == 0:
                        continue
                    
                    # Verwende die gleiche Filter-Logik wie im Workflow (Admin-Kontext)
                    # should_process_tour_admin prüft Ignore-Liste und Allow-Liste korrekt
                    allow_list = filter_data.get("allow_tours", [])
                    if should_process_tour_admin(tour_id, ignore_patterns, allow_list):
                        # Normalisiere für Duplikat-Erkennung
                        normalized = normalize_tour_id(tour_id)
                        
                        # Wenn bereits vorhanden, behalte bessere Version
                        if normalized in tour_map:
                            existing = tour_map[normalized]
                            # Finde bestehende Tour-Info
                            existing_info = next((t for t in all_tours if t['tour_id'] == existing), None)
                            existing_stops = existing_info['stop_count'] if existing_info else 0
                            
                            # Entscheidung: Bevorzuge Version mit mehr Stops, bei Gleichstand kürzere ID
                            should_replace = False
                            if stop_count > existing_stops:
                                should_replace = True
                            elif stop_count == existing_stops:
                                # Gleiche Anzahl Stops: Bevorzuge kürzere Tour-ID
                                if len(tour_id) < len(existing):
                                    should_replace = True
                                elif len(tour_id) == len(existing) and tour_id < existing:
                                    should_replace = True
                            
                            if should_replace:
                                tour_map[normalized] = tour_id
                                logger.debug(f"[TOUR-FILTER] Ersetze '{existing}' durch '{tour_id}' (normalisiert: {normalized})")
                        else:
                            tour_map[normalized] = tour_id
                
                # Debug: Logge Duplikate
                logger.debug(f"[TOUR-FILTER] Normalisierte Touren: {len(tour_map)} eindeutige, {len(all_tours)} total")
                
                # Konvertiere Map zu Liste (sortiert)
                allowed_tours = sorted(tour_map.values())
                
                # Finale Duplikat-Prüfung: Entferne Duplikate basierend auf normalisierten IDs
                final_allowed = []
                seen_normalized = set()
                for tid in allowed_tours:
                    normalized = normalize_tour_id(tid)
                    if normalized not in seen_normalized:
                        final_allowed.append(tid)
                        seen_normalized.add(normalized)
                    else:
                        logger.debug(f"[TOUR-FILTER] Entferne Duplikat: {tid} (normalisiert: {normalized})")
                
                allowed_tours = sorted(final_allowed)
        
        except Exception as db_error:
            logger.warning(f"Fehler beim Abrufen der Touren aus DB: {db_error}")
            # Fallback: Leere Liste
            allowed_tours = []
        
        return JSONResponse({
            "success": True,
            "allowed_tours": allowed_tours,
            "total_count": len(allowed_tours),
            "ignore_patterns": ignore_patterns
        })
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der erlaubten Touren: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der erlaubten Touren: {e}")


@router.put("/api/tour-filter")
async def update_tour_filters(update: TourFilterUpdate):
    """
    Aktualisiert die Tour-Filter (Ignore/Allow-Listen).
    """
    try:
        # Lade aktuelle Daten
        data = load_filter_data()
        
        # Aktualisiere Listen
        data["ignore_tours"] = update.ignore_tours
        data["allow_tours"] = update.allow_tours
        
        # Aktualisiere optionale Felder
        if update.description is not None:
            data["description"] = update.description
        if update.allow_description is not None:
            data["allow_description"] = update.allow_description
        if update.reason is not None:
            data["reason"] = update.reason
        if update.allow_reason is not None:
            data["allow_reason"] = update.allow_reason
        
        # Speichere
        save_filter_data(data)
        
        return JSONResponse({
            "success": True,
            "message": "Tour-Filter erfolgreich aktualisiert",
            "ignore_tours": data["ignore_tours"],
            "allow_tours": data["allow_tours"],
            "last_updated": data["last_updated"]
        })
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren der Tour-Filter: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Fehler beim Aktualisieren der Filter: {e}")

