from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from db.core import ENGINE
from services.osrm_client import OSRMClient

router = APIRouter()  # Kein prefix - Endpoints werden direkt registriert

@router.get("/live")
def health_live():
    return {"status": "ok"}

@router.get("/osrm")
async def health_osrm_endpoint():
    osrm_client = OSRMClient()
    health_status = osrm_client.check_health()
    return health_status
