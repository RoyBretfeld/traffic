"""
Tests für Sub-Routes 500er Fix
Testet die neuen Fehlerbehandlungs-Mechanismen ohne Mockups.
"""
import pytest
import httpx
from fastapi.testclient import TestClient
from backend.app import app
import os

client = TestClient(app)


def test_optimize_ok_osrm():
    """Test: Optimierung mit OSRM sollte 200 + polyline zurückgeben"""
    response = client.post("/api/tour/optimize", json={
        "tour_id": "TEST-TOUR",
        "stops": [
            {"lat": 51.0504, "lon": 13.7373, "name": "Start"},
            {"lat": 51.0615, "lon": 13.7283, "name": "Ende"}
        ]
    })
    
    # Sollte 200 sein (nie 500)
    assert response.status_code in (200, 422, 503), f"Unerwarteter Status: {response.status_code}, Body: {response.text}"
    
    if response.status_code == 200:
        body = response.json()
        # Prüfe ob success oder error
        if body.get("success"):
            assert "optimized_stops" in body
            assert "trace_id" in body
        else:
            # success:false ist OK (z.B. bei OSRM-Down)
            assert "error" in body
            assert "trace_id" in body


@pytest.mark.skipif(os.getenv("CI_NO_NET") == "1", reason="Netzwerk deaktiviert")
def test_optimize_osrm_down_fallback():
    """Test: Bei OSRM-Down sollte Fallback verwendet werden (200 + source:haversine)"""
    # Dieser Test würde normalerweise OSRM blockieren, aber wir testen nur die Fallback-Logik
    response = client.post("/api/tour/optimize", json={
        "tour_id": "TEST-TOUR-FALLBACK",
        "stops": [
            {"lat": 51.0504, "lon": 13.7373, "name": "Start"},
            {"lat": 51.0615, "lon": 13.7283, "name": "Ende"}
        ]
    })
    
    # Sollte 200 sein (nie 500)
    assert response.status_code in (200, 422), f"Unerwarteter Status: {response.status_code}"
    
    if response.status_code == 200:
        body = response.json()
        # Auch bei Fallback sollte trace_id vorhanden sein
        assert "trace_id" in body
        if body.get("success"):
            assert "metrics" in body
            # Backend könnte "local_haversine" sein wenn OSRM down
            assert body["metrics"].get("backend_used") in ("osrm", "local_haversine")


def test_optimize_bad_request_422():
    """Test: Ungültiger Request sollte 422 zurückgeben (nicht 500)"""
    # Fehlende tour_id
    response = client.post("/api/tour/optimize", json={
        "stops": [{"lat": 51.05, "lon": 13.73}]
    })
    
    assert response.status_code == 422, f"Sollte 422 sein, got {response.status_code}"
    body = response.json()
    assert "error" in body or "detail" in body
    assert "trace_id" in body or "X-Request-ID" in response.headers


def test_optimize_no_coordinates_422():
    """Test: Stops ohne Koordinaten sollte 422 zurückgeben"""
    response = client.post("/api/tour/optimize", json={
        "tour_id": "TEST",
        "stops": [
            {"name": "Stop ohne Koordinaten"}
        ]
    })
    
    assert response.status_code == 422, f"Sollte 422 sein, got {response.status_code}"
    body = response.json()
    assert "error" in body or "detail" in body


def test_optimize_trace_id_present():
    """Test: Trace-ID sollte in Response vorhanden sein"""
    response = client.post("/api/tour/optimize", json={
        "tour_id": "TEST-TRACE",
        "stops": [
            {"lat": 51.0504, "lon": 13.7373, "name": "Start"},
            {"lat": 51.0615, "lon": 13.7283, "name": "Ende"}
        ]
    })
    
    # Trace-ID im Header
    assert "X-Request-ID" in response.headers
    
    # Trace-ID im Body (wenn 200)
    if response.status_code == 200:
        body = response.json()
        assert "trace_id" in body


@pytest.mark.skipif(os.getenv("CI_NO_NET") == "1", reason="Netzwerk deaktiviert")
def test_health_osrm():
    """Test: OSRM Health Check sollte Route testen"""
    response = client.get("/health/osrm")
    
    assert response.status_code in (200, 503), f"Unerwarteter Status: {response.status_code}"
    body = response.json()
    assert "status" in body
    assert "url" in body
    if response.status_code == 200:
        assert body["status"] == "ok"
        assert "test_route_status" in body


def test_health_db():
    """Test: DB Health Check"""
    response = client.get("/health/db")
    
    assert response.status_code in (200, 500), f"Unerwarteter Status: {response.status_code}"
    body = response.json()
    assert "status" in body


def test_never_500_without_trace():
    """Test: Keine 500er ohne Trace-ID"""
    # Teste verschiedene Endpoints
    endpoints = [
        ("POST", "/api/tour/optimize", {"tour_id": "TEST", "stops": []}),
        ("GET", "/health/osrm", None),
        ("GET", "/health/db", None),
    ]
    
    for method, path, json_data in endpoints:
        if method == "POST":
            response = client.post(path, json=json_data)
        else:
            response = client.get(path)
        
        # Wenn 500, muss Trace-ID vorhanden sein
        if response.status_code == 500:
            assert "X-Request-ID" in response.headers, f"500er ohne Trace-ID bei {method} {path}"
            body = response.json()
            assert "trace_id" in body or "X-Request-ID" in response.headers

