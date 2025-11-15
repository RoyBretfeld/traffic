"""
Exception Envelope Middleware
Fängt alle Exceptions ab und gibt strukturierte 500er mit Trace-ID zurück.
"""
import uuid
import traceback
import logging
from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class ErrorEnvelopeMiddleware(BaseHTTPMiddleware):
    """
    Middleware die alle unhandled Exceptions abfängt und strukturierte 500er zurückgibt.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Hole Trace-ID aus Request (wird von TraceIDMiddleware gesetzt)
        # request.state ist ein State-Objekt, kein Dict - verwende getattr
        trace_id = getattr(request.state, "trace_id", None) or str(uuid.uuid4())[:8]
        
        try:
            response = await call_next(request)
            return response
        except Exception as exc:
            # Logge Exception mit Trace-ID
            error_detail = str(exc)
            error_type = type(exc).__name__
            
            # WICHTIG: Mappe externe Fehler zu korrekten HTTP-Status-Codes
            # RuntimeError mit "OSRM quota exceeded" → 429 (Too Many Requests)
            # RuntimeError mit "OSRM transient error" → 503 (Service Unavailable)
            http_status = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_message = f"Internal Server Error: {error_type}"
            
            if isinstance(exc, RuntimeError):
                if "OSRM quota exceeded" in error_detail or "quota" in error_detail.lower():
                    # 402 (Payment Required) von externem Service → 429 für Client
                    http_status = status.HTTP_429_TOO_MANY_REQUESTS
                    error_message = "Upstream quota exceeded"
                    logger.warning(
                        f"Quota-Fehler (402→429) in {request.method} {request.url.path}",
                        extra={"trace_id": trace_id, "error": error_detail}
                    )
                elif "OSRM transient error" in error_detail or "transient" in error_detail.lower():
                    # 502/503/504 von externem Service → 503 für Client
                    http_status = status.HTTP_503_SERVICE_UNAVAILABLE
                    error_message = "Upstream service temporarily unavailable"
                    logger.warning(
                        f"Transient-Fehler (502/503/504→503) in {request.method} {request.url.path}",
                        extra={"trace_id": trace_id, "error": error_detail}
                    )
                else:
                    # Andere RuntimeError → 500 (aber logge als Warning, nicht Exception)
                    logger.warning(
                        f"RuntimeError in {request.method} {request.url.path}",
                        extra={
                            "trace_id": trace_id,
                            "path": str(request.url.path),
                            "method": request.method,
                            "error_type": error_type,
                            "error_detail": error_detail[:200]
                        }
                    )
            else:
                # Alle anderen Exceptions → 500 (kritisch)
                logger.exception(
                    f"Unhandled exception in {request.method} {request.url.path}",
                    extra={
                        "trace_id": trace_id,
                        "path": str(request.url.path),
                        "method": request.method,
                        "error_type": error_type,
                        "error_detail": error_detail[:200]
                    }
                )
            
            # Strukturierte Response (kein 500 für erwartbare Fehler)
            return JSONResponse(
                status_code=http_status,
                content={
                    "success": False,
                    "error": error_message,
                    "error_detail": error_detail[:500],  # Erste 500 Zeichen
                    "trace_id": trace_id,
                    "path": str(request.url.path),
                    "method": request.method
                }
            )

