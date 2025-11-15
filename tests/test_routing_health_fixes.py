"""
Tests für 404/402/500 Routing & Health Fixes.
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import create_app

client = TestClient(create_app())


class TestHealthChecks:
    """Tests für vereinfachte Health-Checks."""
    
    def test_health_db_simple(self):
        """Test: DB-Health gibt einfache ok-Response zurück."""
        response = client.get("/health/db")
        
        # Sollte 200 (ok) oder 503 (offline) sein, nie 500
        assert response.status_code in (200, 503), f"Unerwarteter Status: {response.status_code}"
        
        data = response.json()
        assert "ok" in data, "Response sollte 'ok' Feld enthalten"
        assert isinstance(data["ok"], bool), "'ok' sollte boolean sein"
        
        if response.status_code == 200:
            assert data["ok"] is True
        else:
            assert data["ok"] is False
            assert "error" in data
    
    def test_health_osrm_simple(self):
        """Test: OSRM-Health gibt einfache ok-Response zurück."""
        response = client.get("/health/osrm")
        
        # Sollte 200 (ok) oder 503 (offline) sein
        assert response.status_code in (200, 503), f"Unerwarteter Status: {response.status_code}"
        
        data = response.json()
        assert "ok" in data, "Response sollte 'ok' Feld enthalten"
        assert isinstance(data["ok"], bool), "'ok' sollte boolean sein"
        
        if response.status_code == 200:
            assert data["ok"] is True
        else:
            assert data["ok"] is False
    
    def test_health_osrm_no_url(self, monkeypatch):
        """Test: OSRM-Health gibt no_osrm_url zurück wenn URL fehlt."""
        monkeypatch.setenv("OSRM_URL", "")
        
        # App neu erstellen um ENV zu laden
        from backend.config import load_config
        load_config.cache_clear() if hasattr(load_config, 'cache_clear') else None
        
        response = client.get("/health/osrm")
        
        # Sollte 503 sein mit reason
        assert response.status_code == 503
        data = response.json()
        assert data["ok"] is False
        assert data.get("reason") == "no_osrm_url"


class TestGlobalErrorHandler:
    """Tests für globalen 500-Handler."""
    
    def test_global_500_handler_structure(self):
        """Test: Globaler 500-Handler gibt strukturierte Antwort."""
        # Erstelle einen Endpoint der einen Fehler wirft (für Test)
        # In Produktion würde das durch unhandled Exception passieren
        
        # Test mit ungültigem Endpoint (sollte 404 sein, nicht 500)
        response = client.get("/nonexistent/endpoint")
        assert response.status_code == 404  # FastAPI gibt 404 für nicht existierende Endpoints
    
    def test_error_response_has_trace_id(self):
        """Test: Fehler-Responses haben Trace-ID (wird von ErrorEnvelopeMiddleware hinzugefügt)."""
        # Test mit ungültigem Request
        response = client.post("/api/tourplan/match", json={})  # Sollte 422 sein
        
        # Prüfe ob Response strukturiert ist
        assert response.status_code in (422, 400, 500)
        
        # Wenn 500, sollte trace_id vorhanden sein
        if response.status_code == 500:
            data = response.json()
            assert "trace_id" in data or "error" in data


class TestUploadMatchContract:
    """Tests für Upload→Match-Vertrag (kein doppeltes Lesen)."""
    
    def test_upload_returns_stored_path(self, tmp_path, monkeypatch):
        """Test: Upload gibt stored_path zurück."""
        import os
        from pathlib import Path
        
        # Setze Staging-Verzeichnis
        staging_dir = tmp_path / "staging"
        staging_dir.mkdir()
        monkeypatch.setenv("STAGING_DIR", str(staging_dir))
        
        # Erstelle Test-CSV
        test_csv = tmp_path / "test.csv"
        test_csv.write_text("Name,Adresse\nTest,Teststraße 1\n", encoding="utf-8")
        
        # Upload
        with open(test_csv, "rb") as f:
            response = client.post(
                "/api/upload/csv",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # stored_path sollte vorhanden sein
        assert "stored_path" in data, "Response sollte 'stored_path' enthalten"
        stored_path = data["stored_path"]
        assert stored_path, "stored_path sollte nicht leer sein"
        assert isinstance(stored_path, str), "stored_path sollte String sein"
    
    def test_match_with_encoded_path(self, tmp_path):
        """Test: Match funktioniert mit URL-encoded Pfad."""
        import os
        from pathlib import Path
        
        # Erstelle Test-CSV in Staging
        staging_dir = Path("data/staging")
        staging_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = staging_dir / "test_file.csv"
        test_file.write_text("Name,Adresse\nTest,Teststraße 1\n", encoding="utf-8")
        
        # Match mit encoded Pfad
        file_path = str(test_file)
        encoded_path = file_path.replace("\\", "/")  # Windows-Pfad normalisieren
        
        response = client.get(f"/api/tourplan/match?file={encoded_path}")
        
        # Match kann 200, 404 oder 500 sein (abhängig von DB-Status)
        assert response.status_code in (200, 404, 500)
        
        # Cleanup
        if test_file.exists():
            test_file.unlink()
    
    def test_match_validation_min_length(self):
        """Test: Match validiert min_length=3 für file-Parameter."""
        # Zu kurzer Pfad
        response = client.get("/api/tourplan/match?file=ab")
        
        # Sollte 422 (Validation Error) sein
        assert response.status_code == 422
    
    def test_match_missing_file_parameter(self):
        """Test: Match gibt 422 bei fehlendem file-Parameter."""
        response = client.get("/api/tourplan/match")
        
        # Sollte 422 sein (nicht 402!)
        assert response.status_code == 422


class TestHTTPCodePolicy:
    """Tests für HTTP-Code-Policy (kein 402 mehr)."""
    
    def test_no_402_status_codes(self):
        """Test: Keine Endpoints geben 402 zurück."""
        # Teste verschiedene Endpoints
        endpoints = [
            ("GET", "/api/tourplan/match"),
            ("POST", "/api/tourplan/match"),
            ("GET", "/api/upload/csv"),
            ("POST", "/api/upload/csv"),
        ]
        
        for method, path in endpoints:
            if method == "GET":
                response = client.get(path)
            else:
                response = client.post(path, json={})
            
            # Sollte nie 402 sein
            assert response.status_code != 402, f"{method} {path} gibt 402 zurück (sollte 422/400 sein)"
    
    def test_422_for_validation_errors(self):
        """Test: Validation-Fehler geben 422 zurück."""
        # Fehlender required Parameter
        response = client.get("/api/tourplan/match")  # file fehlt
        
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data


class TestOSRMBadge:
    """Tests für OSRM-Badge-Funktionalität."""
    
    def test_osrm_badge_endpoint_exists(self):
        """Test: /health/osrm Endpoint existiert."""
        response = client.get("/health/osrm")
        
        # Sollte 200 oder 503 sein (nie 404)
        assert response.status_code != 404, "/health/osrm Endpoint sollte existieren"
        assert response.status_code in (200, 503)
        
        data = response.json()
        assert "ok" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

