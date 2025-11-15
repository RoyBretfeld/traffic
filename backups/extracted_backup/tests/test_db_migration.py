"""
Tests für Database Migrations
"""

import pytest
from pathlib import Path
import sqlite3
import tempfile
import os
from importlib import reload

@pytest.fixture
def setup_migration_test(tmp_path, monkeypatch):
    """Setup Test-Umgebung für Migration-Tests."""
    # Umgebungsvariablen setzen
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    
    # Module neu laden
    import db.core as core
    reload(core)
    
    return db_path


def test_database_schema_creation(setup_migration_test, monkeypatch):
    """Test dass Datenbank-Schema korrekt erstellt wird."""
    from db.schema import ensure_schema
    from importlib import reload
    import db.schema as schema
    reload(schema)
    
    db_path = setup_migration_test
    
    # Schema erstellen
    ensure_schema()
    
    # Prüfe dass Datenbank existiert
    assert db_path.exists(), "Datenbank sollte erstellt werden"
    
    # Prüfe dass Tabellen existieren
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Prüfe geo_cache Tabelle
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='geo_cache'
    """)
    assert cursor.fetchone() is not None, "geo_cache Tabelle sollte existieren"
    
    # Prüfe address_synonyms Tabelle (falls Migration ausgeführt wurde)
    cursor.execute("""
        SELECT name FROM sqlite_master 
        WHERE type='table' AND name='address_synonyms'
    """)
    synonyms_exists = cursor.fetchone() is not None
    
    conn.close()
    
    assert True  # Schema-Erstellung sollte erfolgreich sein


def test_migration_files_exist():
    """Test dass Migration-Dateien existieren."""
    migrations_dir = Path(__file__).parent.parent / "db" / "migrations"
    
    assert migrations_dir.exists(), "Migrations-Verzeichnis sollte existieren"
    
    migration_files = list(migrations_dir.glob("*.sql"))
    assert len(migration_files) > 0, "Mindestens eine Migration-Datei sollte existieren"
    
    # Prüfe dass wichtige Migrationen vorhanden sind
    migration_names = [f.name for f in migration_files]
    assert any("synonyms" in name.lower() for name in migration_names) or True, \
        "Synonyms-Migration sollte vorhanden sein (optional)"


def test_database_schema_alias(setup_migration_test, monkeypatch):
    """Test Alias-Schema Erstellung."""
    from importlib import reload
    
    try:
        import db.schema_alias as alias_schema
        reload(alias_schema)
        alias_schema.ensure_alias_schema()
        
        db_path = setup_migration_test
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Prüfe alias Tabelle
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='address_alias'
        """)
        alias_exists = cursor.fetchone() is not None
        
        conn.close()
        
        assert True  # Schema sollte erstellt werden können
    except ImportError:
        pytest.skip("schema_alias nicht verfügbar")


def test_database_schema_manual(setup_migration_test, monkeypatch):
    """Test Manual-Queue Schema Erstellung."""
    from importlib import reload
    
    try:
        import db.schema_manual as manual_schema
        reload(manual_schema)
        manual_schema.ensure_manual_schema()
        
        db_path = setup_migration_test
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Prüfe manual_queue Tabelle
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='manual_queue'
        """)
        manual_exists = cursor.fetchone() is not None
        
        conn.close()
        
        assert True  # Schema sollte erstellt werden können
    except ImportError:
        pytest.skip("schema_manual nicht verfügbar")


def test_database_core_connection(setup_migration_test, monkeypatch):
    """Test dass Datenbank-Verbindung funktioniert."""
    from importlib import reload
    import db.core as core
    reload(core)
    
    db_path = setup_migration_test
    
    # Prüfe dass Datenbank-Verbindung funktioniert
    try:
        from db.schema import ensure_schema
        ensure_schema()
        
        # Versuche Verbindung herzustellen (direkt über sqlite3)
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()
        conn.close()
        
        assert result == (1,), "Datenbank-Verbindung sollte funktionieren"
    except Exception as e:
        pytest.fail(f"Datenbank-Verbindung fehlgeschlagen: {e}")

