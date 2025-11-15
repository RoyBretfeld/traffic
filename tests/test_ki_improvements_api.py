"""
Tests für KI-Improvements API-Endpoints.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app

client = TestClient(create_app())


class TestKIImprovementsAPI:
    """Tests für KI-Improvements API."""
    
    def test_recent_endpoint(self):
        """Test: /api/ki-improvements/recent Endpoint."""
        response = client.get("/api/ki-improvements/recent?limit=10")
        
        assert response.status_code == 200
        data = response.json()
        
        assert isinstance(data, list)
        # Kann leer sein wenn keine Verbesserungen vorhanden
    
    def test_recent_endpoint_limit_validation(self):
        """Test: /api/ki-improvements/recent validiert limit."""
        # Zu hoher limit
        response = client.get("/api/ki-improvements/recent?limit=200")
        
        # Sollte 422 sein (limit max 100)
        assert response.status_code == 422
    
    def test_stats_endpoint(self):
        """Test: /api/ki-improvements/stats Endpoint."""
        response = client.get("/api/ki-improvements/stats")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "improvements_today" in data
        assert "successful_count" in data
        assert "failed_count" in data
        assert isinstance(data["improvements_today"], int)
    
    def test_costs_endpoint(self):
        """Test: /api/ki-improvements/costs Endpoint."""
        response = client.get("/api/ki-improvements/costs?period=today")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "stats" in data
        assert "trend" in data
    
    def test_costs_endpoint_period_validation(self):
        """Test: /api/ki-improvements/costs validiert period."""
        # Ungültiger period
        response = client.get("/api/ki-improvements/costs?period=invalid")
        
        assert response.status_code == 422
    
    def test_performance_endpoint(self):
        """Test: /api/ki-improvements/performance Endpoint."""
        response = client.get("/api/ki-improvements/performance?period=today")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "period" in data
        assert "averages" in data or "slowest_files" in data
    
    def test_limits_endpoint(self):
        """Test: /api/ki-improvements/limits Endpoint."""
        response = client.get("/api/ki-improvements/limits")
        
        assert response.status_code == 200
        data = response.json()
        
        assert "can_improve" in data
        assert "message" in data
        assert "limits" in data
        assert "current" in data
        assert "remaining" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

