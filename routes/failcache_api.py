from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from db.core import ENGINE
from datetime import datetime, timezone

router = APIRouter()

@router.get("/api/geocode/fail-cache")
def fail_cache_list(limit: int = Query(100, ge=1, le=500), active_only: bool = True, reason: str | None = None, q: str | None = None):
    """Read-only Fail-Cache API für geo_fail Einträge"""
    sql = ["SELECT address_norm, reason, until, updated_at FROM geo_fail WHERE 1=1"]
    params = {}
    now = datetime.now(timezone.utc)
    
    if active_only:
        sql.append("AND (until IS NOT NULL AND until > :now)")
        params["now"] = now.strftime("%Y-%m-%d %H:%M:%S")
    
    if reason:
        sql.append("AND reason = :reason")
        params["reason"] = reason
    
    if q:
        sql.append("AND address_norm LIKE :q")
        params["q"] = f"%{q}%"
    
    sql.append("ORDER BY until DESC NULLS LAST, updated_at DESC LIMIT :lim")
    params["lim"] = limit
    
    with ENGINE.begin() as c:
        rows = c.execute(text("\n".join(sql)), params).mappings().all()
    
    items = []
    for r in rows:
        until = r.get("until")
        # Rest-TTL in Minuten berechnen (falls DB naive Zeiten liefert, nach UTC interpretieren)
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
            "until": str(until) if until is not None else None,
            "ttl_min": ttl_min,
            "updated_at": str(r.get("updated_at"))
        })
    
    return JSONResponse({
        "count": len(items), 
        "active_only": active_only, 
        "items": items
    }, media_type="application/json; charset=utf-8")
