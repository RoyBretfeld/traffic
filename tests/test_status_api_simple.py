from fastapi.testclient import TestClient
from pathlib import Path
import os
import pytest
from unittest.mock import patch, MagicMock

def test_status_api_file_not_found():
    """Test bei nicht existierender Datei."""
    from fastapi import FastAPI
    import routes.tourplan_status as rts
    
    app = FastAPI(); app.include_router(rts.router)
    client = TestClient(app)
    
    r = client.get("/api/tourplan/status", params={"file": "nonexistent.csv"})
    assert r.status_code == 404
    assert "nicht gefunden" in r.json()["detail"]

def test_status_api_with_mock_data():
    """Test mit Mock-Daten ohne PathPolicy-Komplexität."""
    from fastapi import FastAPI
    import routes.tourplan_status as rts
    import pandas as pd
    
    # Mock der read_tourplan Funktion
    def mock_read_tourplan(path):
        return pd.DataFrame({
            "Kunde": ["X", "Y"],
            "Adresse": ["Test Straße 1", "Test Straße 2"]
        })
    
    # Mock der bulk_get Funktion
    def mock_bulk_get(addrs):
        return {"Test Straße 1": {"lat": 50.0, "lon": 8.0}}
    
    # Patch der Funktionen
    original_read_tourplan = rts.read_tourplan
    original_bulk_get = rts.bulk_get
    
    rts.read_tourplan = mock_read_tourplan
    rts.bulk_get = mock_bulk_get
    
    try:
        app = FastAPI(); app.include_router(rts.router)
        client = TestClient(app)
        
        # Mock Path.exists
        with patch('pathlib.Path.exists', return_value=True):
            r = client.get("/api/tourplan/status", params={"file": "mock.csv"})
            assert r.status_code == 200
            j = r.json()
            
            # Response-Format prüfen
            required_fields = ["file", "total", "cached", "missing", "marker_hits", "examples_missing"]
            for field in required_fields:
                assert field in j, f"Field {field} missing in response"
            
            # Logik prüfen
            assert j["total"] == 2  # Zwei Adressen
            assert j["cached"] == 1  # Eine gecacht
            assert j["missing"] == 1  # Eine fehlend
            assert j["total"] == j["cached"] + j["missing"]
            
    finally:
        # Cleanup
        rts.read_tourplan = original_read_tourplan
        rts.bulk_get = original_bulk_get

def test_status_api_response_format():
    """Test des Response-Formats."""
    from fastapi import FastAPI
    import routes.tourplan_status as rts
    import pandas as pd
    
    # Mock mit verschiedenen Adressen (ohne "adresse" im ersten Eintrag)
    def mock_read_tourplan(path):
        return pd.DataFrame({
            0: ["Kunde A", "Kunde B", "Kunde C"],  # Spalte 0: Kunde
            1: ["Straße 1", "Straße 2", "Straße 3"]  # Spalte 1: Adresse (ohne "adresse" im Text)
        })
    
    def mock_bulk_get(addrs):
        return {"Straße 1": {"lat": 50.0, "lon": 8.0}}  # Nur erste Adresse gecacht
    
    # Patch
    original_read_tourplan = rts.read_tourplan
    original_bulk_get = rts.bulk_get
    
    rts.read_tourplan = mock_read_tourplan
    rts.bulk_get = mock_bulk_get
    
    try:
        app = FastAPI(); app.include_router(rts.router)
        client = TestClient(app)
        
        with patch('pathlib.Path.exists', return_value=True):
            r = client.get("/api/tourplan/status", params={"file": "test.csv"})
            assert r.status_code == 200
            j = r.json()
            
            # Typen prüfen
            assert isinstance(j["total"], int)
            assert isinstance(j["cached"], int)
            assert isinstance(j["missing"], int)
            assert isinstance(j["marker_hits"], int)
            assert isinstance(j["examples_missing"], list)
            
            # Logik prüfen (3 Adressen, 1 gecacht, 2 fehlend)
            assert j["total"] == 3
            assert j["cached"] == 1
            assert j["missing"] == 2
            assert len(j["examples_missing"]) == 2  # Zwei fehlende Adressen
            
    finally:
        # Cleanup
        rts.read_tourplan = original_read_tourplan
        rts.bulk_get = original_bulk_get

def test_status_api_marker_detection():
    """Test der Mojibake-Marker-Erkennung."""
    from fastapi import FastAPI
    import routes.tourplan_status as rts
    import pandas as pd
    
    # Mock mit Mojibake-Markern (ohne "adresse" im ersten Eintrag)
    def mock_read_tourplan(path):
        return pd.DataFrame({
            0: ["Kunde X", "Kunde Y"],  # Spalte 0: Kunde
            1: ["Normale Straße", "Straße mit ┬ Mojibake"]  # Spalte 1: Adresse mit Mojibake
        })
    
    def mock_bulk_get(addrs):
        return {}  # Keine gecachten Adressen
    
    # Patch
    original_read_tourplan = rts.read_tourplan
    original_bulk_get = rts.bulk_get
    
    rts.read_tourplan = mock_read_tourplan
    rts.bulk_get = mock_bulk_get
    
    try:
        app = FastAPI(); app.include_router(rts.router)
        client = TestClient(app)
        
        with patch('pathlib.Path.exists', return_value=True):
            r = client.get("/api/tourplan/status", params={"file": "test.csv"})
            assert r.status_code == 200
            j = r.json()
            
            # Mojibake-Marker sollten erkannt werden
            assert j["marker_hits"] >= 1  # Mindestens ein Marker
            assert j["total"] == 2
            assert j["missing"] == 2  # Beide Adressen fehlend
            
    finally:
        # Cleanup
        rts.read_tourplan = original_read_tourplan
        rts.bulk_get = original_bulk_get
