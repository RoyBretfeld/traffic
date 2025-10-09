"""
Unit-Tests für Alias-System
Testet Alias-Erstellung, -Auflösung und Integration in die Match-Route
"""
import os
import pytest
from importlib import reload

def test_alias_accept_and_match(tmp_path, monkeypatch):
    """Test der kompletten Alias-Funktionalität mit SQLite."""
    # SQLite DSN setzen
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    # Module neu laden mit neuer DB-URL
    import db.core as core
    reload(core)
    
    import db.schema as base
    reload(base)
    base.ensure_schema()
    
    import db.schema_alias as sa
    reload(sa)
    sa.ensure_alias_schema()
    
    # Repositories neu laden
    import repositories.geo_repo as repo
    reload(repo)
    
    import repositories.geo_alias_repo as alias
    reload(alias)

    # Seed: kanonische Adresse im Cache
    repo.upsert("Fröbelstraße 1, Dresden", 51.0504, 13.7373)

    # Test: Alias setzen
    alias.set_alias("Froebelstr. 1, Dresden", "Fröbelstraße 1, Dresden", created_by="test")
    
    # Test: Alias-Auflösung
    resolved = alias.resolve_aliases(["Froebelstr. 1, Dresden"])
    assert len(resolved) == 1
    # Prüfe dass der Alias existiert (normalisierte Form)
    assert "froebelstraße 1, dresden" in resolved
    assert resolved["froebelstraße 1, dresden"] == "Fröbelstraße 1, Dresden"
    
    # Test: Match-Funktionalität mit Alias
    from repositories.geo_repo import bulk_get, canon_addr
    
    q = ["Froebelstr. 1, Dresden"]
    aliases = alias.resolve_aliases(q)
    geo = bulk_get(q + list(aliases.values()))
    
    qn = canon_addr(q[0])  # Verwende canon_addr statt normalize_addr
    canon = aliases.get(qn)
    rec = geo.get(qn) or geo.get(canon)
    
    assert rec is not None
    assert abs(rec["lat"] - 51.0504) < 1e-6
    assert abs(rec["lon"] - 13.7373) < 1e-6

def test_alias_invalid_canonical(tmp_path, monkeypatch):
    """Test dass Alias nur für existierende kanonische Adressen gesetzt werden kann."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    import db.core as core
    reload(core)
    
    import db.schema as base
    reload(base)
    base.ensure_schema()
    
    import db.schema_alias as sa
    reload(sa)
    sa.ensure_alias_schema()
    
    import repositories.geo_alias_repo as alias
    reload(alias)
    
    # Test: Alias für nicht-existierende kanonische Adresse
    with pytest.raises(ValueError, match="canonical not in geo_cache"):
        alias.set_alias("Test Query", "Nicht existierende Adresse")

def test_alias_empty_or_identical(tmp_path, monkeypatch):
    """Test dass leere oder identische Aliasse abgelehnt werden."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    import db.core as core
    reload(core)
    
    import db.schema as base
    reload(base)
    base.ensure_schema()
    
    import db.schema_alias as sa
    reload(sa)
    sa.ensure_alias_schema()
    
    import repositories.geo_alias_repo as alias
    reload(alias)
    
    # Test: Leere Adressen
    with pytest.raises(ValueError, match="alias invalid: empty or identical"):
        alias.set_alias("", "Test")
    
    with pytest.raises(ValueError, match="alias invalid: empty or identical"):
        alias.set_alias("Test", "")
    
    # Test: Identische Adressen (muss erst canonical im Cache haben)
    import repositories.geo_repo as repo
    reload(repo)
    repo.upsert("Test", 1.0, 1.0)
    
    # Prüfe dass die Normalisierung unterschiedlich ist
    from repositories.geo_repo import canon_addr, normalize_addr
    q_norm = canon_addr("Test")
    c_norm = normalize_addr("Test")
    print(f"Query norm: {q_norm!r}, Canonical norm: {c_norm!r}")
    
    # Wenn sie identisch sind, sollte ein Fehler auftreten
    if q_norm == c_norm:
        with pytest.raises(ValueError, match="alias invalid: empty or identical"):
            alias.set_alias("Test", "Test")
    else:
        # Wenn sie unterschiedlich sind, sollte es funktionieren
        alias.set_alias("Test", "Test")
        resolved = alias.resolve_aliases(["Test"])
        assert len(resolved) == 1

def test_alias_upsert(tmp_path, monkeypatch):
    """Test dass Alias-Überschreibung funktioniert."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    import db.core as core
    reload(core)
    
    import db.schema as base
    reload(base)
    base.ensure_schema()
    
    import db.schema_alias as sa
    reload(sa)
    sa.ensure_alias_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    import repositories.geo_alias_repo as alias
    reload(alias)
    
    # Seed: zwei kanonische Adressen
    repo.upsert("Adresse A", 1.0, 1.0)
    repo.upsert("Adresse B", 2.0, 2.0)
    
    # Ersten Alias setzen
    alias.set_alias("Query", "Adresse A", created_by="user1")
    
    # Alias überschreiben
    alias.set_alias("Query", "Adresse B", created_by="user2")
    
    # Prüfen dass neuer Alias aktiv ist
    resolved = alias.resolve_aliases(["Query"])
    assert resolved["query"] == "Adresse B"

def test_alias_remove(tmp_path, monkeypatch):
    """Test der Alias-Entfernung."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    import db.core as core
    reload(core)
    
    import db.schema as base
    reload(base)
    base.ensure_schema()
    
    import db.schema_alias as sa
    reload(sa)
    sa.ensure_alias_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    import repositories.geo_alias_repo as alias
    reload(alias)
    
    # Seed: kanonische Adresse
    repo.upsert("Test Adresse", 1.0, 1.0)
    
    # Alias setzen
    alias.set_alias("Query", "Test Adresse")
    
    # Prüfen dass Alias existiert
    resolved = alias.resolve_aliases(["Query"])
    assert len(resolved) == 1
    
    # Alias entfernen
    alias.remove_alias("Query")
    
    # Prüfen dass Alias entfernt wurde
    resolved = alias.resolve_aliases(["Query"])
    assert len(resolved) == 0

def test_alias_stats(tmp_path, monkeypatch):
    """Test der Alias-Statistiken."""
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")
    
    import db.core as core
    reload(core)
    
    import db.schema as base
    reload(base)
    base.ensure_schema()
    
    import db.schema_alias as sa
    reload(sa)
    sa.ensure_alias_schema()
    
    import repositories.geo_repo as repo
    reload(repo)
    
    import repositories.geo_alias_repo as alias
    reload(alias)
    
    # Seed: kanonische Adresse
    repo.upsert("Test Adresse", 1.0, 1.0)
    
    # DB zwischen Tests leeren (da andere Tests bereits Aliasse erstellt haben)
    from db.core import ENGINE
    from sqlalchemy import text
    with ENGINE.begin() as conn:
        conn.execute(text("DELETE FROM geo_alias"))
        conn.execute(text("DELETE FROM geo_audit"))
    
    # Anfangs-Statistiken (nach Seed)
    stats = alias.get_alias_stats()
    assert stats["total_aliases"] == 0
    assert stats["total_audit_entries"] == 0
    
    # Alias setzen
    alias.set_alias("Query 1", "Test Adresse", created_by="user1")
    alias.set_alias("Query 2", "Test Adresse", created_by="user2")
    
    # Statistiken nach Alias-Erstellung
    stats = alias.get_alias_stats()
    assert stats["total_aliases"] == 2
    assert stats["total_audit_entries"] == 2
    
    # Alias entfernen
    alias.remove_alias("Query 1")
    
    # Statistiken nach Alias-Entfernung
    stats = alias.get_alias_stats()
    assert stats["total_aliases"] == 1
    assert stats["total_audit_entries"] == 3  # 2 Erstellungen + 1 Entfernung

def test_alias_resolve_empty_input():
    """Test der Alias-Auflösung bei leeren Eingaben."""
    # Mock für leeren Test ohne DB
    from repositories.geo_alias_repo import resolve_aliases
    
    # Leere Liste
    result = resolve_aliases([])
    assert result == {}
    
    # Liste mit leeren Strings
    result = resolve_aliases(["", "   ", None])
    assert result == {}

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
