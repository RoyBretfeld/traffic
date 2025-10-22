from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from repositories.geo_fail_repo import (
    clear, get_fail_status, get_fail_stats, get_fail_reasons, cleanup_expired
)
from common.normalize import normalize_address # Importiere normalize_address

router = APIRouter()

@router.post("/api/geocode/force-retry")
def force_retry(address: str = Query(..., description="Adresse für die ein Retry erzwungen werden soll")):
    """
    Erzwingt einen Retry für eine Adresse durch Löschen aus dem Fail-Cache.
    
    - Entfernt die Adresse aus dem Fail-Cache
    - Ermöglicht sofortigen neuen Geocoding-Versuch
    - Nützlich wenn sich die Geocoding-Situation verbessert hat
    """
    norm_addr = normalize_address(address) # Verwende normalize_address
    
    try:
        # Prüfe ob Adresse im Fail-Cache steht
        fail_status = get_fail_status(norm_addr)
        if not fail_status:
            return JSONResponse({
                "ok": True,
                "message": f"Adresse '{address}' steht nicht im Fail-Cache - Retry bereits möglich"
            })
        
        # Entferne aus Fail-Cache
        clear(norm_addr)
        
        return JSONResponse({
            "ok": True,
            "message": f"Fail-Cache für '{address}' gelöscht - Retry möglich",
            "previous_status": fail_status
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Löschen aus Fail-Cache: {str(e)}")

@router.get("/api/geocode/fail-reasons")
def fail_reasons():
    """
    Zeigt eine Gruppierung der Fail-Cache-Einträge nach Grund.
    
    - Gruppiert nach reason (no_result, temp_error, etc.)
    - Zeigt Anzahl pro Grund
    - Hilft bei der Diagnose von Geocoding-Problemen
    """
    try:
        reasons = get_fail_reasons()
        stats = get_fail_stats()
        
        return JSONResponse({
            "ok": True,
            "stats": stats,
            "reasons": reasons,
            "summary": {
                "total_active": sum(reasons.values()),
                "most_common": max(reasons.items(), key=lambda x: x[1]) if reasons else None
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Fail-Gründe: {str(e)}")

@router.get("/api/geocode/fail-status")
def fail_status(address: str = Query(..., description="Adresse deren Fail-Status geprüft werden soll")):
    """
    Prüft den Fail-Status einer spezifischen Adresse.
    
    - Zeigt ob Adresse im Fail-Cache steht
    - Gibt Grund und Ablaufzeit zurück
    - Hilft bei der Diagnose von Geocoding-Problemen
    """
    try:
        norm_addr = normalize_address(address) # Verwende normalize_address
        status = get_fail_status(norm_addr)
        
        if status:
            return JSONResponse({
                "ok": True,
                "in_fail_cache": True,
                "address": address,
                "normalized": norm_addr,
                "status": status
            })
        else:
            return JSONResponse({
                "ok": True,
                "in_fail_cache": False,
                "address": address,
                "normalized": norm_addr,
                "message": "Adresse steht nicht im Fail-Cache - Geocoding möglich"
            })
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Prüfen des Fail-Status: {str(e)}")

@router.post("/api/geocode/cleanup-fail-cache")
def cleanup_fail_cache():
    """
    Bereinigt abgelaufene Einträge aus dem Fail-Cache.
    
    - Entfernt alle Einträge deren TTL abgelaufen ist
    - Verbessert Performance durch Reduzierung der Tabelle
    - Kann regelmäßig aufgerufen werden
    """
    try:
        cleaned_count = cleanup_expired()
        stats = get_fail_stats()
        
        return JSONResponse({
            "ok": True,
            "cleaned_count": cleaned_count,
            "remaining_stats": stats,
            "message": f"{cleaned_count} abgelaufene Einträge bereinigt"
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Bereinigen des Fail-Cache: {str(e)}")

@router.get("/api/geocode/fail-stats")
def fail_stats():
    """
    Zeigt Statistiken über den Fail-Cache.
    
    - Gesamtanzahl Einträge
    - Anzahl aktiver (noch nicht abgelaufener) Einträge
    - Gruppierung nach Gründen
    """
    try:
        stats = get_fail_stats()
        reasons = get_fail_reasons()
        
        return JSONResponse({
            "ok": True,
            "stats": stats,
            "reasons": reasons,
            "interpretation": {
                "total_entries": stats["total"],
                "active_entries": stats["active"],
                "expired_entries": stats["total"] - stats["active"],
                "most_common_reason": max(reasons.items(), key=lambda x: x[1]) if reasons else None
            }
        })
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Fail-Statistiken: {str(e)}")
