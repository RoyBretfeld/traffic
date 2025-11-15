"""
Alias-Repository für FAMO TrafficApp
Verwaltet Alias-Zuordnungen zwischen problematischen und kanonischen Adressen
"""
from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from typing import Iterable, Dict
from db.core import ENGINE
from common.normalize import normalize_address
from repositories.geo_repo import canon_addr

def set_alias(query: str, canonical: str, created_by: str | None = None):
    """
    Setzt einen Alias von query zu canonical.
    
    Args:
        query: Die problematische/abweichende Schreibweise
        canonical: Die kanonische Adresse (muss im geo_cache existieren)
        created_by: Optional Benutzer-Identifikation
    
    Raises:
        ValueError: Wenn canonical nicht im geo_cache existiert oder Alias ungültig ist
    """
    q = canon_addr(query)
    c = normalize_address(canonical)
    
    if not q or not c or q == c:
        raise ValueError("alias invalid: empty or identical")
    
    with ENGINE.begin() as conn:
        # Prüfe ob canonical im Cache existiert
        hit = conn.execute(
            text("SELECT 1 FROM geo_cache WHERE address_norm=:c"), 
            {"c": c}
        ).scalar()
        
        if not hit:
            raise ValueError("canonical not in geo_cache")
        
        # Alias setzen (UPSERT)
        conn.execute(text(
            "INSERT INTO geo_alias(address_norm, canonical_norm, created_by) VALUES (:q,:c,:u) "
            "ON CONFLICT(address_norm) DO UPDATE SET canonical_norm=:c, created_by=:u, created_at=CURRENT_TIMESTAMP"
        ), {"q": q, "c": c, "u": created_by})
        
        # Audit-Log
        conn.execute(text(
            "INSERT INTO geo_audit(action, query, canonical, by_user) VALUES ('alias_set', :q, :c, :u)"
        ), {"q": q, "c": c, "u": created_by})

def resolve_aliases(addresses: Iterable[str]) -> Dict[str, str]:
    """
    Löst Alias-Zuordnungen für eine Liste von Adressen auf.
    
    Args:
        addresses: Liste von Adressen
    
    Returns:
        Dict mapping: query_norm -> canonical_norm
    """
    keys = [canon_addr(a) for a in addresses if a]
    
    if not keys:
        return {}
    
    try:
        with ENGINE.begin() as conn:
            placeholders = ",".join([":addr" + str(i) for i in range(len(keys))])
            params = {f"addr{i}": key for i, key in enumerate(keys)}
            rows = conn.execute(text(
                f"SELECT address_norm, canonical_norm FROM geo_alias WHERE address_norm IN ({placeholders})"
            ), params).mappings().all()
    except OperationalError:
        return {}
    
    return {r["address_norm"]: r["canonical_norm"] for r in rows}

def remove_alias(query: str):
    """
    Entfernt einen Alias.
    
    Args:
        query: Die Adresse deren Alias entfernt werden soll
    """
    q = canon_addr(query)
    
    with ENGINE.begin() as conn:
        conn.execute(text("DELETE FROM geo_alias WHERE address_norm=:q"), {"q": q})
        conn.execute(text("INSERT INTO geo_audit(action, query) VALUES ('alias_remove', :q)"), {"q": q})

def get_alias_stats() -> Dict[str, int]:
    """
    Gibt Statistiken über die Alias-Tabelle zurück.
    
    Returns:
        Dict mit Anzahl der Aliasse und Audit-Einträge
    """
    with ENGINE.begin() as conn:
        alias_count = conn.execute(text("SELECT COUNT(*) FROM geo_alias")).scalar()
        audit_count = conn.execute(text("SELECT COUNT(*) FROM geo_audit")).scalar()
    
    return {
        "total_aliases": alias_count,
        "total_audit_entries": audit_count
    }
