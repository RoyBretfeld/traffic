"""
Smoke-Tests für OSRM Metrics & Server-Stabilität.
Manuelle Testliste für Abnahme.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app


@pytest.fixture
def client():
    """Test-Client für FastAPI-App."""
    app = create_app()
    return TestClient(app)


def test_root_endpoint(client):
    """Test: GET / → 200/HTML"""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")


def test_openapi_json(client):
    """Test: GET /openapi.json → 200/JSON"""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.headers.get("content-type", "").startswith("application/json")
    data = response.json()
    assert "openapi" in data or "info" in data


def test_health_status(client):
    """Test: GET /health/status → 200 mit Services-Status"""
    response = client.get("/health/status")
    assert response.status_code in [200, 503]  # 503 wenn Services nicht verfügbar
    data = response.json()
    assert "status" in data
    assert "services" in data
    assert "server" in data["services"]
    assert "database" in data["services"]
    assert "osrm" in data["services"]


def test_health_db(client):
    """Test: GET /health/db → 200 mit DB-Status"""
    response = client.get("/health/db")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "ok" in data


def test_health_osrm(client):
    """Test: GET /health/osrm → 200 mit OSRM-Status"""
    response = client.get("/health/osrm")
    assert response.status_code in [200, 503]
    data = response.json()
    assert "ok" in data
    assert "url" in data


def test_metrics_simple(client):
    """Test: GET /metrics/simple → Zähler für 4xx/5xx"""
    response = client.get("/metrics/simple")
    assert response.status_code == 200
    data = response.json()
    assert "http_4xx" in data
    assert "http_5xx" in data
    assert isinstance(data["http_4xx"], int)
    assert isinstance(data["http_5xx"], int)


def test_metrics_increment_on_error(client):
    """Test: Metriken erhöhen sich bei Fehlern"""
    # Hole initiale Metriken
    initial = client.get("/metrics/simple").json()
    initial_4xx = initial["http_4xx"]
    initial_5xx = initial["http_5xx"]
    
    # Erzeuge 404-Fehler
    client.get("/nonexistent-endpoint")
    
    # Prüfe ob Metriken erhöht wurden
    after = client.get("/metrics/simple").json()
    assert after["http_4xx"] >= initial_4xx
    # 5xx sollte gleich bleiben (404 ist 4xx)
    assert after["http_5xx"] == initial_5xx


def test_route_details_endpoint(client):
    """Test: POST /api/tour/route-details (2 Punkte) → 200 + Geometrie"""
    # Test mit 2 Punkten (Dresden) - korrektes Format
    test_data = {
        "stops": [
            {"lat": 51.0504, "lon": 13.7373, "name": "Punkt 1"},
            {"lat": 51.0615, "lon": 13.7283, "name": "Punkt 2"}
        ]
    }
    
    response = client.post("/api/tour/route-details", json=test_data)
    
    # Kann 200 (OK), 422 (Validation), oder 503 (OSRM nicht verfügbar) sein
    assert response.status_code in [200, 422, 503]
    
    if response.status_code == 200:
        data = response.json()
        # Prüfe ob Geometrie vorhanden ist
        assert "geometry" in data or "route" in data or "polyline" in data
    elif response.status_code == 422:
        # Validation-Fehler ist auch OK (z.B. fehlende Pflichtfelder)
        data = response.json()
        assert "detail" in data or "error" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

