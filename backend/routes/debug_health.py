# backend/routes/debug_health.py
from fastapi import APIRouter, Request
from pydantic import BaseModel
import httpx

router = APIRouter(prefix="", tags=["_debug"])  # kein extra Prefix, Endpoints sind absolut

@router.get("/_debug/routes")
async def list_routes(request: Request):
    routes = []
    for r in request.app.router.routes:
        try:
            routes.append({"path": r.path, "name": getattr(r, "name", None), "methods": list(r.methods or [])})
        except Exception:
            pass
    routes.sort(key=lambda x: x["path"])  # stabil
    return {"count": len(routes), "routes": routes}

@router.get("/health/live")
async def health_live():
    return {"ok": True}

class OsrmHealth(BaseModel):
    base_url: str
    timeout_ms: int = 1000

@router.get("/health/osrm")
async def health_osrm(base_url: str, timeout_ms: int = 1000):
    # Minimal-Route (keine Geometrie), damit OSRM schnell antwortet
    test = f"{base_url.rstrip('/')}/route/v1/driving/13.7373,51.0504;13.7283,51.0615?overview=false&alternatives=false&steps=false"
    try:
        async with httpx.AsyncClient(timeout=timeout_ms/1000) as client:
            r = await client.get(test)
            data = r.json()
        ok = (r.status_code == 200) and (data.get("code") == "Ok")
        return {"ok": ok, "status": r.status_code, "osrm_code": data.get("code"), "url": test}
    except Exception as e:
        return {"ok": False, "error": str(e), "url": test}
