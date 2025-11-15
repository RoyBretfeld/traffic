# tests/test_audit_geocoding_complete.py
import pytest
from importlib import reload
from pathlib import Path
import tempfile
import os
from fastapi import FastAPI
from fastapi.testclient import TestClient

def test_audit_reports_missing(tmp_path, monkeypatch):
    """Test: Audit erkennt fehlende Adressen in Mini-Tour"""
    # Test-Datenbank konfigurieren
    db_path = tmp_path / "test.db"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    monkeypatch.setenv('TOURPLAN_DIR', str(tmp_path / 'plans'))
    
    # Module neu laden
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    from common.normalize import normalize_address
    
    # Test-CSV schreiben (mit CP850 Encoding wie echte CSV-Dateien)
    pdir = Path(os.environ['TOURPLAN_DIR'])
    pdir.mkdir(parents=True, exist_ok=True)
    csv = pdir / 'Tourenplan test.csv'
    csv.write_bytes(
        'Tourenübersicht;;;;;\r\n'
        'Liefdatum: 01.01.25;;;;;\r\n'
        ';;;;;\r\n'
        'Kdnr;Name;Straße;PLZ;Ort;Gedruckt\r\n'
        ';W-07.00 Uhr Tour;;;;\r\n'
        '1;Test GmbH;Fröbelstraße 1 | Dresden;01159;Dresden;1\r\n'
        '2;Muster AG;Altmarkt 1, Dresden;01067;Dresden;1\r\n'
        '3;Unbekannt;Nichtda 99, Nirgendwo;99999;Nirgendwo;1\r\n'.encode('cp850')
    )
    
    # Zwei Adressen im Cache (A & B), C fehlt
    # Verwende die vollständigen normalisierten Adressen (mit PLZ und Stadt)
    repo.upsert('Fröbelstraße 1, Dresden, 01159 Dresden', 51.0, 13.7)  # Vollständige Adresse
    repo.upsert('Altmarkt 1, Dresden, 01067 Dresden', 51.05, 13.74)  # Vollständige Adresse
    
    
    # App mit Audit-Route
    import routes.audit_geocoding as audit
    reload(audit)
    app = FastAPI()
    app.include_router(audit.router)
    client = TestClient(app)
    
    # Audit-Endpoint aufrufen
    response = client.get('/api/audit/geocoding')
    assert response.status_code == 200
    
    data = response.json()
    
    # Prüfe grundlegende Statistiken
    assert data['csv_files'] == 1
    assert data['unique_addresses_csv'] == 3
    assert data['missing_count'] == 1
    assert data['duplicates_count'] == 0
    assert data['coverage_pct'] == 66.67  # 2 von 3 = 66.67%
    assert data['ok'] == False
    assert data['status'] == 'FAIL'
    
    # Prüfe dass die fehlende Adresse erkannt wurde
    missing = data['missing']
    assert len(missing) == 1
    assert 'Nichtda' in missing[0] or 'Nirgendwo' in missing[0]

def test_audit_reports_duplicates(tmp_path, monkeypatch):
    """Test: Audit erkennt Duplikate (falls vorhanden)"""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    monkeypatch.setenv('TOURPLAN_DIR', str(tmp_path / 'plans'))
    
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    # Test-CSV mit einer Adresse (mit CP850 Encoding)
    pdir = Path(os.environ['TOURPLAN_DIR'])
    pdir.mkdir(parents=True, exist_ok=True)
    csv = pdir / 'Tourenplan test.csv'
    csv.write_bytes(
        'Tourenübersicht;;;;;\r\n'
        'Liefdatum: 01.01.25;;;;;\r\n'
        ';;;;;\r\n'
        'Kdnr;Name;Straße;PLZ;Ort;Gedruckt\r\n'
        ';W-07.00 Uhr Tour;;;;\r\n'
        '1;Test GmbH;Hauptstraße 1, Dresden;01067;Dresden;1\r\n'.encode('cp850')
    )
    
    # Adresse im Cache speichern (vollständige Adresse)
    repo.upsert('Hauptstraße 1, Dresden, 01067 Dresden', 51.0, 13.7)
    
    # App mit Audit-Route
    import routes.audit_geocoding as audit
    reload(audit)
    app = FastAPI()
    app.include_router(audit.router)
    client = TestClient(app)
    
    # Audit-Endpoint aufrufen
    response = client.get('/api/audit/geocoding')
    assert response.status_code == 200
    
    data = response.json()
    
    # Prüfe dass alles OK ist
    assert data['csv_files'] == 1
    assert data['unique_addresses_csv'] == 1
    assert data['missing_count'] == 0
    assert data['duplicates_count'] == 0
    assert data['coverage_pct'] == 100.0
    assert data['ok'] == True
    assert data['status'] == 'PASS'

def test_audit_handles_empty_csv_dir(tmp_path, monkeypatch):
    """Test: Audit funktioniert auch bei leerem CSV-Verzeichnis"""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    monkeypatch.setenv('TOURPLAN_DIR', str(tmp_path / 'empty'))
    
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    # Leeres Verzeichnis erstellen
    empty_dir = Path(os.environ['TOURPLAN_DIR'])
    empty_dir.mkdir(parents=True, exist_ok=True)
    
    # App mit Audit-Route
    import routes.audit_geocoding as audit
    reload(audit)
    app = FastAPI()
    app.include_router(audit.router)
    client = TestClient(app)
    
    # Audit-Endpoint aufrufen
    response = client.get('/api/audit/geocoding')
    assert response.status_code == 200
    
    data = response.json()
    
    # Prüfe dass leeres Verzeichnis korrekt behandelt wird
    assert data['csv_files'] == 0
    assert data['unique_addresses_csv'] == 0
    assert data['missing_count'] == 0
    assert data['duplicates_count'] == 0
    assert data['coverage_pct'] == 0.0
    assert data['ok'] == True
    assert data['status'] == 'PASS'

def test_audit_handles_parse_errors(tmp_path, monkeypatch):
    """Test: Audit behandelt CSV-Parse-Fehler graceful"""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    monkeypatch.setenv('TOURPLAN_DIR', str(tmp_path / 'plans'))
    
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    # Defekte CSV-Datei schreiben
    pdir = Path(os.environ['TOURPLAN_DIR'])
    pdir.mkdir(parents=True, exist_ok=True)
    csv = pdir / 'Tourenplan broken.csv'
    csv.write_text('This is not a valid CSV file', encoding='utf-8')
    
    # App mit Audit-Route
    import routes.audit_geocoding as audit
    reload(audit)
    app = FastAPI()
    app.include_router(audit.router)
    client = TestClient(app)
    
    # Audit-Endpoint aufrufen
    response = client.get('/api/audit/geocoding')
    assert response.status_code == 200
    
    data = response.json()
    
    # Prüfe dass Fehler graceful behandelt werden
    assert data['csv_files'] == 1
    assert data['unique_addresses_csv'] == 0  # Keine gültigen Adressen
    assert data['status'] == 'PASS'  # Keine Fehler, nur leere Datei
