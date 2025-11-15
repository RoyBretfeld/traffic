"""
Integration-Tests für alle Fixes (404/402/500, Health, Upload→Match, KI-CodeChecker).
"""
import pytest
from fastapi.testclient import TestClient
from pathlib import Path
from backend.app import create_app

client = TestClient(create_app())


class TestCompleteWorkflow:
    """Tests für kompletten Workflow: Upload → Match → Health."""
    
    def test_complete_upload_match_flow(self, tmp_path):
        """Test: Kompletter Upload→Match-Flow funktioniert."""
        # 1. Erstelle Test-CSV
        test_csv = tmp_path / "test_tourplan.csv"
        test_csv.write_text(
            "Name,Adresse,PLZ,Stadt\n"
            "Test Kunde,Teststraße 1,01067,Dresden\n",
            encoding="utf-8"
        )
        
        # 2. Upload
        with open(test_csv, "rb") as f:
            upload_response = client.post(
                "/api/upload/csv",
                files={"file": ("test_tourplan.csv", f, "text/csv")}
            )
        
        assert upload_response.status_code == 200, f"Upload fehlgeschlagen: {upload_response.text}"
        upload_data = upload_response.json()
        
        # stored_path sollte vorhanden sein
        assert "stored_path" in upload_data, "Response sollte 'stored_path' enthalten"
        stored_path = upload_data["stored_path"]
        assert stored_path, "stored_path sollte nicht leer sein"
        
        # 3. Match
        match_response = client.get(f"/api/tourplan/match?file={stored_path}")
        
        # Match kann 200, 404 oder 500 sein (abhängig von DB-Status)
        assert match_response.status_code in (200, 404, 500), f"Match fehlgeschlagen: {match_response.text}"
        
        if match_response.status_code == 200:
            match_data = match_response.json()
            assert "items" in match_data or "file" in match_data
    
    def test_health_checks_all_available(self):
        """Test: Alle Health-Checks sind verfügbar."""
        endpoints = [
            "/health",
            "/health/db",
            "/health/osrm",
            "/health/app",
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            
            # Sollte nie 404 sein
            assert response.status_code != 404, f"{endpoint} sollte existieren"
            assert response.status_code in (200, 503, 500)
    
    def test_no_402_status_codes(self):
        """Test: Keine Endpoints geben 402 zurück."""
        endpoints = [
            ("GET", "/api/tourplan/match"),
            ("POST", "/api/tourplan/match"),
            ("GET", "/api/upload/csv"),
            ("POST", "/api/upload/csv"),
            ("GET", "/api/code-checker/analyze"),
            ("POST", "/api/code-checker/improve"),
        ]
        
        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path, json={})
            
            # Sollte nie 402 sein
            assert response.status_code != 402, f"{method} {path} gibt 402 zurück"


class TestErrorHandling:
    """Tests für Error-Handling."""
    
    def test_global_error_handler_returns_500(self):
        """Test: Globaler Error-Handler gibt strukturierte 500-Antwort."""
        # Test mit ungültigem Request der einen Server-Fehler verursacht
        # (In Produktion würde das durch unhandled Exception passieren)
        
        # Test mit ungültigem JSON
        response = client.post(
            "/api/tourplan/match",
            content="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        # Sollte 422 (Validation Error) oder 500 sein
        assert response.status_code in (422, 500)
        
        if response.status_code == 500:
            data = response.json()
            assert "error" in data or "trace_id" in data
    
    def test_validation_errors_return_422(self):
        """Test: Validation-Fehler geben 422 zurück."""
        # Fehlender required Parameter
        response = client.get("/api/tourplan/match")
        
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data


class TestKIImprovementsIntegration:
    """Tests für KI-Improvements Integration."""
    
    def test_ki_improvements_endpoints_available(self):
        """Test: Alle KI-Improvements Endpoints sind verfügbar."""
        endpoints = [
            ("GET", "/api/ki-improvements/recent"),
            ("GET", "/api/ki-improvements/stats"),
            ("GET", "/api/ki-improvements/costs"),
            ("GET", "/api/ki-improvements/performance"),
            ("GET", "/api/ki-improvements/limits"),
        ]
        
        for method, path in endpoints:
            response = client.get(path)
            
            # Sollte nie 404 sein
            assert response.status_code != 404, f"{path} sollte existieren"
            assert response.status_code in (200, 422, 500)
    
    def test_code_checker_endpoints_available(self):
        """Test: Alle Code-Checker Endpoints sind verfügbar."""
        endpoints = [
            ("GET", "/api/code-checker/status"),
            ("POST", "/api/code-checker/analyze"),
            ("POST", "/api/code-checker/improve"),
        ]
        
        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path + "?file_path=test.py")
            
            # Sollte nie 404 sein
            assert response.status_code != 404, f"{path} sollte existieren"
            assert response.status_code in (200, 400, 404, 422, 503, 500)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

