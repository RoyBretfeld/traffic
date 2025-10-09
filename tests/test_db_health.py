import os
from pathlib import Path

def test_db_health_sqlite(tmp_path, monkeypatch):
    # SQLite als minimaler Check (kein Schema‑SET nötig)
    db_path = tmp_path / "t.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_path}")
    monkeypatch.setenv("DB_SCHEMA", "main")
    
    # Import nach Umgebungsvariablen-Setzung
    from importlib import reload
    import db.core as core
    reload(core)
    
    h = core.db_health()
    print(f"Health result: {h}")
    assert h["ok"] is True
    assert "version" in h
    assert h["schema"] == "main"
