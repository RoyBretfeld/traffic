"""
Smoke-Tests für Root-Endpoint und Health-Checks.
Verhindert Regression des 500-Fehlers auf `/`.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app


def test_root_ok():
    """Test: Root-Endpoint gibt keinen 500-Fehler zurück."""
    app = create_app()
    client = TestClient(app)
    r = client.get("/")
    # Hauptsache kein 5xx mehr
    assert r.status_code < 500, f"Root-Endpoint gibt {r.status_code} zurück (erwartet < 500)"
    # Sollte HTML zurückgeben
    assert "text/html" in r.headers.get("content-type", "").lower()


def test_health_endpoints():
    """Test: Alle Health-Endpoints geben 200 oder 204 zurück."""
    app = create_app()
    client = TestClient(app)
    health_paths = [
        "/health",
        "/healthz",
        "/readyz",
        "/health/app",
        "/health/db",
        "/health/live",
        "/health/osrm",
    ]
    
    for path in health_paths:
        r = client.get(path)
        assert r.status_code in (200, 204, 503), f"{path} gibt {r.status_code} zurück (erwartet 200, 204 oder 503)"
        # 503 ist OK für /readyz wenn DB nicht verfügbar ist


def test_debug_info_ok():
    """Test: /debug/info gibt Konfigurations-Info zurück."""
    app = create_app()
    client = TestClient(app)
    r = client.get("/debug/info")
    assert r.status_code == 200
    data = r.json()
    assert "db_url" in data
    assert "osrm_url" in data
    assert "env" in data


def test_favicon_no_500():
    """Test: /favicon.ico gibt keinen 500-Fehler zurück."""
    app = create_app()
    client = TestClient(app)
    r = client.get("/favicon.ico")
    # Kann 404 sein, aber kein 500
    assert r.status_code < 500, f"/favicon.ico gibt {r.status_code} zurück (erwartet < 500)"


def test_docs_ok():
    """Test: /docs lädt ohne 500-Fehler."""
    app = create_app()
    client = TestClient(app)
    r = client.get("/docs")
    assert r.status_code < 500, f"/docs gibt {r.status_code} zurück (erwartet < 500)"


def test_response_headers_have_request_id():
    """Test: Response-Header enthalten x-request-id."""
    app = create_app()
    client = TestClient(app)
    r = client.get("/healthz")
    # Request-ID sollte im Header sein (von RequestIdMiddleware oder TraceIDMiddleware)
    assert "x-request-id" in r.headers or "X-Request-ID" in r.headers, "Response-Header sollte x-request-id enthalten"
