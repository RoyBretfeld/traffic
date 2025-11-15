#!/usr/bin/env python3
"""
FAMO TrafficApp - Einfacher Server-Start
Löst das PowerShell-Problem durch direkten Python-Start
"""

import sys
import os
from pathlib import Path

# Füge das Projektverzeichnis zum Python-Pfad hinzu
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "backend")) # NEU: Fügt das Backend-Verzeichnis hinzu

# Lade Umgebungsvariablen aus config.env falls vorhanden
config_env_path = project_root / "config.env"
if config_env_path.exists():
    with open(config_env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                key = key.strip()
                value = value.strip()
                # Setze nur wenn nicht bereits in Umgebung vorhanden
                if key and value and key not in os.environ:
                    os.environ[key] = value

    # Setze Standardwert für Debug-Routen, falls nicht explizit gesetzt
    os.environ.setdefault("ENABLE_DEBUG_ROUTES", "0")

    # Startup-Skript importieren (stellt DB-Schema sicher)
    import app_startup  # noqa: F401

# DB-Integrity-Check (Phase 1: Quick-Check beim Start)
from backend.config import cfg
if cfg("app:feature_flags:strict_health_checks", False):
    try:
        from db.core import ENGINE
        from sqlalchemy import text
        with ENGINE.connect() as conn:
            result = conn.execute(text("PRAGMA quick_check"))
            check_result = result.scalar()
            if check_result != "ok":
                print(f"[WARNUNG] DB-Integrity-Check fehlgeschlagen: {check_result}")
                print("   Die Datenbank koennte beschaedigt sein. Bitte Backup pruefen.")
            else:
                print("[OK] DB-Integrity-Check: OK")
    except Exception as e:
        print(f"[WARNUNG] DB-Integrity-Check konnte nicht ausgefuehrt werden: {e}")

import uvicorn
import logging

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)

if __name__ == "__main__":
    from db.core import ENGINE
    from pathlib import Path
    from backend.config import get_osrm_settings
    
    # Log Startup-Info
    log.info("=" * 70)
    log.info("FAMO TrafficApp - Server-Start")
    log.info("=" * 70)
    
    # DB-Info
    log.info("DB URL: %s", ENGINE.url)
    try:
        db_path = Path(ENGINE.url.database or "app.db").resolve()
        log.info("DB Pfad (resolv.): %s", db_path)
    except Exception as e:
        log.warning("DB Pfad konnte nicht ermittelt werden: %s", e)
    
    # OSRM-Info
    osrm_settings = get_osrm_settings()
    log.info("OSRM URL: %s", osrm_settings.OSRM_BASE_URL)
    log.info("OSRM Timeout: %s Sekunden", osrm_settings.OSRM_TIMEOUT_S)
    
    # Debug-Routen
    debug_enabled = os.getenv("ENABLE_DEBUG_ROUTES", "0") == "1"
    log.info("Debug-Routen: %s", "aktiviert" if debug_enabled else "deaktiviert")
    
    log.info("=" * 70)
    
    # Verwende factory=True für sauberes Hot-Reload
    uvicorn.run(
        "backend.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8111,
        reload=True,
        reload_dirs=["backend", "services", "routes", "db"],
        log_level="info",
    )
