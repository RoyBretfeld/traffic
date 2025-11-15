# repositories/manual_repo.py
from __future__ import annotations
from typing import List, Dict
from sqlalchemy import text
from db.core import ENGINE
from common.normalize import normalize_address
import db.schema as schema_module
from importlib import reload as _reload_schema

_SCHEMA_READY = False


def _ensure_schema() -> None:
    global _SCHEMA_READY
    if not _SCHEMA_READY:
        _reload_schema(schema_module)
        schema_module.ensure_schema()
        _SCHEMA_READY = True

def add_open(raw_addr: str, reason: str, note: str = "", dedup: bool = True) -> None:
    """
    Fügt eine fehlgeschlagene Adresse zur Manual-Queue hinzu.
    
    Args:
        raw_addr: Ursprüngliche Adresse (vor Normalisierung)
        reason: Grund für das Scheitern (z.B. "geocode_miss", "invalid_address")
        note: Freitext-Notiz
        dedup: Wenn True, vorhandene Einträge werden vor dem Insert entfernt
    """
    key = normalize_address(raw_addr)
    _ensure_schema()
    with ENGINE.begin() as c:
        if dedup:
            c.execute(text("DELETE FROM manual_queue WHERE address_norm = :k"), {"k": key})
        c.execute(text(
            """
            INSERT INTO manual_queue(address_norm, raw_address, reason, note, status)
            VALUES (:k, :raw, :r, :n, 'open')
            """
        ), {"k": key, "raw": raw_addr, "r": reason, "n": note})

def list_open(limit: int = 500) -> List[Dict]:
    """
    Listet alle offenen Manual-Queue Einträge auf.
    
    Args:
        limit: Maximale Anzahl der zurückzugebenden Einträge
        
    Returns:
        Liste von Dictionaries mit Manual-Queue Einträgen
    """
    _ensure_schema()
    with ENGINE.begin() as c:
        rows = c.execute(text(
            "SELECT id, address_norm, raw_address, reason, note, status, created_at FROM manual_queue "
            "WHERE status='open' ORDER BY created_at DESC LIMIT :n"
        ), {"n": limit}).mappings().all()
    return [dict(r) for r in rows]

def export_csv(path: str) -> int:
    """
    Exportiert alle Manual-Queue Einträge als CSV-Datei.
    
    Args:
        path: Pfad zur CSV-Datei
        
    Returns:
        Anzahl der exportierten Einträge
    """
    _ensure_schema()
    import csv
    items = list_open(100000)  # Alle Einträge exportieren
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","address_norm","raw_address","reason","note","status","created_at"])
        w.writeheader()
        w.writerows(items)
    
    return len(items)

def clear_queue() -> int:
    """
    Leert die gesamte Manual-Queue.
    
    Returns:
        Anzahl der gelöschten Einträge
    """
    _ensure_schema()
    with ENGINE.begin() as c:
        result = c.execute(text("DELETE FROM manual_queue"))
        return result.rowcount

def get_stats() -> Dict:
    """
    Liefert Statistiken über die Manual-Queue.
    
    Returns:
        Dict mit Statistiken
    """
    _ensure_schema()
    with ENGINE.begin() as c:
        total = c.execute(text("SELECT COUNT(*) FROM manual_queue")).scalar_one()
        by_reason = c.execute(text(
            "SELECT reason, COUNT(*) FROM manual_queue GROUP BY reason"
        )).fetchall()
        by_status = c.execute(text(
            "SELECT status, COUNT(*) FROM manual_queue GROUP BY status"
        )).fetchall()

    status_map = {row[0]: row[1] for row in by_status}

    return {
        "total": total,
        "open": status_map.get('open', 0),
        "closed": status_map.get('closed', 0),
        "by_reason": {row[0]: row[1] for row in by_reason}
    }

def close(address_norm: str) -> bool:
    """
    Entfernt einen Eintrag aus der Manual-Queue.
    
    Args:
        address_norm: Normalisierte Adresse
        
    Returns:
        True wenn Eintrag gefunden und entfernt wurde
    """
    _ensure_schema()
    with ENGINE.begin() as c:
        result = c.execute(text(
            "UPDATE manual_queue SET status='closed' WHERE address_norm = :addr"
        ), {"addr": address_norm})
        return result.rowcount > 0

def is_open(address_norm: str) -> bool:
    """
    Prüft ob eine Adresse bereits in der Manual-Queue ist.
    
    Args:
        address_norm: Normalisierte Adresse
        
    Returns:
        True wenn Adresse in Manual-Queue ist
    """
    _ensure_schema()
    with ENGINE.begin() as c:
        result = c.execute(text(
            "SELECT 1 FROM manual_queue WHERE address_norm = :addr AND status='open' LIMIT 1"
        ), {"addr": address_norm}).fetchone()
        return result is not None