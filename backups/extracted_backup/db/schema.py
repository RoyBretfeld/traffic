try:
    from sqlalchemy import text
except ImportError:
    # Fallback für SQLAlchemy 1.x oder andere Versionen
    try:
        from sqlalchemy.sql import text
    except ImportError:
        raise ImportError("SQLAlchemy 'text' kann nicht importiert werden. Bitte SQLAlchemy installieren: pip install sqlalchemy")

try:
    from db.core import ENGINE
except ImportError:
    # Fallback für alternative Import-Wege
    import sys
    from pathlib import Path
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    from db.core import ENGINE

# Minimal‑Schema – idempotent; funktioniert auf Postgres & SQLite
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS geo_cache (
  address_norm TEXT PRIMARY KEY,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  source TEXT DEFAULT 'geocoded',
  precision TEXT,
  region_ok INTEGER,
  first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  by_user TEXT,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Manual-Queue Tabelle für fehlgeschlagene Geocodes
CREATE TABLE IF NOT EXISTS manual_queue (
  id INTEGER PRIMARY KEY,
  address_norm TEXT NOT NULL,
  raw_address TEXT,
  reason TEXT,
  note TEXT,
  status TEXT DEFAULT 'open',
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS ix_manual_queue_created ON manual_queue(created_at DESC);
CREATE INDEX IF NOT EXISTS ix_manual_queue_address ON manual_queue(address_norm);
"""

def ensure_schema():
    with ENGINE.begin() as conn:
        # SQLite kann nur eine Anweisung auf einmal ausführen
        statements = SCHEMA_SQL.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                conn.exec_driver_sql(stmt)

        try:
            conn.exec_driver_sql("ALTER TABLE manual_queue ADD COLUMN note TEXT")
        except Exception:
            pass

        try:
            conn.exec_driver_sql("ALTER TABLE manual_queue ADD COLUMN status TEXT DEFAULT 'open'")
        except Exception:
            pass
        
        # Migration: precision Spalte hinzufügen falls fehlt
        try:
            conn.exec_driver_sql("ALTER TABLE geo_cache ADD COLUMN precision TEXT")
        except Exception:
            pass  # Spalte existiert bereits
        
        # Migration: region_ok Spalte hinzufügen falls fehlt
        try:
            conn.exec_driver_sql("ALTER TABLE geo_cache ADD COLUMN region_ok INTEGER")
        except Exception:
            pass  # Spalte existiert bereits
        
        # Migration: first_seen Spalte hinzufügen falls fehlt
        try:
            conn.exec_driver_sql("ALTER TABLE geo_cache ADD COLUMN first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception:
            pass  # Spalte existiert bereits
        
        # Migration: last_seen Spalte hinzufügen falls fehlt
        try:
            conn.exec_driver_sql("ALTER TABLE geo_cache ADD COLUMN last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        except Exception:
            pass  # Spalte existiert bereits
    
    # Migration 001 ausführen (Indizes und weitere Optimierungen)
    try:
        from db.core import apply_migration_001
        apply_migration_001()
    except ImportError:
        # Migration-Funktion nicht vorhanden - optional, weitermachen
        pass
