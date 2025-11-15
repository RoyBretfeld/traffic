from fastapi.testclient import TestClient
from pathlib import Path
import os
import pytest
import pandas as pd
import io

def test_match_endpoint_simple():
    """Einfacher Test ohne komplexe PathPolicy."""
    from fastapi import FastAPI
    from backend.routes.tourplan_match import router
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Test mit nicht existierender Datei
    resp = client.get("/api/tourplan/match", params={"file": "nonexistent.csv"})
    assert resp.status_code == 404
    assert "nicht gefunden" in resp.json()["detail"]

def test_match_endpoint_with_mock_data(tmp_path, monkeypatch):
    """Test mit Mock-Daten ohne PathPolicy-Komplexität."""
    # 1) DB Setup
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    from importlib import reload
    import db.core as core; reload(core)
    import db.schema as schema; reload(schema); schema.ensure_schema()
    import repositories.geo_repo as repo; reload(repo)
    
    # Test-Daten einfügen
    repo.upsert("Löbtauer Straße 1, 01809 Heidenau", 50.9836, 13.8663)
    
    # 2) Mock CSV-Daten direkt als DataFrame
    test_data = pd.DataFrame({
        "Kunde": ["X", "Y"],
        "Adresse": ["Löbtauer Straße 1, 01809 Heidenau", "Unbekannte Straße 123"]
    })
    
    # 3) Mock der read_tourplan Funktion
    def mock_read_tourplan(path):
        return test_data
    
    # 4) Patch der Funktionen
    import backend.routes.tourplan_match as rtm
    from pathlib import Path
    original_read_tourplan = rtm.read_tourplan
    original_path_exists = Path.exists
    
    rtm.read_tourplan = mock_read_tourplan
    Path.exists = lambda self: True  # Mock: alle Pfade existieren
    
    try:
        # 5) App Setup
        from fastapi import FastAPI
        app = FastAPI()
        app.include_router(rtm.router)
        client = TestClient(app)
        
        # 6) Test mit Mock-Datei
        resp = client.get("/api/tourplan/match", params={"file": "mock.csv"})
        assert resp.status_code == 200
        j = resp.json()
        
        # 7) Validierung
        assert j["rows"] == 2
        assert j["ok"] == 1  # Eine Adresse sollte gefunden werden
        assert j["warn"] == 1  # Eine Adresse sollte nicht gefunden werden
        assert j["bad"] == 0  # Keine Mojibake-Marker
        
        # 8) Erste Adresse gefunden
        first = j["items"][0]
        assert first["has_geo"] is True
        assert first["geo"]["lat"] == 50.9836
        assert first["status"] == "ok"
        
        # 9) Zweite Adresse nicht gefunden
        second = j["items"][1]
        assert second["has_geo"] is False
        assert second["status"] == "warn"
        
    finally:
        # Cleanup
        rtm.read_tourplan = original_read_tourplan
        Path.exists = original_path_exists

def test_match_endpoint_mojibake_detection_simple():
    """Test Mojibake-Erkennung ohne komplexe Setup."""
    from fastapi import FastAPI
    from backend.routes.tourplan_match import router
    import pandas as pd
    
    app = FastAPI()
    app.include_router(router)
    client = TestClient(app)
    
    # Mock CSV mit Mojibake
    test_data_with_mojibake = pd.DataFrame({
        "Kunde": ["X", "Y"],
        "Adresse": ["Löbtauer Straße 1, 01809 Heidenau", "Fröbelstraße 5┬"]  # Mojibake-Marker
    })
    
    # Mock der Funktionen
    import backend.routes.tourplan_match as rtm
    from pathlib import Path
    original_read_tourplan = rtm.read_tourplan
    original_path_exists = Path.exists
    
    rtm.read_tourplan = lambda path: test_data_with_mojibake
    Path.exists = lambda self: True  # Mock: alle Pfade existieren
    
    try:
        resp = client.get("/api/tourplan/match", params={"file": "mock.csv"})
        assert resp.status_code == 200
        j = resp.json()
        
        # Mojibake sollte erkannt werden
        assert j["bad"] >= 1  # Mindestens eine Zeile mit Mojibake
        bad_items = [item for item in j["items"] if item["status"] == "bad"]
        assert len(bad_items) >= 1
        assert "┬" in bad_items[0]["markers"]  # Mojibake-Marker sollte erkannt werden
        
    finally:
        # Cleanup
        rtm.read_tourplan = original_read_tourplan
        Path.exists = original_path_exists
