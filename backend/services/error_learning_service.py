"""
Error-Learning-Service: Erfasst Fehler-Events und gruppiert sie zu Patterns.

Zweck: KI-Lernpfad über positives/negatives Logging.
"""

import hashlib
import traceback
import json
from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlalchemy import text
from db.core import ENGINE
from backend.utils.enhanced_logging import get_enhanced_logger

enhanced_logger = get_enhanced_logger(__name__)


def calculate_stack_hash(stacktrace: str) -> str:
    """
    Berechnet Hash über Stacktrace für Pattern-Erkennung.
    
    Args:
        stacktrace: Vollständiger Stacktrace als String
        
    Returns:
        SHA256-Hash (gekürzt auf 16 Zeichen)
    """
    if not stacktrace:
        return ""
    
    # Normalisiere Stacktrace (entferne Pfade, behalte nur Dateinamen)
    normalized = stacktrace
    # Entferne absolute Pfade, behalte nur Dateinamen
    import re
    normalized = re.sub(r'File "[^"]*[/\\]([^/\\"]+)"', r'File "\1"', normalized)
    # Entferne Zeilennummern (variieren bei Code-Änderungen)
    normalized = re.sub(r', line \d+', '', normalized)
    
    # Berechne Hash
    hash_obj = hashlib.sha256(normalized.encode('utf-8'))
    return hash_obj.hexdigest()[:16]


def extract_error_signature(error_type: str, message: str, module: Optional[str] = None) -> str:
    """
    Erstellt lesbare Signatur für ein Fehlermuster.
    
    Args:
        error_type: Exception-Typ (z.B. "ValueError")
        message: Fehlermeldung
        module: Modul/Component (z.B. "subroute_generator")
        
    Returns:
        Signatur-String (z.B. "ValueError in subroute_generator: cannot read property 'legs' of undefined")
    """
    parts = []
    if module:
        parts.append(f"in {module}")
    parts.append(f"{error_type}: {message[:100]}")
    return " ".join(parts)


def log_error_event(
    trace_id: Optional[str] = None,
    endpoint: Optional[str] = None,
    http_method: Optional[str] = None,
    status_code: Optional[int] = None,
    error_type: Optional[str] = None,
    module: Optional[str] = None,
    message: Optional[str] = None,
    stacktrace: Optional[str] = None,
    payload_snapshot: Optional[Dict[str, Any]] = None,
    environment: str = "dev",
    severity: str = "error",
    is_handled: bool = False,
    user_agent: Optional[str] = None,
    ip_address: Optional[str] = None,
    request_duration_ms: Optional[int] = None,
) -> Optional[int]:
    """
    Loggt ein Fehler-Event in die Datenbank.
    
    Args:
        trace_id: Request-Trace-ID
        endpoint: API-Endpoint (z.B. "/api/tour/route-details")
        http_method: HTTP-Methode (GET, POST, etc.)
        status_code: HTTP-Status-Code (500, 422, etc.)
        error_type: Exception-Typ (z.B. "ValueError")
        module: Modul/Component (z.B. "subroute_generator")
        message: Fehlermeldung
        stacktrace: Vollständiger Stacktrace
        payload_snapshot: Gekürzte/Anonymisierte Nutzdaten
        environment: Umgebung (dev, prod, test)
        severity: Schweregrad (info, warn, error, critical)
        is_handled: Wurde der Fehler bewusst behandelt?
        user_agent: User-Agent-String
        ip_address: IP-Adresse
        request_duration_ms: Request-Dauer in Millisekunden
        
    Returns:
        ID des erstellten Events oder None bei Fehler
    """
    try:
        # Berechne Stack-Hash
        stack_hash = calculate_stack_hash(stacktrace or "")
        
        # Kürze Message
        message_short = (message or "")[:500]
        
        # Serialisiere Payload
        payload_json = None
        if payload_snapshot:
            try:
                # Anonymisiere sensible Daten
                anonymized = {}
                for key, value in payload_snapshot.items():
                    if key.lower() in ['password', 'token', 'api_key', 'secret']:
                        anonymized[key] = "***REDACTED***"
                    elif isinstance(value, str) and len(value) > 200:
                        anonymized[key] = value[:200] + "..."
                    else:
                        anonymized[key] = value
                payload_json = json.dumps(anonymized, default=str)
            except Exception:
                payload_json = None
        
        # Kürze Stacktrace (max. 5000 Zeichen)
        stacktrace_short = (stacktrace or "")[:5000] if stacktrace else None
        
        with ENGINE.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO error_events (
                        trace_id, endpoint, http_method, status_code, error_type, module,
                        message_short, stack_hash, stacktrace, payload_snapshot,
                        environment, severity, is_handled, user_agent, ip_address, request_duration_ms
                    ) VALUES (
                        :trace_id, :endpoint, :http_method, :status_code, :error_type, :module,
                        :message_short, :stack_hash, :stacktrace, :payload_snapshot,
                        :environment, :severity, :is_handled, :user_agent, :ip_address, :request_duration_ms
                    )
                """),
                {
                    "trace_id": trace_id,
                    "endpoint": endpoint,
                    "http_method": http_method,
                    "status_code": status_code,
                    "error_type": error_type,
                    "module": module,
                    "message_short": message_short,
                    "stack_hash": stack_hash,
                    "stacktrace": stacktrace_short,
                    "payload_snapshot": payload_json,
                    "environment": environment,
                    "severity": severity,
                    "is_handled": 1 if is_handled else 0,
                    "user_agent": user_agent,
                    "ip_address": ip_address,
                    "request_duration_ms": request_duration_ms,
                }
            )
            event_id = result.lastrowid
            
            # Versuche Pattern zu aktualisieren/erstellen (lazy, kann auch im Aggregator passieren)
            if stack_hash:
                try:
                    conn.execute(
                        text("""
                            INSERT OR IGNORE INTO error_patterns (
                                stack_hash, signature, first_seen, last_seen, occurrences,
                                last_status_code, primary_endpoint, component, status
                            ) VALUES (
                                :stack_hash, :signature, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, 1,
                                :status_code, :endpoint, :component, 'open'
                            )
                        """),
                        {
                            "stack_hash": stack_hash,
                            "signature": extract_error_signature(error_type or "Unknown", message_short, module),
                            "status_code": status_code,
                            "endpoint": endpoint,
                            "component": module or "unknown",
                        }
                    )
                    
                    # Aktualisiere Pattern (falls bereits vorhanden)
                    conn.execute(
                        text("""
                            UPDATE error_patterns
                            SET last_seen = CURRENT_TIMESTAMP,
                                occurrences = occurrences + 1,
                                last_status_code = :status_code,
                                updated_at = CURRENT_TIMESTAMP
                            WHERE stack_hash = :stack_hash
                        """),
                        {
                            "stack_hash": stack_hash,
                            "status_code": status_code,
                        }
                    )
                except Exception as e:
                    enhanced_logger.warning(f"Fehler beim Aktualisieren des Patterns: {e}")
            
            return event_id
            
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Loggen des Error-Events: {e}", exc_info=e)
        return None


def log_success_event(
    endpoint: str,
    http_method: str,
    status_code: int = 200,
    request_duration_ms: Optional[int] = None,
    environment: str = "dev",
) -> None:
    """
    Loggt ein erfolgreiches Event (für Erfolgs-Statistiken).
    
    Args:
        endpoint: API-Endpoint
        http_method: HTTP-Methode
        status_code: HTTP-Status-Code (normalerweise 200)
        request_duration_ms: Request-Dauer in Millisekunden
        environment: Umgebung
    """
    try:
        # Zeit-Bucket (Tag)
        time_bucket = datetime.now().strftime("%Y-%m-%d")
        
        with ENGINE.begin() as conn:
            # Upsert: Erstelle oder aktualisiere Statistik
            conn.execute(
                text("""
                    INSERT INTO success_stats (
                        endpoint, time_bucket, total_calls, success_calls, error_calls, avg_latency_ms
                    ) VALUES (
                        :endpoint, :time_bucket, 1, 1, 0, :latency
                    )
                    ON CONFLICT(endpoint, time_bucket) DO UPDATE SET
                        total_calls = total_calls + 1,
                        success_calls = success_calls + 1,
                        avg_latency_ms = (avg_latency_ms * (total_calls - 1) + :latency) / total_calls,
                        updated_at = CURRENT_TIMESTAMP
                """),
                {
                    "endpoint": endpoint,
                    "time_bucket": time_bucket,
                    "latency": request_duration_ms or 0,
                }
            )
    except Exception as e:
        enhanced_logger.warning(f"Fehler beim Loggen des Success-Events: {e}")


def get_error_patterns(
    status: Optional[str] = None,
    component: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Holt Fehler-Patterns aus der Datenbank.
    
    Args:
        status: Filter nach Status (open, investigating, fixed, ignored)
        component: Filter nach Component
        limit: Maximale Anzahl Ergebnisse
        
    Returns:
        Liste von Pattern-Dictionaries
    """
    try:
        with ENGINE.begin() as conn:
            query = "SELECT * FROM error_patterns WHERE 1=1"
            params = {}
            
            if status:
                query += " AND status = :status"
                params["status"] = status
            
            if component:
                query += " AND component = :component"
                params["component"] = component
            
            query += " ORDER BY occurrences DESC, last_seen DESC LIMIT :limit"
            params["limit"] = limit
            
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            patterns = []
            for row in rows:
                patterns.append({
                    "id": row[0],
                    "stack_hash": row[1],
                    "signature": row[2],
                    "first_seen": row[3],
                    "last_seen": row[4],
                    "occurrences": row[5],
                    "last_status_code": row[6],
                    "primary_endpoint": row[7],
                    "component": row[8],
                    "status": row[9],
                    "root_cause_hint": row[10],
                    "linked_rule_id": row[11],
                    "linked_lesson_id": row[12],
                })
            
            return patterns
            
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Abrufen der Error-Patterns: {e}", exc_info=e)
        return []


def get_error_events(
    pattern_id: Optional[int] = None,
    endpoint: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Holt Error-Events aus der Datenbank.
    
    Args:
        pattern_id: Filter nach Pattern-ID
        endpoint: Filter nach Endpoint
        limit: Maximale Anzahl Ergebnisse
        
    Returns:
        Liste von Event-Dictionaries
    """
    try:
        with ENGINE.begin() as conn:
            query = "SELECT * FROM error_events WHERE 1=1"
            params = {}
            
            if pattern_id:
                query += " AND pattern_id = :pattern_id"
                params["pattern_id"] = pattern_id
            
            if endpoint:
                query += " AND endpoint = :endpoint"
                params["endpoint"] = endpoint
            
            query += " ORDER BY timestamp DESC LIMIT :limit"
            params["limit"] = limit
            
            result = conn.execute(text(query), params)
            rows = result.fetchall()
            
            events = []
            for row in rows:
                events.append({
                    "id": row[0],
                    "timestamp": row[1],
                    "trace_id": row[2],
                    "endpoint": row[3],
                    "http_method": row[4],
                    "status_code": row[5],
                    "error_type": row[6],
                    "module": row[7],
                    "message_short": row[8],
                    "stack_hash": row[9],
                    "stacktrace": row[10],
                    "payload_snapshot": row[11],
                    "environment": row[12],
                    "severity": row[13],
                    "is_handled": bool(row[14]),
                    "pattern_id": row[15],
                })
            
            return events
            
    except Exception as e:
        enhanced_logger.error(f"Fehler beim Abrufen der Error-Events: {e}", exc_info=e)
        return []

