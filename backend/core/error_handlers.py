# backend/core/error_handlers.py
from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import Message
import uuid

async def http_exception_handler(request: Request, exc):
    rid = request.headers.get("x-request-id") or str(uuid.uuid4())
    status = getattr(exc, "status_code", 500)
    # 402 → 400
    if status == 402:
        status = 400
    return JSONResponse({
        "error": type(exc).__name__,
        "detail": getattr(exc, "detail", str(exc)),
        "request_id": rid
    }, status_code=status)

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
