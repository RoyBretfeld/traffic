import os, sqlite3, tempfile
from importlib import import_module

# Erwartet, dass db/schema.py das Symbol ensure_geo_fail_next_attempt + ensure_schema bereitstellt
schema = import_module("db.schema")

def has_column(db_path: str, table: str, column: str) -> bool:
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.execute(f"PRAGMA table_info({table})")
        return any(r[1] == column for r in cur.fetchall())
    finally:
        conn.close()

def test_geo_fail_next_attempt_upgrade_idempotent(tmp_path):
    db_file = tmp_path / "t.db"
    # Simuliere Altbestand: geo_fail ohne next_attempt
    conn = sqlite3.connect(str(db_file))
    try:
        conn.execute("CREATE TABLE geo_fail(id INTEGER PRIMARY KEY, raw TEXT)")
        conn.commit()
    finally:
        conn.close()

    # Engine auf diese Datei zeigen lassen
    from sqlalchemy import create_engine
    eng = create_engine(f"sqlite:///{db_file}")

    # Basisschema einmal laufen lassen (falls weitere Tabellen nötig sind)
    schema.ensure_schema()

    # Härte explizit ausführen (sollte aber schon in ensure_schema enthalten sein)
    with eng.connect() as c:
        schema.ensure_geo_fail_next_attempt(c)

    # Prüfen
    assert has_column(str(db_file), "geo_fail", "next_attempt")
