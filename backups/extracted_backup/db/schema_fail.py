from sqlalchemy import text
from db.core import ENGINE

SQL = """
CREATE TABLE IF NOT EXISTS geo_fail (
  address_norm TEXT PRIMARY KEY,
  reason TEXT,
  until TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def ensure_fail_schema():
    """Erstellt das geo_fail Schema idempotent."""
    try:
        with ENGINE.begin() as c:
            c.exec_driver_sql(SQL)
        print("[SCHEMA] geo_fail Tabelle erstellt/verifiziert")
    except Exception as e:
        print(f"[SCHEMA-ERROR] Fehler beim Erstellen der geo_fail Tabelle: {e}")
        raise
