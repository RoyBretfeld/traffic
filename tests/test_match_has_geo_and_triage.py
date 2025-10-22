from importlib import reload
from fastapi import FastAPI
from fastapi.testclient import TestClient
import os

def _seed(tmp_path, monkeypatch):
    """Setup Test-Datenbank und CSV-Datei"""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    # PathPolicy initialisieren
    import fs.safefs as safefs; reload(safefs)
    orig_path = tmp_path / "Tourplaene"
    staging_path = tmp_path / "data" / "staging"
    output_path = tmp_path / "data" / "output"
    safefs.POLICY = safefs.PathPolicy(orig_path, staging_path, output_path)
    
    import db.core as core; reload(core)
    import db.schema as schema; reload(schema); schema.ensure_schema()
    import db.schema_alias as alias_schema; reload(alias_schema); alias_schema.ensure_alias_schema()
    import db.schema_fail as fail_schema; reload(fail_schema); fail_schema.ensure_fail_schema()
    import db.schema_manual as manual_schema; reload(manual_schema); manual_schema.ensure_manual_schema()
    import repositories.geo_repo as repo; reload(repo)
    
    # Test-Geocache-Eintrag
    repo.upsert("Fröbelstraße 1, Dresden", 51.05, 13.74)
    
    # CSV-Datei erstellen (Verzeichnisse bereits von PathPolicy erstellt)
    orig = tmp_path/"Tourplaene"
    (orig/"p.csv").write_bytes("Kunde;Adresse\nA;Fröbelstraße 1, Dresden\n".encode("cp850"))
    
    return orig/"p.csv"


def test_match_reports_has_geo(tmp_path, monkeypatch):
    """Test: Match-Route liefert has_geo=True wenn Geo-Daten vorhanden"""
    src = _seed(tmp_path, monkeypatch)
    
    import routes.tourplan_match as match; reload(match)
    app = FastAPI(); app.include_router(match.router)
    c = TestClient(app)
    
    response = c.get("/api/tourplan/match", params={"file": str(src)})
    assert response.status_code == 200
    
    j = response.json()
    assert len(j["items"]) == 1
    assert j["items"][0]["has_geo"] is True
    assert j["items"][0]["geo"] is not None


def test_triage_shows_cache_and_alias(tmp_path, monkeypatch):
    """Test: Triage-Route zeigt Cache-Status und Alias-Info"""
    src = _seed(tmp_path, monkeypatch)
    
    import routes.tourplan_triage as tri; reload(tri)
    app = FastAPI(); app.include_router(tri.router)
    c = TestClient(app)
    
    response = c.get("/api/tourplan/triage", params={"file": str(src)})
    assert response.status_code == 200
    
    j = response.json()
    assert j["count"] == 1
    
    it = j["items"][0]
    assert it["in_cache"] is True
    assert it["has_geo"] is True
    assert it["geo"] is not None
    assert it["via_alias"] is False  # Direkter Cache-Treffer
    assert it["alias_of"] is None    # Kein Alias nötig
