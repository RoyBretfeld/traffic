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

def test_status_api_debug_addr_col():
    """Debug-Test für _addr_col Funktion."""
    import routes.tourplan_status as rts
    import pandas as pd
    
    # Test DataFrame mit Header in erster Zeile
    df_with_header = pd.DataFrame({
        0: ["Kunde", "A", "B"],  # Erste Zeile ist Header
        1: ["Adresse", "Adresse 1", "Adresse 2"]
    })
    
    col, offset = rts._addr_col(df_with_header)
    print(f"Header erkannt: col={col}, offset={offset}")
    assert col == 1  # Adresse-Spalte
    assert offset == 1  # Header überspringen
    
    # Test DataFrame ohne Header
    df_no_header = pd.DataFrame({
        0: ["A", "B"],  # Kein Header
        1: ["Adresse 1", "Adresse 2"]
    })
    
    col, offset = rts._addr_col(df_no_header)
    print(f"Kein Header: col={col}, offset={offset}")
    assert col == 1  # Adresse-Spalte (letzte Spalte)
    assert offset == 0  # Kein Header zu überspringen

def test_status_api_simple():
    """Einfacher Test ohne komplexe Mocking."""
    from fastapi import FastAPI
    import routes.tourplan_status as rts
    import pandas as pd
    
    # Mock mit einfachen Daten
    def mock_read_tourplan(path):
        # DataFrame ohne Header (wie echte CSV-Daten)
        return pd.DataFrame({
            0: ["A", "B"],  # Spalte 0: Kunde
            1: ["Adresse 1", "Adresse 2"]  # Spalte 1: Adresse
        })
    
    def mock_bulk_get(addrs):
        return {"Adresse 1": {"lat": 50.0, "lon": 8.0}}
    
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
            
            # Debug-Ausgabe
            print(f"Response: {j}")
            
            # Basis-Checks
            assert "total" in j
            assert "cached" in j
            assert "missing" in j
            assert j["total"] >= 0
            assert j["cached"] >= 0
            assert j["missing"] >= 0
            
    finally:
        # Cleanup
        rts.read_tourplan = original_read_tourplan
        rts.bulk_get = original_bulk_get
