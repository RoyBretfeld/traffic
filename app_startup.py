import os
from fs.safefs import init_policy
from db.schema import ensure_schema
from db.schema_fail import ensure_fail_schema

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
ensure_fail_schema()
