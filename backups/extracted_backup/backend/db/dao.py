from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from typing import Iterable, List, Optional

from .config import get_database_path


@dataclass
class Kunde:
    id: Optional[int]
    name: str
    adresse: str
    lat: Optional[float] = None
    lon: Optional[float] = None


def _connect() -> sqlite3.Connection:
    return sqlite3.connect(get_database_path())


def _ensure_geocache_columns(conn: sqlite3.Connection) -> None:
    cur = conn.execute("PRAGMA table_info(geocache)")
    columns = {row[1] for row in cur.fetchall()}
    if "provider" not in columns:
        conn.execute("ALTER TABLE geocache ADD COLUMN provider TEXT")
    if "updated_at" not in columns:
        conn.execute("ALTER TABLE geocache ADD COLUMN updated_at TEXT DEFAULT (datetime('now'))")
    conn.commit()


def get_db_session():
    """Gibt eine SQLite-Verbindung für den TourManager zurück."""
    return _connect()


def _normalize_string(s: str) -> str:
    """Normalisiert einen String für den Datenbankvergleich (Kleinschreibung, Leerzeichen).
    Entfernt führende/abschließende Leerzeichen und reduziert multiple interne Leerzeichen auf ein einziges.
    """
    if not s:
        return ""
    s = s.strip().lower()
    s = ' '.join(s.split())
    return s

def upsert_kunden(kunden: Iterable[Kunde]) -> List[int]:
    ids: List[int] = []
    with _connect() as conn:
        for k in kunden:
            k.name = _normalize_string(k.name)
            k.adresse = _normalize_string(k.adresse)
            # Versuche insert, bei Duplikat (unique name+adresse) vorhandene ID suchen
            try:
                cur = conn.execute(
                    "INSERT INTO kunden (name, adresse, lat, lon) VALUES (?, ?, ?, ?) ON CONFLICT(name, adresse) DO UPDATE SET lat=excluded.lat, lon=excluded.lon",
                    (k.name, k.adresse, k.lat, k.lon),
                )
                ids.append(int(cur.lastrowid))
            except sqlite3.IntegrityError:
                cur = conn.execute(
                    "SELECT id FROM kunden WHERE name = ? AND adresse = ?",
                    (k.name, k.adresse),
                )
                row = cur.fetchone()
                if row is not None:
                    ids.append(int(row[0]))
        conn.commit()
    return ids

def get_kunde_id_by_name_adresse(name: str, adresse: str) -> Optional[int]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT id FROM kunden WHERE name = ? COLLATE NOCASE AND adresse = ? COLLATE NOCASE",
            (_normalize_string(name), _normalize_string(adresse))
        )
        row = cur.fetchone()
        return row[0] if row else None

def get_kunde_by_id(kunde_id: int) -> Optional[Kunde]:
    with _connect() as conn:
        cur = conn.execute("SELECT id, name, adresse, lat, lon FROM kunden WHERE id = ?", (kunde_id,))
        row = cur.fetchone()
        if row:
            return Kunde(id=row[0], name=row[1], adresse=row[2], lat=row[3], lon=row[4])
        return None

def get_customers_by_ids(customer_ids: List[int]) -> List[Kunde]:
    if not customer_ids:
        return []
    placeholders = ",".join(["?"] * len(customer_ids))
    with _connect() as conn:
        cur = conn.execute(
            f"SELECT id, name, adresse, lat, lon FROM kunden WHERE id IN ({placeholders})",
            tuple(customer_ids)
        )
        return [Kunde(id=row[0], name=row[1], adresse=row[2], lat=row[3], lon=row[4]) for row in cur.fetchall()]

def insert_tour(
    tour_id: str,
    datum: str,
    kunden_ids: Iterable[int],
    dauer_min: Optional[int] = None,
    distanz_km: Optional[float] = None,
    fahrer: Optional[str] = None,
) -> int:
    kunden_ids_json = json.dumps(list(kunden_ids))
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO touren (tour_id, datum, kunden_ids, dauer_min, distanz_km, fahrer) VALUES (?, ?, ?, ?, ?, ?)",
            (tour_id, datum, kunden_ids_json, dauer_min, distanz_km, fahrer),
        )
        conn.commit()
        return int(cur.lastrowid)


def geocache_get(adresse: str) -> Optional[tuple[float, float, Optional[str]]]:
    with _connect() as conn:
        _ensure_geocache_columns(conn)
        cur = conn.execute(
            "SELECT lat, lon, provider FROM geocache WHERE adresse = ?", (adresse,)
        )
        row = cur.fetchone()
        if row and row[0] is not None and row[1] is not None:
            return float(row[0]), float(row[1]), row[2]
        return None


def geocache_set(adresse: str, lat: float, lon: float, provider: Optional[str]) -> None:
    with _connect() as conn:
        _ensure_geocache_columns(conn)
        conn.execute(
            """
            INSERT INTO geocache (adresse, lat, lon, provider)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(adresse) DO UPDATE
            SET lat=excluded.lat,
                lon=excluded.lon,
                provider=excluded.provider,
                updated_at=datetime('now')
            """,
            (adresse, lat, lon, provider),
        )
        conn.commit()


def postal_cache_get(postal_code: str) -> Optional[str]:
    with _connect() as conn:
        cur = conn.execute(
            "SELECT city FROM postal_code_cache WHERE postal_code = ?", (postal_code,)
        )
        row = cur.fetchone()
        if row: # row[0] sollte der City-String sein
            return row[0]
        return None

def postal_cache_set(postal_code: str, city: str) -> None:
    with _connect() as conn:
        conn.execute(
            "INSERT INTO postal_code_cache (postal_code, city) VALUES (?, ?) ON CONFLICT(postal_code) DO UPDATE SET city=excluded.city, updated_at=datetime('now')",
            (postal_code, city),
        )
        conn.commit()