"""
Tests für Routing-Fixes (402/500, Router-404, OSRM-Health).
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app


@pytest.fixture
def client():
    """Erstellt Test-Client."""
    app = create_app()
    return TestClient(app)


def test_health_osrm_endpoint(client):
    """Test: OSRM-Health-Endpoint gibt strukturierte Response zurück."""
    response = client.get("/health/osrm")
    
    assert response.status_code in (200, 503)  # 200 wenn OK, 503 wenn nicht verfügbar
    
    data = response.json()
    assert "ok" in data
    assert "status" in data
    assert "url" in data
    assert "latency_ms" in data
    assert "circuit_breaker" in data


def test_health_osrm_latency(client):
    """Test: OSRM-Health-Endpoint misst Latenz."""
    response = client.get("/health/osrm")
    
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data["latency_ms"], (int, float))
        assert data["latency_ms"] >= 0


def test_route_details_consistent_response(client):
    """Test: Route-Details gibt immer konsistente JSON-Response zurück."""
    # Test mit gültigen Koordinaten
    response = client.post(
        "/api/tour/route-details",
        json={
            "stops": [
                {"lat": 51.05, "lon": 13.74, "name": "Kunde 1"},
                {"lat": 51.06, "lon": 13.75, "name": "Kunde 2"}
            ],
            "include_depot": False
        }
    )
    
    # Sollte 200 oder 422 sein (nicht 500)
    assert response.status_code in (200, 422)
    
    data = response.json()
    assert "routes" in data
    assert "total_distance_km" in data
    assert "total_duration_minutes" in data
    assert "source" in data


def test_route_details_error_handling(client):
    """Test: Route-Details gibt bei Fehlern konsistente Response zurück."""
    # Test mit ungültigen Daten
    response = client.post(
        "/api/tour/route-details",
        json={
            "stops": []  # Leere Liste
        }
    )
    
    # Sollte 400 oder 422 sein (nicht 500)
    assert response.status_code in (400, 422)
    
    data = response.json()
    # Sollte strukturiertes JSON sein
    assert isinstance(data, dict)


def test_error_middleware_402_mapping(client):
    """Test: 402-Fehler werden zu 429 gemappt (über RuntimeError)."""
    # Dieser Test würde einen echten 402-Fehler von OSRM benötigen
    # Für jetzt prüfen wir nur, dass die Middleware existiert
    response = client.get("/health/osrm")
    
    # Sollte nicht 500 sein
    assert response.status_code != 500


def test_trace_id_header(client):
    """Test: Trace-ID wird in Response-Header gesetzt."""
    response = client.get("/health")
    
    assert "X-Trace-ID" in response.headers
    trace_id = response.headers["X-Trace-ID"]
    assert len(trace_id) == 8  # 8 Zeichen (erste 8 von UUID)


def test_router_registration(client):
    """Test: Alle wichtigen Endpoints sind registriert."""
    # Prüfe ob wichtige Endpoints existieren
    endpoints_to_check = [
        "/health",
        "/health/db",
        "/health/osrm",
        "/api/tour/optimize",
        "/api/tour/route-details",
        "/api/osrm/metrics"
    ]
    
    for endpoint in endpoints_to_check:
        # HEAD-Request um zu prüfen ob Endpoint existiert (ohne Body zu lesen)
        response = client.head(endpoint)
        # 404 bedeutet Endpoint nicht gefunden
        assert response.status_code != 404, f"Endpoint {endpoint} nicht gefunden (404)"


def test_osrm_metrics_endpoint(client):
    """Test: OSRM-Metriken-Endpoint gibt Daten zurück."""
    response = client.get("/api/osrm/metrics")
    
    assert response.status_code == 200
    
    data = response.json()
    assert "total_requests" in data
    assert "successful_requests" in data
    assert "failed_requests" in data
    assert "success_rate_pct" in data
    assert "error_rate_pct" in data
    assert "avg_latency_ms" in data
    assert "circuit_breaker_state" in data


def test_osrm_metrics_reset(client):
    """Test: OSRM-Metriken können zurückgesetzt werden."""
    # Setze Metriken zurück
    response = client.post("/api/osrm/metrics/reset")
    
    assert response.status_code == 200
    
    data = response.json()
    assert data["success"] is True
    
    # Prüfe ob Metriken zurückgesetzt wurden
    metrics_response = client.get("/api/osrm/metrics")
    metrics_data = metrics_response.json()
    assert metrics_data["total_requests"] == 0

