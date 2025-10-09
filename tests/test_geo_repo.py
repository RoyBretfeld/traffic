import os
from importlib import reload

def test_geo_repo_sqlite(tmp_path, monkeypatch):
    # SQLite DSN injizieren, damit Test ohne externe DB läuft
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{tmp_path/'t.db'}")

    import db.core as core
    reload(core)

    # Schema anlegen
    import db.schema as schema
    reload(schema)
    schema.ensure_schema()

    # Repository laden
    import repositories.geo_repo as repo
    reload(repo)

    # Upsert & Get
    repo.upsert("Löbtauer Straße 1, 01809 Heidenau", 50.9836, 13.8663)
    row = repo.get("Löbtauer Straße 1, 01809 Heidenau")
    assert row and abs(row["lat"] - 50.9836) < 1e-6 and abs(row["lon"] - 13.8663) < 1e-6

    # Bulk‑Get
    res = repo.bulk_get(["Löbtauer Straße 1, 01809 Heidenau", "Fröbelstraße 5"])
    assert "Löbtauer Straße 1, 01809 Heidenau" in res
