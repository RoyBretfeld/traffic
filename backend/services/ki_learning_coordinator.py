"""
KI-Lernpfad-Koordinator: Koordiniert alle drei KI-Lernkanäle.

Die drei Kanäle:
1. Code-Audit-Kanal: Manuelle Audit-ZIPs + Code-Dateien
2. Runtime-Error-Kanal: error_events + error_patterns (Datenbank)
3. Lessons-/Standards-Kanal: ERROR_CATALOG.md, LESSONS_LOG.md, STANDARDS.md

Zweck:
- Alle drei Kanäle systematisch nutzen
- KI-Feed generieren (alle drei Kanäle kombiniert)
- KI-Analysen koordinieren
- Feedback-Loop verwalten
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from sqlalchemy import text
from db.core import ENGINE
from backend.services.error_learning_service import get_error_patterns, get_error_events
from backend.utils.enhanced_logging import get_enhanced_logger

enhanced_logger = get_enhanced_logger(__name__)


def load_lessons_standards() -> Dict[str, Any]:
    """
    Lädt Lessons-/Standards-Dokumente (Kanal 3).
    
    Returns:
        Dictionary mit Dokument-Inhalten
    """
    try:
        project_root = Path(__file__).parent.parent.parent
        
        lessons_log_path = project_root / "Regeln" / "LESSONS_LOG.md"
        error_catalog_path = project_root / "docs" / "ERROR_CATALOG.md"
        standards_path = project_root / "Regeln" / "STANDARDS.md"
        
        result = {
            "lessons_log": None,
            "error_catalog": None,
            "standards": None,
            "last_updated": None,
        }
        
        if lessons_log_path.exists():
            result["lessons_log"] = lessons_log_path.read_text(encoding="utf-8")
            result["last_updated"] = datetime.fromtimestamp(lessons_log_path.stat().st_mtime).isoformat()
        
        if error_catalog_path.exists():
            result["error_catalog"] = error_catalog_path.read_text(encoding="utf-8")
        
        if standards_path.exists():
            result["standards"] = standards_path.read_text(encoding="utf-8")
        
        enhanced_logger.debug("Lessons-/Standards-Dokumente geladen")
        return result
        
    except Exception as e:
        enhanced_logger.warning(f"Fehler beim Laden der Lessons-/Standards-Dokumente: {e}")
        return {
            "lessons_log": None,
            "error_catalog": None,
            "standards": None,
            "last_updated": None,
        }


def get_runtime_error_patterns(limit: int = 50, status: Optional[str] = "open") -> List[Dict[str, Any]]:
    """
    Holt Runtime-Error-Patterns (Kanal 2).
    
    Args:
        limit: Maximale Anzahl Patterns
        status: Filter nach Status (None = alle)
        
    Returns:
        Liste von Pattern-Dictionaries mit Events
    """
    try:
        patterns = get_error_patterns(status=status, limit=limit)
        
        # Erweitere Patterns mit repräsentativen Events
        for pattern in patterns:
            pattern_id = pattern["id"]
            events = get_error_events(pattern_id=pattern_id, limit=3)
            pattern["representative_events"] = events
        
        enhanced_logger.debug(f"{len(patterns)} Runtime-Error-Patterns geladen")
        return patterns
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Laden der Runtime-Error-Patterns: {e}", exc_info=e)
        return []


def generate_ki_feed(
    include_code_audit: bool = False,
    include_runtime_errors: bool = True,
    include_lessons_standards: bool = True,
    pattern_status: Optional[str] = "open",
    max_patterns: int = 20,
) -> Dict[str, Any]:
    """
    Generiert KI-Feed aus allen drei Kanälen.
    
    Args:
        include_code_audit: Code-Audit-Daten einbeziehen (noch nicht implementiert)
        include_runtime_errors: Runtime-Error-Patterns einbeziehen
        include_lessons_standards: Lessons-/Standards-Dokumente einbeziehen
        pattern_status: Filter für Patterns (None = alle)
        max_patterns: Maximale Anzahl Patterns
        
    Returns:
        Strukturierter KI-Feed
    """
    try:
        enhanced_logger.info("Generiere KI-Feed aus allen drei Kanälen...")
        
        feed = {
            "generated_at": datetime.now().isoformat(),
            "channels": {
                "code_audit": None,
                "runtime_errors": None,
                "lessons_standards": None,
            },
            "summary": {
                "total_patterns": 0,
                "open_patterns": 0,
                "lessons_count": 0,
                "standards_available": False,
            }
        }
        
        # Kanal 1: Code-Audit (noch nicht implementiert)
        if include_code_audit:
            # TODO: Code-Audit-Daten sammeln
            feed["channels"]["code_audit"] = {
                "status": "not_implemented",
                "message": "Code-Audit-Kanal wird noch implementiert"
            }
        
        # Kanal 2: Runtime-Errors
        if include_runtime_errors:
            patterns = get_runtime_error_patterns(limit=max_patterns, status=pattern_status)
            feed["channels"]["runtime_errors"] = {
                "status": "active",
                "patterns": patterns,
                "count": len(patterns),
            }
            feed["summary"]["total_patterns"] = len(patterns)
            feed["summary"]["open_patterns"] = len([p for p in patterns if p.get("status") == "open"])
        
        # Kanal 3: Lessons-/Standards
        if include_lessons_standards:
            lessons_standards = load_lessons_standards()
            feed["channels"]["lessons_standards"] = {
                "status": "active",
                "lessons_log": lessons_standards.get("lessons_log"),
                "error_catalog": lessons_standards.get("error_catalog"),
                "standards": lessons_standards.get("standards"),
                "last_updated": lessons_standards.get("last_updated"),
            }
            # Zähle Lessons (grobe Schätzung)
            if lessons_standards.get("lessons_log"):
                feed["summary"]["lessons_count"] = lessons_standards["lessons_log"].count("##")
            feed["summary"]["standards_available"] = lessons_standards.get("standards") is not None
        
        enhanced_logger.success(f"KI-Feed generiert: {feed['summary']['total_patterns']} Patterns, {feed['summary']['lessons_count']} Lessons")
        return feed
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Generieren des KI-Feeds: {e}", exc_info=e)
        return {
            "error": str(e),
            "generated_at": datetime.now().isoformat(),
        }


def get_ki_learning_status() -> Dict[str, Any]:
    """
    Gibt Status aller drei KI-Lernkanäle zurück.
    
    Returns:
        Status-Dictionary
    """
    try:
        # Kanal 1: Code-Audit
        code_audit_status = {
            "status": "not_implemented",
            "message": "Code-Audit-Kanal wird noch implementiert"
        }
        
        # Kanal 2: Runtime-Errors
        with ENGINE.begin() as conn:
            patterns_total = conn.execute(
                text("SELECT COUNT(*) FROM error_patterns")
            ).scalar()
            
            patterns_open = conn.execute(
                text("SELECT COUNT(*) FROM error_patterns WHERE status = 'open'")
            ).scalar()
            
            events_total = conn.execute(
                text("SELECT COUNT(*) FROM error_events")
            ).scalar()
            
            last_aggregation = conn.execute(
                text("SELECT MAX(updated_at) FROM error_patterns")
            ).scalar()
        
        runtime_error_status = {
            "status": "active",
            "patterns_total": patterns_total,
            "patterns_open": patterns_open,
            "events_total": events_total,
            "last_aggregation": last_aggregation,
        }
        
        # Kanal 3: Lessons-/Standards
        project_root = Path(__file__).parent.parent.parent
        lessons_log_path = project_root / "Regeln" / "LESSONS_LOG.md"
        error_catalog_path = project_root / "docs" / "ERROR_CATALOG.md"
        standards_path = project_root / "Regeln" / "STANDARDS.md"
        
        lessons_standards_status = {
            "status": "active",
            "lessons_log_exists": lessons_log_path.exists(),
            "error_catalog_exists": error_catalog_path.exists(),
            "standards_exists": standards_path.exists(),
            "last_update": None,
        }
        
        if lessons_log_path.exists():
            lessons_standards_status["last_update"] = datetime.fromtimestamp(
                lessons_log_path.stat().st_mtime
            ).isoformat()
        
        return {
            "code_audit_kanal": code_audit_status,
            "runtime_error_kanal": runtime_error_status,
            "lessons_standards_kanal": lessons_standards_status,
            "timestamp": datetime.now().isoformat(),
        }
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Abrufen des KI-Lernpfad-Status: {e}", exc_info=e)
        return {
            "error": str(e),
            "timestamp": datetime.now().isoformat(),
        }


def create_cursor_prompt_for_pattern(pattern_id: int) -> str:
    """
    Erstellt Cursor-Prompt für Pattern-Analyse (nutzt alle drei Kanäle).
    
    Args:
        pattern_id: Pattern-ID
        
    Returns:
        Cursor-Prompt als String
    """
    try:
        # Hole Pattern-Details
        patterns = get_error_patterns(limit=1000)  # Hole alle, dann filtere
        pattern = next((p for p in patterns if p["id"] == pattern_id), None)
        
        if not pattern:
            return f"❌ Pattern {pattern_id} nicht gefunden"
        
        # Hole Events
        events = get_error_events(pattern_id=pattern_id, limit=5)
        
        # Lade Lessons-/Standards
        lessons_standards = load_lessons_standards()
        
        # Erstelle Prompt
        prompt = f"""# Error-Pattern-Analyse: Pattern #{pattern_id}

## Pattern-Details

- **Signatur:** {pattern['signature']}
- **Component:** {pattern.get('component', 'unknown')}
- **Occurrences:** {pattern['occurrences']}
- **Primary Endpoint:** {pattern.get('primary_endpoint', 'unknown')}
- **Status:** {pattern['status']}
- **First Seen:** {pattern['first_seen']}
- **Last Seen:** {pattern['last_seen']}

## Repräsentative Events ({len(events)})

"""
        
        for i, event in enumerate(events[:3], 1):
            prompt += f"""
### Event {i}
- **Timestamp:** {event['timestamp']}
- **Error Type:** {event['error_type']}
- **Message:** {event['message_short'][:200]}
- **Stacktrace:** {event.get('stacktrace', '')[:500] if event.get('stacktrace') else 'N/A'}
"""
        
        prompt += f"""
## Kontext aus Lessons-/Standards

"""
        
        if lessons_standards.get("lessons_log"):
            prompt += f"### LESSONS_LOG (Auszug)\n{lessons_standards['lessons_log'][:1000]}...\n\n"
        
        if lessons_standards.get("error_catalog"):
            prompt += f"### ERROR_CATALOG (Auszug)\n{lessons_standards['error_catalog'][:1000]}...\n\n"
        
        prompt += """
## Aufgabe

Bitte:
1. Analysiere die repräsentativen Events
2. Identifiziere die Root Cause (nutze Lessons-/Standards als Kontext)
3. Erstelle Fix-Vorschlag
4. Dokumentiere in LESSONS_LOG (falls erfolgreich)
"""
        
        return prompt
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Erstellen des Cursor-Prompts: {e}", exc_info=e)
        return f"❌ Fehler beim Erstellen des Prompts: {e}"

