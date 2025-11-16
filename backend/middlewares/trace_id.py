"""
Trace-ID Middleware
Setzt X-Request-ID Header für Request-Tracing.
Erweitert: Latenz-Messung und strukturiertes Logging.
"""
import uuid
import time
import logging
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class TraceIDMiddleware(BaseHTTPMiddleware):
    """
    Middleware die eine Trace-ID für jeden Request generiert und im Request-State speichert.
    Erweitert: Misst Request-Dauer und loggt strukturiert.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Hole Trace-ID aus Header oder generiere neue
        trace_id_header = request.headers.get("X-Request-ID")
        trace_id = trace_id_header if trace_id_header else str(uuid.uuid4())[:8]
        
        # Speichere Trace-ID im Request-State
        request.state.trace_id = trace_id
        
        # Start-Zeit für Latenz-Messung (für Error-Learning)
        start_time = time.time()
        request.state.request_start_time = start_time
        
        # Rufe nächste Middleware/Handler auf
        response = await call_next(request)
        
        # Berechne Dauer
        duration_ms = (time.time() - start_time) * 1000
        
        # Error-Learning: Logge erfolgreiche Requests (nur bei 2xx)
        if 200 <= response.status_code < 300:
            try:
                from backend.services.error_learning_service import log_success_event
                log_success_event(
                    endpoint=str(request.url.path),
                    http_method=request.method,
                    status_code=response.status_code,
                    request_duration_ms=int(duration_ms),
                    environment=_get_environment(),
                )
            except Exception as e:
                # Fehler beim Success-Logging darf nicht den Request killen
                logging.getLogger(__name__).debug(f"Fehler beim Success-Logging: {e}")
        
        # Füge Trace-ID zum Response-Header hinzu
        # ✅ Header direkt setzen - keine Scope-Manipulation
        try:
            response.headers["X-Request-ID"] = trace_id
        except (AttributeError, TypeError):
            # Header-Setzen darf nie den Request killen
            logger.debug("Could not attach X-Request-ID header to response")
        
        # Logge Request mit Trace-ID und Metriken (wenn JSON-Logging aktiviert)
        try:
            logger = logging.getLogger(__name__)
            logger.info(
                f"{request.method} {request.url.path}",
                extra={
                    "trace_id": trace_id,
                    "route": str(request.url.path),
                    "method": request.method,
                    "duration_ms": round(duration_ms, 2),
                    "status_code": response.status_code
                }
            )
        except Exception as log_err:
            # Logging darf nie den Request killen
            logging.getLogger(__name__).debug(f"Failed to log request metrics: {log_err}")
        
        return response


def _get_environment() -> str:
    """Bestimmt die aktuelle Umgebung (dev, prod, test)."""
    import os
    env = os.getenv("ENVIRONMENT", "dev")
    if env.lower() in ["production", "prod"]:
        return "prod"
    elif env.lower() in ["test", "testing"]:
        return "test"
    return "dev"

