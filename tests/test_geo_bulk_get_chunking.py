"""Test für bulk_get Chunking und Skalierung."""
from importlib import reload
import os
from pathlib import Path
import tempfile
import sys

# Füge das Projekt-Root-Verzeichnis zum Python-Pfad hinzu
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_bulk_get_chunks(tmp_path, monkeypatch):
    """Test dass bulk_get große Listen in Chunks verarbeitet."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    
    import db.core as core; reload(core)
    import db.schema as schema; reload(schema); schema.ensure_schema()
    import repositories.geo_repo as repo; reload(repo)

    # 1200 Einträge erstellen (mehr als CHUNK=800)
    print("Erstelle 1200 Test-Einträge...")
    for i in range(1200):
        repo.upsert(f"Teststraße {i}, Stadt", 50.0 + i*1e-6, 13.0 + i*1e-6)
    
    # Bulk-Lookup testen
    keys = [f"Teststraße {i}, Stadt" for i in range(1200)]
    print(f"Teste bulk_get mit {len(keys)} Adressen...")
    
    out = repo.bulk_get(keys)
    assert len(out) == 1200, f"Erwartet 1200, erhalten {len(out)}"
    
    # Prüfe dass alle Einträge 'src': 'cache' haben
    for addr, data in out.items():
        assert 'src' in data, f"Kein 'src' Feld für {addr}"
        assert data['src'] == 'cache', f"Falsches 'src' für {addr}: {data['src']}"
        assert 'lat' in data, f"Kein 'lat' Feld für {addr}"
        assert 'lon' in data, f"Kein 'lon' Feld für {addr}"
    
    print(f"✓ bulk_get erfolgreich: {len(out)} Einträge mit korrekten Feldern")

def test_bulk_get_empty():
    """Test bulk_get mit leerer Liste."""
    import repositories.geo_repo as repo; reload(repo)
    
    out = repo.bulk_get([])
    assert out == {}, f"Leere Liste sollte leeres Dict zurückgeben: {out}"
    
    out = repo.bulk_get([None, "", "   "])
    assert out == {}, f"None/leere Strings sollten ignoriert werden: {out}"

def test_bulk_get_partial():
    """Test bulk_get mit teilweise vorhandenen Adressen."""
    import repositories.geo_repo as repo; reload(repo)
    
    # Nur einige Adressen in DB
    repo.upsert("Vorhanden 1, Stadt", 50.0, 13.0)
    repo.upsert("Vorhanden 2, Stadt", 50.1, 13.1)
    
    # Mix aus vorhandenen und nicht vorhandenen Adressen
    keys = ["Vorhanden 1, Stadt", "Nicht vorhanden, Stadt", "Vorhanden 2, Stadt", "Auch nicht da, Stadt"]
    
    out = repo.bulk_get(keys)
    assert len(out) == 2, f"Erwartet 2, erhalten {len(out)}"
    assert "vorhanden 1, stadt" in out, "Erste Adresse nicht gefunden"
    assert "vorhanden 2, stadt" in out, "Zweite Adresse nicht gefunden"

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Mock monkeypatch für direkten Aufruf
        class MockMonkeypatch:
            def setenv(self, key, value):
                os.environ[key] = value

        print("=== Bulk Get Chunking Test ===")
        test_bulk_get_chunks(Path(tmp_dir), MockMonkeypatch())
        test_bulk_get_empty()
        test_bulk_get_partial()
        print("✓ Alle Tests erfolgreich!")
