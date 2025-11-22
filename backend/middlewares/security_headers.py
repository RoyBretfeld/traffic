"""
Security-Header Middleware (SC-11).
Setzt Security-Header für alle Responses.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import os

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Setzt Security-Header für alle HTTP-Responses.
    SC-11: Security Headers (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)
    """
    
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # X-Frame-Options: Verhindert Clickjacking
        response.headers["X-Frame-Options"] = "DENY"
        
        # X-Content-Type-Options: Verhindert MIME-Sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Referrer-Policy: Begrenzt Referrer-Informationen
        response.headers["Referrer-Policy"] = "no-referrer"
        
        # X-XSS-Protection: Legacy, aber für ältere Browser
        response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # Content-Security-Policy: Für Admin-UI
        # Erlaubt: Self, Inline-Scripts/Styles (für Bootstrap/jQuery), Maps/CDNs
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; "
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com; "
            "img-src 'self' data: https: blob:; "
            "font-src 'self' data: https://fonts.gstatic.com; "
            "connect-src 'self' http://127.0.0.1:* https://api.openrouteservice.org https://*.tile.openstreetmap.org; "
            "frame-src 'self' https://www.openstreetmap.org;"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Strict-Transport-Security: Nur in Production mit HTTPS
        is_production = os.getenv("APP_ENV", "development") == "production"
        if is_production:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response

