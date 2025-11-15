# tests/test_persist_and_flags.py
from importlib import reload
import tempfile
from pathlib import Path

def test_persist_sets_flags(tmp_path, monkeypatch):
    """Test dass Persist-Writer korrekt Flags setzt."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    import repositories.geo_repo as repo
    reload(repo)
    from services.geocode_persist import write_result

    # Test mit zip_centroid Ergebnis
    res = write_result('01159 Dresden', [{
        "lat": "51.05",
        "lon": "13.73",
        "_note": "zip_centroid",
        "address": {"postcode": "01159", "state": "Sachsen"}
    }])
    
    assert res is not None
    assert res['source'] == 'geocoder'
    assert res['precision'] == 'zip_centroid'
    assert res['region_ok'] == 1  # Sachsen ist ok
    
    # Prüfe dass in DB gespeichert wurde
    got = repo.bulk_get(['01159 Dresden'])
    assert got and list(got.values())[0]['precision'] == 'zip_centroid'
    assert list(got.values())[0]['source'] == 'geocoder'
    assert list(got.values())[0]['region_ok'] == 1

def test_persist_synonym_flags(tmp_path, monkeypatch):
    """Test dass Synonym-Persistierung korrekt funktioniert."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    from services.geocode_persist import write_synonym_result
    from common.synonyms import SynonymHit

    # Test mit Synonym-Hit
    synonym_hit = SynonymHit("PF:JOCHEN", "Pf-Depot Jochen, Dresden", 51.05, 13.7373)
    res = write_synonym_result('Jochen - PF', synonym_hit)
    
    assert res is not None
    assert res['source'] == 'synonym'
    assert res['precision'] is None
    assert res['region_ok'] == 1  # Synonyme sind immer in Dresden

def test_persist_manual_queue_on_miss(tmp_path, monkeypatch):
    """Test dass fehlgeschlagene Geocodes in Manual-Queue landen."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    from services.geocode_persist import write_result
    import repositories.manual_repo as mr
    reload(mr)

    # Kein Treffer → Manual-Queue
    out = write_result('nan, nan Pulsnitz', [])
    assert out is None
    
    # Prüfe dass in Manual-Queue ist
    items = mr.list_open(limit=10)
    assert len(items) >= 1
    assert any('nan, nan Pulsnitz' in item['raw_address'] for item in items)

def test_persist_invalid_coordinates(tmp_path, monkeypatch):
    """Test dass ungültige Koordinaten in Manual-Queue landen."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    from services.geocode_persist import write_result
    import repositories.manual_repo as mr
    reload(mr)

    # Ungültige Koordinaten → Manual-Queue
    out = write_result('Teststraße 1', [{"lat": "invalid", "lon": "invalid"}])
    assert out is None
    
    # Prüfe dass in Manual-Queue ist
    items = mr.list_open(limit=10)
    assert len(items) >= 1
    assert any('Teststraße 1' in item['raw_address'] for item in items)

def test_upsert_ex_functionality(tmp_path, monkeypatch):
    """Test dass upsert_ex korrekt funktioniert."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    import repositories.geo_repo as repo
    reload(repo)

    # Test upsert_ex
    result = repo.upsert_ex(
        address="Teststraße 1, 01069 Dresden",
        lat=51.05,
        lon=13.74,
        source="geocoder",
        precision="full",
        region_ok=1
    )
    
    assert result['source'] == 'geocoder'
    assert result['precision'] == 'full'
    assert result['region_ok'] == 1
    
    # Prüfe dass in DB gespeichert wurde
    got = repo.bulk_get(['Teststraße 1, 01069 Dresden'])
    assert got
    entry = list(got.values())[0]
    assert entry['source'] == 'geocoder'
    assert entry['precision'] == 'full'
    assert entry['region_ok'] == 1
