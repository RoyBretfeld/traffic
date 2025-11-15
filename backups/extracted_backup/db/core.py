from pathlib import Path
from sqlalchemy import create_engine, text, event
from settings import SETTINGS

ENGINE = create_engine(SETTINGS.database_url, pool_pre_ping=True, future=True)


def configure_sqlite_pragmas(conn):
    """Setzt SQLite PRAGMA-Einstellungen für bessere Performance und Robustheit."""
    if "sqlite" in SETTINGS.database_url.lower():
        # WAL-Mode für bessere Concurrency
        conn.execute(text("PRAGMA journal_mode=WAL"))
        # NORMAL synchronous: Balance zwischen Performance und Integrität
        conn.execute(text("PRAGMA synchronous=NORMAL"))
        # Busy-Timeout erhöhen
        conn.execute(text("PRAGMA busy_timeout=30000"))
        # Foreign Keys aktivieren
        conn.execute(text("PRAGMA foreign_keys=ON"))


# Event-Handler: Setze PRAGMA bei jeder SQLite-Verbindung
@event.listens_for(ENGINE, "connect")
def set_sqlite_pragmas(dbapi_conn, connection_record):
    """Automatisch PRAGMA-Einstellungen bei SQLite-Verbindungen setzen."""
    if "sqlite" in SETTINGS.database_url.lower():
        # dbapi_conn ist die rohe SQLite-Verbindung
        dbapi_conn.execute("PRAGMA journal_mode=WAL")
        dbapi_conn.execute("PRAGMA synchronous=NORMAL")
        dbapi_conn.execute("PRAGMA busy_timeout=30000")
        dbapi_conn.execute("PRAGMA foreign_keys=ON")


def apply_migration_001():
    """Führt Migration 001 aus: Indizes und weitere Optimierungen."""
    migration_file = Path(__file__).parent / "migrations" / "001_address_corrections.sql"
    if not migration_file.exists():
        return
    
    with ENGINE.begin() as conn:
        # Nur bei SQLite ausführen
        if "sqlite" not in SETTINGS.database_url.lower():
            return
        
        sql = migration_file.read_text(encoding="utf-8")
        # SQL in einzelne Statements aufteilen
        statements = [s.strip() for s in sql.split(";") if s.strip() and not s.strip().startswith("--")]
        
        for stmt in statements:
            try:
                conn.execute(text(stmt))
            except Exception as e:
                # PRAGMA-Anweisungen können fehlschlagen, wenn bereits gesetzt
                # Indizes können bereits existieren (CREATE INDEX IF NOT EXISTS)
                # Daher ignorieren wir Fehler hier
                pass

def db_health() -> dict:
    try:
        with ENGINE.begin() as conn:
            # Schema setzen (nur für PostgreSQL, SQLite unterstützt das nicht)
            if "sqlite" not in SETTINGS.database_url.lower():
                try:
                    conn.execute(text(f"SET search_path TO {SETTINGS.db_schema}"))
                except Exception:
                    pass
            
            # Version abfragen (DB-spezifisch)
            try:
                if "sqlite" in SETTINGS.database_url.lower():
                    version = conn.execute(text("SELECT sqlite_version()")).scalar_one()
                else:
                    version = conn.execute(text("SELECT version()")).scalar_one()
            except Exception:
                version = "unknown"
            
            # Zähle Tabellen im Zielschema (falls verfügbar)
            try:
                if "sqlite" in SETTINGS.database_url.lower():
                    tables = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table'")).scalar_one()
                else:
                    tables = conn.execute(text(
                        "select count(*) from information_schema.tables where table_schema=:s"),
                        {"s": SETTINGS.db_schema}
                    ).scalar_one()
            except Exception:
                tables = None
                
        return {"ok": True, "version": version, "schema": SETTINGS.db_schema, "tables": tables}
    except Exception as e:
        return {"ok": False, "error": str(e)}
