from sqlalchemy import create_engine, text
from settings import SETTINGS

ENGINE = create_engine(SETTINGS.database_url, pool_pre_ping=True, future=True)

def db_health() -> dict:
    try:
        with ENGINE.begin() as conn:
            # Schema setzen (wenn DB das unterstützt)
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
