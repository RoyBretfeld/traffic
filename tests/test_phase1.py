"""
Tests für Phase 1: Polyline6, Stats, Admin, Health
"""
import pytest
import httpx
from fastapi.testclient import TestClient
from backend.app import create_app
app = create_app()
import os

client = TestClient(app)


def test_health_app():
    """Test App Health-Check."""
    r = client.get("/health/app")
    assert r.status_code == 200
    body = r.json()
    assert body['status'] == 'ok'
    assert 'feature_flags' in body
    assert 'osrm' in body


@pytest.mark.skipif(os.getenv("CI_NO_NET") == "1", reason="Netzwerk deaktiviert")
def test_health_osrm():
    """Test OSRM Health-Check."""
    r = client.get("/health/osrm")
    assert r.status_code in (200, 503)  # 200 wenn OK, 503 wenn nicht verfügbar
    body = r.json()
    assert 'status' in body
    assert 'url' in body
    if 'latency_ms' in body:
        assert isinstance(body['latency_ms'], int)


@pytest.mark.skipif(os.getenv("CI_NO_NET") == "1", reason="Netzwerk deaktiviert")
def test_health_osrm_sample():
    """Test OSRM Sample Route (Polyline6)."""
    r = client.get("/health/osrm/sample-route")
    assert r.status_code in (200, 503)
    body = r.json()
    assert 'ok' in body
    assert 'polyline6_len' in body
    if body.get('ok'):
        assert body['polyline6_len'] > 0


def test_health_db():
    """Test DB Health-Check."""
    r = client.get("/health/db")
    assert r.status_code in (200, 500)
    body = r.json()
    assert 'status' in body


def test_route_details_min():
    """Test Route-Details Endpoint (minimal)."""
    r = client.post("/api/tour/route-details", json={
        "stops": [
            {"lat": 51.0504, "lon": 13.7373, "name": "Start"},
            {"lat": 51.0615, "lon": 13.7283, "name": "Ende"}
        ]
    })
    # 200 wenn OSRM erreichbar, 502 wenn remote down, 400 wenn ungültig
    assert r.status_code in (200, 400, 502, 503)
    if r.status_code == 200:
        body = r.json()
        assert 'routes' in body
        if body.get('routes'):
            route = body['routes'][0]
            # Prüfe ob geometry_type vorhanden ist wenn geometry vorhanden
            if route.get('geometry'):
                assert 'geometry_type' in route or route.get('source') == 'osrm'


def test_stats_overview():
    """Test Stats-API."""
    r = client.get("/api/stats/overview")
    # 200 wenn OK, 500 wenn Tabellen fehlen, 503 wenn Feature-Flag deaktiviert
    assert r.status_code in (200, 500, 503)
    if r.status_code == 200:
        body = r.json()
        assert 'monthly_tours' in body
        assert 'avg_stops' in body
        assert 'km_osrm_month' in body
    elif r.status_code == 500:
        # Bei 500 sollte eine Fehlermeldung vorhanden sein
        body = r.json()
        assert 'error' in body

