"""
Tests für Systemregeln-API.
Prüft GET/PUT Endpoints und Authentifizierung.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
import tempfile
import json
from pathlib import Path


@pytest.fixture
def client():
    """Erstellt Test-Client."""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def mock_auth_session(client):
    """Mockt Admin-Session für Tests."""
    # Simuliere Login
    response = client.post(
        "/api/auth/login",
        json={"username": "Bretfeld", "password": "Lisa01Bessy02"}
    )
    assert response.status_code == 200
    return response.json()["session_id"]


class TestSystemRulesAPI:
    """Tests für Systemregeln-API."""
    
    def test_get_system_rules_without_file(self, client):
        """Test: GET ohne Datei gibt Standardwerte zurück."""
        response = client.get("/api/system/rules")
        assert response.status_code == 200
        data = response.json()
        assert data["time_budget_without_return"] == 65
        assert data["time_budget_with_return"] == 90
        assert "depot_coords" in data
    
    def test_get_system_rules_with_file(self, client, tmp_path):
        """Test: GET mit Datei gibt Datei-Werte zurück."""
        # Erstelle temporäre JSON-Datei
        import backend.services.system_rules_service as service_module
        original_file = service_module.SYSTEM_RULES_FILE
        
        test_file = tmp_path / "system_rules.json"
        test_data = {
            "time_budget_without_return": 70,
            "time_budget_with_return": 95,
            "service_time_per_stop": 2.5,
            "speed_kmh": 55.0,
            "safety_factor": 1.4,
            "depot_lat": 51.0,
            "depot_lon": 13.7,
            "rules_version": "1.0"
        }
        with open(test_file, "w", encoding="utf-8") as f:
            json.dump(test_data, f)
        
        service_module.SYSTEM_RULES_FILE = test_file
        
        try:
            response = client.get("/api/system/rules")
            assert response.status_code == 200
            data = response.json()
            assert data["time_budget_without_return"] == 70
        finally:
            service_module.SYSTEM_RULES_FILE = original_file
    
    def test_put_system_rules_unauthorized(self, client):
        """Test: PUT ohne Auth gibt 401."""
        response = client.put(
            "/api/system/rules",
            json={
                "time_budget_without_return": 70,
                "time_budget_with_return": 95,
                "service_time_per_stop": 2.5,
                "speed_kmh": 55.0,
                "safety_factor": 1.4,
                "depot_lat": 51.0,
                "depot_lon": 13.7
            }
        )
        assert response.status_code == 401
    
    def test_put_system_rules_valid(self, client, mock_auth_session, tmp_path):
        """Test: PUT mit validen Daten und Auth gibt 200."""
        import backend.services.system_rules_service as service_module
        original_file = service_module.SYSTEM_RULES_FILE
        test_file = tmp_path / "system_rules.json"
        service_module.SYSTEM_RULES_FILE = test_file
        
        try:
            response = client.put(
                "/api/system/rules",
                json={
                    "time_budget_without_return": 70,
                    "time_budget_with_return": 95,
                    "service_time_per_stop": 2.5,
                    "speed_kmh": 55.0,
                    "safety_factor": 1.4,
                    "depot_lat": 51.0,
                    "depot_lon": 13.7
                }
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["rules"]["time_budget_without_return"] == 70
            
            # Prüfe dass Datei erstellt wurde
            assert test_file.exists()
        finally:
            service_module.SYSTEM_RULES_FILE = original_file
    
    def test_put_system_rules_invalid_validation(self, client, mock_auth_session):
        """Test: PUT mit invaliden Daten gibt 422."""
        response = client.put(
            "/api/system/rules",
            json={
                "time_budget_without_return": 100,
                "time_budget_with_return": 90,  # Ungültig: ohne > mit
                "service_time_per_stop": 2.0,
                "speed_kmh": 50.0,
                "safety_factor": 1.3,
                "depot_lat": 51.0,
                "depot_lon": 13.7
            }
        )
        assert response.status_code == 422
    
    def test_self_check_endpoint(self, client):
        """Test: Self-Check Endpoint funktioniert."""
        response = client.get("/api/system/rules/self-check")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "checks" in data
        assert "source" in data["checks"]

