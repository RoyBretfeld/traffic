"""
Lessons-Updater: Aktualisiert LESSONS_LOG.md automatisch.

Erstellt LESSONS_LOG-Einträge automatisch, wenn:
- Pattern als "fixed" markiert wird
- Pattern keine neuen Events mehr hat (bestätigt fixed)
- Kritische Patterns erkannt werden
"""

from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from sqlalchemy import text
from db.core import ENGINE
from backend.utils.enhanced_logging import get_enhanced_logger

enhanced_logger = get_enhanced_logger(__name__)


def create_lessons_log_entry(
    pattern_id: int,
    title: Optional[str] = None,
    category: str = "Backend",
    severity: str = "🟡 MEDIUM",
    files: Optional[list] = None,
) -> bool:
    """
    Erstellt automatisch einen LESSONS_LOG-Eintrag für ein Pattern.
    
    Args:
        pattern_id: Pattern-ID
        title: Titel (optional, wird aus Pattern generiert)
        category: Kategorie (Backend/Frontend/DB/Infrastruktur)
        severity: Schweregrad
        files: Betroffene Dateien (optional)
        
    Returns:
        True wenn erfolgreich, False bei Fehler
    """
    try:
        # Hole Pattern-Details
        with ENGINE.begin() as conn:
            pattern = conn.execute(
                text("SELECT * FROM error_patterns WHERE id = :id"),
                {"id": pattern_id}
            ).fetchone()
            
            if not pattern:
                enhanced_logger.warning(f"Pattern {pattern_id} nicht gefunden")
                return False
            
            # Hole Feedback
            feedback = conn.execute(
                text("""
                    SELECT note, resolution_status, source
                    FROM error_feedback
                    WHERE pattern_id = :id
                    ORDER BY created_at DESC
                    LIMIT 1
                """),
                {"id": pattern_id}
            ).fetchone()
            
            # Hole repräsentative Events
            events = conn.execute(
                text("""
                    SELECT error_type, message_short, endpoint, module
                    FROM error_events
                    WHERE pattern_id = :id
                    ORDER BY timestamp DESC
                    LIMIT 3
                """),
                {"id": pattern_id}
            ).fetchall()
        
        # Generiere Titel
        if not title:
            title = pattern[2][:80]  # Signature (gekürzt)
        
        # Generiere Eintrag
        date_str = datetime.now().strftime("%Y-%m-%d")
        entry = f"""## {date_str} – {title}

**Kategorie:** {category}  
**Schweregrad:** {severity}  
**Pattern-ID:** {pattern_id}  
**Dateien:** {', '.join(files) if files else 'Siehe Pattern-Details'}

### Symptom
- Pattern: `{pattern[2]}`
- Occurrences: {pattern[5]}
- Primary Endpoint: `{pattern[7] or 'unknown'}`
- Component: `{pattern[8] or 'unknown'}`

### Repräsentative Events
"""
        
        for i, event in enumerate(events, 1):
            entry += f"""
**Event {i}:**
- Error Type: `{event[0]}`
- Message: `{event[1][:200]}`
- Endpoint: `{event[2] or 'unknown'}`
- Module: `{event[3] or 'unknown'}`
"""
        
        entry += f"""
### Ursache
- Stack Hash: `{pattern[1]}`
- First Seen: {pattern[3]}
- Last Seen: {pattern[4]}

"""
        
        if feedback:
            entry += f"""
### Fix
{feedback[0]}

**Quelle:** {feedback[1]} ({feedback[2]})

"""
        
        if pattern[10]:  # root_cause_hint
            entry += f"""
### Root Cause Hint
{pattern[10]}

"""
        
        entry += """
### Was die KI künftig tun soll
1. Erkenne ähnliche Patterns frühzeitig
2. Nutze diese Erkenntnisse bei Code-Analysen
3. Verhindere ähnliche Fehler proaktiv
4. Dokumentiere ähnliche Fälle in ERROR_CATALOG

---
"""
        
        # Füge Eintrag zu LESSONS_LOG.md hinzu
        project_root = Path(__file__).parent.parent.parent
        lessons_log_path = project_root / "Regeln" / "LESSONS_LOG.md"
        
        if not lessons_log_path.exists():
            enhanced_logger.warning(f"LESSONS_LOG.md nicht gefunden: {lessons_log_path}")
            return False
        
        # Lade bestehenden Inhalt
        content = lessons_log_path.read_text(encoding="utf-8")
        
        # Füge neuen Eintrag am Anfang hinzu (nach Header)
        header_end = content.find("---")
        if header_end == -1:
            header_end = 0
        
        new_content = content[:header_end + 3] + "\n\n" + entry + "\n" + content[header_end + 3:]
        
        # Speichere
        lessons_log_path.write_text(new_content, encoding="utf-8")
        
        enhanced_logger.success(f"LESSONS_LOG-Eintrag für Pattern {pattern_id} erstellt: {title}")
        
        # Aktualisiere Pattern (verknüpfe mit LESSONS_LOG)
        with ENGINE.begin() as conn:
            conn.execute(
                text("""
                    UPDATE error_patterns
                    SET linked_lesson_id = :lesson_id,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :pattern_id
                """),
                {
                    "pattern_id": pattern_id,
                    "lesson_id": f"{date_str}-{pattern_id}",
                }
            )
        
        return True
        
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Erstellen des LESSONS_LOG-Eintrags: {e}", exc_info=e)
        return False


def auto_update_lessons_for_fixed_patterns():
    """
    Prüft alle "fixed" Patterns und erstellt LESSONS_LOG-Einträge für die, die noch keinen haben.
    
    Läuft periodisch (z.B. täglich) als Hintergrund-Job.
    """
    try:
        enhanced_logger.info("Prüfe fixed Patterns für LESSONS_LOG-Updates...")
        
        with ENGINE.begin() as conn:
            # Finde fixed Patterns ohne LESSONS_LOG-Verknüpfung
            fixed_patterns = conn.execute(
                text("""
                    SELECT id, signature, component, occurrences
                    FROM error_patterns
                    WHERE status = 'fixed'
                    AND (linked_lesson_id IS NULL OR linked_lesson_id = '')
                    AND last_seen < datetime('now', '-1 day')
                    ORDER BY occurrences DESC
                    LIMIT 10
                """)
            ).fetchall()
            
            if not fixed_patterns:
                enhanced_logger.debug("Keine fixed Patterns ohne LESSONS_LOG-Verknüpfung gefunden")
                return
            
            enhanced_logger.info(f"Erstelle LESSONS_LOG-Einträge für {len(fixed_patterns)} Patterns...")
            
            for pattern in fixed_patterns:
                pattern_id, signature, component, occurrences = pattern
                
                # Bestimme Kategorie
                category = "Backend"
                if component and ("frontend" in component.lower() or "js" in component.lower()):
                    category = "Frontend"
                elif component and ("db" in component.lower() or "schema" in component.lower()):
                    category = "DB"
                elif component and ("osrm" in component.lower() or "infra" in component.lower()):
                    category = "Infrastruktur"
                
                # Bestimme Schweregrad
                severity = "🟡 MEDIUM"
                if occurrences > 50:
                    severity = "🔴 KRITISCH"
                elif occurrences > 20:
                    severity = "🟠 HOCH"
                
                # Erstelle Eintrag
                success = create_lessons_log_entry(
                    pattern_id=pattern_id,
                    title=signature[:80],
                    category=category,
                    severity=severity,
                )
                
                if success:
                    enhanced_logger.info(f"LESSONS_LOG-Eintrag für Pattern {pattern_id} erstellt")
                else:
                    enhanced_logger.warning(f"Fehler beim Erstellen des LESSONS_LOG-Eintrags für Pattern {pattern_id}")
            
            enhanced_logger.success(f"LESSONS_LOG-Updates abgeschlossen: {len(fixed_patterns)} Patterns verarbeitet")
            
    except Exception as e:
        enhanced_logger.error(f"Fehler bei automatischen LESSONS_LOG-Updates: {e}", exc_info=e)

