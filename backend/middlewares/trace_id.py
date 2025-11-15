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
        
        # Start-Zeit für Latenz-Messung
        start_time = time.time()
        
        # Rufe nächste Middleware/Handler auf
        response = await call_next(request)
        
        # Berechne Dauer
        duration_ms = (time.time() - start_time) * 1000
        
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

