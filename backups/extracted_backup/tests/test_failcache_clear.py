import os
from importlib import reload
from fastapi.testclient import TestClient
from sqlalchemy import text

def test_failcache_clear(tmp_path, monkeypatch):
    """Test der Fail-Cache-Clear-API mit SQLite."""
    # SQLite DSN setzen
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    # Core & Schemas neu laden
    import db.core as core
    reload(core)
    
    import db.schema_fail as sf
    reload(sf)
    sf.ensure_fail_schema()
    
    # Seed: fülle Fail-Cache via Insert
    with core.ENGINE.begin() as c:
        c.execute(text("INSERT INTO geo_fail(address_norm, reason) VALUES ('A','temp_error')"))
        c.execute(text("INSERT INTO geo_fail(address_norm, reason) VALUES ('B','no_result')"))
    
    # API Route laden
    import routes.failcache_clear as api
    reload(api)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    
    # Test: Einzelnen Eintrag löschen
    r = client.post('/api/geocode/fail-cache/clear', json={"addresses": ["A"]})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] == True
    assert j["cleared"] == 1
    
    # Test: Zweiter Call – sollte nur noch einen löschen
    r = client.post('/api/geocode/fail-cache/clear', json={"addresses": ["A","B"]})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] == True
    assert j["cleared"] == 1  # Nur B wurde gelöscht, A war bereits weg
    
    # Test: Dritter Call – sollte nichts mehr löschen
    r = client.post('/api/geocode/fail-cache/clear', json={"addresses": ["A","B"]})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] == True
    assert j["cleared"] == 0

def test_failcache_clear_empty_request(tmp_path, monkeypatch):
    """Test der Fail-Cache-Clear-API mit leerer Anfrage."""
    # SQLite DSN setzen (andere Datei als erster Test)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'empty.db'}")
    
    # Core & Schemas neu laden
    import db.core as core
    reload(core)
    
    # ENGINE explizit neu erstellen
    core.ENGINE.dispose()
    from sqlalchemy import create_engine
    import os
    core.ENGINE = create_engine(os.getenv("DATABASE_URL"))
    
    import db.schema_fail as sf
    reload(sf)
    sf.ensure_fail_schema()
    
    # API Route laden
    import routes.failcache_clear as api
    reload(api)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    
    # Test: Leere Adressliste
    r = client.post('/api/geocode/fail-cache/clear', json={"addresses": []})
    assert r.status_code == 422  # Validation Error
    
    # Test: Leere Adressliste mit leeren Strings
    r = client.post('/api/geocode/fail-cache/clear', json={"addresses": ["", "   ", ""]})
    assert r.status_code == 400  # "no addresses" Error

def test_failcache_clear_multiple_addresses(tmp_path, monkeypatch):
    """Test der Fail-Cache-Clear-API mit mehreren Adressen."""
    # SQLite DSN setzen (andere Datei als andere Tests)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'multiple.db'}")
    
    # Core & Schemas neu laden
    import db.core as core
    reload(core)
    
    # ENGINE explizit neu erstellen
    core.ENGINE.dispose()
    from sqlalchemy import create_engine
    import os
    core.ENGINE = create_engine(os.getenv("DATABASE_URL"))
    
    import db.schema_fail as sf
    reload(sf)
    sf.ensure_fail_schema()
    
    # Seed: mehrere Einträge
    with core.ENGINE.begin() as c:
        c.execute(text("INSERT INTO geo_fail(address_norm, reason) VALUES ('A','temp_error')"))
        c.execute(text("INSERT INTO geo_fail(address_norm, reason) VALUES ('B','no_result')"))
        c.execute(text("INSERT INTO geo_fail(address_norm, reason) VALUES ('C','temp_error')"))
        c.execute(text("INSERT INTO geo_fail(address_norm, reason) VALUES ('D','no_result')"))
    
    # API Route laden
    import routes.failcache_clear as api
    reload(api)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    
    # Test: Mehrere Adressen auf einmal löschen
    r = client.post('/api/geocode/fail-cache/clear', json={"addresses": ["A", "B", "C"]})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] == True
    assert j["cleared"] == 3
    
    # Test: Verbleibende Adresse löschen
    r = client.post('/api/geocode/fail-cache/clear', json={"addresses": ["D"]})
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] == True
    assert j["cleared"] == 1
