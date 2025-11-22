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

CREATE TABLE IF NOT EXISTS geo_fail (
  id INTEGER PRIMARY KEY,
  address_norm TEXT NOT NULL UNIQUE,
  raw_address TEXT,
  reason TEXT,
  retries INTEGER DEFAULT 0,
  last_attempt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  next_attempt INTEGER,
  first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- WICHTIG: Indizes für geo_fail werden in ensure_geo_fail_next_attempt() erstellt
-- (nachdem sichergestellt wurde, dass die Spalten existieren)
CREATE UNIQUE INDEX IF NOT EXISTS idx_geo_fail_address_norm ON geo_fail(address_norm);

-- Systemregeln Audit-Tabelle für Änderungshistorie
CREATE TABLE IF NOT EXISTS system_rules_audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  changed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  changed_by TEXT,
  changed_by_ip TEXT,
  old_values TEXT,
  new_values TEXT,
  changed_fields TEXT
);

CREATE INDEX IF NOT EXISTS idx_system_rules_audit_changed_at ON system_rules_audit(changed_at DESC);
"""

def column_exists(conn, table, column):
    q = text("SELECT 1 FROM pragma_table_info(:t) WHERE name=:c")
    return conn.execute(q, {"t": table, "c": column}).fetchone() is not None

def table_exists(conn, table: str) -> bool:
    cur = conn.exec_driver_sql(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None

def ensure_geo_fail_next_attempt(conn) -> None:
    """Idempotent: Stellt sicher, dass geo_fail.next_attempt + first_seen + Indizes existieren."""
    if not table_exists(conn, "geo_fail"):
        import logging
        logging.getLogger(__name__).warning("[WARN] Tabelle geo_fail existiert nicht für ensure_geo_fail_next_attempt. Wird beim restlichen SCHEMA_SQL erstellt.")
        return
    
    # Spalte next_attempt hinzufügen (falls nicht vorhanden)
    if not column_exists(conn, "geo_fail", "next_attempt"):
        conn.exec_driver_sql("ALTER TABLE geo_fail ADD COLUMN next_attempt INTEGER")
        import logging
        logging.getLogger(__name__).info("Spalte 'next_attempt' (INTEGER) zu geo_fail hinzugefügt.")
    else:
        import logging
        logging.getLogger(__name__).info("Spalte 'next_attempt' ist bereits vorhanden in geo_fail.")
    
    # Spalte first_seen hinzufügen (falls nicht vorhanden)
    if not column_exists(conn, "geo_fail", "first_seen"):
        conn.exec_driver_sql("ALTER TABLE geo_fail ADD COLUMN first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP")
        import logging
        logging.getLogger(__name__).info("Spalte 'first_seen' (TIMESTAMP) zu geo_fail hinzugefügt.")
    else:
        import logging
        logging.getLogger(__name__).info("Spalte 'first_seen' ist bereits vorhanden in geo_fail.")

    # Indizes erstellen (nur wenn Spalten existieren)
    if column_exists(conn, "geo_fail", "next_attempt"):
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_geo_fail_next_attempt ON geo_fail(next_attempt)"
        )
        import logging
        logging.getLogger(__name__).info("Index geprüft/angelegt: idx_geo_fail_next_attempt.")
    
    if column_exists(conn, "geo_fail", "first_seen"):
        conn.exec_driver_sql(
            "CREATE INDEX IF NOT EXISTS idx_geo_fail_first_seen ON geo_fail(first_seen)"
        )
        import logging
        logging.getLogger(__name__).info("Index geprüft/angelegt: idx_geo_fail_first_seen.")

def ensure_schema():
    with ENGINE.begin() as conn:
        # SQLite kann nur eine Anweisung auf einmal ausführen
        statements = SCHEMA_SQL.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt:
                conn.exec_driver_sql(stmt)
        
        # **Härtung**: nach Basisschema gezielt Altbestände upgraden
        try:
            ensure_geo_fail_next_attempt(conn)
            # Prüfe, ob Einträge vorhanden sind - nur dann loggen
            result = conn.execute(text("SELECT COUNT(*) FROM geo_fail"))
            count = result.scalar()
            import logging
            if count > 0:
                logging.getLogger(__name__).info(f"[SCHEMA] geo_fail Tabelle verifiziert ({count} Einträge vorhanden)")
            # Keine Meldung wenn Tabelle leer - bei 100% Erkennungsrate ist das normal
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[SCHEMA] geo_fail Härtung fehlgeschlagen (kann ignoriert werden, wenn Tabelle neu): {e}")

        # Migrationen für manual_queue
        if not column_exists(conn, 'manual_queue', 'note'):
            conn.exec_driver_sql("ALTER TABLE manual_queue ADD COLUMN note TEXT")
            import logging
            logging.getLogger(__name__).info("Spalte 'note' zu manual_queue hinzugefügt.")

        if not column_exists(conn, 'manual_queue', 'status'):
            conn.exec_driver_sql("ALTER TABLE manual_queue ADD COLUMN status TEXT DEFAULT 'open'")
            import logging
            logging.getLogger(__name__).info("Spalte 'status' zu manual_queue hinzugefügt.")

        # Migration: ALTER TABLE statements for geo_cache (Python handled, not in SCHEMA_SQL)
        if not column_exists(conn, 'geo_cache', 'precision'):
            conn.exec_driver_sql("ALTER TABLE geo_cache ADD COLUMN precision TEXT")
            import logging
            logging.getLogger(__name__).info("Spalte 'precision' zu geo_cache hinzugefügt.")

        if not column_exists(conn, 'geo_cache', 'region_ok'):
            conn.exec_driver_sql("ALTER TABLE geo_cache ADD COLUMN region_ok INTEGER")
            import logging
            logging.getLogger(__name__).info("Spalte 'region_ok' zu geo_cache hinzugefügt.")

        # `first_seen` und `last_seen` in `geo_cache` sind bereits in SCHEMA_SQL definiert. 
        # Keine weiteren ALTER TABLE hier nötig.

    # Migration 001 ausführen (Indizes und weitere Optimierungen)
    try:
        from db.core import apply_migration_001
        apply_migration_001()
    except ImportError:
        # Migration-Funktion nicht vorhanden - optional, weitermachen
        pass
    
    # Phase 2 Migration: Routing-Stats & OSRM-Cache
    try:
        from pathlib import Path
        migration_path = Path(__file__).parent.parent / "docs" / "migrations" / "2025-11-09_add_routing_stats.sql"
        if migration_path.exists():
            migration_sql = migration_path.read_text(encoding="utf-8")
            with ENGINE.begin() as conn:
                # Prüfe ob Migration bereits angewendet wurde
                try:
                    conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS __schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT)")
                    cur = conn.exec_driver_sql("SELECT 1 FROM __schema_migrations WHERE name=?", ("2025-11-09_add_routing_stats",))
                    if cur.fetchone():
                        # Migration bereits angewendet
                        pass
                    else:
                        # Wende Migration an
                        statements = migration_sql.split(';')
                        for stmt in statements:
                            stmt = stmt.strip()
                            if stmt:
                                conn.exec_driver_sql(stmt)
                        # Markiere Migration als angewendet
                        conn.exec_driver_sql(
                            "INSERT INTO __schema_migrations(name, applied_at) VALUES(?, datetime('now'))",
                            ("2025-11-09_add_routing_stats",)
                        )
                        import logging
                        logging.getLogger(__name__).info("Phase 2 Migration angewendet: 2025-11-09_add_routing_stats")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Phase 2 Migration fehlgeschlagen: {e}")
    except Exception as e:
        import logging
        logging.getLogger(__name__).debug(f"Phase 2 Migration nicht verfügbar: {e}")
    
    # Phase 3: Error-Learning-Schema (KI-Lernpfad)
    try:
        from db.schema_error_learning import ensure_error_learning_schema
        with ENGINE.begin() as conn:
            ensure_error_learning_schema(conn)
        import logging
        logging.getLogger(__name__).info("[SCHEMA] Error-Learning-Tabellen erstellt/verifiziert")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning(f"[SCHEMA] Error-Learning-Schema fehlgeschlagen: {e}")
    
    # Migration 020: Tour-Import & Vorladen
    try:
        from pathlib import Path
        migration_path = Path(__file__).parent.parent / "db" / "migrations" / "020_import_batches.sql"
        if migration_path.exists():
            migration_sql = migration_path.read_text(encoding="utf-8")
            with ENGINE.begin() as conn:
                # Prüfe ob Migration bereits angewendet wurde
                try:
                    conn.exec_driver_sql("CREATE TABLE IF NOT EXISTS __schema_migrations (name TEXT PRIMARY KEY, applied_at TEXT)")
                    cur = conn.exec_driver_sql("SELECT 1 FROM __schema_migrations WHERE name=?", ("020_import_batches",))
                    if cur.fetchone():
                        # Migration bereits angewendet
                        pass
                    else:
                        # Wende Migration an
                        # WICHTIG: Führe Statements in der richtigen Reihenfolge aus
                        # (erst Tabellen, dann Indizes)
                        statements = migration_sql.split(';')
                        for stmt in statements:
                            stmt = stmt.strip()
                            if stmt and not stmt.startswith('--') and not stmt.upper().startswith('PRAGMA'):
                                try:
                                    conn.exec_driver_sql(stmt)
                                except Exception as stmt_error:
                                    # Wenn Index-Erstellung fehlschlägt (Tabelle existiert nicht), 
                                    # versuche es später nochmal nach Tabellen-Erstellung
                                    if 'INDEX' in stmt.upper() and 'no such table' in str(stmt_error).lower():
                                        import logging
                                        logging.getLogger(__name__).warning(f"Migration 020: Index-Erstellung fehlgeschlagen (Tabelle existiert noch nicht): {stmt[:50]}... - wird später erneut versucht")
                                    else:
                                        raise  # Andere Fehler weiterwerfen
                        
                        # PRAGMA-Statements separat ausführen (nach Tabellen-Erstellung)
                        for stmt in statements:
                            stmt = stmt.strip()
                            if stmt and stmt.upper().startswith('PRAGMA'):
                                try:
                                    conn.exec_driver_sql(stmt)
                                except Exception:
                                    pass  # PRAGMA-Fehler sind nicht kritisch
                        
                        # Markiere Migration als angewendet
                        conn.exec_driver_sql(
                            "INSERT INTO __schema_migrations(name, applied_at) VALUES(?, datetime('now'))",
                            ("020_import_batches",)
                        )
                        import logging
                        logging.getLogger(__name__).info("Migration 020 angewendet: Tour-Import & Vorladen")
                except Exception as e:
                    import logging
                    logging.getLogger(__name__).warning(f"Migration 020 fehlgeschlagen: {e}")
    except Exception as e:
        import logging
        logging.getLogger(__name__).debug(f"Migration 020 nicht verfügbar: {e}")