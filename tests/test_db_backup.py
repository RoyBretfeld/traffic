"""
Tests für das Datenbank-Backup-System
"""

import pytest
import sqlite3
from pathlib import Path
import sys
import tempfile
import shutil

# Projekt-Root finden
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.db_backup import (
    create_backup,
    list_backups,
    restore_backup,
    cleanup_old_backups,
    get_database_path,
    BACKUP_DIR
)


@pytest.fixture
def test_db(tmp_path):
    """Erstellt eine temporäre Test-Datenbank."""
    test_db_path = tmp_path / "test_traffic.db"
    
    # Erstelle Test-DB mit ein paar Tabellen
    conn = sqlite3.connect(str(test_db_path))
    conn.execute("CREATE TABLE IF NOT EXISTS geo_cache (address_norm TEXT PRIMARY KEY, lat REAL, lon REAL)")
    conn.execute("INSERT INTO geo_cache VALUES ('test address', 51.0, 13.0)")
    conn.commit()
    conn.close()
    
    yield test_db_path
    
    # Cleanup
    if test_db_path.exists():
        test_db_path.unlink()


@pytest.fixture
def mock_backup_dir(tmp_path, monkeypatch):
    """Mock das Backup-Verzeichnis."""
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock BACKUP_DIR
    import scripts.db_backup as backup_module
    monkeypatch.setattr(backup_module, "BACKUP_DIR", backup_dir)
    
    yield backup_dir


def test_get_database_path():
    """Test: Findet Datenbank-Pfad."""
    db_path = get_database_path()
    assert isinstance(db_path, Path)
    # Die DB muss nicht existieren für diesen Test


def test_create_backup_success(test_db, mock_backup_dir, monkeypatch):
    """Test: Backup erfolgreich erstellen."""
    # Mock get_database_path
    import scripts.db_backup as backup_module
    monkeypatch.setattr(backup_module, "get_database_path", lambda: test_db)
    monkeypatch.setattr(backup_module, "cleanup_old_backups", lambda: None)
    
    success, message = create_backup()
    
    assert success is True
    assert "Backup erfolgreich erstellt" in message
    assert "traffic_backup_" in message
    
    # Prüfe ob Backup-Datei existiert
    backups = list(mock_backup_dir.glob("traffic_backup_*.db"))
    assert len(backups) == 1
    
    # Prüfe Backup-Inhalt
    backup_path = backups[0]
    backup_conn = sqlite3.connect(str(backup_path))
    rows = backup_conn.execute("SELECT * FROM geo_cache").fetchall()
    backup_conn.close()
    
    assert len(rows) == 1
    assert rows[0] == ("test address", 51.0, 13.0)


def test_list_backups(mock_backup_dir, monkeypatch):
    """Test: Backups auflisten."""
    # Mock BACKUP_DIR
    import scripts.db_backup as backup_module
    monkeypatch.setattr(backup_module, "BACKUP_DIR", mock_backup_dir)
    
    # Erstelle einige Test-Backups
    (mock_backup_dir / "traffic_backup_20250101_120000.db").write_bytes(b"fake backup 1")
    (mock_backup_dir / "traffic_backup_20250102_120000.db").write_bytes(b"fake backup 2")
    
    backups = list_backups()
    
    assert len(backups) == 2
    assert all("traffic_backup_" in b["filename"] for b in backups)
    assert all("size_mb" in b for b in backups)
    assert all("created" in b for b in backups)


def test_restore_backup(test_db, mock_backup_dir, monkeypatch):
    """Test: Backup wiederherstellen."""
    # Mock get_database_path und BACKUP_DIR
    import scripts.db_backup as backup_module
    monkeypatch.setattr(backup_module, "get_database_path", lambda: test_db)
    monkeypatch.setattr(backup_module, "BACKUP_DIR", mock_backup_dir)
    
    # Erstelle Backup
    backup_file = mock_backup_dir / "traffic_backup_test.db"
    shutil.copy2(test_db, backup_file)
    
    # Lösche Original-DB (simuliere Datenverlust)
    test_db.unlink()
    
    # Restore
    success, message = restore_backup("traffic_backup_test.db")
    
    assert success is True
    assert "wiederhergestellt" in message.lower()
    assert test_db.exists()  # DB wurde wiederhergestellt
    
    # Prüfe Inhalt
    conn = sqlite3.connect(str(test_db))
    rows = conn.execute("SELECT * FROM geo_cache").fetchall()
    conn.close()
    
    assert len(rows) == 1


def test_cleanup_old_backups(mock_backup_dir, monkeypatch):
    """Test: Alte Backups bereinigen."""
    from datetime import datetime, timedelta
    import time
    
    # Erstelle alte und neue Backups
    old_file = mock_backup_dir / "traffic_backup_old.db"
    new_file = mock_backup_dir / "traffic_backup_new.db"
    
    old_file.write_bytes(b"old")
    new_file.write_bytes(b"new")
    
    # Setze mtime für altes Backup (vor 31 Tagen)
    old_time = (datetime.now() - timedelta(days=31)).timestamp()
    
    # Mock stat() für altes File (Windows-kompatibel über os.utime)
    import os
    import time
    
    # Setze mtime direkt mit os.utime (funktioniert auf Windows)
    try:
        os.utime(str(old_file), (old_time, old_time))
    except (OSError, AttributeError):
        # Fallback: Mock über monkeypatch
        from unittest.mock import Mock, MagicMock
        
        def mock_stat(self):
            if str(self) == str(old_file) or self.name == "traffic_backup_old.db":
                result = MagicMock()
                result.st_mtime = old_time
                return result
            return Path.stat(self)
        
        monkeypatch.setattr(Path, "stat", mock_stat)
    
    # Cleanup aufrufen (mit reduzierter Retention für Test)
    import scripts.db_backup as backup_module
    original_retention = backup_module.BACKUP_RETENTION_DAYS
    monkeypatch.setattr(backup_module, "BACKUP_RETENTION_DAYS", 30)
    
    cleanup_old_backups()
    
    # Altes Backup sollte gelöscht sein
    assert not old_file.exists()
    # Neues Backup sollte noch existieren
    assert new_file.exists()


def test_backup_with_missing_db(monkeypatch):
    """Test: Backup bei fehlender DB."""
    import scripts.db_backup as backup_module
    
    def mock_get_db_path():
        return Path("/nonexistent/path/to/db.db")
    
    monkeypatch.setattr(backup_module, "get_database_path", mock_get_db_path)
    
    success, message = create_backup()
    
    assert success is False
    assert "nicht gefunden" in message


@pytest.mark.integration
def test_backup_restore_cycle(mock_backup_dir, monkeypatch, tmp_path):
    """Integrationstest: Kompletter Backup/Restore-Zyklus."""
    # Erstelle Test-DB
    test_db = tmp_path / "test_traffic.db"
    conn = sqlite3.connect(str(test_db))
    conn.execute("CREATE TABLE test_table (id INTEGER PRIMARY KEY, data TEXT)")
    conn.execute("INSERT INTO test_table (data) VALUES ('test1'), ('test2')")
    conn.commit()
    conn.close()
    
    # Mock
    import scripts.db_backup as backup_module
    monkeypatch.setattr(backup_module, "get_database_path", lambda: test_db)
    monkeypatch.setattr(backup_module, "BACKUP_DIR", mock_backup_dir)
    monkeypatch.setattr(backup_module, "cleanup_old_backups", lambda: None)
    
    # 1. Backup erstellen
    success, message = create_backup()
    assert success is True
    
    backups = list_backups()
    assert len(backups) > 0
    backup_filename = backups[0]["filename"]
    
    # 2. Original-DB löschen
    test_db.unlink()
    
    # 3. Backup wiederherstellen
    success, message = restore_backup(backup_filename)
    assert success is True
    assert test_db.exists()
    
    # 4. Inhalt prüfen
    conn = sqlite3.connect(str(test_db))
    rows = conn.execute("SELECT * FROM test_table").fetchall()
    conn.close()
    
    assert len(rows) == 2
    assert rows[0][1] == "test1"
    assert rows[1][1] == "test2"

