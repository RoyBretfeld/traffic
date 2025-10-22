#!/usr/bin/env python3
"""
Tests für bulk_get IN-Klausel Fix
"""

import pytest
import tempfile
import os
from pathlib import Path
from importlib import reload


def test_bulk_get_returns_records(tmp_path, monkeypatch):
    """Teste dass bulk_get mit expanding bindparam korrekt funktioniert."""
    # SQLite DSN für Test
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    # Module neu laden mit Test-DB
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    # Zwei Einträge mit Umlauten einfügen
    repo.upsert("Fröbelstraße 1, Dresden", 51.0504, 13.7373)
    repo.upsert("Löbtauer Straße 2, Heidenau", 50.9836, 13.8663)
    
    # Bulk-Lookup testen (inkl. Trim/Norm)
    res = repo.bulk_get([
        " Fröbelstraße 1, Dresden ",  # Mit Leerzeichen
        "Löbtauer Straße 2, Heidenau",
        "Fehlt 9"  # Nicht vorhanden
    ])
    
    # Prüfe dass beide vorhandenen Adressen gefunden wurden
    expected_keys = {
        repo.normalize_addr("Fröbelstraße 1, Dresden"),
        repo.normalize_addr("Löbtauer Straße 2, Heidenau"),
    }
    assert set(res.keys()) == expected_keys
    
    # Prüfe Koordinaten
    froebel_key = repo.normalize_addr("Fröbelstraße 1, Dresden")
    assert abs(res[froebel_key]["lat"] - 51.0504) < 1e-6
    assert abs(res[froebel_key]["lon"] - 13.7373) < 1e-6
    
    loebtauer_key = repo.normalize_addr("Löbtauer Straße 2, Heidenau")
    assert abs(res[loebtauer_key]["lat"] - 50.9836) < 1e-6
    assert abs(res[loebtauer_key]["lon"] - 13.8663) < 1e-6


def test_bulk_get_empty_list():
    """Teste dass bulk_get mit leerer Liste korrekt umgeht."""
    import repositories.geo_repo as repo
    
    res = repo.bulk_get([])
    assert res == {}
    
    res = repo.bulk_get([""])
    assert res == {}
    
    res = repo.bulk_get([None])
    assert res == {}


def test_bulk_get_large_list(tmp_path, monkeypatch):
    """Teste dass bulk_get mit großen Listen (Chunking) funktioniert."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    import db.core as core
    reload(core)
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    # Viele Einträge einfügen
    addresses = []
    for i in range(100):
        addr = f"Teststraße {i}, Teststadt"
        repo.upsert(addr, 51.0 + i*0.001, 13.0 + i*0.001)
        addresses.append(addr)
    
    # Bulk-Lookup testen
    res = repo.bulk_get(addresses)
    
    # Alle sollten gefunden werden
    assert len(res) == 100
    
    # Prüfe ein paar spezifische Werte
    test_key = repo.normalize_addr("Teststraße 50, Teststadt")
    assert test_key in res
    assert abs(res[test_key]["lat"] - 51.05) < 1e-6


def test_normalize_addr_consistency():
    """Teste dass normalize_addr konsistent ist."""
    import repositories.geo_repo as repo
    
    test_cases = [
        "Fröbelstraße 1, Dresden",
        " Fröbelstraße 1, Dresden ",
        "Fröbelstraße  1,  Dresden",  # Mehrfach-Leerzeichen
        "Fröbelstraße 1, Dresden\n",  # Mit Newline
    ]
    
    normalized = [repo.normalize_addr(addr) for addr in test_cases]
    
    # Alle sollten identisch normalisiert werden
    assert all(n == normalized[0] for n in normalized)
    assert normalized[0] == "Fröbelstraße 1, Dresden"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
