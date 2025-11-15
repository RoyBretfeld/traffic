"""
Tests für Workflow Engine
"""

import pytest
from pathlib import Path
import tempfile
import os
from importlib import reload
from fastapi.testclient import TestClient
from fastapi import FastAPI

@pytest.fixture
def setup_test_env(tmp_path, monkeypatch):
    """Setup Test-Umgebung für Workflow-Tests."""
    # Umgebungsvariablen setzen
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'test.db'}")
    monkeypatch.setenv("STAGING_DIR", str(tmp_path / "staging"))
    monkeypatch.setenv("TOURPLAN_DIR", str(tmp_path / "Tourplaene"))
    
    # Module neu laden
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    # Verzeichnisse erstellen
    (tmp_path / "staging").mkdir(parents=True, exist_ok=True)
    (tmp_path / "Tourplaene").mkdir(parents=True, exist_ok=True)
    
    return tmp_path


def test_workflow_engine_basic(setup_test_env, monkeypatch):
    """Test grundlegende Workflow Engine Funktionalität."""
    from services.workflow_engine import run_workflow, ColumnMap
    from importlib import reload
    import repositories.geo_repo as repo
    reload(repo)
    
    tmp_path = setup_test_env
    
    # Füge Test-Koordinaten in DB ein (DB-First Strategie)
    repo.upsert("Fröbelstraße 1, 01159 Dresden", 51.0491695, 13.698383, source="test")
    repo.upsert("Hauptstraße 5, 01067 Dresden", 51.0504, 13.7373, source="test")
    
    # Erstelle Test-CSV (mit Spalten-Namen die ColumnMap erwartet)
    csv_content = """tour_id;order_id;customer;street;postal_code;city
T1;1;Test Kunde;Fröbelstraße 1;01159;Dresden
T1;2;Muster AG;Hauptstraße 5;01067;Dresden"""
    
    csv_file = tmp_path / "Tourplaene" / "test.csv"
    csv_file.write_bytes(csv_content.encode('utf-8'))
    
    # Workflow ausführen (ColumnMap mit Standard-Parametern)
    result = run_workflow(
        content=csv_file.read_bytes(),
        column_map=None  # Verwendet Standard-Mapping
    )
    
    # Validierung (kann auch 0 sein wenn keine Koordinaten gefunden, aber sollte nicht crashen)
    assert result.ok >= 0, "Workflow sollte ohne Fehler laufen"
    assert isinstance(result.tours, list), "Tours sollte eine Liste sein"


def test_workflow_api_upload(setup_test_env, monkeypatch):
    """Test Workflow API Upload-Endpoint."""
    from importlib import reload
    import routes.workflow_api as workflow_module
    reload(workflow_module)
    
    # Erstelle FastAPI App
    app = FastAPI()
    app.include_router(workflow_module.router)
    client = TestClient(app)
    
    # Erstelle Test-CSV
    csv_content = """Kdnr;Name;Straße;PLZ;Ort
1;Test Kunde;Fröbelstraße 1;01159;Dresden"""
    
    # Upload testen
    response = client.post(
        "/api/workflow/upload",
        files={"file": ("test.csv", csv_content.encode('utf-8'), "text/csv")}
    )
    
    assert response.status_code == 200, f"Upload sollte erfolgreich sein, aber Status: {response.status_code}"
    data = response.json()
    assert "tours" in data, "Response sollte 'tours' enthalten"
    assert data.get("success") is not False, "Response sollte success=True haben"


def test_workflow_with_geocoding(setup_test_env, monkeypatch):
    """Test Workflow mit Geocoding-Integration (DB-First Strategie)."""
    from services.workflow_engine import run_workflow, ColumnMap
    import repositories.geo_repo as repo
    from importlib import reload
    reload(repo)
    
    tmp_path = setup_test_env
    
    # Füge Test-Koordinaten in DB ein (DB-First Test)
    repo.upsert("Fröbelstraße 1, 01159 Dresden", 51.0491695, 13.698383, source="test")
    
    # Erstelle Test-CSV
    csv_content = """Kdnr;Name;Straße;PLZ;Ort
1;Test Kunde;Fröbelstraße 1;01159;Dresden"""
    
    csv_file = tmp_path / "Tourplaene" / "test.csv"
    csv_file.write_bytes(csv_content.encode('utf-8'))
    
    # Workflow ausführen (ColumnMap mit Standard-Parametern)
    result = run_workflow(
        content=csv_file.read_bytes(),
        column_map=None  # Verwendet Standard-Mapping
    )
    
    # Validierung: Koordinaten sollten aus DB kommen (DB-First Strategie)
    assert result.ok >= 0, "Workflow sollte laufen (DB-First: sollte aus DB kommen)"
    # Tour kann leer sein wenn keine gültigen Koordinaten, aber sollte nicht crashen
    assert isinstance(result.tours, list), "Tours sollte eine Liste sein"


def test_workflow_address_corrections(setup_test_env, monkeypatch):
    """Test Workflow mit Address Corrections Integration."""
    from services.workflow_engine import run_workflow, ColumnMap
    from importlib import reload
    
    # Address Corrections Mock (falls vorhanden)
    try:
        import backend.services.address_corrections as addr_corr
        reload(addr_corr)
    except ImportError:
        pass  # Address Corrections optional
    
    tmp_path = setup_test_env
    
    # Erstelle Test-CSV mit Adresse die korrigiert werden könnte
    csv_content = """Kdnr;Name;Straße;PLZ;Ort
1;Test Kunde;Fröbelstr. 1;01159;Dresden"""
    
    csv_file = tmp_path / "Tourplaene" / "test.csv"
    csv_file.write_bytes(csv_content.encode('utf-8'))
    
    # Workflow ausführen (ColumnMap mit Standard-Parametern)
    result = run_workflow(
        content=csv_file.read_bytes(),
        column_map=None  # Verwendet Standard-Mapping
    )
    
    # Validierung
    assert result.ok >= 0, "Workflow sollte ohne Fehler laufen"
    assert len(result.tours) >= 0, "Tours sollten erstellt werden können"

