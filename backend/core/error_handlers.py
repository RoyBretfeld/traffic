# backend/core/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
import uuid
import traceback
import sys
from typing import Optional

async def http_exception_handler(request: Request, exc):
    """
    Zentraler Exception-Handler für HTTPExceptions.
    Erweitert: Loggt Fehler in Error-Learning-System.
    """
    rid = request.headers.get("x-request-id") or getattr(request.state, "trace_id", None) or str(uuid.uuid4())
    status = getattr(exc, "status_code", 500)
    # 402 → 400
    if status == 402:
        status = 400
    
    # Error-Learning: Logge Fehler-Event (nur bei 4xx/5xx)
    if status >= 400:
        try:
            from backend.services.error_learning_service import log_error_event
            
            # Extrahiere Stacktrace
            exc_type, exc_value, exc_tb = sys.exc_info()
            stacktrace = None
            if exc_tb:
                stacktrace = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            
            # Extrahiere Module aus Stacktrace
            module = None
            if stacktrace:
                # Versuche Modul aus Stacktrace zu extrahieren
                import re
                match = re.search(r'File "[^"]*[/\\]([^/\\"]+\.py)"', stacktrace)
                if match:
                    module = match.group(1).replace('.py', '')
            
            # Extrahiere Request-Dauer (falls verfügbar)
            request_duration_ms = None
            if hasattr(request.state, "request_start_time"):
                import time
                request_duration_ms = int((time.time() - request.state.request_start_time) * 1000)
            
            # Logge Event
            log_error_event(
                trace_id=rid,
                endpoint=str(request.url.path),
                http_method=request.method,
                status_code=status,
                error_type=type(exc).__name__,
                module=module,
                message=str(getattr(exc, "detail", str(exc))),
                stacktrace=stacktrace,
                payload_snapshot=_extract_payload_snapshot(request),
                environment=_get_environment(),
                severity="error" if status >= 500 else "warn",
                is_handled=True,  # HTTPException ist bewusst behandelt
                user_agent=request.headers.get("user-agent"),
                ip_address=request.client.host if request.client else None,
                request_duration_ms=request_duration_ms,
            )
        except Exception as e:
            # Fehler beim Error-Logging darf nicht den Request killen
            import logging
            logging.getLogger(__name__).warning(f"Fehler beim Error-Learning-Logging: {e}")
    
    return JSONResponse({
        "error": type(exc).__name__,
        "detail": getattr(exc, "detail", str(exc)),
        "request_id": rid,
        "trace_id": rid
    }, status_code=status)


def _extract_payload_snapshot(request: Request) -> Optional[dict]:
    """
    Extrahiert gekürzte/Anonymisierte Payload-Daten aus Request.
    """
    try:
        snapshot = {}
        
        # Query-Parameter
        if request.query_params:
            snapshot["query_params"] = dict(list(request.query_params.items())[:5])  # Max. 5
        
        # Path-Parameter
        if request.path_params:
            snapshot["path_params"] = dict(request.path_params)
        
        # Headers (nur relevante)
        relevant_headers = ["content-type", "content-length", "accept"]
        snapshot["headers"] = {
            k: v for k, v in request.headers.items()
            if k.lower() in relevant_headers
        }
        
        return snapshot if snapshot else None
        
    except Exception:
        return None


def _get_environment() -> str:
    """
    Bestimmt die aktuelle Umgebung (dev, prod, test).
    """
    import os
    env = os.getenv("ENVIRONMENT", "dev")
    if env.lower() in ["production", "prod"]:
        return "prod"
    elif env.lower() in ["test", "testing"]:
        return "test"
    return "dev"

class RequestIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware die eine Request-ID für jeden Request generiert und im Response-Header setzt.
    Header werden direkt gesetzt - keine Scope-Manipulation (funktioniert mit allen Response-Typen).
    """
    async def dispatch(self, request: Request, call_next):
        # Hole Request-ID aus Header oder generiere neue
        rid = request.headers.get("x-request-id") or str(uuid.uuid4())
        
        # Rufe nächste Middleware/Handler auf
        response = await call_next(request)
        
        # ✅ RICHTIG: Header direkt setzen (funktioniert auch bei StreamingResponse, solange noch nicht gesendet)
        # Header-Setzen darf nie den Request killen
        try:
            response.headers["x-request-id"] = rid
        except (AttributeError, TypeError):
            # Manche Response-Typen haben keine headers (extrem selten)
            # Logge nur im Debug-Modus, nicht als Fehler
            import logging
            logger = logging.getLogger(__name__)
            logger.debug("Could not attach x-request-id header to response")
        
        return response
