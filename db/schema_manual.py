from sqlalchemy import text
from db.core import ENGINE

SQL = """
CREATE TABLE IF NOT EXISTS geo_manual (
  address_norm TEXT PRIMARY KEY,
  reason TEXT,                 -- z.B. 'no_result', 'temp_error'
  note TEXT,
  status TEXT DEFAULT 'open',  -- 'open'|'closed'
  attempts INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def ensure_manual_schema():
    """Erstellt die geo_manual Tabelle falls sie nicht existiert."""
    with ENGINE.begin() as c:
        c.exec_driver_sql(SQL)
