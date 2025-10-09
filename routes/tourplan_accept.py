"""
Accept-Endpoint für FAMO TrafficApp
Ermöglicht das Übernehmen von Fuzzy-Vorschlägen als Alias-Zuordnungen
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from repositories.geo_alias_repo import set_alias, get_alias_stats

router = APIRouter()

class AcceptBody(BaseModel):
    """Request-Body für das Übernehmen von Vorschlägen."""
    query: str = Field(..., min_length=3, description="Die problematische/abweichende Adresse")
    accept: str = Field(..., min_length=3, description="Die kanonische Adresse (muss im geo_cache existieren)")
    by_user: str | None = Field(None, description="Optional: Benutzer-Identifikation")

@router.post("/api/tourplan/suggest/accept")
def api_accept_suggestion(body: AcceptBody):
    """
    Nimmt einen Fuzzy-Vorschlag als Alias-Zuordnung an.
    
    - Prüft ob die kanonische Adresse im geo_cache existiert
    - Erstellt Alias-Zuordnung ohne Daten-Duplikation
    - Loggt die Aktion im Audit-Log
    
    Args:
        body: AcceptBody mit query, accept und optional by_user
    
    Returns:
        JSONResponse mit Erfolgsstatus
    
    Raises:
        HTTPException: 400 wenn canonical nicht im geo_cache existiert oder Alias ungültig
    """
    try:
        set_alias(body.query, body.accept, body.by_user)
        return JSONResponse({
            "ok": True,
            "message": f"Alias gesetzt: '{body.query}' → '{body.accept}'"
        }, media_type="application/json; charset=utf-8")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Unerwarteter Fehler: {str(e)}")

@router.get("/api/tourplan/suggest/accept/stats")
def api_alias_stats():
    """
    Gibt Statistiken über das Alias-System zurück.
    
    Returns:
        JSONResponse mit Anzahl der Aliasse und Audit-Einträge
    """
    try:
        stats = get_alias_stats()
        return JSONResponse(stats, media_type="application/json; charset=utf-8")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Abrufen der Statistiken: {str(e)}")

@router.delete("/api/tourplan/suggest/accept/{query:path}")
def api_remove_alias(query: str):
    """
    Entfernt einen Alias.
    
    Args:
        query: Die Adresse deren Alias entfernt werden soll
    
    Returns:
        JSONResponse mit Erfolgsstatus
    """
    try:
        from repositories.geo_alias_repo import remove_alias
        remove_alias(query)
        return JSONResponse({
            "ok": True,
            "message": f"Alias für '{query}' entfernt"
        }, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Entfernen des Alias: {str(e)}")
