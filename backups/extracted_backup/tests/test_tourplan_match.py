from fastapi.testclient import TestClient
from pathlib import Path
import os
import pytest

# App/DB vorbereiten
def _setup_sqlite(monkeypatch, tmp_path):
    """Setup SQLite-Datenbank für Tests."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    from importlib import reload
    import db.core as core; reload(core)
    import db.schema as schema; reload(schema); schema.ensure_schema()
    import repositories.geo_repo as repo; reload(repo)
    
    # Test-Daten einfügen
    repo.upsert("Löbtauer Straße 1, 01809 Heidenau", 50.9836, 13.8663)
    repo.upsert("Hauptstraße 42, 01067 Dresden", 51.0504, 13.7373)
    
    return repo

def _write_cp850(p: Path, text: str):
    """Schreibt Text als CP850-kodierte Datei."""
    p.write_bytes(text.encode("cp850"))

def test_match_endpoint(tmp_path, monkeypatch):
    """Testet die /api/tourplan/match Route."""
    # 1) DB Setup
    repo = _setup_sqlite(monkeypatch, tmp_path)

    # 2) Original-CSV ablegen (cp850)
    orig_dir = tmp_path/"Tourplaene"; orig_dir.mkdir()
    sample = "Kunde;Adresse\nX;Löbtauer Straße 1, 01809 Heidenau\nY;Fröbelstraße 5\nZ;Hauptstraße 42, 01067 Dresden"
    src = orig_dir/"Plan.csv"; _write_cp850(src, sample)

    # 3) ENV für Pfade, Staging
    stag = tmp_path/"data"/"staging"; stag.mkdir(parents=True)
    monkeypatch.setenv("STAGING_DIR", str(stag))
    monkeypatch.setenv("IN_ENCODING", "cp850")
    monkeypatch.setenv("ORIG_DIR", str(orig_dir))
    monkeypatch.setenv("VERIFY_ORIG_ON_INGEST", "0")  # Integritätswächter für Tests deaktivieren
    monkeypatch.setenv("ORIG_DIR", str(orig_dir))  # PathPolicy-Initialisierung für Tests

    # 4) PathPolicy initialisieren
    from fs.safefs import init_policy
    init_policy()
    
    # 5) App zusammenstecken
    from importlib import reload
    import ingest.reader as reader; reload(reader)
    import routes.tourplan_match as rtm; reload(rtm)

    from fastapi import FastAPI
    app = FastAPI(); app.include_router(rtm.router)
    client = TestClient(app)

    # 5) Call
    resp = client.get("/api/tourplan/match", params={"file": str(src)})
    assert resp.status_code == 200
    j = resp.json()
    
    # 6) Validierung
    assert j["rows"] == 3
    assert j["ok"] >= 1  # Mindestens eine Adresse sollte gefunden werden
    assert j["warn"] >= 0  # Nicht gefundene Adressen
    assert j["bad"] == 0  # Keine Mojibake-Marker erwartet
    
    # 7) Erste Adresse gefunden → ok
    first = j["items"][0]
    assert first["has_geo"] is True
    assert first["geo"]["lat"] == 50.9836
    assert first["geo"]["lon"] == 13.8663
    assert first["status"] == "ok"
    
    # 8) Zweite Adresse nicht gefunden → warn
    second = j["items"][1]
    assert second["has_geo"] is False
    assert second["geo"] is None
    assert second["status"] == "warn"
    
    # 9) Dritte Adresse gefunden → ok
    third = j["items"][2]
    assert third["has_geo"] is True
    assert third["geo"]["lat"] == 51.0504
    assert third["geo"]["lon"] == 13.7373
    assert third["status"] == "ok"

def test_match_endpoint_file_not_found(tmp_path, monkeypatch):
    """Testet 404-Fehler bei nicht existierender Datei."""
    from fastapi import FastAPI
    import routes.tourplan_match as rtm
    
    app = FastAPI(); app.include_router(rtm.router)
    client = TestClient(app)
    
    resp = client.get("/api/tourplan/match", params={"file": "nonexistent.csv"})
    assert resp.status_code == 404
    assert "nicht gefunden" in resp.json()["detail"]

def test_match_endpoint_mojibake_detection(tmp_path, monkeypatch):
    """Testet Erkennung von Mojibake-Markern."""
    # 1) DB Setup
    _setup_sqlite(monkeypatch, tmp_path)

    # 2) CSV mit Mojibake erstellen
    orig_dir = tmp_path/"Tourplaene"; orig_dir.mkdir()
    sample_with_mojibake = "Kunde;Adresse\nX;Löbtauer Straße 1, 01809 Heidenau\nY;Fröbelstraße 5┬"  # Mojibake-Marker
    src = orig_dir/"Plan.csv"; _write_cp850(src, sample_with_mojibake)

    # 3) ENV Setup
    stag = tmp_path/"data"/"staging"; stag.mkdir(parents=True)
    monkeypatch.setenv("STAGING_DIR", str(stag))
    monkeypatch.setenv("IN_ENCODING", "cp850")
    monkeypatch.setenv("ORIG_DIR", str(orig_dir))
    monkeypatch.setenv("VERIFY_ORIG_ON_INGEST", "0")  # Integritätswächter für Tests deaktivieren
    monkeypatch.setenv("ORIG_DIR", str(orig_dir))  # PathPolicy-Initialisierung für Tests

    # 4) App Setup
    from importlib import reload
    import ingest.reader as reader; reload(reader)
    import routes.tourplan_match as rtm; reload(rtm)

    from fastapi import FastAPI
    app = FastAPI(); app.include_router(rtm.router)
    client = TestClient(app)

    # 5) Call
    resp = client.get("/api/tourplan/match", params={"file": str(src)})
    assert resp.status_code == 200
    j = resp.json()
    
    # 6) Mojibake sollte erkannt werden
    assert j["bad"] >= 1  # Mindestens eine Zeile mit Mojibake
    bad_items = [item for item in j["items"] if item["status"] == "bad"]
    assert len(bad_items) >= 1
    assert "┬" in bad_items[0]["markers"]  # Mojibake-Marker sollte erkannt werden
