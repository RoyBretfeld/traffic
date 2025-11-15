# tests/test_geo_unique_index.py
import pytest
from importlib import reload
from pathlib import Path
import tempfile
import os

def test_unique_index_and_upsert(tmp_path, monkeypatch):
    """Test: Unique-Index verhindert Duplikate, Upsert funktioniert korrekt"""
    # Test-Datenbank konfigurieren
    db_path = tmp_path / "test.db"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    
    # Module neu laden mit Test-DB
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    # Test 1: Gleiche Adresse zweimal upserten -> nur ein Eintrag
    repo.upsert('Fröbelstraße 1, Dresden', 51.0, 13.7)
    repo.upsert('Fröbelstraße 1 | Dresden', 51.000001, 13.700001)  # Pipe wird normalisiert
    
    with repo.ENGINE.begin() as c:
        n = c.execute(repo.text('SELECT COUNT(*) FROM geo_cache')).scalar_one()
    assert n == 1, f"Erwartet 1 Eintrag, aber {n} gefunden"
    
    # Test 2: Prüfe dass die neueren Koordinaten gespeichert wurden
    result = repo.get('Fröbelstraße 1, Dresden')
    assert result is not None
    assert abs(result['lat'] - 51.000001) < 0.000001
    assert abs(result['lon'] - 13.700001) < 0.000001
    
    # Test 3: Verschiedene Adressen -> verschiedene Einträge
    repo.upsert('Altmarkt 1, Dresden', 51.05, 13.74)
    
    with repo.ENGINE.begin() as c:
        n = c.execute(repo.text('SELECT COUNT(*) FROM geo_cache')).scalar_one()
    assert n == 2, f"Erwartet 2 Einträge, aber {n} gefunden"
    
    # Test 4: Duplikat-Check (sollte 0 sein wegen PRIMARY KEY)
    with repo.ENGINE.begin() as c:
        duplicates = c.execute(repo.text(
            "SELECT address_norm, COUNT(*) as n FROM geo_cache GROUP BY address_norm HAVING n>1"
        )).fetchall()
    assert len(duplicates) == 0, f"Duplikate gefunden: {duplicates}"

def test_upsert_with_company_name(tmp_path, monkeypatch):
    """Test: Upsert mit Firmenname funktioniert korrekt"""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    # Adresse mit Firmenname speichern
    result = repo.upsert('Hauptstraße 1, Dresden', 51.0, 13.7, company_name='Test GmbH')
    
    # Prüfe dass beide Varianten gespeichert wurden
    with repo.ENGINE.begin() as c:
        n = c.execute(repo.text('SELECT COUNT(*) FROM geo_cache')).scalar_one()
    assert n >= 2, f"Erwartet mindestens 2 Einträge (Adresse + Firmenname), aber {n} gefunden"
    
    # Prüfe dass beide Varianten abrufbar sind
    addr_result = repo.get('Hauptstraße 1, Dresden')
    company_result = repo.get('Test GmbH, Hauptstraße 1, Dresden')
    
    assert addr_result is not None
    assert company_result is not None
    assert addr_result['lat'] == company_result['lat']
    assert addr_result['lon'] == company_result['lon']

def test_primary_key_constraint(tmp_path, monkeypatch):
    """Test: PRIMARY KEY verhindert Duplikate auch bei direkter INSERT"""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv('DATABASE_URL', f"sqlite:///{db_path}")
    
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    # Ersten Eintrag einfügen
    repo.upsert('Teststraße 1, Dresden', 51.0, 13.7)
    
    # Versuche Duplikat direkt einzufügen (sollte fehlschlagen)
    with pytest.raises(Exception):  # SQLite IntegrityError oder ähnlich
        with repo.ENGINE.begin() as c:
            c.execute(repo.text(
                "INSERT INTO geo_cache (address_norm, lat, lon) VALUES (:addr, :lat, :lon)"
            ), {"addr": "Teststraße 1, Dresden", "lat": 51.1, "lon": 13.8})
