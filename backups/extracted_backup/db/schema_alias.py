"""
Alias-Schema für FAMO TrafficApp
Erstellt geo_alias und geo_audit Tabellen für Vorschlag-Übernahme ohne Daten-Duplikate
"""
from sqlalchemy import text
from db.core import ENGINE

def ensure_alias_schema():
    """Erstellt die Alias-Tabellen idempotent."""
    with ENGINE.begin() as c:
        # geo_alias Tabelle
        c.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS geo_alias (
          address_norm TEXT PRIMARY KEY,          -- die problematische/abweichende Schreibweise
          canonical_norm TEXT NOT NULL,           -- verweist auf vorhandenen Cache-Eintrag (address_norm in geo_cache)
          created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          created_by TEXT
        );
        """)
        
        # geo_audit Tabelle
        c.exec_driver_sql("""
        CREATE TABLE IF NOT EXISTS geo_audit (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
          action TEXT NOT NULL,                   -- z.B. 'alias_set'
          query TEXT,
          canonical TEXT,
          by_user TEXT
        );
        """)
