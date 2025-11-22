"""
Rate-Limiting Middleware für Login und kritische Endpunkte.
SC-04: Login-Rate-Limit aktiv (z. B. 5–10 Versuche/15 min/IP)
"""
import os
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Dict, Tuple
import logging

logger = logging.getLogger(__name__)

# Rate-Limit-Konfiguration
LOGIN_RATE_LIMIT = {
    "max_attempts": int(os.getenv("LOGIN_RATE_LIMIT_MAX", "10")),
    "window_minutes": int(os.getenv("LOGIN_RATE_LIMIT_WINDOW", "15"))
}

# In-Memory Store für Rate-Limits (in Prod: Redis verwenden)
_rate_limit_store: Dict[str, list] = defaultdict(list)


def _cleanup_old_entries(ip: str, window_minutes: int):
    """Entfernt alte Einträge außerhalb des Zeitfensters."""
    cutoff = datetime.now() - timedelta(minutes=window_minutes)
    _rate_limit_store[ip] = [
        timestamp for timestamp in _rate_limit_store[ip]
        if timestamp > cutoff
    ]


def check_rate_limit(ip: str, max_attempts: int, window_minutes: int) -> Tuple[bool, int]:
    """
    Prüft ob Rate-Limit überschritten wurde.
    Returns: (is_allowed, remaining_attempts)
    """
    _cleanup_old_entries(ip, window_minutes)
    
    attempts = len(_rate_limit_store[ip])
    remaining = max(0, max_attempts - attempts)
    
    if attempts >= max_attempts:
        return False, 0
    
    return True, remaining


def record_attempt(ip: str):
    """Zeichnet einen Versuch auf."""
    _rate_limit_store[ip].append(datetime.now())


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate-Limiting für Login-Endpunkt.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Nur für Login-Endpunkt
        if request.url.path == "/api/auth/login" and request.method == "POST":
            ip = request.client.host if request.client else "unknown"
            
            is_allowed, remaining = check_rate_limit(
                ip,
                LOGIN_RATE_LIMIT["max_attempts"],
                LOGIN_RATE_LIMIT["window_minutes"]
            )
            
            if not is_allowed:
                logger.warning(f"Rate-Limit überschritten für IP {ip}")
                raise HTTPException(
                    status_code=429,
                    detail=f"Zu viele Login-Versuche. Bitte versuchen Sie es in {LOGIN_RATE_LIMIT['window_minutes']} Minuten erneut."
                )
            
            # Führe Request aus
            response = await call_next(request)
            
            # Wenn Login fehlgeschlagen: Versuch aufzeichnen
            if response.status_code == 401:
                record_attempt(ip)
                # Füge Rate-Limit-Header hinzu
                response.headers["X-RateLimit-Remaining"] = str(max(0, remaining - 1))
                response.headers["X-RateLimit-Limit"] = str(LOGIN_RATE_LIMIT["max_attempts"])
            
            return response
        
        # Für alle anderen Endpunkte: Weiterleiten
        return await call_next(request)

