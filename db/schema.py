from sqlalchemy import text
from db.core import ENGINE

# Minimal‑Schema – idempotent; funktioniert auf Postgres & SQLite
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS geo_cache (
  address_norm TEXT PRIMARY KEY,
  lat DOUBLE PRECISION NOT NULL,
  lon DOUBLE PRECISION NOT NULL,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
-- Optional für Postgres: schneller Lookup auf address_norm (LOWER)
-- CREATE INDEX IF NOT EXISTS idx_geo_cache_addr ON geo_cache (address_norm);
"""

def ensure_schema():
    with ENGINE.begin() as conn:
        conn.exec_driver_sql(SCHEMA_SQL)
