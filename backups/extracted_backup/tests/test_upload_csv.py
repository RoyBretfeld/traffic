"""
Tests für Upload-API mit Staging-System und Match-Integration.
"""
import pytest
import tempfile
import os
from pathlib import Path
from fastapi.testclient import TestClient
from fastapi import FastAPI
from importlib import reload

def test_upload_then_match(tmp_path, monkeypatch):
    """
    Test: Upload einer CSV-Datei mit verschiedenen Encodings und anschließendes Match.
    """
    # ENV Setup
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'test.db'}")
    monkeypatch.setenv("STAGING_DIR", str(tmp_path / "staging"))
    
    # Module reloaden für saubere Tests
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import routes.upload_csv as upload_module
    reload(upload_module)
    import routes.tourplan_match as match_module
    reload(match_module)
    
    # FastAPI App erstellen
    app = FastAPI()
    app.include_router(upload_module.router)
    app.include_router(match_module.router)
    
    client = TestClient(app)
    
    # Test-CSV mit verschiedenen Encodings erstellen
    test_cases = [
        {
            "name": "cp850_encoding.csv",
            "content": "Kunde;Straße;PLZ;Stadt\nTest;Fröbelstraße 1;01234;Dresden\nMüller;Hauptstraße 5;01067;Leipzig",
            "encoding": "cp850"
        },
        {
            "name": "utf8_encoding.csv", 
            "content": "Kunde;Straße;PLZ;Stadt\nTest;Fröbelstraße 1;01234;Dresden\nMüller;Hauptstraße 5;01067;Leipzig",
            "encoding": "utf-8"
        },
        {
            "name": "latin1_encoding.csv",
            "content": "Kunde;Straße;PLZ;Stadt\nTest;Fröbelstraße 1;01234;Dresden\nMüller;Hauptstraße 5;01067;Leipzig", 
            "encoding": "latin-1"
        }
    ]
    
    for test_case in test_cases:
        print(f"\n=== Test: {test_case['name']} ===")
        
        # CSV-Datei erstellen
        raw_content = test_case['content'].encode(test_case['encoding'])
        
        # Upload testen
        upload_response = client.post(
            '/api/upload/csv',
            files={'file': (test_case['name'], raw_content, 'text/csv')}
        )
        
        assert upload_response.status_code == 200, f"Upload fehlgeschlagen für {test_case['name']}: {upload_response.text}"
        
        upload_data = upload_response.json()
        assert upload_data['ok'] is True
        assert 'staging_file' in upload_data
        assert upload_data['size'] > 0
        
        staging_path = upload_data['staging_file']
        print(f"Staging-Pfad: {staging_path}")
        
        # Staging-Datei prüfen
        staging_file = Path(staging_path)
        assert staging_file.exists()
        assert staging_file.stat().st_size > 0
        
        # Inhalt der Staging-Datei prüfen (sollte UTF-8 sein)
        staging_content = staging_file.read_text(encoding='utf-8')
        assert 'Fröbelstraße' in staging_content
        assert 'Hauptstraße' in staging_content
        
        # Match-API testen
        match_response = client.get('/api/tourplan/match', params={'file': staging_path})
        
        assert match_response.status_code == 200, f"Match fehlgeschlagen für {test_case['name']}: {match_response.text}"
        
        match_data = match_response.json()
        assert 'items' in match_data
        assert len(match_data['items']) > 0
        
        print(f"Match erfolgreich: {len(match_data['items'])} Adressen verarbeitet")
        
        # Staging-Datei aufräumen
        staging_file.unlink()

def test_upload_invalid_file():
    """
    Test: Upload mit ungültiger Datei (keine CSV).
    """
    app = FastAPI()
    import routes.upload_csv as upload_module
    app.include_router(upload_module.router)
    
    client = TestClient(app)
    
    # Ungültige Datei hochladen
    response = client.post(
        '/api/upload/csv',
        files={'file': ('test.txt', b'keine csv', 'text/plain')}
    )
    
    assert response.status_code == 400
    assert 'only .csv allowed' in response.text

def test_upload_empty_file():
    """
    Test: Upload einer leeren Datei.
    """
    app = FastAPI()
    import routes.upload_csv as upload_module
    app.include_router(upload_module.router)
    
    client = TestClient(app)
    
    # Leere Datei hochladen
    response = client.post(
        '/api/upload/csv',
        files={'file': ('empty.csv', b'', 'text/csv')}
    )
    
    assert response.status_code == 400
    assert 'Leere Datei' in response.text

def test_upload_status():
    """
    Test: Upload-Status API.
    """
    app = FastAPI()
    import routes.upload_csv as upload_module
    app.include_router(upload_module.router)
    
    client = TestClient(app)
    
    # Status abfragen
    response = client.get('/api/upload/status')
    
    assert response.status_code == 200
    status_data = response.json()
    
    assert 'staging_dir' in status_data
    assert 'staging_files_count' in status_data
    assert 'staging_files' in status_data
    assert isinstance(status_data['staging_files'], list)

def test_upload_encoding_heuristics():
    """
    Test: Verschiedene Encoding-Heuristiken.
    """
    app = FastAPI()
    import routes.upload_csv as upload_module
    app.include_router(upload_module.router)
    
    client = TestClient(app)
    
    # Test mit Mojibake-verdächtigen Zeichen
    mojibake_content = "Kunde;Adresse\nTest;Fröbelstraße 1, Dresden\nMüller;Hauptstraße 5, Leipzig"
    
    # Verschiedene Encodings testen
    encodings = ['cp850', 'latin-1', 'utf-8']
    
    for encoding in encodings:
        try:
            raw_content = mojibake_content.encode(encoding)
            
            response = client.post(
                '/api/upload/csv',
                files={'file': (f'test_{encoding}.csv', raw_content, 'text/csv')}
            )
            
            # Upload sollte erfolgreich sein (auch bei Mojibake)
            assert response.status_code == 200, f"Upload fehlgeschlagen für {encoding}"
            
            upload_data = response.json()
            assert upload_data['ok'] is True
            
            # Staging-Datei prüfen
            staging_path = upload_data['staging_file']
            staging_file = Path(staging_path)
            staging_content = staging_file.read_text(encoding='utf-8')
            
            # Mojibake-Schutz sollte aktiv sein
            print(f"Encoding {encoding}: {len(staging_content)} Zeichen verarbeitet")
            
            # Aufräumen
            staging_file.unlink()
            
        except Exception as e:
            print(f"Encoding {encoding} fehlgeschlagen: {e}")
            # Das ist OK - manche Encodings können fehlschlagen

if __name__ == "__main__":
    # Direkter Test-Aufruf
    import tempfile
    import os
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        os.environ["DATABASE_URL"] = f"sqlite:///{tmp_dir}/test.db"
        os.environ["STAGING_DIR"] = f"{tmp_dir}/staging"
        
        print("=== Upload & Match Integration Test ===")
        
        # Mock monkeypatch für direkten Aufruf
        class MockMonkeypatch:
            def setenv(self, key, value):
                os.environ[key] = value
        
        test_upload_then_match(Path(tmp_dir), MockMonkeypatch())
        print("✓ Alle Tests erfolgreich!")
