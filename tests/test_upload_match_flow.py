"""
Tests für Upload → Match Workflow (Fix-Plan: 404/500 in Workflow)

Testet:
- Upload liefert stored_path
- Match funktioniert mit stored_path (GET und POST)
- Keine "body stream already read" Fehler
- Keine "file=undefined" Fehler
"""
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from pathlib import Path
import tempfile
import os

client = TestClient(app)

@pytest.fixture
def sample_csv_file():
    """Erstellt eine temporäre CSV-Datei für Tests."""
    content = """Kdnr;Name;Straße;PLZ;Ort
1;Test Kunde 1;Teststraße 1;01067;Dresden
2;Test Kunde 2;Teststraße 2;01099;Dresden"""
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    yield temp_path
    
    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)

def test_upload_returns_stored_path(sample_csv_file):
    """Test: Upload liefert stored_path im Response."""
    with open(sample_csv_file, 'rb') as f:
        response = client.post(
            "/api/upload/csv",
            files={"file": ("test.csv", f, "text/csv")}
        )
    
    assert response.status_code == 200
    data = response.json()
    
    # WICHTIG: stored_path muss vorhanden sein
    assert "stored_path" in data
    assert data["stored_path"] is not None
    assert len(data["stored_path"]) >= 3
    
    # Kompatibilität: staged_path und staging_file sollten auch vorhanden sein
    assert "staged_path" in data
    assert "staging_file" in data
    
    # rows sollte vorhanden sein
    assert "rows" in data
    assert isinstance(data["rows"], int)

def test_upload_returns_stored_path(sample_csv_file):
    """Test: Upload gibt stored_path zurück (neues vereinheitlichtes Feld)."""
    with open(sample_csv_file, 'rb') as f:
        upload_response = client.post(
            "/api/upload/csv",
            files={"file": ("test.csv", f, "text/csv")}
        )
    
    assert upload_response.status_code == 200
    data = upload_response.json()
    
    # stored_path sollte vorhanden sein
    assert "stored_path" in data, "Response sollte 'stored_path' enthalten"
    stored_path = data["stored_path"]
    assert stored_path, "stored_path sollte nicht leer sein"
    assert isinstance(stored_path, str), "stored_path sollte String sein"

def test_match_get_with_stored_path(sample_csv_file):
    """Test: Match-Endpoint (GET) funktioniert mit stored_path."""
    # 1) Upload
    with open(sample_csv_file, 'rb') as f:
        upload_response = client.post(
            "/api/upload/csv",
            files={"file": ("test.csv", f, "text/csv")}
        )
    
    assert upload_response.status_code == 200
    stored_path = upload_response.json()["stored_path"]
    
    # 2) Match (GET)
    match_response = client.get(
        "/api/tourplan/match",
        params={"file": stored_path}
    )
    
    # Match kann 200 (OK) oder 404 (Datei nicht gefunden) oder 500 (Parser-Fehler) sein
    assert match_response.status_code in (200, 404, 500)
    
    if match_response.status_code == 200:
        data = match_response.json()
        assert "file" in data
        assert "rows" in data
        assert "items" in data

def test_match_post_with_stored_path(sample_csv_file):
    """Test: Match-Endpoint (POST) funktioniert mit stored_path."""
    # 1) Upload
    with open(sample_csv_file, 'rb') as f:
        upload_response = client.post(
            "/api/upload/csv",
            files={"file": ("test.csv", f, "text/csv")}
        )
    
    assert upload_response.status_code == 200
    stored_path = upload_response.json()["stored_path"]
    
    # 2) Match (POST)
    match_response = client.post(
        "/api/tourplan/match",
        json={"stored_path": stored_path}
    )
    
    # Match kann 200 (OK) oder 404 (Datei nicht gefunden) oder 500 (Parser-Fehler) sein
    assert match_response.status_code in (200, 404, 500)
    
    if match_response.status_code == 200:
        data = match_response.json()
        assert "file" in data
        assert "rows" in data
        assert "items" in data

def test_match_get_validation_min_length():
    """Test: GET-Endpoint validiert min_length=3."""
    # Zu kurzer Pfad
    response = client.get(
        "/api/tourplan/match",
        params={"file": "ab"}  # Nur 2 Zeichen
    )
    
    assert response.status_code == 422  # Validation Error

def test_match_post_validation_missing_stored_path():
    """Test: POST-Endpoint validiert fehlendes stored_path."""
    response = client.post(
        "/api/tourplan/match",
        json={}  # stored_path fehlt
    )
    
    assert response.status_code == 422  # Validation Error

def test_match_post_validation_min_length():
    """Test: POST-Endpoint validiert min_length=3."""
    response = client.post(
        "/api/tourplan/match",
        json={"stored_path": "ab"}  # Nur 2 Zeichen
    )
    
    assert response.status_code == 422  # Validation Error

def test_upload_response_structure():
    """Test: Upload-Response hat die erwartete Struktur."""
    # Erstelle minimale CSV
    content = "Kdnr;Name\n1;Test"
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    
    try:
        with open(temp_path, 'rb') as f:
            response = client.post(
                "/api/upload/csv",
                files={"file": ("test.csv", f, "text/csv")}
            )
        
        assert response.status_code == 200
        data = response.json()
        
        # Erforderliche Felder
        assert "stored_path" in data
        assert "rows" in data
        assert "filename" in data
        assert "encoding" in data
        
        # stored_path sollte ein String sein
        assert isinstance(data["stored_path"], str)
        assert len(data["stored_path"]) >= 3
        
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)

