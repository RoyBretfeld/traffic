"""Test für Upload & Match Integration mit verschiedenen Encodings."""
from importlib import reload
from fastapi import FastAPI
from fastapi.testclient import TestClient
import os
from pathlib import Path
import tempfile
import sys

# Füge das Projekt-Root-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_upload_then_match(tmp_path, monkeypatch):
    """Test Upload mit verschiedenen Encodings und anschließendes Match."""
    # ENV
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    monkeypatch.setenv("STAGING_DIR", str(tmp_path/"staging"))

    # App
    import db.core as core; reload(core)
    import db.schema as schema; reload(schema); schema.ensure_schema()
    import routes.upload_csv as up; reload(up)
    import routes.tourplan_match as match; reload(match)
    import backend.parsers.tour_plan_parser as parser; reload(parser)
    import services.geocode_fill as geocode_fill; reload(geocode_fill)
    import repositories.geo_repo as geo_repo; reload(geo_repo)
    import ingest.guards as guards; reload(guards)

    app = FastAPI(); app.include_router(up.router); app.include_router(match.router)
    client = TestClient(app)

    # Testfälle für verschiedene Encodings
    test_cases = {
        "cp850_encoding.csv": "Kunde;Straße;PLZ;Stadt\r\nTest;Fröbelstraße 1;01234;Dresden\r\nMüller;Hauptstraße 5;01067;Leipzig".encode("cp850"),
        "utf8_encoding.csv": "Kunde;Straße;PLZ;Stadt\r\nTest;Fröbelstraße 1;01234;Dresden\r\nMüller;Hauptstraße 5;01067;Leipzig".encode("utf-8"),
        "latin1_encoding.csv": "Kunde;Straße;PLZ;Stadt\r\nTest;Fröbelstraße 1;01234;Dresden\r\nMüller;Hauptstraße 5;01067;Leipzig".encode("latin-1"),
    }

    for filename, raw_content in test_cases.items():
        print(f"\n=== Test: {filename} ===")
        # Upload
        r = client.post('/api/upload/csv', files={'file': (filename, raw_content, 'text/csv')})
        assert r.status_code == 200, f"Upload failed for {filename}: {r.text}"
        j = r.json()
        assert 'encoding_used' in j, f"No encoding_used in response for {filename}"
        assert j['encoding_used'].startswith('cp') or 'utf-8' in j['encoding_used'], f"Invalid encoding_used: {j['encoding_used']}"
        p = j['staging_file']
        print(f"Staging-Pfad: {p}, Encoding: {j['encoding_used']}")

        # Match sollte laufen
        r2 = client.get('/api/tourplan/match', params={'file': p})
        assert r2.status_code == 200, f"Match failed for {filename}: {r2.text}"
        j2 = r2.json()
        assert j2.get('items') is not None, f"No items in match response for {filename}: {j2}"
        assert len(j2['items']) > 0, f"No addresses matched for {filename}: {j2}"
        print(f"✓ Match erfolgreich für {filename}: {len(j2['items'])} Adressen verarbeitet")

        # Prüfe, ob die Adressen korrekt geparst wurden (kein Mojibake)
        for item in j2['items']:
            norm_address = item['norm']
            # Hier sollte kein Mojibake mehr sein
            assert '?' not in norm_address and '├' not in norm_address and 'Â' not in norm_address, \
                f"Mojibake detected in normalized address for {filename}: {norm_address}"
            print(f"  - {item['raw']} -> {norm_address} (has_geo: {item['has_geo']})")

if __name__ == "__main__":
    # Direkter Test-Aufruf
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Mock monkeypatch für direkten Aufruf
        class MockMonkeypatch:
            def setenv(self, key, value):
                os.environ[key] = value

        print("=== Upload & Match Integration Test ===")
        test_upload_then_match(Path(tmp_dir), MockMonkeypatch())
        print("✓ Alle Tests erfolgreich!")
