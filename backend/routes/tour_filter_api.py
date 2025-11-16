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

