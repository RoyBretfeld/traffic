# tests/test_manual_queue_and_export.py
from importlib import reload
from pathlib import Path
import tempfile

def test_manual_queue_on_miss_and_export(tmp_path, monkeypatch):
    """Test dass Manual-Queue bei Misses funktioniert und Export möglich ist."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    import repositories.manual_repo as mr
    reload(mr)
    from services.geocode_persist import write_result

    # Kein Treffer → Manual-Queue
    out = write_result('nan, nan Pulsnitz', [])
    assert out is None

    # Prüfe dass in Manual-Queue ist
    items = mr.list_open(limit=10)
    assert len(items) >= 1
    assert any('nan, nan Pulsnitz' in item['raw_address'] for item in items)

    # Test Export
    out_csv = tmp_path / 'pending.csv'
    n = mr.export_csv(str(out_csv))
    assert n >= 1
    assert out_csv.exists()
    assert out_csv.stat().st_size > 0

    # Prüfe CSV-Inhalt
    content = out_csv.read_text(encoding='utf-8')
    assert 'nan, nan Pulsnitz' in content
    assert 'geocode_miss' in content

def test_manual_queue_multiple_reasons(tmp_path, monkeypatch):
    """Test dass verschiedene Gründe für Manual-Queue funktionieren."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    import repositories.manual_repo as mr
    reload(mr)

    # Verschiedene Gründe hinzufügen
    mr.add_open('Adresse 1', 'geocode_miss')
    mr.add_open('Adresse 2', 'invalid_coordinates')
    mr.add_open('Adresse 3', 'timeout')

    # Prüfe dass alle in Queue sind
    items = mr.list_open(limit=10)
    assert len(items) >= 3
    
    reasons = [item['reason'] for item in items]
    assert 'geocode_miss' in reasons
    assert 'invalid_coordinates' in reasons
    assert 'timeout' in reasons

def test_manual_queue_is_open_check(tmp_path, monkeypatch):
    """Test dass is_open Check funktioniert."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    import repositories.manual_repo as mr
    reload(mr)

    # Adresse hinzufügen
    mr.add_open('Test Adresse', 'geocode_miss')
    
    # Prüfe is_open
    assert mr.is_open('Test Adresse')
    assert not mr.is_open('Andere Adresse')

def test_manual_queue_clear(tmp_path, monkeypatch):
    """Test dass Manual-Queue geleert werden kann."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    import repositories.manual_repo as mr
    reload(mr)

    # Mehrere Einträge hinzufügen
    mr.add_open('Adresse 1', 'geocode_miss')
    mr.add_open('Adresse 2', 'invalid_coordinates')
    
    # Prüfe dass Einträge da sind
    items = mr.list_open(limit=10)
    assert len(items) >= 2
    
    # Queue leeren
    deleted_count = mr.clear_queue()
    assert deleted_count >= 2
    
    # Prüfe dass Queue leer ist
    items = mr.list_open(limit=10)
    assert len(items) == 0

def test_manual_queue_limit(tmp_path, monkeypatch):
    """Test dass Limit-Parameter funktioniert."""
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{tmp_path/'t.db'}")
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    import repositories.manual_repo as mr
    reload(mr)

    # Mehrere Einträge hinzufügen
    for i in range(5):
        mr.add_open(f'Adresse {i}', 'geocode_miss')
    
    # Test mit Limit
    items = mr.list_open(limit=3)
    assert len(items) <= 3
    
    # Test ohne Limit (Standard)
    items_all = mr.list_open()
    assert len(items_all) >= 5
