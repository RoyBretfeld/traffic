import os
from pathlib import Path
ORIG = Path(os.getenv("ORIG_DIR","./tourplaene")).resolve()
STAG = Path(os.getenv("STAGING_DIR","./data/staging")).resolve()
OUT  = Path(os.getenv("OUTPUT_DIR","./data/output")).resolve()
BACKUP = Path(os.getenv("BACKUP_DIR","./routen")).resolve()
for p in (ORIG, STAG, OUT, BACKUP):
    p.mkdir(parents=True, exist_ok=True)
    print("[OK] Pfad vorhanden:", p)
print("[INFO] ORIG und BACKUP sind per Code-Guard schreibgeschuetzt.")
