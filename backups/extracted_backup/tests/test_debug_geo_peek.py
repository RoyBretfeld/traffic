#!/usr/bin/env python3
"""
Tests für debug_geo Route
"""

import pytest
import tempfile
import os
from pathlib import Path
from importlib import reload
from fastapi.testclient import TestClient


def test_debug_peek(tmp_path, monkeypatch):
    """Teste debug/geo/peek Endpoint."""
    # Isoliere Test-Datenbank
    test_db_path = tmp_path / "test_debug.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    # Test-Eintrag einfügen
    repo.upsert("Froebelstraße 1, Dresden", 51.0504, 13.7373)
    
    import routes.debug_geo as dbg
    reload(dbg)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(dbg.router)
    client = TestClient(app)
    
    # Test mit normalisierter Adresse
    response = client.get("/debug/geo/peek", params={"addr": " Froebelstraße 1, Dresden "})
    assert response.status_code == 200
    
    data = response.json()
    assert data["hit"] is True
    assert data["row"]["lat"] == 51.0504
    assert data["row"]["lon"] == 13.7373
    assert data["norm"] == repo.normalize_addr("Froebelstraße 1, Dresden")
    
    # Test mit nicht vorhandener Adresse
    response = client.get("/debug/geo/peek", params={"addr": "Nicht Vorhanden 999, Teststadt"})
    assert response.status_code == 200
    
    data = response.json()
    assert data["hit"] is False
    assert data["row"] is None


def test_debug_stats(tmp_path, monkeypatch):
    """Teste debug/geo/stats Endpoint."""
    # Isoliere Test-Datenbank
    test_db_path = tmp_path / "test_stats.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{test_db_path}")
    
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    # Datenbank leeren vor Test
    with core.ENGINE.begin() as c:
        c.execute(core.text("DELETE FROM geo_cache"))
    
    # Mehrere Test-Einträge einfügen
    repo.upsert("Teststraße 1, Teststadt", 51.0, 13.0, source="geocoded")
    repo.upsert("Teststraße 2, Teststadt", 51.1, 13.1, source="manual", by_user="test")
    
    import routes.debug_geo as dbg
    reload(dbg)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(dbg.router)
    client = TestClient(app)
    
    response = client.get("/debug/geo/stats")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total_entries"] == 2
    assert len(data["by_source"]) == 2
    
    # Prüfe Source-Gruppierung
    sources = {s["source"]: s["count"] for s in data["by_source"]}
    assert sources["geocoded"] == 1
    assert sources["manual"] == 1
    
    # Prüfe recent updates
    assert len(data["recent_updates"]) == 2
    assert all("address_norm" in update for update in data["recent_updates"])


def test_debug_peek_missing_param():
    """Teste dass fehlender Parameter korrekt behandelt wird."""
    import routes.debug_geo as dbg
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(dbg.router)
    client = TestClient(app)
    
    # Ohne addr Parameter sollte 422 zurückgeben
    response = client.get("/debug/geo/peek")
    assert response.status_code == 422


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
