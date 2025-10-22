import os
from pathlib import Path
from fs.safefs import init_policy
from db.schema import ensure_schema
from db.schema_fail import ensure_fail_schema
from db.schema_alias import ensure_alias_schema
from db.schema_manual import ensure_manual_schema
from db.migrate_schema import migrate_geo_cache_schema

# Logging initialisieren
import logging_setup  # noqa: F401 (initialisiert Logging)

# PathPolicy initialisieren
init_policy(
    os.getenv("ORIG_DIR","./tourplaene"), 
    os.getenv("STAGING_DIR","./data/staging"), 
    os.getenv("OUTPUT_DIR","./data/output"),
    os.getenv("BACKUP_DIR","./routen")
)

# DB-Schema sicherstellen
ensure_schema()
# migrate_geo_cache_schema()  # ENTFERNT: redundant - ensure_schema() erstellt bereits alle Spalten
ensure_fail_schema()
ensure_alias_schema()
ensure_manual_schema()

# Google Drive Sync konfigurieren
drive_path = os.getenv("GOOGLE_DRIVE_PATH", "")
if drive_path:
    from services.temp_cleanup import set_drive_mount_point
    try:
        path = Path(drive_path)
        if path.exists():
            set_drive_mount_point(drive_path)
            print(f"[STARTUP] Google Drive konfiguriert: {drive_path}")
        else:
            print(f"[STARTUP] ⚠️  Google Drive Pfad existiert nicht: {drive_path}")
    except Exception as e:
        print(f"[STARTUP] ⚠️  Google Drive Konfiguration fehlgeschlagen: {e}")
else:
    print(f"[STARTUP] ℹ️  Google Drive nicht konfiguriert (GOOGLE_DRIVE_PATH nicht gesetzt)")
