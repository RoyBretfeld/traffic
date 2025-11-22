from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from db.core import ENGINE
from datetime import datetime, timezone

router = APIRouter()

@router.get("/api/geocode/fail-cache")
def fail_cache_list(limit: int = Query(100, ge=1, le=500), active_only: bool = True, reason: str | None = None, q: str | None = None):
    """
    Read-only Fail-Cache API für geo_fail Einträge.
    
    WICHTIG: Verwendet next_attempt (INTEGER = Unix-Timestamp) statt until (TIMESTAMP).
    """
    from db.schema import column_exists
    import time
    
    # Prüfe welche Spalte vorhanden ist
    with ENGINE.begin() as c:
        has_next_attempt = column_exists(c, "geo_fail", "next_attempt")
        has_until = column_exists(c, "geo_fail", "until")
    
    # Baue SQL basierend auf vorhandenen Spalten
    if has_next_attempt:
        # Verwende next_attempt (INTEGER = Unix-Timestamp)
        sql = ["SELECT address_norm, reason, next_attempt, updated_at FROM geo_fail WHERE 1=1"]
        params = {}
        current_timestamp = int(time.time())
        
        if active_only:
            sql.append("AND (next_attempt IS NOT NULL AND next_attempt > :now)")
            params["now"] = current_timestamp
    elif has_until:
        # Fallback: Verwende until (TIMESTAMP)
        sql = ["SELECT address_norm, reason, until, updated_at FROM geo_fail WHERE 1=1"]
        params = {}
        now = datetime.now(timezone.utc)
        
        if active_only:
            sql.append("AND (until IS NOT NULL AND until > :now)")
            params["now"] = now.strftime("%Y-%m-%d %H:%M:%S")
    else:
        # Keine Zeit-Spalte vorhanden - zeige alle Einträge
        sql = ["SELECT address_norm, reason, updated_at FROM geo_fail WHERE 1=1"]
        params = {}
    
    if reason:
        sql.append("AND reason = :reason")
        params["reason"] = reason
    
    if q:
        sql.append("AND address_norm LIKE :q")
        params["q"] = f"%{q}%"
    
    # ORDER BY anpassen
    if has_next_attempt:
        sql.append("ORDER BY next_attempt DESC NULLS LAST, updated_at DESC LIMIT :lim")
    elif has_until:
        sql.append("ORDER BY until DESC NULLS LAST, updated_at DESC LIMIT :lim")
    else:
        sql.append("ORDER BY updated_at DESC LIMIT :lim")
    
    params["lim"] = limit
    
    with ENGINE.begin() as c:
        rows = c.execute(text("\n".join(sql)), params).mappings().all()
    
    items = []
    now = datetime.now(timezone.utc)
    for r in rows:
        # TTL berechnen basierend auf vorhandener Spalte
        ttl_min = None
        until_value = None
        
        if has_next_attempt:
            next_attempt = r.get("next_attempt")
            if next_attempt:
                until_value = datetime.fromtimestamp(next_attempt, tz=timezone.utc).isoformat()
                current_timestamp = int(time.time())
                ttl_min = max(0, (next_attempt - current_timestamp) // 60)
        elif has_until:
            until = r.get("until")
            until_value = str(until) if until is not None else None
            try:
                dt = until if isinstance(until, datetime) else datetime.fromisoformat(str(until).replace("Z","+00:00"))
                if dt.tzinfo is None: 
                    dt = dt.replace(tzinfo=timezone.utc)
                ttl_min = max(0, int((dt - now).total_seconds()//60))
            except Exception:
                ttl_min = None
        
        items.append({
            "address": r["address_norm"],
            "reason": r.get("reason"),
            "until": until_value,
            "ttl_min": ttl_min,
            "updated_at": str(r.get("updated_at"))
        })
    
    return JSONResponse({
        "count": len(items), 
        "active_only": active_only, 
        "items": items
    }, media_type="application/json; charset=utf-8")
