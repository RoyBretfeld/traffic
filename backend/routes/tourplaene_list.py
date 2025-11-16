from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pathlib import Path
import os
from backend.utils.enhanced_logging import get_enhanced_logger

# Enhanced Logger initialisieren
enhanced_logger = get_enhanced_logger(__name__)

router = APIRouter()

@router.get("/api/tourplaene/list")
async def api_tourplaene_list():
    """
    Listet alle verfügbaren Tourplan-CSV-Dateien auf.
    
    Returns:
        JSON mit Liste der CSV-Dateien und deren Metadaten
    """
    try:
        # Tourplaene-Verzeichnis finden
        tourplaene_dir = Path("./tourplaene")
        if not tourplaene_dir.exists():
            # Fallback: Suche nach anderen möglichen Verzeichnissen
            possible_dirs = ["./Tourplaene", "./data/tourplaene", "./tourplaene"]
            for dir_path in possible_dirs:
                if Path(dir_path).exists():
                    tourplaene_dir = Path(dir_path)
                    break
            else:
                raise HTTPException(404, detail="Tourplaene-Verzeichnis nicht gefunden")
        
        # CSV-Dateien auflisten
        csv_files = []
        for csv_file in tourplaene_dir.glob("*.csv"):
            try:
                stat = csv_file.stat()
                csv_files.append({
                    "name": csv_file.name,
                    "path": str(csv_file),
                    "size": stat.st_size,
                    "modified": stat.st_mtime
                })
            except Exception as e:
                enhanced_logger.warning(f"Fehler beim Lesen von {csv_file}: {e}")
                continue
        
        # Nach Name sortieren
        csv_files.sort(key=lambda x: x["name"])
        
        return JSONResponse({
            "success": True,
            "files": csv_files,
            "count": len(csv_files)
        }, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Auflisten der Dateien: {str(e)}")
