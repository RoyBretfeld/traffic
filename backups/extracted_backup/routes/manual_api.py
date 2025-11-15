from fastapi import APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from repositories.manual_repo import list_open, get_stats, close, add_open

router = APIRouter()

@router.get("/api/manual/list")
def manual_list(limit: int = Query(200, ge=1, le=1000, description="Maximale Anzahl zurückzugebender Einträge")):
    """
    Listet alle offenen Einträge aus der Manual-Queue.
    
    - Zeigt Adressen die manuell bearbeitet werden müssen
    - Sortiert nach Erstellungsdatum (neueste zuerst)
    - Limitierbar für Performance
    """
    items = list_open(limit)
    stats = get_stats()
    
    return JSONResponse({
        "stats": stats,
        "items": items,
        "count": len(items)
    }, media_type="application/json; charset=utf-8")

@router.get("/api/manual/stats")
def manual_stats():
    """
    Gibt Statistiken über die Manual-Queue zurück.
    
    - Total: Gesamtanzahl Einträge
    - Open: Offene Einträge (zu bearbeiten)
    - Closed: Geschlossene Einträge (bearbeitet)
    """
    stats = get_stats()
    return JSONResponse(stats, media_type="application/json; charset=utf-8")

@router.post("/api/manual/close")
def manual_close(address: str = Query(..., description="Adresse die geschlossen werden soll")):
    """
    Schließt einen Eintrag in der Manual-Queue.
    
    - Setzt status='closed' für die angegebene Adresse
    - Wird aufgerufen nach manueller Bearbeitung
    """
    try:
        close(address)
        return JSONResponse({
            "ok": True,
            "message": f"Eintrag für '{address}' wurde geschlossen"
        }, media_type="application/json; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Schließen: {str(e)}")

@router.post("/api/manual/add")
def manual_add(address: str = Query(..., description="Adresse die zur Manual-Queue hinzugefügt werden soll"),
               reason: str = Query("manual", description="Grund für manuelle Bearbeitung"),
               note: str = Query("", description="Zusätzliche Notiz")):
    """
    Fügt eine Adresse zur Manual-Queue hinzu.
    
    - Für manuelle Eingabe von Adressen die bearbeitet werden müssen
    - Reason: 'manual', 'no_result', 'temp_error', etc.
    """
    try:
        add_open(address, reason=reason, note=note)
        return JSONResponse({
            "ok": True,
            "message": f"Adresse '{address}' zur Manual-Queue hinzugefügt"
        }, media_type="application/json; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Hinzufügen: {str(e)}")
