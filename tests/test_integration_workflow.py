#!/usr/bin/env python3
"""
Integration-Tests für kompletten Workflow
CSV-Upload → Geocoding → Optimierung → Sub-Routen
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import io

from backend.app import create_app


@pytest.fixture
def client():
    """FastAPI Test-Client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_workflow_csv():
    """Beispiel-CSV für Workflow-Test"""
    return """Tour;Name;Straße;PLZ;Ort;
W-07.00 Uhr Tour;Kuli's Carpoint;Reisstr. 40;01257;Dresden
W-07.00 Uhr Tour;DISTREX Fahrzeugservice e.K.;Wiener Str. 10;01069;Dresden
W-07.00 Uhr Tour;1a autoservice Menzel;Bauerweg 12;01109;Dresden
W-07.00 Uhr Tour;Motorenreinstandsetzung;Am Trachauer Bahnhof 11;01139;Dresden
W-07.00 Uhr Tour;Autohaus Zimmermann;Am Trachauer Bahnhof 9;01139;Dresden
"""


class TestIntegrationWorkflow:
    """Integration-Tests für den kompletten Workflow"""
    
    def test_health_endpoints(self, client):
        """Test: Alle Health-Endpoints sind erreichbar"""
        endpoints = [
            "/health/app",
            "/health/db",
            "/health/osrm",
            "/health/status"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            assert response.status_code in [200, 503], f"{endpoint} nicht erreichbar: {response.status_code}"
    
    def test_api_docs_accessible(self, client):
        """Test: OpenAPI-Dokumentation ist zugänglich"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "paths" in data
    
    def test_workflow_upload_endpoint_exists(self, client):
        """Test: Workflow-Upload-Endpoint existiert"""
        # POST ohne Datei sollte 422 geben
        response = client.post("/api/workflow/upload")
        assert response.status_code == 422
    
    def test_tour_optimize_endpoint_exists(self, client):
        """Test: Tour-Optimize-Endpoint existiert"""
        # POST ohne Body sollte 422 geben
        response = client.post("/api/tour/optimize")
        assert response.status_code == 422
    
    def test_workflow_upload_with_csv(self, client, sample_workflow_csv):
        """Test: CSV-Upload im Workflow"""
        files = {
            "file": ("test_workflow.csv", io.BytesIO(sample_workflow_csv.encode('cp850')), "text/csv")
        }
        
        response = client.post("/api/workflow/upload", files=files)
        
        # Prüfe Response
        assert response.status_code == 200, f"Workflow-Upload fehlgeschlagen: {response.status_code}"
        data = response.json()
        
        # Prüfe Struktur
        assert "success" in data
        assert "tours" in data
        
        if data.get("success"):
            tours = data.get("tours", [])
            assert isinstance(tours, list)
    
    def test_tour_optimization_with_valid_data(self, client):
        """Test: Tour-Optimierung mit gültigen Daten"""
        tour_data = {
            "tour_id": "TEST-TOUR",
            "stops": [
                {
                    "customer_number": "1001",
                    "name": "Test Kunde 1",
                    "address": "Teststraße 1, 01234 Dresden",
                    "lat": 51.0404,
                    "lon": 13.7320
                },
                {
                    "customer_number": "1002",
                    "name": "Test Kunde 2",
                    "address": "Teststraße 2, 01234 Dresden",
                    "lat": 51.0636,
                    "lon": 13.7404
                }
            ]
        }
        
        response = client.post("/api/tour/optimize", json=tour_data)
        
        # Sollte 200 zurückgeben (mit success:true oder success:false)
        assert response.status_code == 200, f"Tour-Optimierung fehlgeschlagen: {response.status_code}"
        data = response.json()
        
        assert "success" in data
        
        if data.get("success"):
            assert "optimized_stops" in data
            assert "estimated_driving_time_minutes" in data
            assert "estimated_service_time_minutes" in data
            assert "estimated_total_time_minutes" in data
    
    def test_tour_optimization_with_invalid_data(self, client):
        """Test: Tour-Optimierung mit ungültigen Daten"""
        invalid_data = {
            "tour_id": "INVALID",
            "stops": []  # Keine Stopps
        }
        
        response = client.post("/api/tour/optimize", json=invalid_data)
        
        # Sollte 200 mit success:false oder 422 geben
        assert response.status_code in [200, 422]
    
    def test_geocoding_flow(self, client):
        """Test: Geocoding-Flow (DB-Upload → Geocoding → Stats)"""
        # 1. Lade DB-Statistiken VOR Upload
        response_before = client.get("/api/db/stats")
        assert response_before.status_code == 200
        stats_before = response_before.json()
        
        # 2. Upload CSV für Geocoding
        csv_content = """Tour;Name;Straße;PLZ;Ort
W-Test;Test GmbH;Teststr. 1;01234;Dresden
"""
        files = {
            "file": ("geocode_test.csv", io.BytesIO(csv_content.encode('cp850')), "text/csv")
        }
        
        response_upload = client.post("/api/tourplan/batch-geocode", files=files)
        assert response_upload.status_code == 200
        
        # 3. Lade DB-Statistiken NACH Upload
        response_after = client.get("/api/db/stats")
        assert response_after.status_code == 200
        stats_after = response_after.json()
        
        # Statistiken sollten sich geändert haben (oder gleich bleiben bei Duplikaten)
        assert stats_after["total_customers"] >= stats_before["total_customers"]


class TestSystemRulesAPI:
    """Tests für System-Regeln-API"""
    
    def test_get_system_rules(self, client):
        """Test: System-Regeln abrufen"""
        response = client.get("/api/system/rules")
        assert response.status_code == 200
        
        data = response.json()
        
        # Prüfe erforderliche Felder
        required_fields = [
            "time_budget_without_return",
            "time_budget_with_return",
            "service_time_per_stop",
            "speed_kmh",
            "safety_factor",
            "depot_lat",
            "depot_lon"
        ]
        
        for field in required_fields:
            assert field in data, f"Feld {field} fehlt in System-Regeln"
    
    def test_system_rules_self_check(self, client):
        """Test: System-Regeln Self-Check"""
        response = client.get("/api/system/rules/self-check")
        assert response.status_code in [200, 500]
        
        data = response.json()
        assert "status" in data
        assert "details" in data


class TestErrorHandling:
    """Tests für Fehlerbehandlung"""
    
    def test_404_for_nonexistent_endpoint(self, client):
        """Test: 404 für nicht-existierende Endpoints"""
        response = client.get("/api/nonexistent/endpoint")
        assert response.status_code == 404
    
    def test_405_for_wrong_method(self, client):
        """Test: 405 für falsche HTTP-Methode"""
        # GET statt POST
        response = client.get("/api/tour/optimize")
        assert response.status_code in [405, 422]
    
    def test_422_for_missing_parameters(self, client):
        """Test: 422 für fehlende Parameter"""
        # POST ohne required body
        response = client.post("/api/tour/optimize")
        assert response.status_code == 422
    
    def test_unicode_in_response(self, client):
        """Test: Unicode in API-Responses wird korrekt behandelt"""
        # Upload CSV mit Umlauten
        csv_with_umlauts = """Tour;Name;Straße;PLZ;Ort
W-Test;Müller GmbH;Äußere Straße 1;01234;München
"""
        files = {
            "file": ("umlauts.csv", io.BytesIO(csv_with_umlauts.encode('cp850')), "text/csv")
        }
        
        response = client.post("/api/workflow/upload", files=files)
        
        # Sollte nicht crashen
        assert response.status_code == 200
        
        # Response sollte parsebar sein
        try:
            data = response.json()
            success = True
        except Exception:
            success = False
        
        assert success, "Response mit Umlauten konnte nicht geparst werden"


class TestMetricsAndMonitoring:
    """Tests für Metriken und Monitoring"""
    
    def test_metrics_endpoint(self, client):
        """Test: Metriken-Endpoint"""
        response = client.get("/metrics/simple")
        
        if response.status_code == 200:
            data = response.json()
            assert "http_4xx" in data or "http_5xx" in data
    
    def test_health_status_comprehensive(self, client):
        """Test: Umfassender Health-Status"""
        response = client.get("/health/status")
        assert response.status_code == 200
        
        data = response.json()
        
        # Prüfe ob wichtige Services gelistet sind
        assert "app" in data or "db" in data or "osrm" in data


class TestConcurrencyAndRaceConditions:
    """Tests für Concurrency und Race-Conditions"""
    
    @pytest.mark.slow
    def test_concurrent_tour_optimizations(self, client):
        """Test: Mehrere Tour-Optimierungen gleichzeitig"""
        import concurrent.futures
        
        def optimize_tour(tour_id):
            tour_data = {
                "tour_id": tour_id,
                "stops": [
                    {"customer_number": "1", "name": "Kunde 1", "address": "Test 1", "lat": 51.0, "lon": 13.7},
                    {"customer_number": "2", "name": "Kunde 2", "address": "Test 2", "lat": 51.1, "lon": 13.8}
                ]
            }
            return client.post("/api/tour/optimize", json=tour_data)
        
        # Führe 5 Optimierungen parallel aus
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(optimize_tour, f"CONCURRENT-{i}") for i in range(5)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        
        # Alle sollten erfolgreich sein (oder graceful fail mit 200)
        for response in results:
            assert response.status_code == 200


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

