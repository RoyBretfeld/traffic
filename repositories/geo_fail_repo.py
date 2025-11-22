from sqlalchemy import text
from datetime import datetime, timedelta
from typing import Iterable, Set
from db.core import ENGINE
import db.schema_fail as schema_fail_module
from importlib import reload as _reload_fail_schema
import unicodedata
import re

# WICHTIG: Fail-Cache ist jetzt nur noch für sehr kurzfristiges Rate-Limiting
# Adressen werden NICHT permanent gespeichert, sondern immer wieder versucht
# Ziel: 100% Abdeckung durch wiederholtes Versuchen
# TTL: Sehr kurz (5-10 Min), damit Adressen schnell wieder versucht werden
_DEF_TTL_MIN = 5  # 5 Minuten für temporäre Fehler (Rate-Limiting)
_DEF_TTL_NOHIT_MIN = 10  # 10 Minuten für "keine Treffer" (Rate-Limiting)

_SCHEMA_READY = False


def _ensure_schema():
    global _SCHEMA_READY
    if not _SCHEMA_READY:
        try:
            _reload_fail_schema(schema_fail_module)
            schema_fail_module.ensure_fail_schema()
            _SCHEMA_READY = True
        except Exception as exc:
            print(f"[FAIL-CACHE-ERROR] Schema konnte nicht erstellt werden: {exc}")


def _def_norm(s: str) -> str:
    """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung."""
    return re.sub(r"\s+", " ", unicodedata.normalize('NFC', s or '').strip())

def skip_set(addresses: Iterable[str]) -> Set[str]:
    """
    Gibt eine Menge von Adressen zurück, die aktuell im Fail-Cache stehen
    und noch nicht abgelaufen sind.
    
    WICHTIG: Dieser Cache ist nur für kurzfristiges Rate-Limiting (5-10 Min).
    Adressen werden NICHT permanent blockiert, sondern immer wieder versucht.
    Ziel: 100% Abdeckung durch wiederholtes Versuchen.
    
    Bei Verbesserungen der Erkennungsroutine sollten alle Einträge gelöscht werden,
    damit verbesserte Routinen auch auf bisher fehlgeschlagene Adressen angewendet werden.
    """
    _ensure_schema()
    now = datetime.utcnow()
    try:
        with ENGINE.begin() as c:
            # Nur sehr aktuelle Einträge (letzte 10 Minuten) berücksichtigen
            rows = c.execute(text(
                "SELECT address_norm FROM geo_fail WHERE until IS NOT NULL AND until > :now"
            ), {"now": now}).fetchall()
        skipped = {r[0] for r in rows}
        if skipped:
            print(f"[FAIL-CACHE] {len(skipped)} Adressen temporär übersprungen (Rate-Limiting, max 10 Min)")
        return skipped
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Lesen des Fail-Cache: {e}")
        return set()

def mark_temp(address: str, minutes: int = _DEF_TTL_MIN, reason: str = "temp_error"):
    """
    Markiert eine Adresse als temporär fehlgeschlagen (Rate-Limiting).
    TTL: Standard 5 Minuten für temporäre Fehler.
    WICHTIG: Adressen werden NICHT permanent blockiert, nur kurzzeitig für Rate-Limiting.
    Nach Ablauf werden sie automatisch wieder versucht.
    """
    addr = _def_norm(address)
    _ensure_schema()
    try:
        with ENGINE.begin() as c:
            c.execute(text(
                "INSERT INTO geo_fail(address_norm, reason, until) VALUES (:a, :r, DATETIME('now', '+%d minutes')) "
                "ON CONFLICT(address_norm) DO UPDATE SET reason=:r, until=DATETIME('now', '+%d minutes'), updated_at=CURRENT_TIMESTAMP" % (minutes, minutes)
            ), {"a": addr, "r": reason})
        print(f"[FAIL-CACHE] Temporärer Fehler markiert: {addr} ({reason}, {minutes}min TTL)")
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Markieren temporärer Fehler: {e}")

def mark_nohit(address: str, minutes: int = _DEF_TTL_NOHIT_MIN, reason: str = "no_result"):
    """
    Markiert eine Adresse als "keine Treffer" (Rate-Limiting).
    TTL: Standard 10 Minuten für No-Hit-Adressen.
    WICHTIG: Adressen werden NICHT permanent blockiert, nur kurzzeitig für Rate-Limiting.
    Nach Ablauf werden sie automatisch wieder versucht.
    Bei Verbesserungen der Erkennungsroutine sollten diese Einträge gelöscht werden.
    """
    addr = _def_norm(address)
    _ensure_schema()
    try:
        with ENGINE.begin() as c:
            c.execute(text(
                "INSERT INTO geo_fail(address_norm, reason, until) VALUES (:a, :r, DATETIME('now', '+%d minutes')) "
                "ON CONFLICT(address_norm) DO UPDATE SET reason=:r, until=DATETIME('now', '+%d minutes'), updated_at=CURRENT_TIMESTAMP" % (minutes, minutes)
            ), {"a": addr, "r": reason})
        print(f"[FAIL-CACHE] No-Hit markiert: {addr} ({reason}, {minutes}min TTL - wird erneut versucht)")
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Markieren von No-Hit: {e}")

def clear(address: str):
    """
    Entfernt eine Adresse aus dem Fail-Cache.
    Wird aufgerufen, wenn eine Adresse erfolgreich geokodiert wurde.
    """
    addr = _def_norm(address)
    _ensure_schema()
    try:
        with ENGINE.begin() as c:
            result = c.execute(text("DELETE FROM geo_fail WHERE address_norm=:a"), {"a": addr})
            if result.rowcount > 0:
                print(f"[FAIL-CACHE] Fail-Eintrag entfernt (Erfolg): {addr}")
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Löschen aus Fail-Cache: {e}")

def clear_all():
    """
    Löscht ALLE Einträge aus dem Fail-Cache.
    
    Verwendung: Wenn die Erkennungsroutine überarbeitet/verbessert wurde,
    sollte dieser Cache geleert werden, damit alle Adressen erneut versucht werden.
    Ziel: 100% Abdeckung durch wiederholtes Versuchen mit verbesserten Routinen.
    """
    _ensure_schema()
    try:
        with ENGINE.begin() as c:
            result = c.execute(text("DELETE FROM geo_fail"))
            count = result.rowcount
            print(f"[FAIL-CACHE] ALLE Einträge gelöscht ({count}) - alle Adressen werden erneut versucht")
            return count
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Löschen aller Einträge: {e}")
        return 0

def get_fail_stats():
    """
    Gibt Statistiken über den Fail-Cache zurück.
    """
    _ensure_schema()
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

def get_fail_status(address: str):
    """
    Prüft ob eine Adresse im Fail-Cache steht und gibt Details zurück.
    """
    addr = _def_norm(address)
    _ensure_schema()
    try:
        with ENGINE.begin() as c:
            row = c.execute(text(
                "SELECT address_norm, reason, until FROM geo_fail WHERE address_norm=:a AND until > CURRENT_TIMESTAMP"
            ), {"a": addr}).mappings().first()
            return dict(row) if row else None
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Prüfen des Fail-Status: {e}")
        return None

def get_fail_reasons():
    """
    Gibt eine Gruppierung der Fail-Cache-Einträge nach Grund zurück.
    """
    _ensure_schema()
    try:
        with ENGINE.begin() as c:
            rows = c.execute(text(
                "SELECT reason, COUNT(*) as count FROM geo_fail WHERE until > CURRENT_TIMESTAMP GROUP BY reason"
            )).mappings().all()
            return {row["reason"]: row["count"] for row in rows}
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Abrufen der Fail-Gründe: {e}")
        return {}

def cleanup_expired():
    """
    Bereinigt abgelaufene Einträge aus dem Fail-Cache.
    Diese Funktion wird automatisch aufgerufen, damit abgelaufene Adressen wieder versucht werden.
    
    WICHTIG: Verwendet next_attempt (INTEGER = Unix-Timestamp) statt until (TIMESTAMP).
    """
    _ensure_schema()
    try:
        import time
        current_timestamp = int(time.time())
        
        with ENGINE.begin() as c:
            # Prüfe ob Spalte next_attempt existiert
            from db.schema import column_exists
            if column_exists(c, "geo_fail", "next_attempt"):
                # Verwende next_attempt (INTEGER = Unix-Timestamp)
                result = c.execute(text("DELETE FROM geo_fail WHERE next_attempt IS NOT NULL AND next_attempt <= :now"), {"now": current_timestamp})
            else:
                # Fallback: Versuche until (falls vorhanden)
                try:
                    result = c.execute(text("DELETE FROM geo_fail WHERE until IS NOT NULL AND until <= CURRENT_TIMESTAMP"))
                except Exception:
                    # Weder next_attempt noch until vorhanden - nichts zu bereinigen
                    return 0
            
            count = result.rowcount
            if count > 0:
                print(f"[FAIL-CACHE] {count} abgelaufene Einträge bereinigt - werden erneut versucht")
            return count
    except Exception as e:
        print(f"[FAIL-CACHE-ERROR] Fehler beim Bereinigen des Fail-Cache: {e}")
        return 0
