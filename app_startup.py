import os
from fs.safefs import init_policy
from db.schema import ensure_schema
from db.schema_fail import ensure_fail_schema
from db.schema_alias import ensure_alias_schema
from db.schema_manual import ensure_manual_schema
from db.migrate_schema import migrate_geo_cache_schema

# Logging initialisieren
import logging_setup  # noqa: F401 (initialisiert Logging)

# PathPolicy initialisieren
init_policy(
    os.getenv("ORIG_DIR","./tourplaene"), 
    os.getenv("STAGING_DIR","./data/staging"), 
    os.getenv("OUTPUT_DIR","./data/output"),
    os.getenv("BACKUP_DIR","./routen")
)

# DB-Schema sicherstellen
ensure_schema()
# migrate_geo_cache_schema()  # ENTFERNT: redundant - ensure_schema() erstellt bereits alle Spalten
ensure_fail_schema()
ensure_alias_schema()
ensure_manual_schema()

# Touren- und Kunden-Tabellen sicherstellen (für Stats-Aggregation)
try:
    from backend.db.models import init_db
    init_db()
except ImportError:
    # Falls backend.db.schema nicht verfügbar, erstelle Tabellen manuell
    try:
        from db.core import ENGINE
        from sqlalchemy import text
        with ENGINE.begin() as conn:
            # Erstelle touren-Tabelle falls nicht vorhanden
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS touren (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tour_id TEXT NOT NULL,
                    datum TEXT NOT NULL,
                    kunden_ids TEXT,
                    dauer_min INTEGER,
                    distanz_km REAL,
                    fahrer TEXT,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """))
            # Erstelle kunden-Tabelle falls nicht vorhanden
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS kunden (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    adresse TEXT NOT NULL,
                    lat REAL,
                    lon REAL,
                    created_at TEXT DEFAULT (datetime('now'))
                )
            """))
            # Erstelle Indizes
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS touren_unique_by_date
                ON touren(tour_id, datum)
            """))
            # Performance-Index für monatliche Filterung
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_touren_datum
                ON touren(datum)
            """))
            conn.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS kunden_unique_name_addr
                ON kunden(name COLLATE NOCASE, adresse COLLATE NOCASE)
            """))
    except Exception as e:
        import logging
        logging.warning(f"Konnte touren/kunden Tabellen nicht erstellen: {e}")
    
    # Phase 2: Schema-Erweiterung (wenn Feature-Flag aktiviert)
    try:
        from db.schema_phase2 import ensure_phase2_schema
        ensure_phase2_schema()
    except ImportError:
        pass  # Phase 2 Schema-Modul nicht verfügbar