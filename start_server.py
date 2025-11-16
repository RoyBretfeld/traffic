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

    # Venv Health Check (PRÜFT UND REPARIERT AUTOMATISCH)
    # WICHTIG: Logger muss VOR Health Check definiert sein!
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    try:
        from backend.utils.venv_health_check import run_venv_health_check
        logger.info("Führe Venv Health Check durch...")
        venv_ok = run_venv_health_check(auto_fix=True)
        if not venv_ok:
            logger.error("=" * 70)
            logger.error("VENV HEALTH CHECK FEHLGESCHLAGEN")
            logger.error("=" * 70)
            logger.error("Der Server kann nicht gestartet werden.")
            logger.error("")
            logger.error("Bitte behebe die Probleme manuell:")
            logger.error("  1. Venv aktivieren: .\\venv\\Scripts\\Activate.ps1")
            logger.error("  2. Oder venv neu erstellen: .\\recreate_venv.ps1")
            logger.error("")
            logger.error("Dann Server erneut starten.")
            logger.error("=" * 70)
            sys.exit(1)
        logger.info("[OK] Venv Health Check: OK")
    except ImportError as e:
        logger.warning(f"Venv Health Check nicht verfügbar: {e}")
        logger.warning("Server startet ohne Health Check (nicht empfohlen)")
    except Exception as e:
        logger.error(f"Venv Health Check fehlgeschlagen: {e}")
        logger.error("Server startet trotzdem (kann zu Fehlern führen)")
    
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
import threading
import time
try:
    import requests
except ImportError:
    requests = None  # Optional für Port-Check

# Setup Logging (FRÜH, damit Health Check loggen kann)
# WICHTIG: Wird auch in Health Check verwendet, daher hier definiert
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
log = logging.getLogger(__name__)
logger = log  # Alias für Kompatibilität

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
    
    # Startup-Log-Datei für Port-Check
    from datetime import datetime
    from pathlib import Path
    startup_log_dir = Path("logs")
    startup_log_dir.mkdir(exist_ok=True)
    port_check_log_path = startup_log_dir / f"port_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    
    # Port-Bindungs-Verifizierung nach Start
    def verify_port_binding():
        """Prüft ob Port 8111 nach Start erreichbar ist."""
        check_start = time.time()
        
        # Log in Datei
        with open(port_check_log_path, 'w', encoding='utf-8') as f:
            f.write(f"Port-Check gestartet: {datetime.now().isoformat()}\n")
            f.write("=" * 70 + "\n")
        
        if requests is None:
            log.warning("[PORT-CHECK] requests-Modul nicht verfügbar - Port-Check übersprungen")
            with open(port_check_log_path, 'a', encoding='utf-8') as f:
                f.write("FEHLER: requests-Modul nicht verfügbar\n")
            return False
        
        max_attempts = 20  # 20 Sekunden
        log.info(f"[PORT-CHECK] 🔍 Starte Port-Verifizierung (max. {max_attempts}s)...")
        
        with open(port_check_log_path, 'a', encoding='utf-8') as f:
            f.write(f"Max. Versuche: {max_attempts}\n")
            f.write(f"Ziel: http://127.0.0.1:8111/health\n")
            f.write("-" * 70 + "\n")
        
        for i in range(max_attempts):
            elapsed = time.time() - check_start
            try:
                with open(port_check_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"[{i+1}/{max_attempts}] Versuch nach {elapsed:.1f}s... ")
                
                response = requests.get("http://127.0.0.1:8111/health", timeout=2)
                if response.status_code == 200:
                    elapsed_total = time.time() - check_start
                    log.info(f"[PORT-CHECK] ✅ Port 8111 ist nach {elapsed_total:.1f}s erreichbar (Versuch {i+1})")
                    with open(port_check_log_path, 'a', encoding='utf-8') as f:
                        f.write(f"✅ ERFOLG! Status: {response.status_code}\n")
                        f.write(f"Gesamtzeit: {elapsed_total:.2f}s\n")
                    return True
                else:
                    with open(port_check_log_path, 'a', encoding='utf-8') as f:
                        f.write(f"Status: {response.status_code} (nicht 200)\n")
            except requests.exceptions.ConnectionError as e:
                with open(port_check_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"❌ ConnectionError: {e}\n")
            except requests.exceptions.Timeout as e:
                with open(port_check_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"❌ Timeout: {e}\n")
            except Exception as e:
                with open(port_check_log_path, 'a', encoding='utf-8') as f:
                    f.write(f"❌ Fehler: {type(e).__name__}: {e}\n")
            
            time.sleep(1)
        
        elapsed_total = time.time() - check_start
        log.error(f"[PORT-CHECK] ❌ Port 8111 ist nach {elapsed_total:.1f}s nicht erreichbar - möglicherweise blockiert")
        with open(port_check_log_path, 'a', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write(f"❌ FEHLGESCHLAGEN nach {max_attempts} Versuchen ({elapsed_total:.1f}s)\n")
            f.write("Mögliche Ursachen:\n")
            f.write("  - Startup-Event blockiert noch\n")
            f.write("  - Port-Bindung fehlgeschlagen\n")
            f.write("  - Firewall blockiert Port\n")
            f.write(f"Log-Datei: {port_check_log_path}\n")
        return False
    
    # Starte Port-Verifizierung in separatem Thread (nach 5 Sekunden)
    log.info(f"[PORT-CHECK] 📝 Port-Check-Log: {port_check_log_path}")
    port_check_thread = threading.Thread(target=lambda: (time.sleep(5), verify_port_binding()), daemon=True)
    port_check_thread.start()
    
    # Verwende factory=True für sauberes Hot-Reload
    # WICHTIG: reload=True kann zu Timing-Problemen führen und Server nach Reload zum Absturz bringen
    # Deaktiviere Reload-Mode für Stabilität (Server muss manuell neu gestartet werden)
    # Falls Hot-Reload benötigt wird: ENABLE_RELOAD=1 setzen, aber dann Server nach Änderungen manuell prüfen
    reload_enabled = os.getenv("ENABLE_RELOAD", "0") == "1"  # Standard: deaktiviert
    log.info(f"Reload-Mode: {'aktiviert' if reload_enabled else 'deaktiviert (Standard für Stabilität)'}")
    
    uvicorn.run(
        "backend.app:create_app",
        factory=True,
        host="127.0.0.1",
        port=8111,
        reload=reload_enabled,
        reload_dirs=["backend", "services", "routes", "db"] if reload_enabled else None,
        log_level="info",
    )
