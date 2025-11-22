"""
Benutzer-Schema für Authentifizierung und Benutzerverwaltung.
Erstellt users, user_sessions und user_audit_log Tabellen.
"""
from sqlalchemy import text
from db.core import ENGINE
import logging

logger = logging.getLogger(__name__)


def ensure_users_schema():
    """Erstellt Benutzer-Schema falls nicht vorhanden."""
    try:
        from pathlib import Path
        migration_path = Path(__file__).parent.parent / "db" / "migrations" / "022_users_table.sql"
        
        if not migration_path.exists():
            logger.warning(f"[SCHEMA] Migration 022_users_table.sql nicht gefunden: {migration_path}")
            return
        
        migration_sql = migration_path.read_text(encoding="utf-8")
        
        with ENGINE.begin() as conn:
            # Führe Migration aus (SQLite kann mehrere Statements)
            statements = [s.strip() for s in migration_sql.split(';') if s.strip()]
            for stmt in statements:
                if stmt:
                    try:
                        conn.execute(text(stmt))
                    except Exception as e:
                        # Ignoriere "already exists" Fehler
                        if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                            logger.warning(f"[SCHEMA] Fehler bei Statement: {e}")
            
            # Prüfe ob Tabelle existiert
            result = conn.execute(text("SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='users'"))
            if result.scalar() > 0:
                logger.info("[SCHEMA] ✅ Benutzer-Tabellen erstellt/verifiziert")
            else:
                logger.warning("[SCHEMA] ⚠️ Benutzer-Tabellen konnten nicht erstellt werden")
    
    except Exception as e:
        logger.error(f"[SCHEMA] Fehler beim Erstellen des Benutzer-Schemas: {e}", exc_info=True)


if __name__ == "__main__":
    ensure_users_schema()

