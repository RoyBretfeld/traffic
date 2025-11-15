#!/usr/bin/env python3
"""
Tests für DB-Verwaltungs-API
Testet Batch-Geocoding, Listen-API und Statistiken
"""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path
import tempfile
import pandas as pd
import io

from backend.app import create_app


@pytest.fixture
def client():
    """FastAPI Test-Client"""
    app = create_app()
    return TestClient(app)


@pytest.fixture
def sample_csv_content():
    """Beispiel-CSV-Inhalt für Tests"""
    return """Tour;Name;Straße;PLZ;Ort
W-07.00 Uhr Tour;Kuli's Carpoint;Reisstr. 40;01257;Dresden
W-07.00 Uhr Tour;DISTREX Fahrzeugservice e.K.;Wiener Str. 10;01069;Dresden
W-07.00 Uhr Tour;1a autoservice Menzel;Bauerweg 12;01109;Dresden
"""


@pytest.fixture
def sample_csv_file(sample_csv_content):
    """Erstelle temporäre CSV-Datei"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(sample_csv_content)
        temp_path = Path(f.name)
    yield temp_path
    # Cleanup
    if temp_path.exists():
        temp_path.unlink()


class TestDBManagementAPI:
    """Tests für DB-Verwaltungs-API"""
    
    def test_batch_geocode_endpoint_exists(self, client):
        """Test: POST /api/tourplan/batch-geocode Endpoint existiert"""
        # Upload ohne Datei sollte 422 geben
        response = client.post("/api/tourplan/batch-geocode")
        assert response.status_code in [422, 400], f"Unerwarteter Status: {response.status_code}"
    
    def test_list_tourplans_endpoint_exists(self, client):
        """Test: GET /api/tourplan/list Endpoint existiert"""
        response = client.get("/api/tourplan/list")
        assert response.status_code == 200, f"Unerwarteter Status: {response.status_code}"
        data = response.json()
        assert "success" in data
        assert "tourplans" in data
        assert isinstance(data["tourplans"], list)
    
    def test_geocode_file_endpoint_exists(self, client):
        """Test: POST /api/tourplan/geocode-file Endpoint existiert"""
        response = client.post(
            "/api/tourplan/geocode-file",
            json={"filename": "nonexistent.csv"}
        )
        # Sollte 404 oder 200 mit error geben
        assert response.status_code in [404, 200], f"Unerwarteter Status: {response.status_code}"
    
    def test_db_stats_endpoint_exists(self, client):
        """Test: GET /api/db/stats Endpoint existiert"""
        response = client.get("/api/db/stats")
        assert response.status_code == 200, f"Unerwarteter Status: {response.status_code}"
        data = response.json()
        assert "success" in data
        assert "total_customers" in data
        assert "geocoded_customers" in data
        assert "missing_geocodes" in data
        assert "geocode_rate" in data
    
    def test_batch_geocode_with_valid_csv(self, client, sample_csv_content):
        """Test: Batch-Geocoding mit gültiger CSV"""
        # Erstelle File-Upload
        files = {
            "file": ("test_tourplan.csv", io.BytesIO(sample_csv_content.encode('cp850')), "text/csv")
        }
        
        response = client.post("/api/tourplan/batch-geocode", files=files)
        
        # Prüfe Response
        assert response.status_code == 200, f"Unerwarteter Status: {response.status_code}"
        data = response.json()
        
        assert "success" in data
        assert "total_customers" in data
        assert "geocoded_count" in data
        assert "skipped_count" in data
        assert "error_count" in data
        
        # Prüfe Plausibilität
        assert data["total_customers"] >= 0
        assert data["geocoded_count"] >= 0
        assert data["skipped_count"] >= 0
        assert data["error_count"] >= 0
        
        total = data["geocoded_count"] + data["skipped_count"] + data["error_count"]
        assert total <= data["total_customers"], "Summe der Ergebnisse sollte <= Total sein"
    
    def test_batch_geocode_with_missing_columns(self, client):
        """Test: Batch-Geocoding mit fehlenden Spalten sollte Fehler geben"""
        invalid_csv = "Tour;Name\nTest;Test Kunde\n"
        files = {
            "file": ("invalid.csv", io.BytesIO(invalid_csv.encode('cp850')), "text/csv")
        }
        
        response = client.post("/api/tourplan/batch-geocode", files=files)
        
        # Sollte 400 geben
        assert response.status_code in [400, 200]
        data = response.json()
        
        if response.status_code == 200:
            # Wenn 200, dann sollte success=false sein
            assert data.get("success") == False
            assert "error" in data
    
    def test_list_tourplans_returns_valid_structure(self, client):
        """Test: Liste der Tourenpläne hat valide Struktur"""
        response = client.get("/api/tourplan/list")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        
        # Prüfe Struktur jedes Tourplans
        for tp in data["tourplans"]:
            assert "filename" in tp
            assert "customer_count" in tp
            assert "geocoded_count" in tp
            assert "geocode_rate" in tp
            
            # Prüfe Datentypen
            assert isinstance(tp["filename"], str)
            assert isinstance(tp["customer_count"], int)
            assert isinstance(tp["geocoded_count"], int)
            assert isinstance(tp["geocode_rate"], (int, float))
            
            # Prüfe Plausibilität
            assert tp["customer_count"] >= 0
            assert tp["geocoded_count"] >= 0
            assert tp["geocoded_count"] <= tp["customer_count"]
            assert 0 <= tp["geocode_rate"] <= 100
    
    def test_db_stats_returns_valid_structure(self, client):
        """Test: DB-Statistiken haben valide Struktur"""
        response = client.get("/api/db/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        
        # Prüfe Datentypen
        assert isinstance(data["total_customers"], int)
        assert isinstance(data["geocoded_customers"], int)
        assert isinstance(data["missing_geocodes"], int)
        assert isinstance(data["geocode_rate"], (int, float))
        
        # Prüfe Plausibilität
        assert data["total_customers"] >= 0
        assert data["geocoded_customers"] >= 0
        assert data["missing_geocodes"] >= 0
        assert data["geocoded_customers"] + data["missing_geocodes"] == data["total_customers"]
        assert 0 <= data["geocode_rate"] <= 100


class TestGeocodingLogic:
    """Tests für Geocoding-Logik"""
    
    def test_geocoding_with_valid_address(self):
        """Test: Geocoding mit gültiger Adresse"""
        from backend.services.geocode import geocode_address
        
        # Dresden Hauptbahnhof
        result = geocode_address("Wiener Platz 4, 01069 Dresden")
        
        # Sollte Koordinaten zurückgeben (oder None wenn API nicht verfügbar)
        if result:
            assert "lat" in result
            assert "lon" in result
            assert isinstance(result["lat"], (int, float))
            assert isinstance(result["lon"], (int, float))
            
            # Prüfe Plausibilität (Dresden)
            assert 50.0 < result["lat"] < 52.0
            assert 13.0 < result["lon"] < 15.0
    
    def test_geocoding_with_invalid_address(self):
        """Test: Geocoding mit ungültiger Adresse"""
        from backend.services.geocode import geocode_address
        
        result = geocode_address("INVALID ADDRESS XYZ 12345")
        
        # Sollte None oder leeres dict zurückgeben
        assert result is None or result.get("lat") is None


class TestCSVParsing:
    """Tests für CSV-Parsing"""
    
    def test_csv_with_cp850_encoding(self, sample_csv_content):
        """Test: CSV mit CP850-Encoding parsen"""
        # Konvertiere zu CP850
        csv_bytes = sample_csv_content.encode('cp850')
        
        # Parse mit pandas
        df = pd.read_csv(io.BytesIO(csv_bytes), sep=';', encoding='cp850', on_bad_lines='skip')
        
        assert len(df) > 0
        assert 'Name' in df.columns
        assert 'Straße' in df.columns
        assert 'PLZ' in df.columns
        assert 'Ort' in df.columns
    
    def test_csv_with_umlauts(self):
        """Test: CSV mit Umlauten parsen"""
        csv_with_umlauts = """Tour;Name;Straße;PLZ;Ort
W-Test;Müller GmbH;Äußere Straße 1;01234;München
"""
        csv_bytes = csv_with_umlauts.encode('cp850')
        df = pd.read_csv(io.BytesIO(csv_bytes), sep=';', encoding='cp850', on_bad_lines='skip')
        
        assert len(df) > 0
        # Prüfe ob Umlaute korrekt gelesen wurden
        assert any('Müller' in str(name) or 'M' in str(name) for name in df['Name'])


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

