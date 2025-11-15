from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from sqlalchemy import text
from db.core import ENGINE
from datetime import datetime

router = APIRouter()

@router.get("/api/audit/geo")
def audit_geo(limit: int = Query(50, ge=1, le=500), action: str | None = None, q: str | None = None, since: str | None = None):
    """Read-only Audit-Log API für geo_audit Einträge"""
    # SQL dynamisch, aber sicher via Bind-Parameter
    sql = ["SELECT id, ts, action, query, canonical, by_user FROM geo_audit WHERE 1=1"]
    params = {}
    
    if action:
        sql.append("AND action = :action")
        params["action"] = action
    
    if q:
        sql.append("AND (query LIKE :q OR canonical LIKE :q)")
        params["q"] = f"%{q}%"
    
    if since:
        # ISO 8601 erwartet; Fallback ignoriert Filter
        try:
            _ = datetime.fromisoformat(since.replace("Z","+00:00"))
            sql.append("AND ts >= :since")
            params["since"] = since
        except Exception:
            pass
    
    sql.append("ORDER BY ts DESC LIMIT :lim")
    params["lim"] = limit

    with ENGINE.begin() as c:
        rows = c.execute(text("\n".join(sql)), params).mappings().all()
    
    return JSONResponse({
        "count": len(rows),
        "items": [dict(r) for r in rows]
    }, media_type="application/json; charset=utf-8")
