"""
HT-02: Pydantic-Validation schärfen.
Standardisierte Validierungs-Models mit Limits für Stops, Dateigröße, Status-Enum, Koordinatenbereich, ISO-Datetime.
"""
from pydantic import BaseModel, Field, validator
from typing import List, Optional
from datetime import datetime
from enum import Enum


class TourStatus(str, Enum):
    """Standardisierte Tour-Status (HT-02)."""
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABORTED = "aborted"
    CANCELLED = "cancelled"


class CoordinateModel(BaseModel):
    """Koordinaten-Model mit Validierung (HT-02)."""
    lat: float = Field(..., ge=-90.0, le=90.0, description="Breitengrad (-90 bis 90)")
    lon: float = Field(..., ge=-180.0, le=180.0, description="Längengrad (-180 bis 180)")

    @validator('lat', 'lon')
    def validate_coordinates(cls, v):
        """Zusätzliche Validierung für Koordinaten."""
        if not isinstance(v, (int, float)):
            raise ValueError("Koordinaten müssen Zahlen sein")
        return float(v)


class StopModel(BaseModel):
    """Stop-Model mit Validierung (HT-02)."""
    customer_id: Optional[str] = None
    address: str = Field(..., min_length=1, max_length=500)
    lat: float = Field(..., ge=-90.0, le=90.0)
    lon: float = Field(..., ge=-180.0, le=180.0)
    sequence: int = Field(..., ge=0, le=1000)
    planned_time_window_start: Optional[datetime] = None
    planned_time_window_end: Optional[datetime] = None


class TourRequest(BaseModel):
    """Tour-Request mit scharfer Validierung (HT-02)."""
    tour_id: str = Field(..., min_length=1, max_length=100)
    date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$', description="Datum im Format YYYY-MM-DD")
    stops: List[StopModel] = Field(..., min_items=1, max_items=100, description="1-100 Stops pro Tour")
    status: TourStatus = Field(default=TourStatus.PLANNED)
    driver_id: Optional[str] = Field(None, max_length=100)
    region: Optional[str] = Field(None, max_length=50)

    @validator('date')
    def validate_date_format(cls, v):
        """Validiert ISO-Datetime-Format."""
        try:
            datetime.strptime(v, '%Y-%m-%d')
        except ValueError:
            raise ValueError("Datum muss im Format YYYY-MM-DD sein")
        return v


class ImportRequest(BaseModel):
    """Import-Request mit Validierung (HT-02)."""
    filename: str = Field(..., min_length=1, max_length=255, regex=r'^[A-Za-z0-9_.\-]+$')
    max_size_bytes: int = Field(50 * 1024 * 1024, ge=1, le=100 * 1024 * 1024, description="Max. 100 MB")
    encoding: Optional[str] = Field("utf-8", regex=r'^(utf-8|cp850|latin-1)$')


class GeocodeRequest(BaseModel):
    """Geocode-Request mit Validierung (HT-02)."""
    address: str = Field(..., min_length=1, max_length=500)
    customer_id: Optional[str] = Field(None, max_length=100)
    retry_count: int = Field(0, ge=0, le=5, description="Max. 5 Retries")


class RouteRequest(BaseModel):
    """Route-Request mit Validierung (HT-02)."""
    coordinates: List[CoordinateModel] = Field(..., min_items=2, max_items=1000, description="2-1000 Koordinaten")
    profile: str = Field("driving", regex=r'^(driving|walking|cycling)$')
    optimize: bool = Field(False)


class StatsRequest(BaseModel):
    """Stats-Request mit Validierung (HT-02)."""
    start_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    end_date: str = Field(..., regex=r'^\d{4}-\d{2}-\d{2}$')
    region: Optional[str] = Field(None, max_length=50)

    @validator('end_date')
    def validate_date_range(cls, v, values):
        """Validiert dass end_date >= start_date."""
        if 'start_date' in values:
            start = datetime.strptime(values['start_date'], '%Y-%m-%d')
            end = datetime.strptime(v, '%Y-%m-%d')
            if end < start:
                raise ValueError("end_date muss >= start_date sein")
        return v

