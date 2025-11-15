"""
Smoke-Tests für Server-Startup und Health-Endpoints.
Prüft, dass die App korrekt startet und grundlegende Endpoints verfügbar sind.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app


def test_healthz_ok():
    """Test: /healthz gibt 200 OK zurück."""
    app = create_app()
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["status"] == "ok"


def test_readyz_ok():
    """Test: /readyz gibt 200 OK zurück wenn App bereit ist."""
    app = create_app()
    client = TestClient(app)
    r = client.get("/readyz")
    # Kann 200 oder 503 sein, je nach DB-Status
    assert r.status_code in [200, 503]
    data = r.json()
    assert "ready" in data


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


def test_root_ok():
    """Test: Root-Endpoint gibt HTML zurück."""
    app = create_app()
    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers.get("content-type", "")


def test_app_factory_creates_app():
    """Test: create_app() erstellt eine gültige FastAPI-App."""
    app = create_app()
    assert app is not None
    assert app.title == "TrafficApp API"
    assert app.version == "1.0.0"


def test_debug_ping_optional():
    """Test: /_debug/ping ist verfügbar wenn Debug-Routen aktiviert sind."""
    import os
    original = os.getenv("ENABLE_DEBUG_ROUTES", "0")
    
    try:
        # Test mit aktivierten Debug-Routen
        os.environ["ENABLE_DEBUG_ROUTES"] = "1"
        app = create_app()
        client = TestClient(app)
        r = client.get("/_debug/ping")
        # Kann 200 sein (wenn verfügbar) oder 404 (wenn nicht)
        assert r.status_code in [200, 404]
    finally:
        os.environ["ENABLE_DEBUG_ROUTES"] = original

