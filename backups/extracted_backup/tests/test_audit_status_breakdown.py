# tests/test_audit_status_breakdown.py
from importlib import reload
from pathlib import Path
from fastapi import FastAPI
from fastapi.testclient import TestClient
import tempfile

def test_audit_status_reports_missing_and_stats(tmp_path, monkeypatch):
    """Test dass Audit-Status fehlende Adressen und Statistiken korrekt meldet."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    monkeypatch.setenv('TOURPLAN_DIR', str(tmp_path / 'plans'))

    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    # Test-CSV erstellen
    pdir = Path(monkeypatch.getenv('TOURPLAN_DIR'))
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / 'plan.csv').write_text(
        'Kdnr;Name;Straße;PLZ;Ort;Gedruckt\n'
        '1;Test Firma;Altmarkt 1;01067;Dresden;1\n'
        '2;Andere Firma;Hauptstraße 5;01159;Dresden;1\n',
        encoding='utf-8'
    )

    # Eine Adresse in Cache einfügen
    import repositories.geo_repo as repo
    reload(repo)
    repo.upsert_ex(
        address="Altmarkt 1, 01067 Dresden",
        lat=51.05,
        lon=13.74,
        source="geocoder",
        precision="full",
        region_ok=1
    )

    # Audit-Status Endpoint testen
    import routes.audit_status as audit
    reload(audit)
    app = FastAPI()
    app.include_router(audit.router)
    c = TestClient(app)

    response = c.get('/api/audit/status?limit=10')
    assert response.status_code == 200

    j = response.json()
    assert j['unique_addresses_csv'] == 2
    assert j['missing_count'] == 1
    assert j['coverage_pct'] == 50.0
    assert any('Hauptstraße' in x for x in j['missing_preview'])
    assert j['sources']['geocoder'] == 1
    assert j['precision']['full'] == 1
    assert j['region_stats']['ok'] == 1

def test_audit_status_manual_queue_endpoint(tmp_path, monkeypatch):
    """Test dass Manual-Queue Endpoint funktioniert."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")

    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    # Manual-Queue Einträge hinzufügen
    import repositories.manual_repo as mr
    reload(mr)
    mr.add_open('Test Adresse 1', 'geocode_miss')
    mr.add_open('Test Adresse 2', 'invalid_coordinates')

    # Manual-Queue Endpoint testen
    import routes.audit_status as audit
    reload(audit)
    app = FastAPI()
    app.include_router(audit.router)
    c = TestClient(app)

    response = c.get('/api/audit/manual-queue?limit=10')
    assert response.status_code == 200

    j = response.json()
    assert j['count'] >= 2
    assert len(j['items']) >= 2
    assert any('Test Adresse 1' in item['raw_address'] for item in j['items'])
    assert any('Test Adresse 2' in item['raw_address'] for item in j['items'])

def test_audit_status_export_endpoint(tmp_path, monkeypatch):
    """Test dass Export-Endpoint funktioniert."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")

    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    # Manual-Queue Einträge hinzufügen
    import repositories.manual_repo as mr
    reload(mr)
    mr.add_open('Export Test', 'geocode_miss')

    # Export-Endpoint testen
    import routes.audit_status as audit
    reload(audit)
    app = FastAPI()
    app.include_router(audit.router)
    c = TestClient(app)

    response = c.post('/api/audit/export-manual-queue')
    assert response.status_code == 200

    j = response.json()
    assert j['success'] is True
    assert j['exported_count'] >= 1
    assert 'pending_' in j['export_path']
    assert j['export_path'].endswith('.csv')

def test_audit_status_coverage_calculation(tmp_path, monkeypatch):
    """Test dass Coverage-Berechnung korrekt funktioniert."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    monkeypatch.setenv('TOURPLAN_DIR', str(tmp_path / 'plans'))

    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    # Test-CSV mit verschiedenen Adressen erstellen
    pdir = Path(monkeypatch.getenv('TOURPLAN_DIR'))
    pdir.mkdir(parents=True, exist_ok=True)
    (pdir / 'test.csv').write_text(
        'Kdnr;Name;Straße;PLZ;Ort;Gedruckt\n'
        '1;Firma 1;Straße 1;01067;Dresden;1\n'
        '2;Firma 2;Straße 2;01069;Dresden;1\n'
        '3;Firma 3;Straße 3;01159;Dresden;1\n'
        '4;Firma 4;Straße 4;01237;Dresden;1\n',
        encoding='utf-8'
    )

    # Nur 2 von 4 Adressen in Cache einfügen
    import repositories.geo_repo as repo
    reload(repo)
    repo.upsert_ex(
        address="Straße 1, 01067 Dresden",
        lat=51.05, lon=13.74, source="geocoder", precision="full", region_ok=1
    )
    repo.upsert_ex(
        address="Straße 2, 01069 Dresden",
        lat=51.05, lon=13.74, source="synonym", precision=None, region_ok=1
    )

    # Audit-Status testen
    import routes.audit_status as audit
    reload(audit)
    app = FastAPI()
    app.include_router(audit.router)
    c = TestClient(app)

    response = c.get('/api/audit/status')
    assert response.status_code == 200

    j = response.json()
    assert j['unique_addresses_csv'] == 4
    assert j['missing_count'] == 2
    assert j['coverage_pct'] == 50.0
    assert j['sources']['geocoder'] == 1
    assert j['sources']['synonym'] == 1
