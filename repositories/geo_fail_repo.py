from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Iterable, Set
from db.core import ENGINE
import unicodedata
import re

_DEF_TTL_MIN = 60  # 1h für temporäre Fehler
_DEF_TTL_NOHIT_MIN = 24 * 60  # 24h für "keine Treffer"

def _def_norm(s: str) -> str:
    """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung."""
    return re.sub(r"\s+", " ", unicodedata.normalize('NFC', s or '').strip())

def skip_set(addresses: Iterable[str]) -> Set[str]:
    """
    Gibt eine Menge von Adressen zurück, die aktuell im Fail-Cache stehen
    und noch nicht abgelaufen sind.
    """
    now = datetime.utcnow()
    try:
        with ENGINE.begin() as c:
            rows = c.execute(text(
                "SELECT address_norm FROM geo_fail WHERE until IS NOT NULL AND until > :now"
            ), {"now": now}).fetchall()
        return {r[0] for r in rows}
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Lesen des Fail-Cache: {e}")
        return set()

def mark_temp(address: str, minutes: int = _DEF_TTL_MIN, reason: str = "temp_error"):
    """
    Markiert eine Adresse als temporär fehlgeschlagen.
    TTL: Standard 1 Stunde für temporäre Fehler.
    """
    addr = _def_norm(address)
    try:
        with ENGINE.begin() as c:
            c.execute(text(
                "INSERT INTO geo_fail(address_norm, reason, until) VALUES (:a, :r, DATETIME('now', '+%d minutes')) "
                "ON CONFLICT(address_norm) DO UPDATE SET reason=:r, until=DATETIME('now', '+%d minutes'), updated_at=CURRENT_TIMESTAMP" % (minutes, minutes)
            ), {"a": addr, "r": reason})
        print(f"[FAIL-CACHE] Temporärer Fehler markiert: {addr} ({reason}, {minutes}min)")
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Markieren temporärer Fehler: {e}")

def mark_nohit(address: str, minutes: int = _DEF_TTL_NOHIT_MIN, reason: str = "no_result"):
    """
    Markiert eine Adresse als "keine Treffer".
    TTL: Standard 24 Stunden für No-Hit-Adressen.
    """
    addr = _def_norm(address)
    try:
        with ENGINE.begin() as c:
            c.execute(text(
                "INSERT INTO geo_fail(address_norm, reason, until) VALUES (:a, :r, DATETIME('now', '+%d minutes')) "
                "ON CONFLICT(address_norm) DO UPDATE SET reason=:r, until=DATETIME('now', '+%d minutes'), updated_at=CURRENT_TIMESTAMP" % (minutes, minutes)
            ), {"a": addr, "r": reason})
        print(f"[FAIL-CACHE] No-Hit markiert: {addr} ({reason}, {minutes}min)")
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Markieren von No-Hit: {e}")

def clear(address: str):
    """
    Entfernt eine Adresse aus dem Fail-Cache.
    Wird aufgerufen, wenn eine Adresse erfolgreich geokodiert wurde.
    """
    addr = _def_norm(address)
    try:
        with ENGINE.begin() as c:
            result = c.execute(text("DELETE FROM geo_fail WHERE address_norm=:a"), {"a": addr})
            if result.rowcount > 0:
                print(f"[FAIL-CACHE] Fail-Eintrag entfernt: {addr}")
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Löschen aus Fail-Cache: {e}")

def get_fail_stats():
    """
    Gibt Statistiken über den Fail-Cache zurück.
    """
    try:
        with ENGINE.begin() as c:
            total = c.execute(text("SELECT COUNT(*) FROM geo_fail")).fetchone()[0]
            active = c.execute(text(
                "SELECT COUNT(*) FROM geo_fail WHERE until IS NOT NULL AND until > CURRENT_TIMESTAMP"
            )).fetchone()[0]
            return {"total": total, "active": active}
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Abrufen der Fail-Cache-Statistiken: {e}")
        return {"total": 0, "active": 0}
