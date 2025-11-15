"""
Tests für MVP Patchplan
"""
import pytest
from httpx import AsyncClient
from backend.app import app


@pytest.mark.asyncio
async def test_health_osrm():
    """Test OSRM Health-Check."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health/osrm")
        assert r.status_code in (200, 503)  # 200 wenn OK, 503 wenn nicht verfügbar
        body = r.json()
        assert 'status' in body
        assert 'url' in body


@pytest.mark.asyncio
async def test_health_app():
    """Test App Health-Check mit Feature-Flags."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/health/app")
        assert r.status_code == 200
        body = r.json()
        assert body['status'] == 'ok'
        assert 'feature_flags' in body
        assert 'osrm' in body


@pytest.mark.asyncio
async def test_route_details_min():
    """Test Route-Details Endpoint (minimal)."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.post("/api/tour/route-details", json={
            "stops": [
                {"lat": 51.0504, "lon": 13.7373, "name": "Start"},
                {"lat": 51.0615, "lon": 13.7283, "name": "Ende"}
            ]
        })
        # 200 wenn OSRM erreichbar, 502 wenn remote down, 400 wenn ungültig
        assert r.status_code in (200, 400, 502, 503)
        if r.status_code == 200:
            body = r.json()
            assert 'routes' in body or 'total_distance_km' in body


@pytest.mark.asyncio
async def test_stats_overview():
    """Test Stats-API."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        r = await ac.get("/api/stats/overview")
        assert r.status_code in (200, 503)  # 503 wenn Feature-Flag deaktiviert
        if r.status_code == 200:
            body = r.json()
            assert 'monthly_tours' in body
            assert 'avg_stops' in body
            assert 'km_osrm_month' in body

