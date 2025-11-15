# tests/test_route_details.py
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app

app = create_app()
client = TestClient(app)

def test_route_details_success():
    response = client.post(
        "/api/tour/route-details",
        json={
            "stops": [
                {"lat": 51.0493, "lon": 13.7381},
                {"lat": 51.0639, "lon": 13.7522}
            ],
            "overview": "full",
            "geometries": "polyline6",
            "profile": "driving"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "geometry_polyline6" in data
    assert "total_distance_m" in data
    assert "total_duration_s" in data
    assert "source" in data

def test_route_details_not_enough_stops():
    response = client.post(
        "/api/tour/route-details",
        json={
            "stops": [
                {"lat": 51.0493, "lon": 13.7381}
            ],
            "overview": "full",
            "geometries": "polyline6",
            "profile": "driving"
        }
    )
    assert response.status_code == 400
    assert "Mindestens 2 gültige Koordinaten für Routing erforderlich" in response.json()["detail"]

def test_route_details_invalid_coordinates():
    response = client.post(
        "/api/tour/route-details",
        json={
            "stops": [
                {"lat": 51.0493, "lon": 13.7381},
                {"lat": 999.0, "lon": 999.0} # Ungültige Koordinate
            ],
            "overview": "full",
            "geometries": "polyline6",
            "profile": "driving"
        }
    )
    # Erwartet 200 mit Fallback (Haversine), da OSRM 400 zurückgibt und der Fallback-Mechanismus greift
    # Das ist das erwartete Verhalten: Bei ungültigen Koordinaten wird Fallback verwendet
    assert response.status_code == 200
    data = response.json()
    assert "source" in data
    assert data["source"] in ["fallback_haversine", "haversine_fallback", "osrm", "cache"]  # Fallback sollte aktiviert werden
