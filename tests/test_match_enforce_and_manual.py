import os
from importlib import reload
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
import respx
import httpx

@pytest.mark.asyncio
@respx.mock
async def test_match_enforces_geocode_and_manual(tmp_path, monkeypatch):
    """Testet dass Match-Route Geocoding erzwingt und No-Hits in Manual-Queue landen."""
    # ENV-Konfiguration
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    monkeypatch.setenv("GEOCODE_ENFORCE", "1")
    monkeypatch.setenv("GEOCODE_BATCH_LIMIT", "10")
    monkeypatch.setenv("GEOCODE_NO_RESULT_TO_MANUAL", "1")
    monkeypatch.setenv("STAGING_DIR", str(tmp_path / "staging"))
    monkeypatch.setenv("ORIG_DIR", str(tmp_path / "Tourplaene"))

    # DB/Schemas initialisieren
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    import db.schema_manual as man
    reload(man)
    man.ensure_manual_schema()

    # Test-CSV erstellen (cp850)
    orig = tmp_path / "Tourplaene"
    orig.mkdir()
    csv_content = "Kunde;Adresse\nA;Fröbelstraße 1, Dresden\nB;Nicht Gefunden 99, Nirgendwo\n"
    src = orig / "test.csv"
    src.write_bytes(csv_content.encode("cp850"))

    # Staging-Dir erstellen
    staging = tmp_path / "staging"
    staging.mkdir()

    # Mock Nominatim: erste Adresse Treffer, zweite leer
    def J(lat, lon):
        return [{"lat": str(lat), "lon": str(lon)}]
    
    route = respx.get("https://nominatim.openstreetmap.org/search")
    route.side_effect = [
        httpx.Response(200, json=J(51.05, 13.74)),  # Fröbelstraße Treffer
        httpx.Response(200, json=[])                # Nicht Gefunden = No-Hit
    ]

    # Route laden und testen
    import routes.tourplan_match as r
    reload(r)
    app = FastAPI()
    app.include_router(r.router)
    client = TestClient(app)

    # API-Call
    resp = client.get("/api/tourplan/match", params={"file": str(src)})
    assert resp.status_code == 200
    
    j = resp.json()
    assert j["rows"] == 2
    
    # Prüfe dass erste Adresse geocodiert wurde
    items = {item["address"]: item for item in j["items"]}
    froebel = items["Fröbelstraße 1, Dresden"]
    assert froebel["has_geo"] is True
    assert froebel["geo"]["lat"] == 51.05
    assert froebel["geo"]["lon"] == 13.74
    
    # Prüfe dass zweite Adresse in Manual-Queue gelandet ist
    nicht_gefunden = items["Nicht Gefunden 99, Nirgendwo"]
    assert nicht_gefunden["has_geo"] is False
    assert nicht_gefunden["manual_needed"] is True

@pytest.mark.asyncio
@respx.mock
async def test_manual_queue_api(tmp_path, monkeypatch):
    """Testet die Manual-Queue API-Endpoints."""
    # ENV-Konfiguration
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")

    # DB/Schemas initialisieren
    import db.core as core
    reload(core)
    import db.schema_manual as man
    reload(man)
    man.ensure_manual_schema()

    # Manual-Repo laden
    import repositories.manual_repo as repo
    reload(repo)

    # Test-App erstellen
    import routes.manual_api as api
    reload(api)
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)

    # Test-Daten hinzufügen
    repo.add_open("Teststraße 123, Teststadt", reason="no_result", note="Test-Eintrag")

    # Liste abrufen
    resp = client.get("/api/manual/list")
    assert resp.status_code == 200
    j = resp.json()
    assert j["count"] == 1
    assert j["stats"]["open"] == 1
    assert j["items"][0]["address_norm"] == "Teststraße 123, Teststadt"
    assert j["items"][0]["reason"] == "no_result"

    # Statistiken abrufen
    resp = client.get("/api/manual/stats")
    assert resp.status_code == 200
    j = resp.json()
    assert j["total"] == 1
    assert j["open"] == 1
    assert j["closed"] == 0

    # Eintrag schließen
    resp = client.post("/api/manual/close", params={"address": "Teststraße 123, Teststadt"})
    assert resp.status_code == 200
    j = resp.json()
    assert j["ok"] is True

    # Prüfen dass geschlossen
    resp = client.get("/api/manual/stats")
    assert resp.status_code == 200
    j = resp.json()
    assert j["open"] == 0
    assert j["closed"] == 1

@pytest.mark.asyncio
async def test_geocode_fill_with_manual_queue(tmp_path, monkeypatch):
    """Testet dass fill_missing No-Hits in Manual-Queue einträgt."""
    # ENV-Konfiguration
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    monkeypatch.setenv("GEOCODE_NO_RESULT_TO_MANUAL", "1")

    # DB/Schemas initialisieren
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    import db.schema_manual as man
    reload(man)
    man.ensure_manual_schema()

    # Services laden
    import services.geocode_fill as fill
    reload(fill)
    import repositories.manual_repo as repo
    reload(repo)

    # Mock für No-Hit
    with respx.mock:
        respx.get("https://nominatim.openstreetmap.org/search").mock(
            return_value=httpx.Response(200, json=[])
        )

        # fill_missing aufrufen
        result = await fill.fill_missing(["Nicht Gefunden 99, Nirgendwo"], limit=1, dry_run=False)
        
        # Prüfen dass No-Hit in Manual-Queue gelandet ist
        assert len(result) == 2  # 1 Ergebnis + 1 Meta
        assert result[0]["status"] == "nohit"
        
        # Prüfen dass in Manual-Queue
        items = repo.list_open()
        assert len(items) == 1
        assert items[0]["address_norm"] == "Nicht Gefunden 99, Nirgendwo"
        assert items[0]["reason"] == "no_result"

def test_env_configuration():
    """Testet dass ENV-Variablen korrekt gelesen werden."""
    # Test mit verschiedenen ENV-Werten
    test_cases = [
        ("1", True),
        ("0", False),
        ("false", False),
        ("False", False),
        ("", True),  # Default
    ]
    
    for value, expected in test_cases:
        os.environ["GEOCODE_ENFORCE"] = value
        from importlib import reload
        import routes.tourplan_match as r
        reload(r)
        assert r.ENFORCE == expected, f"ENV='{value}' should give {expected}"
    
    # Cleanup
    if "GEOCODE_ENFORCE" in os.environ:
        del os.environ["GEOCODE_ENFORCE"]
