#!/usr/bin/env python3
import argparse, os, re, sqlite3, sys
from urllib.parse import urlparse

# Default: liest DATABASE_URL oder nutzt ./app.db

def resolve_db_path(cli_path: str | None) -> str:
    if cli_path:
        return cli_path
    db_url = os.environ.get("DATABASE_URL", "sqlite:///app.db")
    if db_url.startswith("sqlite:"):
        # Formate: sqlite:///rel/od/er.db  | sqlite:////abs/pfad.db
        m = re.match(r"sqlite:(?://)?(/.*)", db_url)
        if m:
            return m.group(1)
        # Fallback auf app.db im Projektroot
        return os.path.join(os.getcwd(), "app.db")
    # Unerwartet: für Nicht-SQLite geben wir auf
    print(f"[ERROR] Unsupported DATABASE_URL for this hotfix: {db_url}")
    sys.exit(2)


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table})")
    return any(row[1] == column for row in cur.fetchall())


def table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)
    )
    return cur.fetchone() is not None


def ensure_geo_fail_next_attempt(conn: sqlite3.Connection) -> None:
    if not table_exists(conn, "geo_fail"):
        print("[WARN] Tabelle geo_fail existiert nicht – starte App einmal, damit Schema erstellt wird.")
        return
    if not column_exists(conn, "geo_fail", "next_attempt"):
        print("[FIX] Spalte geo_fail.next_attempt fehlt – füge hinzu…")
        # INTEGER (Unix-Timestamp oder ISO-Epoch), NULL erlaubt
        conn.execute("ALTER TABLE geo_fail ADD COLUMN next_attempt INTEGER")
    else:
        print("[OK] Spalte geo_fail.next_attempt ist bereits vorhanden.")
    # Index anlegen (idempotent)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_geo_fail_next_attempt ON geo_fail(next_attempt)"
    )
    conn.commit()


def main():
    ap = argparse.ArgumentParser(description="Hotfix: geo_fail.next_attempt hinzufügen + index")
    ap.add_argument("--db", dest="db_path", default=None, help="Pfad zur SQLite-DB-Datei (optional)")
    args = ap.parse_args()

    db_path = resolve_db_path(args.db_path)
    if not os.path.exists(db_path):
        print(f"[ERROR] DB-Datei nicht gefunden: {db_path}")
        sys.exit(1)

    print(f"[INFO] Öffne DB: {db_path}")
    conn = sqlite3.connect(db_path)
    try:
        ensure_geo_fail_next_attempt(conn)
        # Verifikation
        ok = column_exists(conn, "geo_fail", "next_attempt")
        print("[OK] Verifikation:", "Spalte vorhanden" if ok else "FEHLT")
        sys.exit(0 if ok else 3)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
