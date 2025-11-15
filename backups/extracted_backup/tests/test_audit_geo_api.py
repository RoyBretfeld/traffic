import os
from importlib import reload
from fastapi.testclient import TestClient

def test_audit_api_lists_entries(tmp_path, monkeypatch):
    """Test der Audit-API mit SQLite."""
    # SQLite DSN setzen
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    # Core & Schemas neu laden
    import db.core as core
    reload(core)
    
    import db.schema as base
    reload(base)
    base.ensure_schema()
    
    import db.schema_alias as sa
    reload(sa)
    sa.ensure_alias_schema()
    
    # Seed: fülle Audit via Insert
    from sqlalchemy import text
    with core.ENGINE.begin() as c:
        c.execute(text("INSERT INTO geo_audit(action, query, canonical, by_user) VALUES ('alias_set','Froebelstr. 1','Fröbelstraße 1','tester')"))
        c.execute(text("INSERT INTO geo_audit(action, query, canonical, by_user) VALUES ('alias_remove','Foo','', 'tester')"))
    
    # API Route laden
    import routes.audit_geo as api
    reload(api)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    
    # Test: Alle Einträge abrufen
    r = client.get('/api/audit/geo?limit=10')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] == 2
    assert len(j['items']) == 2
    
    # Test: Filter nach Action
    r = client.get('/api/audit/geo?limit=10&action=alias_set')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] == 1
    assert j['items'][0]['action'] == 'alias_set'
    
    # Test: Filter nach Query (Free-Text)
    r = client.get('/api/audit/geo?limit=10&q=Froebel')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] == 1
    assert 'Froebel' in j['items'][0]['query']
    
    # Test: Limit funktioniert
    r = client.get('/api/audit/geo?limit=1')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] == 1
    assert len(j['items']) == 1

def test_audit_api_empty_result(tmp_path, monkeypatch):
    """Test der Audit-API mit leerer Datenbank."""
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
    
    import db.schema_alias as sa
    reload(sa)
    sa.ensure_alias_schema()
    
    # API Route laden
    import routes.audit_geo as api
    reload(api)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    
    # Test: Leere Datenbank
    r = client.get('/api/audit/geo')
    assert r.status_code == 200
    j = r.json()
    assert j['count'] == 0
    assert len(j['items']) == 0

def test_audit_api_invalid_params(tmp_path, monkeypatch):
    """Test der Audit-API mit ungültigen Parametern."""
    # SQLite DSN setzen (andere Datei als andere Tests)
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'invalid.db'}")
    
    # Core & Schemas neu laden
    import db.core as core
    reload(core)
    
    import db.schema_alias as sa
    reload(sa)
    sa.ensure_alias_schema()
    
    # API Route laden
    import routes.audit_geo as api
    reload(api)
    
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(api.router)
    client = TestClient(app)
    
    # Test: Limit zu hoch (sollte auf 500 begrenzt werden)
    r = client.get('/api/audit/geo?limit=1000')
    assert r.status_code == 422  # FastAPI validiert automatisch
    
    # Test: Limit zu niedrig (sollte auf 1 begrenzt werden)
    r = client.get('/api/audit/geo?limit=0')
    assert r.status_code == 422  # Validation Error
