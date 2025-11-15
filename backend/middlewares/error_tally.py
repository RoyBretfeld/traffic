"""
Error-Tally-Middleware: Zählt 4xx und 5xx HTTP-Status-Codes.
"""
from starlette.requests import Request
from starlette.responses import Response, JSONResponse
from typing import Dict
import logging

logger = logging.getLogger(__name__)

# Globale Metriken (Thread-safe für FastAPI)
METRICS: Dict[str, int] = {"http_4xx": 0, "http_5xx": 0}


async def error_tally(request: Request, call_next):
    """
    Middleware: Zählt 4xx und 5xx HTTP-Status-Codes.
    
    Args:
        request: Starlette Request
        call_next: Next middleware/route handler
        
    Returns:
        Response mit Status-Code
    """
    try:
        resp: Response = await call_next(request)
        
        # Zähle Status-Codes
        if 400 <= resp.status_code < 500:
            METRICS["http_4xx"] += 1
            logger.debug(f"4xx Error: {resp.status_code} for {request.url.path}")
        elif 500 <= resp.status_code < 600:
            METRICS["http_5xx"] += 1
            logger.warning(f"5xx Error: {resp.status_code} for {request.url.path}")
        
        return resp
    except Exception as e:
        # Uncaught Exception -> 500
        METRICS["http_5xx"] += 1
        logger.error(f"Uncaught exception in error_tally: {e}", exc_info=True)
        return JSONResponse({"detail": "internal", "error": "internal_server_error"}, status_code=500)


def get_metrics() -> Dict[str, int]:
    """
    Gibt aktuelle Metriken zurück.
    
    Returns:
        Dict mit http_4xx und http_5xx Zählern
    """
    return METRICS.copy()


def reset_metrics() -> None:
    """Setzt Metriken zurück (für Tests)."""
    METRICS["http_4xx"] = 0
    METRICS["http_5xx"] = 0

