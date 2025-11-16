"""
API-Endpoints für KI-Lernpfad-Koordinator.

Endpoints:
- GET /api/ki-learning/feed - Generiert KI-Feed (alle drei Kanäle)
- GET /api/ki-learning/patterns - Neue/Offene Patterns für KI
- POST /api/ki-learning/analyze-pattern/{id} - Triggert KI-Analyse für Pattern
- GET /api/ki-learning/status - Status aller drei Kanäle
- GET /api/ki-learning/prompt/{pattern_id} - Cursor-Prompt für Pattern
"""

from fastapi import APIRouter, Query, HTTPException, Path
from fastapi.responses import JSONResponse
from typing import Optional
from backend.services.ki_learning_coordinator import (
    generate_ki_feed,
    get_ki_learning_status,
    create_cursor_prompt_for_pattern,
)
from backend.utils.enhanced_logging import get_enhanced_logger

enhanced_logger = get_enhanced_logger(__name__)

router = APIRouter()


@router.get("/api/ki-learning/feed")
async def get_ki_feed(
    include_code_audit: bool = Query(False, description="Code-Audit-Daten einbeziehen"),
    include_runtime_errors: bool = Query(True, description="Runtime-Error-Patterns einbeziehen"),
    include_lessons_standards: bool = Query(True, description="Lessons-/Standards-Dokumente einbeziehen"),
    pattern_status: Optional[str] = Query("open", description="Filter für Patterns (open, fixed, all)"),
    max_patterns: int = Query(20, ge=1, le=100, description="Maximale Anzahl Patterns"),
):
    """
    Generiert KI-Feed aus allen drei Kanälen.
    
    Kombiniert:
    - Code-Audit-Kanal (optional)
    - Runtime-Error-Kanal (error_patterns)
    - Lessons-/Standards-Kanal (ERROR_CATALOG.md, LESSONS_LOG.md, STANDARDS.md)
    """
    try:
        # Konvertiere pattern_status
        status_filter = None if pattern_status == "all" else pattern_status
        
        feed = generate_ki_feed(
            include_code_audit=include_code_audit,
            include_runtime_errors=include_runtime_errors,
            include_lessons_standards=include_lessons_standards,
            pattern_status=status_filter,
            max_patterns=max_patterns,
        )
        
        return JSONResponse({
            "success": True,
            "feed": feed,
        })
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Generieren des KI-Feeds: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Generieren des KI-Feeds: {str(e)}")


@router.get("/api/ki-learning/patterns")
async def get_ki_patterns(
    status: Optional[str] = Query("open", description="Filter nach Status (open, fixed, all)"),
    limit: int = Query(20, ge=1, le=100, description="Maximale Anzahl Patterns"),
):
    """
    Gibt neue/offene Patterns für KI-Analyse zurück.
    
    Enthält Pattern-Details + repräsentative Events.
    """
    try:
        from backend.services.ki_learning_coordinator import get_runtime_error_patterns
        
        status_filter = None if status == "all" else status
        patterns = get_runtime_error_patterns(limit=limit, status=status_filter)
        
        return JSONResponse({
            "success": True,
            "patterns": patterns,
            "count": len(patterns),
        })
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Abrufen der KI-Patterns: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Abrufen der Patterns: {str(e)}")


@router.get("/api/ki-learning/prompt/{pattern_id}")
async def get_cursor_prompt(
    pattern_id: int = Path(..., description="Pattern-ID"),
):
    """
    Erstellt Cursor-Prompt für Pattern-Analyse.
    
    Nutzt alle drei KI-Lernkanäle als Kontext.
    """
    try:
        prompt = create_cursor_prompt_for_pattern(pattern_id)
        
        return JSONResponse({
            "success": True,
            "pattern_id": pattern_id,
            "prompt": prompt,
        })
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Erstellen des Cursor-Prompts: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Erstellen des Prompts: {str(e)}")


@router.post("/api/ki-learning/analyze-pattern/{pattern_id}")
async def trigger_pattern_analysis(
    pattern_id: int = Path(..., description="Pattern-ID"),
):
    """
    Triggert KI-Analyse für ein Pattern.
    
    Erstellt Cursor-Prompt und gibt ihn zurück (KI-Analyse selbst muss manuell durchgeführt werden).
    """
    try:
        prompt = create_cursor_prompt_for_pattern(pattern_id)
        
        enhanced_logger.info(f"KI-Analyse für Pattern {pattern_id} getriggert")
        
        return JSONResponse({
            "success": True,
            "pattern_id": pattern_id,
            "prompt": prompt,
            "message": "Prompt erstellt. Bitte in Cursor einfügen und analysieren lassen.",
        })
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Triggern der Pattern-Analyse: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Triggern der Analyse: {str(e)}")


@router.get("/api/ki-learning/status")
async def get_ki_learning_status_endpoint():
    """
    Gibt Status aller drei KI-Lernkanäle zurück.
    
    Für Monitoring und Dashboard.
    """
    try:
        status = get_ki_learning_status()
        
        return JSONResponse({
            "success": True,
            "status": status,
        })
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Abrufen des KI-Lernpfad-Status: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Abrufen des Status: {str(e)}")

