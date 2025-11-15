"""
JSON-Logging für strukturierte Logs mit Trace-ID und Metriken.
"""
import json
import logging
import sys
from datetime import datetime
from typing import Any, Dict, Optional
from pathlib import Path


class JSONFormatter(logging.Formatter):
    """Formatter für strukturierte JSON-Logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatiert Log-Record als JSON."""
        log_data = {
            "ts": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Trace-ID hinzufügen (falls vorhanden)
        if hasattr(record, 'trace_id'):
            log_data["trace_id"] = record.trace_id
        
        # Route/Path hinzufügen (falls vorhanden)
        if hasattr(record, 'route'):
            log_data["route"] = record.route
        
        # Duration/Latenz hinzufügen (falls vorhanden)
        if hasattr(record, 'duration_ms'):
            log_data["duration_ms"] = record.duration_ms
        
        # OSRM-Metriken hinzufügen (falls vorhanden)
        if hasattr(record, 'osrm_latency_ms'):
            log_data["osrm_latency_ms"] = record.osrm_latency_ms
        if hasattr(record, 'osrm_status'):
            log_data["osrm_status"] = record.osrm_status
        
        # Error-Code hinzufügen (falls vorhanden)
        if hasattr(record, 'error_code'):
            log_data["error_code"] = record.error_code
        
        # Exception-Info hinzufügen (falls vorhanden)
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Extra-Felder hinzufügen
        if hasattr(record, 'extra'):
            log_data.update(record.extra)
        
        return json.dumps(log_data, ensure_ascii=False)


def setup_json_logging(
    log_file: Optional[Path] = None,
    level: str = "INFO",
    console: bool = True
) -> None:
    """
    Konfiguriert JSON-Logging.
    
    Args:
        log_file: Optionaler Pfad zur Log-Datei
        level: Log-Level (DEBUG, INFO, WARNING, ERROR)
        console: Ob Logs auch auf Console ausgegeben werden sollen
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))
    
    # Entferne alle bestehenden Handler
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)
    
    formatter = JSONFormatter()
    
    # Console-Handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)
    
    # File-Handler (falls angegeben)
    if log_file:
        log_file.parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)
    
    # FastAPI/Uvicorn etwas ruhiger machen
    noisy_loggers = [
        "uvicorn.access",
        "uvicorn.error",
        "fastapi",
        "httpx"
    ]
    
    for logger_name in noisy_loggers:
        logging.getLogger(logger_name).setLevel(logging.WARNING)
    
    root_logger.info("JSON-Logging initialisiert", extra={"level": level})


def log_with_trace(
    logger: logging.Logger,
    level: int,
    message: str,
    trace_id: Optional[str] = None,
    route: Optional[str] = None,
    duration_ms: Optional[float] = None,
    **extra
) -> None:
    """
    Loggt mit Trace-ID und optionalen Metriken.
    
    Args:
        logger: Logger-Instanz
        level: Log-Level (logging.INFO, logging.ERROR, etc.)
        message: Log-Nachricht
        trace_id: Optional Trace-ID
        route: Optional Route/Path
        duration_ms: Optional Dauer in Millisekunden
        **extra: Weitere Felder
    """
    extra_fields = {}
    if trace_id:
        extra_fields["trace_id"] = trace_id
    if route:
        extra_fields["route"] = route
    if duration_ms is not None:
        extra_fields["duration_ms"] = duration_ms
    extra_fields.update(extra)
    
    logger.log(level, message, extra=extra_fields)

