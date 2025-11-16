"""
API-Endpoints für Error-Learning-System (KI-Lernpfad).

Endpoints:
- GET /api/audit/error-patterns - Liste aller Patterns
- GET /api/audit/error-patterns/{id} - Detailansicht eines Patterns
- GET /api/audit/error-events - Liste von Events (mit Filtern)
- POST /api/audit/error-feedback - Feedback zu einem Pattern
"""

from fastapi import APIRouter, Query, HTTPException, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from backend.services.error_learning_service import (
    get_error_patterns,
    get_error_events,
    log_error_event,
)
from backend.utils.enhanced_logging import get_enhanced_logger
from sqlalchemy import text
from db.core import ENGINE

enhanced_logger = get_enhanced_logger(__name__)

router = APIRouter()


class ErrorFeedbackRequest(BaseModel):
    """Request-Model für Error-Feedback."""
    pattern_id: int
    source: str  # "dev", "cursor", "user", "monitoring"
    note: str
    resolution_status: str = "todo"  # "todo", "in_progress", "fixed", "won't_fix"


@router.get("/api/audit/error-patterns")
async def get_error_patterns_endpoint(
    status: Optional[str] = Query(None, description="Filter nach Status (open, investigating, fixed, ignored)"),
    component: Optional[str] = Query(None, description="Filter nach Component"),
    limit: int = Query(50, ge=1, le=500, description="Maximale Anzahl Ergebnisse"),
):
    """
    Gibt Liste aller Error-Patterns zurück.
    
    Filterbar nach Status und Component.
    """
    try:
        patterns = get_error_patterns(status=status, component=component, limit=limit)
        
        return JSONResponse({
            "success": True,
            "patterns": patterns,
            "count": len(patterns),
        })
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Abrufen der Error-Patterns: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Abrufen der Patterns: {str(e)}")


@router.get("/api/audit/error-patterns/{pattern_id}")
async def get_error_pattern_detail(
    pattern_id: int = Path(..., description="Pattern-ID"),
):
    """
    Gibt Detailansicht eines Error-Patterns zurück.
    
    Enthält Pattern-Info + repräsentative Events.
    """
    try:
        with ENGINE.begin() as conn:
            # Hole Pattern
            pattern = conn.execute(
                text("SELECT * FROM error_patterns WHERE id = :id"),
                {"id": pattern_id}
            ).fetchone()
            
            if not pattern:
                raise HTTPException(404, detail=f"Pattern {pattern_id} nicht gefunden")
            
            # Hole repräsentative Events (max. 5)
            events = get_error_events(pattern_id=pattern_id, limit=5)
            
            # Hole Feedback
            feedback = conn.execute(
                text("SELECT * FROM error_feedback WHERE pattern_id = :id ORDER BY created_at DESC"),
                {"id": pattern_id}
            ).fetchall()
            
            feedback_list = []
            for fb in feedback:
                feedback_list.append({
                    "id": fb[0],
                    "source": fb[2],
                    "note": fb[3],
                    "resolution_status": fb[4],
                    "created_at": fb[5],
                })
            
            return JSONResponse({
                "success": True,
                "pattern": {
                    "id": pattern[0],
                    "stack_hash": pattern[1],
                    "signature": pattern[2],
                    "first_seen": pattern[3],
                    "last_seen": pattern[4],
                    "occurrences": pattern[5],
                    "last_status_code": pattern[6],
                    "primary_endpoint": pattern[7],
                    "component": pattern[8],
                    "status": pattern[9],
                    "root_cause_hint": pattern[10],
                    "linked_rule_id": pattern[11],
                    "linked_lesson_id": pattern[12],
                },
                "events": events,
                "feedback": feedback_list,
            })
            
    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Abrufen des Pattern-Details: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Abrufen des Pattern-Details: {str(e)}")


@router.get("/api/audit/error-events")
async def get_error_events_endpoint(
    pattern_id: Optional[int] = Query(None, description="Filter nach Pattern-ID"),
    endpoint: Optional[str] = Query(None, description="Filter nach Endpoint"),
    limit: int = Query(100, ge=1, le=1000, description="Maximale Anzahl Ergebnisse"),
):
    """
    Gibt Liste von Error-Events zurück.
    
    Filterbar nach Pattern-ID und Endpoint.
    """
    try:
        events = get_error_events(pattern_id=pattern_id, endpoint=endpoint, limit=limit)
        
        return JSONResponse({
            "success": True,
            "events": events,
            "count": len(events),
        })
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Abrufen der Error-Events: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Abrufen der Events: {str(e)}")


@router.post("/api/audit/error-feedback")
async def post_error_feedback(feedback: ErrorFeedbackRequest):
    """
    Speichert Feedback zu einem Error-Pattern.
    
    Wird von Dev/KI verwendet, um Patterns zu kommentieren und Status zu setzen.
    """
    try:
        with ENGINE.begin() as conn:
            # Prüfe ob Pattern existiert
            pattern = conn.execute(
                text("SELECT id FROM error_patterns WHERE id = :id"),
                {"id": feedback.pattern_id}
            ).fetchone()
            
            if not pattern:
                raise HTTPException(404, detail=f"Pattern {feedback.pattern_id} nicht gefunden")
            
            # Speichere Feedback
            result = conn.execute(
                text("""
                    INSERT INTO error_feedback (pattern_id, source, note, resolution_status)
                    VALUES (:pattern_id, :source, :note, :resolution_status)
                """),
                {
                    "pattern_id": feedback.pattern_id,
                    "source": feedback.source,
                    "note": feedback.note,
                    "resolution_status": feedback.resolution_status,
                }
            )
            feedback_id = result.lastrowid
            
            # Aktualisiere Pattern-Status (wenn resolution_status != "todo")
            if feedback.resolution_status in ["fixed", "won't_fix"]:
                conn.execute(
                    text("""
                        UPDATE error_patterns
                        SET status = :status, updated_at = CURRENT_TIMESTAMP
                        WHERE id = :pattern_id
                    """),
                    {
                        "pattern_id": feedback.pattern_id,
                        "status": feedback.resolution_status,
                    }
                )
            
            enhanced_logger.info(f"Feedback zu Pattern {feedback.pattern_id} gespeichert: {feedback.resolution_status}")
            
            return JSONResponse({
                "success": True,
                "feedback_id": feedback_id,
                "message": "Feedback gespeichert",
            })
            
    except HTTPException:
        raise
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Speichern des Feedbacks: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Speichern des Feedbacks: {str(e)}")


@router.get("/api/audit/error-stats")
async def get_error_stats():
    """
    Gibt aggregierte Statistiken über Error-Patterns zurück.
    
    Für Dashboards und Monitoring.
    """
    try:
        with ENGINE.begin() as conn:
            # Gesamt-Statistiken
            total_patterns = conn.execute(
                text("SELECT COUNT(*) FROM error_patterns")
            ).scalar()
            
            open_patterns = conn.execute(
                text("SELECT COUNT(*) FROM error_patterns WHERE status = 'open'")
            ).scalar()
            
            fixed_patterns = conn.execute(
                text("SELECT COUNT(*) FROM error_patterns WHERE status = 'fixed'")
            ).scalar()
            
            total_events = conn.execute(
                text("SELECT COUNT(*) FROM error_events")
            ).scalar()
            
            # Top-Patterns (nach Occurrences)
            top_patterns = conn.execute(
                text("""
                    SELECT id, signature, occurrences, last_seen, status
                    FROM error_patterns
                    ORDER BY occurrences DESC
                    LIMIT 10
                """)
            ).fetchall()
            
            top_patterns_list = []
            for p in top_patterns:
                top_patterns_list.append({
                    "id": p[0],
                    "signature": p[1],
                    "occurrences": p[2],
                    "last_seen": p[3],
                    "status": p[4],
                })
            
            return JSONResponse({
                "success": True,
                "stats": {
                    "total_patterns": total_patterns,
                    "open_patterns": open_patterns,
                    "fixed_patterns": fixed_patterns,
                    "total_events": total_events,
                },
                "top_patterns": top_patterns_list,
            })
            
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Abrufen der Error-Stats: {e}", exc_info=e)
        raise HTTPException(500, detail=f"Fehler beim Abrufen der Stats: {str(e)}")

