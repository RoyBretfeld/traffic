"""
Datenbank-Schema für Error-Learning-System (KI-Lernpfad).

Erweitert das Basis-Schema um Tabellen für:
- error_events: Rohdaten aller Fehler-Ereignisse
- error_patterns: Gruppierte Fehlermuster
- error_feedback: Feedback von Dev/KI zu Patterns
- success_stats: Aggregierte Erfolgs-Statistiken
"""

from sqlalchemy import text

# Schema für Error-Learning-Tabellen
ERROR_LEARNING_SCHEMA = """
-- Tabelle: error_events - Rohdaten aller Fehler-Ereignisse
CREATE TABLE IF NOT EXISTS error_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    trace_id TEXT,
    endpoint TEXT,
    http_method TEXT,
    status_code INTEGER,
    error_type TEXT,
    module TEXT,
    message_short TEXT,
    stack_hash TEXT,
    stacktrace TEXT,
    payload_snapshot TEXT,
    environment TEXT DEFAULT 'dev',
    severity TEXT DEFAULT 'error',
    is_handled INTEGER DEFAULT 0,
    pattern_id INTEGER,
    user_agent TEXT,
    ip_address TEXT,
    request_duration_ms INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indizes für error_events
CREATE INDEX IF NOT EXISTS idx_error_events_timestamp ON error_events(timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_error_events_trace_id ON error_events(trace_id);
CREATE INDEX IF NOT EXISTS idx_error_events_endpoint ON error_events(endpoint);
CREATE INDEX IF NOT EXISTS idx_error_events_stack_hash ON error_events(stack_hash);
CREATE INDEX IF NOT EXISTS idx_error_events_pattern_id ON error_events(pattern_id);
CREATE INDEX IF NOT EXISTS idx_error_events_status_code ON error_events(status_code);
CREATE INDEX IF NOT EXISTS idx_error_events_module ON error_events(module);

-- Tabelle: error_patterns - Gruppierte Fehlermuster
CREATE TABLE IF NOT EXISTS error_patterns (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    stack_hash TEXT UNIQUE NOT NULL,
    signature TEXT NOT NULL,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    occurrences INTEGER DEFAULT 1,
    last_status_code INTEGER,
    primary_endpoint TEXT,
    component TEXT,
    status TEXT DEFAULT 'open',
    root_cause_hint TEXT,
    linked_rule_id TEXT,
    linked_lesson_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indizes für error_patterns
CREATE INDEX IF NOT EXISTS idx_error_patterns_stack_hash ON error_patterns(stack_hash);
CREATE INDEX IF NOT EXISTS idx_error_patterns_status ON error_patterns(status);
CREATE INDEX IF NOT EXISTS idx_error_patterns_component ON error_patterns(component);
CREATE INDEX IF NOT EXISTS idx_error_patterns_last_seen ON error_patterns(last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_error_patterns_occurrences ON error_patterns(occurrences DESC);

-- Tabelle: error_feedback - Feedback von Dev/KI zu Patterns
CREATE TABLE IF NOT EXISTS error_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pattern_id INTEGER NOT NULL,
    source TEXT NOT NULL,
    note TEXT,
    resolution_status TEXT DEFAULT 'todo',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (pattern_id) REFERENCES error_patterns(id) ON DELETE CASCADE
);

-- Indizes für error_feedback
CREATE INDEX IF NOT EXISTS idx_error_feedback_pattern_id ON error_feedback(pattern_id);
CREATE INDEX IF NOT EXISTS idx_error_feedback_resolution_status ON error_feedback(resolution_status);
CREATE INDEX IF NOT EXISTS idx_error_feedback_source ON error_feedback(source);

-- Tabelle: success_stats - Aggregierte Erfolgs-Statistiken
CREATE TABLE IF NOT EXISTS success_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    endpoint TEXT NOT NULL,
    time_bucket TEXT NOT NULL,
    total_calls INTEGER DEFAULT 0,
    success_calls INTEGER DEFAULT 0,
    error_calls INTEGER DEFAULT 0,
    avg_latency_ms REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(endpoint, time_bucket)
);

-- Indizes für success_stats
CREATE INDEX IF NOT EXISTS idx_success_stats_endpoint ON success_stats(endpoint);
CREATE INDEX IF NOT EXISTS idx_success_stats_time_bucket ON success_stats(time_bucket DESC);
CREATE INDEX IF NOT EXISTS idx_success_stats_updated_at ON success_stats(updated_at DESC);
"""

def ensure_error_learning_schema(conn):
    """
    Idempotent: Stellt sicher, dass alle Error-Learning-Tabellen existieren.
    
    WICHTIG: SQLite kann nur ein Statement auf einmal ausführen!
    """
    try:
        # SQLite kann nur ein Statement auf einmal ausführen
        # Teile ERROR_LEARNING_SCHEMA in einzelne Statements
        statements = ERROR_LEARNING_SCHEMA.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                try:
                    conn.execute(text(stmt))
                except Exception as stmt_error:
                    # Einzelnes Statement-Fehler (z.B. Tabelle existiert bereits)
                    # Logge nur im Debug-Modus, nicht als Fehler
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.debug(f"[SCHEMA] Statement-Fehler (kann ignoriert werden): {stmt_error}")
                    # Weiter mit nächstem Statement
                    continue
        conn.commit()
    except Exception as e:
        # Allgemeiner Fehler
        import logging
        logging.getLogger(__name__).warning(f"[SCHEMA] Fehler beim Erstellen der Error-Learning-Tabellen: {e}")
        # Versuche trotzdem weiter (Tabellen könnten bereits existieren)
        pass

