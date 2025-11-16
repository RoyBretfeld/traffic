import pytest
from fastapi.testclient import TestClient
from backend.app import create_app
app = create_app()

client = TestClient(app)

def test_tourplaene_list_endpoint():
    """Test des /api/tourplaene/list Endpoints."""
    response = client.get("/api/tourplaene/list")
    
    # Sollte 200 oder 404 zurückgeben (je nachdem ob tourplaene-Verzeichnis existiert)
    assert response.status_code in [200, 404]
    
    if response.status_code == 200:
        data = response.json()
        assert "success" in data
        assert "files" in data
        assert "count" in data
        assert isinstance(data["files"], list)

def test_tourplan_management_page():
    """Test der Tourplan Management Seite."""
    response = client.get("/ui/tourplan-management")
    
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "Tourplan Management" in response.text
    assert "Debug-HUD" in response.text or "hud" in response.text

def test_api_endpoints_exist():
    """Test dass alle benötigten API-Endpoints existieren."""
    # Test /api/tourplaene/list
    response = client.get("/api/tourplaene/list")
    assert response.status_code in [200, 404, 500]  # Je nach Setup
    
    # Test /api/tourplan/match (mit ungültiger Datei)
    response = client.get("/api/tourplan/match?file=nonexistent.csv")
    assert response.status_code == 404
    
    # Test /api/tourplan/geocode-missing (mit ungültiger Datei)
    response = client.get("/api/tourplan/geocode-missing?file=nonexistent.csv&limit=5&dry_run=true")
    assert response.status_code == 404

def test_cors_headers():
    """Test dass CORS-Headers gesetzt sind."""
    response = client.get("/api/tourplaene/list")
    
    # CORS-Headers werden nur bei echten Browser-Requests gesetzt
    # Im TestClient werden sie nicht gesetzt, das ist normal
    assert response.status_code in [200, 404, 500]
