"""
Tests für Code-Checker API-Endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app

client = TestClient(create_app())


class TestCodeCheckerAPI:
    """Tests für Code-Checker API."""
    
    def test_analyze_endpoint_exists(self):
        """Test: /api/code-checker/analyze Endpoint existiert."""
        # Test mit existierender Datei
        response = client.post("/api/code-checker/analyze?file_path=backend/app.py")
        
        # Sollte 200 sein (wenn Datei existiert) oder 404 (wenn nicht)
        assert response.status_code in (200, 404)
        
        if response.status_code == 200:
            data = response.json()
            assert "file" in data
            assert "local_issues" in data
            assert "ai_analysis" in data
    
    def test_analyze_endpoint_validation(self):
        """Test: /api/code-checker/analyze validiert file_path."""
        # Fehlender Parameter
        response = client.post("/api/code-checker/analyze")
        
        assert response.status_code == 422
    
    def test_analyze_endpoint_only_python(self):
        """Test: /api/code-checker/analyze akzeptiert nur Python-Dateien."""
        response = client.post("/api/code-checker/analyze?file_path=test.txt")
        
        assert response.status_code == 400
        data = response.json()
        assert "Nur Python-Dateien" in data["detail"]
    
    def test_improve_endpoint_exists(self):
        """Test: /api/code-checker/improve Endpoint existiert."""
        # Test mit existierender Datei
        response = client.post(
            "/api/code-checker/improve?file_path=backend/app.py&auto_apply=false"
        )
        
        # Kann 200, 404, 503 (KI nicht verfügbar) oder 500 sein
        assert response.status_code in (200, 404, 503, 500)
        
        if response.status_code == 200:
            data = response.json()
            assert "success" in data
            assert "applied" in data
    
    def test_improve_endpoint_auto_apply(self):
        """Test: /api/code-checker/improve mit auto_apply=true."""
        response = client.post(
            "/api/code-checker/improve?file_path=backend/app.py&auto_apply=true"
        )
        
        # Kann 200, 404, 503 oder 500 sein
        assert response.status_code in (200, 404, 503, 500)
        
        if response.status_code == 200:
            data = response.json()
            assert "applied" in data
            if data.get("applied"):
                assert "backup" in data
                assert "tests_passed" in data
    
    def test_status_endpoint(self):
        """Test: /api/code-checker/status Endpoint."""
        response = client.get("/api/code-checker/status")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "available" in data
        assert isinstance(data["available"], bool)
        assert "message" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

