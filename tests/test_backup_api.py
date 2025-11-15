"""
Tests für Backup-API-Endpoints
"""

import pytest
import sys
from pathlib import Path
from fastapi.testclient import TestClient

# Projekt-Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import create_app


@pytest.fixture
def client():
    """Erstellt TestClient für API-Tests."""
    app = create_app()
    return TestClient(app)


def test_create_backup_endpoint(client, monkeypatch, tmp_path):
    """Test: Backup erstellen über API."""
    # Mock BACKUP_DIR
    import scripts.db_backup as backup_module
    mock_backup_dir = tmp_path / "backups"
    mock_backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Mock create_backup Funktion
    def mock_create_backup():
        return True, f"Backup erfolgreich erstellt: traffic_backup_test.db (1.0 MB)"
    
    monkeypatch.setattr("routes.backup_api.create_backup", mock_create_backup)
    
    response = client.post("/api/backup/create")
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data or "message" in data


def test_list_backups_endpoint(client, monkeypatch, tmp_path):
    """Test: Backups auflisten über API."""
    # Mock BACKUP_DIR und list_backups
    import scripts.db_backup as backup_module
    mock_backup_dir = tmp_path / "backups"
    mock_backup_dir.mkdir(parents=True, exist_ok=True)
    
    # Erstelle Test-Backups
    (mock_backup_dir / "traffic_backup_test1.db").write_bytes(b"fake backup")
    
    def mock_list_backups():
        return [
            {
                "filename": "traffic_backup_test1.db",
                "size_mb": 0.001,
                "created": "2025-01-01T12:00:00"
            }
        ]
    
    monkeypatch.setattr("routes.backup_api.list_backups", mock_list_backups)
    
    response = client.get("/api/backup/list")
    
    assert response.status_code == 200
    data = response.json()
    assert "backups" in data or isinstance(data, list)
    assert len(data.get("backups", data)) > 0


def test_restore_backup_endpoint(client, monkeypatch):
    """Test: Backup wiederherstellen über API."""
    # Mock restore_backup
    def mock_restore_backup(filename):
        return True, f"Backup {filename} erfolgreich wiederhergestellt"
    
    monkeypatch.setattr("routes.backup_api.restore_backup", mock_restore_backup)
    
    response = client.post(
        "/api/backup/restore",
        json={"backup_filename": "traffic_backup_test.db"}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data or "message" in data


def test_cleanup_backups_endpoint(client, monkeypatch):
    """Test: Alte Backups bereinigen über API."""
    # Mock cleanup_old_backups
    def mock_cleanup():
        return {"deleted": 2, "kept": 5}
    
    monkeypatch.setattr("routes.backup_api.cleanup_old_backups", mock_cleanup)
    
    response = client.post("/api/backup/cleanup")
    
    assert response.status_code == 200
    data = response.json()
    assert "success" in data or "deleted" in data

