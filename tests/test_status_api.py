from fastapi.testclient import TestClient
from pathlib import Path
import os
import pytest

def test_status_api(tmp_path, monkeypatch):
    """Test des Status-API-Endpoints."""
    # SQLite-DB aufsetzen
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    from importlib import reload
    import db.core as core; reload(core)
    import db.schema as schema; reload(schema); schema.ensure_schema()
    import repositories.geo_repo as repo; reload(repo)

    # Eine Adresse in Cache
    repo.upsert("Fröbelstraße 1", 51.05, 13.74)

    # Original-CSV (cp850) schreiben
    orig = tmp_path/"Tourplaene"; orig.mkdir()
    src = orig/"Plan.csv"
    src.write_bytes("Kunde;Adresse\nX;Fröbelstraße 1\nY;Löbtauer Straße 2\n".encode("cp850"))

    # Staging setzen
    stag = tmp_path/"data"/"staging"; stag.mkdir(parents=True)
    monkeypatch.setenv("STAGING_DIR", str(stag))
    monkeypatch.setenv("VERIFY_ORIG_ON_INGEST", "0")  # Integritätswächter für Tests deaktivieren
    monkeypatch.setenv("ORIG_DIR", str(orig))

    # App mit Status-Route
    import routes.tourplan_status as rts; reload(rts)
    from fastapi import FastAPI
    app = FastAPI(); app.include_router(rts.router)
    client = TestClient(app)

    r = client.get("/api/tourplan/status", params={"file": str(src)})
    assert r.status_code == 200
    j = r.json()
    assert j["total"] == 2 and j["cached"] == 1 and j["missing"] == 1
    assert "examples_missing" in j
    assert len(j["examples_missing"]) == 1  # Eine fehlende Adresse

def test_status_api_file_not_found():
    """Test bei nicht existierender Datei."""
    from fastapi import FastAPI
    import routes.tourplan_status as rts
    
    app = FastAPI(); app.include_router(rts.router)
    client = TestClient(app)
    
    r = client.get("/api/tourplan/status", params={"file": "nonexistent.csv"})
    assert r.status_code == 404
    assert "nicht gefunden" in r.json()["detail"]

def test_status_api_response_format(tmp_path, monkeypatch):
    """Test des Response-Formats."""
    # Minimal Setup
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    from importlib import reload
    import db.core as core; reload(core)
    import db.schema as schema; reload(schema); schema.ensure_schema()
    
    # CSV erstellen
    orig = tmp_path/"Tourplaene"; orig.mkdir()
    src = orig/"Test.csv"
    src.write_bytes("Kunde;Adresse\nA;Test Straße 1\nB;Test Straße 2\n".encode("cp850"))
    
    # Staging
    stag = tmp_path/"data"/"staging"; stag.mkdir(parents=True)
    monkeypatch.setenv("STAGING_DIR", str(stag))
    monkeypatch.setenv("VERIFY_ORIG_ON_INGEST", "0")
    monkeypatch.setenv("ORIG_DIR", str(orig))
    
    # Test
    import routes.tourplan_status as rts; reload(rts)
    from fastapi import FastAPI
    app = FastAPI(); app.include_router(rts.router)
    client = TestClient(app)
    
    r = client.get("/api/tourplan/status", params={"file": str(src)})
    assert r.status_code == 200
    j = r.json()
    
    # Response-Format prüfen
    required_fields = ["file", "total", "cached", "missing", "marker_hits", "examples_missing"]
    for field in required_fields:
        assert field in j, f"Field {field} missing in response"
    
    # Typen prüfen
    assert isinstance(j["total"], int)
    assert isinstance(j["cached"], int)
    assert isinstance(j["missing"], int)
    assert isinstance(j["marker_hits"], int)
    assert isinstance(j["examples_missing"], list)
    
    # Logik prüfen
    assert j["total"] == j["cached"] + j["missing"]
    assert j["total"] == 2  # Zwei Adressen in der Test-CSV
