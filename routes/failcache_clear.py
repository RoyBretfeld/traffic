from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from sqlalchemy import text
from db.core import ENGINE

router = APIRouter()

class ClearBody(BaseModel):
    addresses: list[str] = Field(..., min_length=1, description="address_norm Werte, wie in geo_fail gespeichert")

@router.post("/api/geocode/fail-cache/clear")
def fail_cache_clear(body: ClearBody):
    """Gezieltes Leeren einzelner Einträge aus dem Fail-Cache"""
    addrs = [a.strip() for a in body.addresses if a and a.strip()]
    if not addrs:
        raise HTTPException(status_code=400, detail="no addresses")
    
    # Sichere SQL-Abfrage mit Bind-Parametern
    qmarks = ",".join([":a%d"%i for i,_ in enumerate(addrs)])
    params = {f"a{i}": v for i,v in enumerate(addrs)}
    
    with ENGINE.begin() as c:
        n = c.execute(text(f"DELETE FROM geo_fail WHERE address_norm IN ({qmarks})"), params).rowcount
    
    return JSONResponse({
        "ok": True, 
        "cleared": int(n)
    }, media_type="application/json; charset=utf-8")
