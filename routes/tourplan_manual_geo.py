from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from repositories.geo_repo import upsert
from typing import Optional

router = APIRouter()

class ManualGeoBody(BaseModel):
    address: str = Field(..., min_length=3, description="Vollständige Adresse")
    latitude: float = Field(..., ge=-90, le=90, description="Breitengrad (-90 bis 90)")
    longitude: float = Field(..., ge=-180, le=180, description="Längengrad (-180 bis 180)")
    by_user: Optional[str] = Field(None, description="Benutzer der die Koordinaten eingibt")

@router.post("/api/tourplan/manual-geo", tags=["manual"], summary="Koordinaten manuell eingeben")
def api_manual_geo(body: ManualGeoBody):
    """Speichert manuelle Koordinaten für eine Adresse in geo_cache."""
    try:
        # Validierung der Koordinaten
        if not (-90 <= body.latitude <= 90):
            raise ValueError("Breitengrad muss zwischen -90 und 90 liegen")
        if not (-180 <= body.longitude <= 180):
            raise ValueError("Längengrad muss zwischen -180 und 180 liegen")
        
        # Speichern in geo_cache mit source="manual"
        upsert(
            address=body.address,
            lat=body.latitude,
            lon=body.longitude,
            source="manual",
            by_user=body.by_user
        )
        
        return JSONResponse({
            "ok": True,
            "message": f"Koordinaten für '{body.address}' gespeichert",
            "coordinates": {
                "lat": body.latitude,
                "lon": body.longitude
            }
        }, media_type="application/json; charset=utf-8")
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der Koordinaten: {str(e)}")
