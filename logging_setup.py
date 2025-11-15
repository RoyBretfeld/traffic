"""
Logging-Baseline für FAMO TrafficApp
Einheitliches, ruhiges Logging mit UTF-8-Unterstützung
Optional: JSON-Logging für strukturierte Logs
"""
import logging
import os
import sys
from pathlib import Path

# Konfiguration aus Umgebungsvariablen
LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ACCESS_LEVEL = os.getenv("LOG_ACCESS_LEVEL", "WARNING").upper()
USE_JSON_LOGGING = os.getenv("USE_JSON_LOGGING", "false").lower() == "true"
LOG_FILE = os.getenv("LOG_FILE", None)

def setup_logging():
    """Initialisiert das Logging-System."""
    
    # Prüfe ob JSON-Logging aktiviert ist
    if USE_JSON_LOGGING:
        try:
            from backend.utils.json_logging import setup_json_logging
            log_file_path = Path(LOG_FILE) if LOG_FILE else None
            setup_json_logging(
                log_file=log_file_path,
                level=LEVEL,
                console=True
            )
            logger = logging.getLogger(__name__)
            logger.info("JSON-Logging aktiviert", extra={"level": LEVEL})
            return
        except Exception as e:
            print(f"[WARNING] JSON-Logging konnte nicht aktiviert werden: {e}, verwende Standard-Logging")
    
    # Standard-Logging (Text-Format)
    FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    
    # UTF-8-fähiger Handler für stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(FORMAT))
    
    # Root-Logger konfigurieren
    root = logging.getLogger()
    root.setLevel(LEVEL)
    
    # Doppelte Handler verhindern
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)
    
    # File-Handler (falls angegeben)
    if LOG_FILE:
        log_file_path = Path(LOG_FILE)
        log_file_path.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(FORMAT))
        root.addHandler(file_handler)
    
    # FastAPI/Uvicorn etwas ruhiger machen
    noisy_loggers = [
        "uvicorn.access",
        "uvicorn.error", 
        "fastapi",
        "httpx"
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(ACCESS_LEVEL)
    
    # Erfolgreiche Initialisierung loggen
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialisiert: Level={LEVEL}, Access-Level={ACCESS_LEVEL}")

# Automatische Initialisierung beim Import
setup_logging()
