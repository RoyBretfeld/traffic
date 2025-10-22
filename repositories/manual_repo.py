# repositories/manual_repo.py
from __future__ import annotations
from typing import List, Dict
from sqlalchemy import text
from db.core import ENGINE
from common.normalize import normalize_address

def add_open(raw_addr: str, reason: str) -> None:
    """
    Fügt eine fehlgeschlagene Adresse zur Manual-Queue hinzu.
    
    Args:
        raw_addr: Ursprüngliche Adresse (vor Normalisierung)
        reason: Grund für das Scheitern (z.B. "geocode_miss", "invalid_address")
    """
    key = normalize_address(raw_addr)
    with ENGINE.begin() as c:
        c.execute(text(
            """
            INSERT INTO manual_queue(address_norm, raw_address, reason)
            VALUES (:k, :raw, :r)
            """
        ), {"k": key, "raw": raw_addr, "r": reason})

def list_open(limit: int = 500) -> List[Dict]:
    """
    Listet alle offenen Manual-Queue Einträge auf.
    
    Args:
        limit: Maximale Anzahl der zurückzugebenden Einträge
        
    Returns:
        Liste von Dictionaries mit Manual-Queue Einträgen
    """
    with ENGINE.begin() as c:
        rows = c.execute(text(
            "SELECT id, address_norm, raw_address, reason, created_at FROM manual_queue ORDER BY created_at DESC LIMIT :n"
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
    import csv
    items = list_open(100000)  # Alle Einträge exportieren
    
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["id","address_norm","raw_address","reason","created_at"])
        w.writeheader()
        w.writerows(items)
    
    return len(items)

def clear_queue() -> int:
    """
    Leert die gesamte Manual-Queue.
    
    Returns:
        Anzahl der gelöschten Einträge
    """
    with ENGINE.begin() as c:
        result = c.execute(text("DELETE FROM manual_queue"))
        return result.rowcount

def get_stats() -> Dict:
    """
    Liefert Statistiken über die Manual-Queue.
    
    Returns:
        Dict mit Statistiken
    """
    with ENGINE.begin() as c:
        total = c.execute(text("SELECT COUNT(*) FROM manual_queue")).scalar_one()
        by_reason = c.execute(text(
            "SELECT reason, COUNT(*) FROM manual_queue GROUP BY reason"
        )).fetchall()
    
    return {
        "total": total,
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
    with ENGINE.begin() as c:
        result = c.execute(text(
            "DELETE FROM manual_queue WHERE address_norm = :addr"
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
    with ENGINE.begin() as c:
        result = c.execute(text(
            "SELECT 1 FROM manual_queue WHERE address_norm = :addr LIMIT 1"
        ), {"addr": address_norm}).fetchone()
        return result is not None