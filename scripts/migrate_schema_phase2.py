"""
Migration-Script für Phase 2 Schema-Erweiterung
Erstellt neue Tabellen: stats_monthly, routes, route_legs, osrm_cache

Features:
- Automatisches Backup vor Migration
- Rollback-Funktionalität
- Validierung der Migration
- Dry-Run Modus
"""
import sys
from pathlib import Path
from datetime import datetime
import sqlite3
import shutil
from typing import Tuple, Optional

# Projekt-Root hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from db.core import ENGINE
from db.schema_phase2 import PHASE2_SCHEMA_SQL
from sqlalchemy import text


def get_database_path() -> Path:
    """Ermittelt den Pfad zur Datenbank."""
    from settings import SETTINGS
    db_url = SETTINGS.database_url
    
    if db_url.startswith("sqlite:///"):
        db_path = Path(db_url.replace("sqlite:///", ""))
    elif db_url.startswith("sqlite://"):
        db_path = Path(db_url.replace("sqlite://", ""))
    else:
        raise ValueError(f"Unbekanntes Datenbank-URL-Format: {db_url}")
    
    return db_path.resolve()


def create_backup() -> Tuple[bool, Optional[Path]]:
    """
    Erstellt ein Backup der Datenbank vor der Migration.
    
    Returns:
        (success: bool, backup_path: Optional[Path])
    """
    try:
        db_path = get_database_path()
        
        if not db_path.exists():
            print(f"[ERROR] Datenbank nicht gefunden: {db_path}")
            return False, None
        
        # Backup-Verzeichnis
        backup_dir = PROJECT_ROOT / "data" / "backups" / "migrations"
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Backup-Dateiname
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"pre_phase2_migration_{timestamp}.db"
        backup_path = backup_dir / backup_filename
        
        # SQLite Backup (sicherer als shutil.copy)
        source_conn = sqlite3.connect(str(db_path), timeout=30.0)
        backup_conn = sqlite3.connect(str(backup_path), timeout=30.0)
        
        try:
            source_conn.backup(backup_conn)
            backup_conn.commit()
            backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            print(f"[OK] Backup erstellt: {backup_filename} ({backup_size:.2f} MB)")
            return True, backup_path
        finally:
            source_conn.close()
            backup_conn.close()
    
    except Exception as e:
        print(f"[ERROR] Backup-Fehler: {e}")
        return False, None


def check_tables_exist() -> dict:
    """
    Prüft welche Phase 2 Tabellen bereits existieren.
    
    Returns:
        dict mit {table_name: exists}
    """
    tables = {
        'stats_monthly': False
    }
    
    try:
        with ENGINE.connect() as conn:
            for table_name in tables.keys():
                result = conn.execute(text(f"""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='{table_name}'
                """))
                tables[table_name] = result.fetchone() is not None
    except Exception as e:
        print(f"[WARN] Fehler beim Pruefen der Tabellen: {e}")
    
    return tables


def migrate(dry_run: bool = False) -> Tuple[bool, str]:
    """
    Führt die Phase 2 Migration durch.
    
    Args:
        dry_run: Wenn True, wird nichts geändert, nur geprüft
    
    Returns:
        (success: bool, message: str)
    """
    try:
        # Prüfe welche Tabellen bereits existieren
        existing_tables = check_tables_exist()
        existing_count = sum(1 for exists in existing_tables.values() if exists)
        
        if existing_count == 1:
            return True, "[OK] Alle Phase 2 Tabellen existieren bereits. Migration nicht noetig."
        
        if existing_count > 0:
            existing_list = [name for name, exists in existing_tables.items() if exists]
            print(f"[WARN] Einige Tabellen existieren bereits: {', '.join(existing_list)}")
        
        if dry_run:
            print("[DRY-RUN] Wuerde folgende Tabellen erstellen:")
            for table_name, exists in existing_tables.items():
                if not exists:
                    print(f"  - {table_name}")
            return True, "Dry-Run erfolgreich. Keine Aenderungen vorgenommen."
        
        # Erstelle Backup
        print("[BACKUP] Erstelle Backup vor Migration...")
        backup_success, backup_path = create_backup()
        
        if not backup_success:
            return False, "Backup fehlgeschlagen. Migration abgebrochen."
        
        # Führe Migration durch
        print("[MIGRATION] Fuehre Migration durch...")
        with ENGINE.begin() as conn:
            # Teile SQL in CREATE TABLE und CREATE INDEX Statements
            statements = PHASE2_SCHEMA_SQL.split(';')
            create_table_statements = []
            create_index_statements = []
            created_tables = []
            created_indexes = []
            
            # Trenne CREATE TABLE und CREATE INDEX Statements
            for stmt in statements:
                stmt = stmt.strip()
                if not stmt or stmt.startswith('--'):
                    continue
                
                stmt_lower = stmt.lower()
                if 'create table' in stmt_lower:
                    create_table_statements.append(stmt)
                elif 'create index' in stmt_lower:
                    create_index_statements.append(stmt)
            
            # Führe zuerst alle CREATE TABLE Statements aus
            for stmt in create_table_statements:
                try:
                    conn.execute(text(stmt))
                    # Extrahiere Tabellenname
                    stmt_lower = stmt.lower()
                    if 'if not exists' in stmt_lower:
                        parts = stmt.split('if not exists', 1)[1].strip().split()
                        if parts:
                            table_name = parts[0].strip()
                            if table_name not in created_tables:
                                created_tables.append(table_name)
                                print(f"[OK] Tabelle erstellt: {table_name}")
                except Exception as e:
                    if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                        print(f"[WARN] Fehler beim Erstellen der Tabelle: {e}")
                        print(f"   Statement: {stmt[:100]}...")
            
            # Führe dann alle CREATE INDEX Statements aus
            for stmt in create_index_statements:
                try:
                    conn.execute(text(stmt))
                    # Extrahiere Indexname
                    stmt_lower = stmt.lower()
                    if 'if not exists' in stmt_lower:
                        parts = stmt.split('if not exists', 1)[1].strip().split()
                        if parts:
                            index_name = parts[0].strip()
                            if index_name not in created_indexes:
                                created_indexes.append(index_name)
                except Exception as e:
                    # Ignoriere Fehler wenn Index bereits existiert
                    if "already exists" not in str(e).lower() and "duplicate" not in str(e).lower():
                        print(f"[WARN] Fehler beim Erstellen des Index: {e}")
                        print(f"   Statement: {stmt[:100]}...")
        
        # Validiere Migration
        print("[VALIDATION] Validiere Migration...")
        final_tables = check_tables_exist()
        missing_tables = [name for name, exists in final_tables.items() if not exists]
        
        if missing_tables:
            return False, f"[ERROR] Migration unvollstaendig. Fehlende Tabellen: {', '.join(missing_tables)}"
        
        print(f"[OK] Migration erfolgreich!")
        print(f"   Erstellt: {len(created_tables)} Tabellen, {len(created_indexes)} Indizes")
        print(f"   Backup: {backup_path.name}")
        
        return True, f"Migration erfolgreich. Backup: {backup_path.name}"
    
    except Exception as e:
        return False, f"Migration fehlgeschlagen: {str(e)}"


def rollback(backup_path: Path) -> Tuple[bool, str]:
    """
    Rollback: Stellt die Datenbank aus einem Backup wieder her.
    
    Args:
        backup_path: Pfad zum Backup
    
    Returns:
        (success: bool, message: str)
    """
    try:
        if not backup_path.exists():
            return False, f"Backup nicht gefunden: {backup_path}"
        
        db_path = get_database_path()
        
        if not db_path.exists():
            return False, f"Datenbank nicht gefunden: {db_path}"
        
        print(f"[ROLLBACK] Stelle Datenbank aus Backup wieder her: {backup_path.name}")
        
        # Schließe alle Verbindungen (wichtig für SQLite)
        ENGINE.dispose()
        
        # Kopiere Backup zurück
        shutil.copy2(backup_path, db_path)
        
        print("[OK] Rollback erfolgreich!")
        return True, f"Rollback erfolgreich. Datenbank wiederhergestellt aus: {backup_path.name}"
    
    except Exception as e:
        return False, f"Rollback fehlgeschlagen: {str(e)}"


def main():
    """Hauptfunktion für Kommandozeilen-Aufruf."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Phase 2 Schema Migration")
    parser.add_argument("--dry-run", action="store_true", help="Nur prüfen, nichts ändern")
    parser.add_argument("--rollback", type=str, help="Rollback aus Backup (Pfad zum Backup)")
    parser.add_argument("--check", action="store_true", help="Nur prüfen welche Tabellen existieren")
    
    args = parser.parse_args()
    
    if args.check:
        print("[CHECK] Pruefe existierende Tabellen...")
        tables = check_tables_exist()
        for table_name, exists in tables.items():
            status = "[OK]" if exists else "[FEHLT]"
            print(f"  {status} {table_name}")
        return
    
    if args.rollback:
        backup_path = Path(args.rollback)
        if not backup_path.is_absolute():
            backup_path = PROJECT_ROOT / "data" / "backups" / "migrations" / args.rollback
        
        success, message = rollback(backup_path)
        print(message)
        sys.exit(0 if success else 1)
    
    # Migration durchführen
    success, message = migrate(dry_run=args.dry_run)
    print(message)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

