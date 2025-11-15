"""
Phase 2: Schema-Erweiterung
Neue Tabellen für Stats, Routes, Route-Legs, OSRM-Cache
"""
from sqlalchemy import text
from db.core import ENGINE

PHASE2_SCHEMA_SQL = """
-- Stats: Monatliche Statistiken
CREATE TABLE IF NOT EXISTS stats_monthly (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    month TEXT NOT NULL,
    tours_count INTEGER DEFAULT 0,
    stops_count INTEGER DEFAULT 0,
    total_km REAL DEFAULT 0.0,
    avg_stops_per_tour REAL DEFAULT 0.0,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(month)
);

CREATE INDEX IF NOT EXISTS idx_stats_monthly_month ON stats_monthly(month);
"""


def ensure_phase2_schema():
    """Erstellt Phase 2 Tabellen wenn Feature-Flag aktiviert ist."""
    try:
        from backend.config import cfg
        if not cfg("app:feature_flags:new_schema_enabled", False):
            return  # Feature-Flag deaktiviert
    except ImportError:
        return  # Config nicht verfügbar
    
    with ENGINE.begin() as conn:
        statements = PHASE2_SCHEMA_SQL.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    conn.execute(text(stmt))
                except Exception as e:
                    # Ignoriere Fehler wenn Tabelle/Index bereits existiert
                    if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                        import logging
                        logging.warning(f"Fehler beim Erstellen Phase 2 Schema: {e}")

