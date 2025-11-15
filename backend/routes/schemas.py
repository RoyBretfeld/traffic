"""
Pydantic Schemas für Request-Validierung (Pydantic V2)
"""
from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import List, Optional, Literal


class StopModel(BaseModel):
    """Einzelner Stop in einer Tour"""
    model_config = ConfigDict(extra='ignore')  # Ignoriere zusätzliche Felder (z.B. street, postal_code, city)
    
    customer_number: Optional[str] = None
    name: Optional[str] = None
    address: Optional[str] = None
    lat: Optional[float] = Field(None, ge=-90, le=90)
    lon: Optional[float] = Field(None, ge=-180, le=180)
    bar_flag: Optional[bool] = False
    
    @field_validator('lat', 'lon')
    @classmethod
    def validate_coordinates(cls, v, info):
        if v is not None:
            field_name = info.field_name
            if field_name == 'lat' and not (-90 <= v <= 90):
                raise ValueError(f"Latitude muss zwischen -90 und 90 liegen, got {v}")
            if field_name == 'lon' and not (-180 <= v <= 180):
                raise ValueError(f"Longitude muss zwischen -180 und 180 liegen, got {v}")
        return v


class OptimizeTourRequest(BaseModel):
    """Request für Tour-Optimierung"""
    tour_id: str = Field(..., min_length=1, max_length=100)
    stops: List[StopModel] = Field(..., min_length=1, max_length=200)
    is_bar_tour: Optional[bool] = False
    profile: Literal["car", "bike", "foot"] = "car"
    strategy: Literal["mld", "ch"] = "mld"
    
    @field_validator('stops')
    @classmethod
    def validate_stops_have_coordinates(cls, v):
        """Validiere dass mindestens ein Stop Koordinaten hat"""
        valid_stops = [s for s in v if s.lat is not None and s.lon is not None]
        if len(valid_stops) == 0:
            raise ValueError("Mindestens ein Stop muss gültige Koordinaten (lat, lon) haben")
        return v

