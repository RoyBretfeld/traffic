"""Tests für admin.address_admin_app_fixed (v1.0.2)"""

import pytest
from pathlib import Path
from fastapi.testclient import TestClient

# Setup
import sys
PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def admin_app():
    """Erstellt Test-Client für Admin-App."""
    from admin.address_admin_app_fixed import app
    return TestClient(app)


@pytest.fixture
def temp_db(monkeypatch, tmp_path):
    """Erstellt temporäre DB für Tests."""
    db_path = tmp_path / "test_address_corrections.sqlite3"
    monkeypatch.setenv("ADDR_DB_PATH", str(db_path))
    return db_path


def test_ping_endpoint(admin_app, temp_db):
    """Test 1: /api/ping zeigt Pfade."""
    response = admin_app.get("/api/ping")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "db" in data
    assert "migrations" in data
    assert "address_corrections.sqlite3" in data["db"] or "test_address_corrections.sqlite3" in data["db"]


def test_pending_endpoint(admin_app, temp_db):
    """Test 2: /api/pending antwortet."""
    response = admin_app.get("/api/pending")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_resolve_validation_lat_out_of_range(admin_app, temp_db):
    """Test 3: Validierung greift (lat außerhalb Bereich → 422)."""
    payload = {
        "key": "test_street|01067|Dresden|DE",
        "lat": 999,  # Außerhalb [-90, 90]
        "lon": 0
    }
    response = admin_app.post("/api/resolve", json=payload)
    assert response.status_code == 422  # Validation Error


def test_resolve_validation_lon_out_of_range(admin_app, temp_db):
    """Test 4: Validierung greift (lon außerhalb Bereich → 422)."""
    payload = {
        "key": "test_street|01067|Dresden|DE",
        "lat": 51.0,
        "lon": 999  # Außerhalb [-180, 180]
    }
    response = admin_app.post("/api/resolve", json=payload)
    assert response.status_code == 422  # Validation Error


def test_resolve_valid_coordinates(admin_app, temp_db):
    """Test 5: Gültige Koordinaten werden akzeptiert."""
    payload = {
        "key": "test_street|01067|Dresden|DE",
        "lat": 51.05,
        "lon": 13.74
    }
    response = admin_app.post("/api/resolve", json=payload)
    # Kann 404 sein wenn Key nicht existiert, aber nicht 422 (Validation Error)
    assert response.status_code != 422


def test_stats_endpoint(admin_app, temp_db):
    """Test 6: /api/stats liefert Statistiken."""
    response = admin_app.get("/api/stats")
    assert response.status_code == 200
    data = response.json()
    assert "pending" in data
    assert "corrections" in data
    assert isinstance(data["pending"], int)
    assert isinstance(data["corrections"], int)


def test_index_page(admin_app):
    """Test 7: Index-Seite lädt."""
    response = admin_app.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "FAMO" in response.text or "Adress-Admin" in response.text

