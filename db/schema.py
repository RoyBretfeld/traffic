from sqlalchemy import text
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
