"""
API-Endpunkte für Datenbank-Backup
"""

from fastapi import APIRouter, HTTPException, Query, Depends
from fastapi.responses import JSONResponse
from pathlib import Path
from datetime import datetime
import sys
from backend.routes.auth_api import require_admin

# Projekt-Root finden
PROJECT_ROOT = Path(__file__).resolve().parent.parent

router = APIRouter(dependencies=[Depends(require_admin)])


@router.post("/api/backup/create")
async def api_create_backup():
    """
    Erstellt manuell ein Backup der Datenbank.
    """
    try:
        # Rufe Backup-Script auf
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from scripts.db_backup import create_backup
        
        success, message = create_backup()
        
        if success:
            return JSONResponse({
                "success": True,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }, media_type="application/json; charset=utf-8")
        else:
            raise HTTPException(500, detail=message)
    
    except Exception as e:
        raise HTTPException(500, detail=f"Backup-Fehler: {str(e)}")


@router.get("/api/backup/list")
async def api_list_backups():
    """
    Listet alle verfügbaren Backups auf.
    """
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from scripts.db_backup import list_backups
        
        backups = list_backups()
        
        return JSONResponse({
            "success": True,
            "backups": backups,
            "count": len(backups)
        }, media_type="application/json; charset=utf-8")
    
    except Exception as e:
        raise HTTPException(500, detail=f"Fehler beim Auflisten: {str(e)}")


@router.post("/api/backup/restore")
async def api_restore_backup(backup_filename: str = Query(..., description="Name der Backup-Datei")):
    """
    Stellt ein Backup wieder her.
    
    Args:
        backup_filename: Name der Backup-Datei (z.B. traffic_backup_20250115_160000.db)
    """
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from scripts.db_backup import restore_backup
        
        success, message = restore_backup(backup_filename)
        
        if success:
            return JSONResponse({
                "success": True,
                "message": message,
                "restored_file": backup_filename,
                "timestamp": datetime.now().isoformat()
            }, media_type="application/json; charset=utf-8")
        else:
            raise HTTPException(400, detail=message)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(500, detail=f"Wiederherstellungs-Fehler: {str(e)}")


@router.post("/api/backup/cleanup")
async def api_cleanup_backups():
    """
    Bereinigt alte Backups (älter als 30 Tage).
    """
    try:
        import sys
        sys.path.insert(0, str(PROJECT_ROOT))
        from scripts.db_backup import cleanup_old_backups
        
        cleanup_old_backups()
        
        return JSONResponse({
            "success": True,
            "message": "Bereinigung abgeschlossen",
            "timestamp": datetime.now().isoformat()
        }, media_type="application/json; charset=utf-8")
    
    except Exception as e:
        raise HTTPException(500, detail=f"Bereinigungs-Fehler: {str(e)}")

