import os
from importlib import reload
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

def test_failcache_list(tmp_path, monkeypatch):
    """Test der Fail-Cache-API mit SQLite."""
    # SQLite DSN setzen
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    # Core & Schemas neu laden
    import db.core as core
    reload(core)
    
    import db.schema_fail as sf
    reload(sf)
    sf.ensure_fail_schema()
    
    # Seed: fülle Fail-Cache via Insert
    from sqlalchemy import text
    import datetime
    now = datetime.datetime.now()
    future_time = (now + datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    past_time = (now - datetime.timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    
    with core.ENGINE.begin() as c:
        c.execute(text("INSERT INTO geo_fail(address_norm, reason, until) VALUES ('A','temp_error', :future)"), {"future": future_time})
        c.execute(text("INSERT INTO geo_fail(address_norm, reason, until) VALUES ('B','no_result', :past)"), {"past": past_time})
        c.execute(text("INSERT INTO geo_fail(address_norm, reason, until) VALUES ('C','temp_error', :future2)"), {"future2": future_time})
    
    # API Route laden
    import routes.failcache_api as api
    reload(api)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    
    # Test: nur aktive Einträge
    r = client.get('/api/geocode/fail-cache?active_only=true')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] >= 1  # Mindestens ein aktiver Eintrag
    assert j['active_only'] == True
    
    # Test: alle Einträge
    r = client.get('/api/geocode/fail-cache?active_only=false')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] == 3  # Alle drei Einträge
    assert j['active_only'] == False
    
    # Test: Filter nach Grund
    r = client.get('/api/geocode/fail-cache?reason=temp_error&active_only=false')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] == 2  # A und C haben temp_error
    assert all(item['reason'] == 'temp_error' for item in j['items'])
    
    # Test: Filter nach Adresse
    r = client.get('/api/geocode/fail-cache?q=A&active_only=false')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] == 1
    assert j['items'][0]['address'] == 'A'

def test_failcache_empty_result(tmp_path, monkeypatch):
    """Test der Fail-Cache-API mit leerer Datenbank."""
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
    import routes.failcache_api as api
    reload(api)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    
    # Test: Leere Datenbank
    r = client.get('/api/geocode/fail-cache')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] == 0
    assert len(j['items']) == 0
    assert j['active_only'] == True

def test_failcache_invalid_params(tmp_path, monkeypatch):
    """Test der Fail-Cache-API mit ungültigen Parametern."""
    # SQLite DSN setzen (andere Datei als andere Tests)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'invalid.db'}")
    
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
    import routes.failcache_api as api
    reload(api)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    
    # Test: Limit zu hoch (sollte auf 500 begrenzt werden)
    r = client.get('/api/geocode/fail-cache?limit=1000')
    assert r.status_code == 422  # FastAPI validiert automatisch
    
    # Test: Limit zu niedrig (sollte auf 1 begrenzt werden)
    r = client.get('/api/geocode/fail-cache?limit=0')
    assert r.status_code == 422  # Validation Error
