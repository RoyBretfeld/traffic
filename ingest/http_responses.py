#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Zentrale HTTP-Response-Konfiguration für FAMO TrafficApp
========================================================

Dieses Modul stellt einheitliche HTTP-Response-Konfigurationen bereit,
um das Encoding-Chaos in HTTP-Antworten zu beenden.
"""

from fastapi import Response
from fastapi.responses import JSONResponse, HTMLResponse
from typing import Any, Dict, Optional

def create_utf8_json_response(
    content: Any,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> JSONResponse:
    """
    Erstellt eine JSONResponse mit korrekten UTF-8 Headers.
    
    Args:
        content: Der JSON-Inhalt
        status_code: HTTP-Status-Code
        headers: Zusätzliche Headers
        
    Returns:
        JSONResponse mit UTF-8-Konfiguration
    """
    response_headers = {
        "Content-Type": "application/json; charset=utf-8",
        **(headers or {})
    }
    
    return JSONResponse(
        content=content,
        status_code=status_code,
        headers=response_headers,
        media_type="application/json; charset=utf-8"
    )

def create_utf8_html_response(
    content: str,
    status_code: int = 200,
    headers: Optional[Dict[str, str]] = None
) -> HTMLResponse:
    """
    Erstellt eine HTMLResponse mit korrekten UTF-8 Headers.
    
    Args:
        content: Der HTML-Inhalt
        status_code: HTTP-Status-Code
        headers: Zusätzliche Headers
        
    Returns:
        HTMLResponse mit UTF-8-Konfiguration
    """
    response_headers = {
        "Content-Type": "text/html; charset=utf-8",
        **(headers or {})
    }
    
    return HTMLResponse(
        content=content,
        status_code=status_code,
        headers=response_headers,
        media_type="text/html; charset=utf-8"
    )

def ensure_utf8_headers(response: Response) -> Response:
    """
    Stellt sicher, dass eine Response UTF-8 Headers hat.
    
    Args:
        response: Die zu konfigurierende Response
        
    Returns:
        Response mit UTF-8-Konfiguration
    """
    if "charset" not in response.headers.get("content-type", ""):
        content_type = response.headers.get("content-type", "")
        if content_type.startswith("application/json"):
            response.headers["content-type"] = "application/json; charset=utf-8"
        elif content_type.startswith("text/html"):
            response.headers["content-type"] = "text/html; charset=utf-8"
        elif content_type.startswith("text/plain"):
            response.headers["content-type"] = "text/plain; charset=utf-8"
    
    return response

if __name__ == "__main__":
    # Test der Funktionen
    print("HTTP-Response Test")
    
    # Test JSON Response
    json_resp = create_utf8_json_response({"test": "Löbtauer Straße"})
    print(f"JSON Response Content-Type: {json_resp.headers.get('content-type')}")
    
    # Test HTML Response
    html_resp = create_utf8_html_response("<html><body>Löbtauer Straße</body></html>")
    print(f"HTML Response Content-Type: {html_resp.headers.get('content-type')}")
    
    print("HTTP-Response Test erfolgreich")
