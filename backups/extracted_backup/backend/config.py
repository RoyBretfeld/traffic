"""
Konfigurations-Loader für app.yaml
"""
from pathlib import Path
import yaml
import logging

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

