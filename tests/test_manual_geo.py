import os
from importlib import reload
import pytest
from pathlib import Path
import sqlite3

def test_manual_geo_api(tmp_path, monkeypatch):
    """Test der manuellen Koordinaten-Eingabe API."""
    # SQLite DSN setzen
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    # Module neu laden mit neuer DB-URL
    import db.core as core
    reload(core)
    
    import db.schema as base
    reload(base)
    base.ensure_schema()
    
    # Repositories neu laden
    import repositories.geo_repo as repo
    reload(repo)
    
    # Test: Manuelle Koordinaten speichern
    test_address = "Teststraße 123, 01234 Teststadt"
    test_lat = 51.0504
    test_lon = 13.7373
    
    # Speichern mit source="manual"
    result = repo.upsert(test_address, test_lat, test_lon, source="manual", by_user="test_user")
    
    assert result["address_norm"] == test_address
    assert result["lat"] == test_lat
    assert result["lon"] == test_lon
    assert result["source"] == "manual"
    assert result["by_user"] == "test_user"
    
    # Verifizieren dass in DB gespeichert (SQLite direkt)
    db_path = Path(tmp_path) / "t.db"
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT address_norm, lat, lon, source, by_user FROM geo_cache WHERE address_norm=?",
        (test_address,)
    )
    row = cursor.fetchone()
    conn.close()
    
    assert row is not None, "Eintrag sollte in DB gespeichert sein"
    assert row[0] == test_address, "address_norm sollte übereinstimmen"
    assert abs(row[1] - test_lat) < 1e-6, "lat sollte übereinstimmen"
    assert abs(row[2] - test_lon) < 1e-6, "lon sollte übereinstimmen"
    assert row[3] == "manual", "source sollte 'manual' sein"
    assert row[4] == "test_user", "by_user sollte 'test_user' sein"

def test_manual_geo_api_endpoint(tmp_path, monkeypatch):
    """Test des API-Endpoints für manuelle Koordinaten."""
    # SQLite DSN setzen
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    # Module neu laden
    import db.core as core
    reload(core)
    
    import db.schema as base
    reload(base)
    base.ensure_schema()
    
    # Migration ausführen - ENTFERNT: redundant da ensure_schema() bereits alle Spalten erstellt
    # from db.migrate_schema import migrate_geo_cache_schema
    # migrate_geo_cache_schema()
    
    # FastAPI App importieren
    from backend.app import create_app
    app = create_app()
    
    from fastapi.testclient import TestClient
    client = TestClient(app)
    
    # Test: POST /api/tourplan/manual-geo
    response = client.post("/api/tourplan/manual-geo", json={
        "address": "Teststraße 123, 01234 Teststadt",
        "latitude": 51.0504,
        "longitude": 13.7373,
        "by_user": "test_user"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["ok"] is True
    assert "Koordinaten für" in data["message"]
    assert data["coordinates"]["lat"] == 51.0504
    assert data["coordinates"]["lon"] == 13.7373
    
    # Test: Ungültige Koordinaten
    response = client.post("/api/tourplan/manual-geo", json={
        "address": "Teststraße 123, 01234 Teststadt",
        "latitude": 91.0,  # Ungültig (> 90)
        "longitude": 13.7373,
        "by_user": "test_user"
    })
    
    assert response.status_code == 422  # Pydantic-Validierung gibt 422 zurück
    error_detail = response.json()["detail"]
    assert any("less than or equal to 90" in str(error) for error in error_detail)

def test_manual_geo_update_existing():
    """Test dass manuelle Koordinaten bestehende Einträge aktualisieren."""
    # Test mit bestehender Adresse
    test_address = "Update Teststraße 456, 05678 Updatestadt"
    
    # Erst normale Geocoding-Koordinaten
    from repositories.geo_repo import upsert, get
    upsert(test_address, 50.0, 10.0, source="geocoded", by_user="nominatim")
    
    # Dann manuelle Koordinaten (sollte Update sein)
    result = upsert(test_address, 51.0, 11.0, source="manual", by_user="user")
    
    assert result["lat"] == 51.0
    assert result["lon"] == 11.0
    assert result["source"] == "manual"
    assert result["by_user"] == "user"
    
    # Verifizieren dass nur ein Eintrag existiert
    retrieved = get(test_address)
    assert retrieved is not None
    assert abs(retrieved["lat"] - 51.0) < 1e-6
    assert abs(retrieved["lon"] - 11.0) < 1e-6
