"""
Konfigurations-Loader für app.yaml
Erweitert: Pydantic Settings für OSRM-Konfiguration (Phase 1 Runbook)
"""
from pathlib import Path
import yaml
import logging
import os
from typing import Optional
logger = logging.getLogger(__name__)

_CFG = None


def load_config():
    """Lädt app.yaml und cached das Ergebnis."""
    global _CFG
    if _CFG is None:
        p = Path("config/app.yaml")
        if not p.exists():
            logger.warning(f"config/app.yaml nicht gefunden, verwende Defaults")
            _CFG = {}
        else:
            try:
                with p.open("r", encoding="utf-8") as f:
                    _CFG = yaml.safe_load(f) or {}
            except Exception as e:
                logger.error(f"Fehler beim Laden von config/app.yaml: {e}")
                _CFG = {}
    return _CFG


def cfg(path: str, default=None):
    """
    Holt einen Wert aus der Config.
    
    Args:
        path: Pfad im Format "osrm:base_url" oder "app:feature_flags:stats_box_enabled"
        default: Default-Wert wenn nicht gefunden
    
    Returns:
        Config-Wert oder default
    """
    c = load_config()
    node = c
    for key in path.split(":"):
        if isinstance(node, dict):
            node = node.get(key, {})
        else:
            return default
    
    return node if node != {} else default


class OSRMSettings:
    """
    OSRM-Konfiguration (Phase 1 + Phase 2 Runbook).
    Kann über Umgebungsvariablen überschrieben werden.
    Verwendet einfache Dataclass statt BaseSettings (kein pydantic-settings nötig).
    """
    def __init__(self):
        """Lädt Settings aus Umgebungsvariablen oder verwendet Defaults."""
        # Defaults (Phase 1)
        self.OSRM_BASE_URL = os.getenv("OSRM_BASE_URL", "http://127.0.0.1:5000")
        self.OSRM_TIMEOUT_S = int(os.getenv("OSRM_TIMEOUT_S", "4"))
        self.OSRM_RETRIES = int(os.getenv("OSRM_RETRIES", "2"))
        self.OSRM_RETRY_BACKOFF_MS = int(os.getenv("OSRM_RETRY_BACKOFF_MS", "250"))
        self.FEATURE_OSRM_FALLBACK = os.getenv("FEATURE_OSRM_FALLBACK", "true").lower() == "true"
        self.FEATURE_ROUTE_WARNINGS = os.getenv("FEATURE_ROUTE_WARNINGS", "true").lower() == "true"
        
        # Phase 2: Erweiterte Konfiguration
        self.OSRM_TIMEOUT_SEC = int(os.getenv("OSRM_TIMEOUT_SEC", "6"))  # Phase 2: Standard 6s
        self.OSRM_RETRY_MAX = int(os.getenv("OSRM_RETRY_MAX", "2"))  # Phase 2: Standard 2
        self.OSRM_BREAKER_MAX_FAILS = int(os.getenv("OSRM_BREAKER_MAX_FAILS", "5"))  # Phase 2
        self.OSRM_BREAKER_RESET_SEC = int(os.getenv("OSRM_BREAKER_RESET_SEC", "60"))  # Phase 2
        self.ROUTING_CACHE_TTL_SEC = int(os.getenv("ROUTING_CACHE_TTL_SEC", "86400"))  # Phase 2: 24h
        
        # Optional: Lade aus .env-Datei (falls vorhanden)
        try:
            env_file = Path(".env")
            if env_file.exists():
                with env_file.open("r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            key, value = line.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            
                            if key == "OSRM_BASE_URL":
                                self.OSRM_BASE_URL = value
                            elif key == "OSRM_TIMEOUT_S":
                                self.OSRM_TIMEOUT_S = int(value)
                            elif key == "OSRM_RETRIES":
                                self.OSRM_RETRIES = int(value)
                            elif key == "OSRM_RETRY_BACKOFF_MS":
                                self.OSRM_RETRY_BACKOFF_MS = int(value)
                            elif key == "FEATURE_OSRM_FALLBACK":
                                self.FEATURE_OSRM_FALLBACK = value.lower() == "true"
                            elif key == "FEATURE_ROUTE_WARNINGS":
                                self.FEATURE_ROUTE_WARNINGS = value.lower() == "true"
        except Exception as e:
            logger.debug(f"Fehler beim Laden von .env: {e}")


# Globale Instanz
_osrm_settings: Optional[OSRMSettings] = None


def get_osrm_settings() -> OSRMSettings:
    """Gibt globale OSRM-Settings-Instanz zurück."""
    global _osrm_settings
    if _osrm_settings is None:
        _osrm_settings = OSRMSettings()
    return _osrm_settings

