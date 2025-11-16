"""
Error-Pattern-Aggregator: Gruppiert Error-Events zu Patterns.

Läuft als Hintergrund-Job und aktualisiert error_patterns basierend auf error_events.
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy import text
from db.core import ENGINE
from backend.utils.enhanced_logging import get_enhanced_logger

enhanced_logger = get_enhanced_logger(__name__)


async def aggregate_error_patterns():
    """
    Gruppiert Error-Events zu Patterns und aktualisiert error_patterns.
    
    Läuft periodisch (z.B. alle 5 Minuten) als Hintergrund-Job.
    """
    try:
        enhanced_logger.info("Starte Error-Pattern-Aggregation...")
        
        with ENGINE.begin() as conn:
            # 1. Finde alle Events ohne pattern_id
            events_without_pattern = conn.execute(
                text("""
                    SELECT id, stack_hash, endpoint, status_code, error_type, module, message_short
                    FROM error_events
                    WHERE pattern_id IS NULL AND stack_hash IS NOT NULL AND stack_hash != ''
                    ORDER BY timestamp DESC
                    LIMIT 1000
                """)
            ).fetchall()
            
            if not events_without_pattern:
                enhanced_logger.debug("Keine neuen Events für Aggregation gefunden")
                return
            
            enhanced_logger.info(f"Verarbeite {len(events_without_pattern)} Events ohne Pattern...")
            
            # 2. Für jedes Event: Finde oder erstelle Pattern
            for event in events_without_pattern:
                event_id, stack_hash, endpoint, status_code, error_type, module, message_short = event
                
                # Prüfe ob Pattern existiert
                pattern = conn.execute(
                    text("SELECT id FROM error_patterns WHERE stack_hash = :stack_hash"),
                    {"stack_hash": stack_hash}
                ).fetchone()
                
                if pattern:
                    pattern_id = pattern[0]
                    # Aktualisiere Pattern
                    conn.execute(
                        text("""
                            UPDATE error_patterns
                            SET last_seen = CURRENT_TIMESTAMP,
                                occurrences = occurrences + 1,
                                last_status_code = :status_code,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE id = :pattern_id
                        """),
                        {
                            "pattern_id": pattern_id,
                            "status_code": status_code,
                        }
                    )
                else:
                    # Erstelle neues Pattern
                    from backend.services.error_learning_service import extract_error_signature
                    signature = extract_error_signature(error_type or "Unknown", message_short or "", module)
                    
                    result = conn.execute(
                        text("""
                            INSERT INTO error_patterns (
                                stack_hash, signature, first_seen, last_seen, occurrences,
                                last_status_code, primary_endpoint, component, status
                            ) VALUES (
                                :stack_hash, :signature, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1,
                                :status_code, :endpoint, :component, 'open'
                            )
                        """),
                        {
                            "stack_hash": stack_hash,
                            "signature": signature,
                            "status_code": status_code,
                            "endpoint": endpoint,
                            "component": module or "unknown",
                        }
                    )
                    pattern_id = result.lastrowid
                
                # Verknüpfe Event mit Pattern
                conn.execute(
                    text("UPDATE error_events SET pattern_id = :pattern_id WHERE id = :event_id"),
                    {"pattern_id": pattern_id, "event_id": event_id}
                )
            
            # 3. Prüfe Patterns auf "fixed" Status (wenn keine neuen Events in letzter Zeit)
            # Wenn Pattern als "fixed" markiert wurde und keine neuen Events mehr kommen,
            # kann Status bestätigt werden
            fixed_patterns = conn.execute(
                text("""
                    SELECT id, stack_hash, last_seen
                    FROM error_patterns
                    WHERE status = 'fixed'
                    AND last_seen < datetime('now', '-1 day')
                """)
            ).fetchall()
            
            for pattern in fixed_patterns:
                pattern_id, stack_hash, last_seen = pattern
                # Prüfe ob es neue Events gibt
                recent_events = conn.execute(
                    text("""
                        SELECT COUNT(*) FROM error_events
                        WHERE pattern_id = :pattern_id
                        AND timestamp > datetime('now', '-1 day')
                    """),
                    {"pattern_id": pattern_id}
                ).scalar()
                
                if recent_events == 0:
                    # Pattern ist wirklich fixed - könnte automatisch LESSONS_LOG-Eintrag erzeugen
                    enhanced_logger.info(f"Pattern {pattern_id} bestätigt als fixed (keine neuen Events)")
            
            enhanced_logger.success(f"Error-Pattern-Aggregation abgeschlossen: {len(events_without_pattern)} Events verarbeitet")
            
    except Exception as e:
        enhanced_logger.error(f"Fehler bei Error-Pattern-Aggregation: {e}", exc_info=e)


async def run_aggregator_loop(interval_minutes: int = 5):
    """
    Läuft als Hintergrund-Loop und führt Aggregation periodisch aus.
    
    Args:
        interval_minutes: Intervall in Minuten zwischen Aggregationen
    """
    while True:
        try:
            await aggregate_error_patterns()
        except Exception as e:
            enhanced_logger.error(f"Fehler im Aggregator-Loop: {e}", exc_info=e)
        
        # Warte bis zur nächsten Ausführung
        await asyncio.sleep(interval_minutes * 60)

