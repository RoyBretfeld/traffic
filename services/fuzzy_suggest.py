"""
Fuzzy-Suggest Service für FAMO TrafficApp
Ermittelt ähnliche Adressen aus dem geo_cache für fehlende Adressen
"""
from __future__ import annotations
from typing import List, Tuple, Iterable, Dict, Any
from sqlalchemy import text
from db.core import ENGINE
from repositories.geo_repo import canon_addr

# Optional: RapidFuzz für bessere Performance, sonst Fallback auf difflib
try:
    from rapidfuzz import fuzz, process
    HAS_RAPIDFUZZ = True
    
    def _topn(query: str, choices: Iterable[str], n: int = 3) -> List[Tuple[str, float, Any]]:
        """Verwendet RapidFuzz für bessere Fuzzy-Search."""
        return process.extract(query, choices, scorer=fuzz.WRatio, limit=n)
        
except ImportError:
    HAS_RAPIDFUZZ = False
    import difflib
    
    def _topn(query: str, choices: Iterable[str], n: int = 3) -> List[Tuple[str, float, Any]]:
        """Fallback auf difflib für Fuzzy-Search."""
        seq = difflib.get_close_matches(query, choices, n=n, cutoff=0.0)
        return [(c, 100.0 * (1.0 - idx * 0.1), None) for idx, c in enumerate(seq)]

# Standard-Limit für bekannte Adressen
_DEF_LIMIT = 50000

def known_addresses(limit: int = _DEF_LIMIT) -> List[str]:
    """Holt alle bekannten Adressen aus dem geo_cache."""
    with ENGINE.begin() as c:
        rows = c.execute(
            text("SELECT address_norm FROM geo_cache LIMIT :lim"), 
            {"lim": limit}
        ).fetchall()
    return [r[0] for r in rows]

def suggest_for(
    missing: List[str], 
    *, 
    topk: int = 3, 
    threshold: int = 70, 
    pool: List[str] | None = None
) -> List[Dict[str, Any]]:
    """
    Ermittelt Vorschläge für fehlende Adressen basierend auf Ähnlichkeitssuche.
    
    Args:
        missing: Liste der fehlenden Adressen
        topk: Maximale Anzahl Vorschläge pro Adresse
        threshold: Mindest-Score für Vorschläge (0-100)
        pool: Optional vorgegebener Pool von Adressen (sonst aus DB)
    
    Returns:
        Liste von Dicts mit 'query' und 'suggestions'
    """
    if not missing:
        return []
    
    # Pool aus DB holen falls nicht vorgegeben
    if pool is None:
        pool = known_addresses()
    
    # Kanonische Normalisierung für besseres Matching
    pool_canon = {canon_addr(p): p for p in pool}  # map canon→original
    choices = list(pool_canon.keys())
    
    if not choices:
        return [{"query": m, "suggestions": []} for m in missing]
    
    results = []
    
    for missing_addr in missing:
        if not missing_addr or not missing_addr.strip():
            results.append({"query": missing_addr, "suggestions": []})
            continue
            
        # Kanonische Normalisierung der fehlenden Adresse
        query_canon = canon_addr(missing_addr)
        
        # Fuzzy-Search durchführen
        candidates = _topn(query_canon, choices, n=topk)
        
        suggestions = []
        for canon_name, score, _ in candidates:
            if score is None or score < threshold:
                continue
                
            suggestions.append({
                "address": pool_canon[canon_name],
                "score": float(score)
            })
        
        results.append({
            "query": missing_addr,
            "suggestions": suggestions
        })
    
    return results

def get_suggestions_stats() -> Dict[str, Any]:
    """Gibt Statistiken über den Fuzzy-Suggest Service zurück."""
    with ENGINE.begin() as c:
        total_count = c.execute(text("SELECT COUNT(*) FROM geo_cache")).scalar()
    
    return {
        "total_cached_addresses": total_count,
        "fuzzy_engine": "rapidfuzz" if HAS_RAPIDFUZZ else "difflib",
        "max_pool_size": _DEF_LIMIT
    }
