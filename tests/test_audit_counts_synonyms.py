# tests/test_audit_counts_synonyms.py
from importlib import reload
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import tempfile
import os

def test_audit_treats_synonyms_as_geocoded(tmp_path, monkeypatch):
    """Test dass Audit Synonyme als geokodiert zählt."""
    # Temporäre Datenbank und Verzeichnisse einrichten
    db_path = tmp_path / 'test.db'
    plans_path = tmp_path / 'plans'
    plans_path.mkdir(parents=True, exist_ok=True)
    
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    monkeypatch.setenv('TOURPLAN_DIR', str(plans_path))
    
    # Datenbank-Schema erstellen
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    # CSV mit einem PF-Eintrag erstellen
    csv_content = """Kdnr;Name;Straße;PLZ;Ort;Gedruckt
4586;Jochen - PF;Reisstr. 40;01257;Dresden;1"""
    (plans_path / 'plan.csv').write_text(csv_content, encoding='utf-8')
    
    # Synonym in Cache einfügen (wie geocode_fill es tun würde)
    import repositories.geo_repo as repo
    reload(repo)
    from common.synonyms import resolve_synonym
    
    hit = resolve_synonym('Jochen - PF')
    assert hit is not None
    repo.upsert(hit.resolved_address, hit.lat, hit.lon)
    
    # Audit-Endpoint testen
    import routes.audit_geocoding as audit
    reload(audit)
    app = FastAPI()
    app.include_router(audit.router)
    c = TestClient(app)
    
    response = c.get('/api/audit/geocoding')
    assert response.status_code == 200
    
    j = response.json()
    assert j['missing_count'] == 0, f"Synonyme sollten als geokodiert zählen, aber missing_count ist {j['missing_count']}"

def test_audit_counts_mixed_synonyms_and_normal():
    """Test dass Audit korrekt zwischen Synonymen und normalen Adressen unterscheidet."""
    # Temporäre Datenbank und Verzeichnisse einrichten
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / 'test.db'
        plans_path = tmp_path / 'plans'
        plans_path.mkdir(parents=True, exist_ok=True)
        
        # CSV mit gemischten Einträgen erstellen
        csv_content = """Kdnr;Name;Straße;PLZ;Ort;Gedruckt
4586;Jochen - PF;Reisstr. 40;01257;Dresden;1
5205;Normale Firma;Wiener Straße 10;01069;Dresden;1"""
        (plans_path / 'mixed.csv').write_text(csv_content, encoding='utf-8')
        
        # Datenbank-Schema erstellen
        import db.core as core
        reload(core)
        import db.schema as schema
        reload(schema)
        schema.ensure_schema()
        
        # Synonym und normale Adresse in Cache einfügen
        import repositories.geo_repo as repo
        reload(repo)
        from common.synonyms import resolve_synonym
        
        # PF-Synonym einfügen
        pf_hit = resolve_synonym('Jochen - PF')
        assert pf_hit is not None
        repo.upsert(pf_hit.resolved_address, pf_hit.lat, pf_hit.lon)
        
        # Normale Adresse einfügen
        repo.upsert("Wiener Straße 10, 01069 Dresden", 51.05, 13.74)
        
        # Audit-Endpoint testen - nur die Test-CSV verwenden
        import routes.audit_geocoding as audit
        reload(audit)
        app = FastAPI()
        app.include_router(audit.router)
        c = TestClient(app)
        
        # Nur die Test-CSV analysieren - verwende den spezifischen Endpoint
        response = c.get(f'/api/audit/geocoding?file={plans_path}/mixed.csv')
        assert response.status_code == 200
        
        j = response.json()
        # Beide Adressen sollten als geokodiert zählen
        assert j['missing_count'] == 0, f"Beide Adressen sollten geokodiert sein, aber missing_count ist {j['missing_count']}"
        assert j['total_count'] >= 2, f"Sollte mindestens 2 Adressen haben, aber total_count ist {j['total_count']}"

def test_synonym_cache_integration():
    """Test dass Synonyme korrekt in den Cache integriert werden."""
    # Temporäre Datenbank einrichten
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        db_path = tmp_path / 'test.db'
        
        # Datenbank-Schema erstellen
        import db.core as core
        reload(core)
        import db.schema as schema
        reload(schema)
        schema.ensure_schema()
        
        # Synonym in Cache einfügen
        import repositories.geo_repo as repo
        reload(repo)
        from common.synonyms import resolve_synonym
        
        hit = resolve_synonym('Sven - PF')
        assert hit is not None
        
        # Cache-Eintrag erstellen
        repo.upsert(hit.resolved_address, hit.lat, hit.lon)
        
        # Prüfen dass Eintrag im Cache ist
        cached = repo.get(hit.resolved_address)
        assert cached is not None
        assert cached['lat'] == hit.lat
        assert cached['lon'] == hit.lon
        
        # Prüfen dass Bulk-Get funktioniert
        bulk_result = repo.bulk_get([hit.resolved_address])
        assert hit.resolved_address in bulk_result
        assert bulk_result[hit.resolved_address]['lat'] == hit.lat