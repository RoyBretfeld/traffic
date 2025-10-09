"""
Logging-Baseline für FAMO TrafficApp
Einheitliches, ruhiges Logging mit UTF-8-Unterstützung
"""
import logging
import os
import sys

# Konfiguration aus Umgebungsvariablen
LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
ACCESS_LEVEL = os.getenv("LOG_ACCESS_LEVEL", "WARNING").upper()
FORMAT = "%(asctime)s %(levelname)s %(name)s: %(message)s"

def setup_logging():
    """Initialisiert das Logging-System."""
    
    # UTF-8-fähiger Handler für stdout
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(FORMAT))
    
    # Root-Logger konfigurieren
    root = logging.getLogger()
    root.setLevel(LEVEL)
    
    # Doppelte Handler verhindern
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        root.addHandler(handler)
    
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
