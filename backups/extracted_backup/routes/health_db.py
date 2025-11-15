from fastapi import APIRouter
from fastapi.responses import JSONResponse
from db.core import db_health

router = APIRouter()

@router.get("/health/db")
def health_db():
    status = db_health()
    code = 200 if status.get("ok") else 503
    return JSONResponse(status, status_code=code, media_type="application/json; charset=utf-8")
