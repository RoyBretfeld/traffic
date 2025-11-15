"""
Pydantic-Modelle für Systemregeln.
Zentrale Definition der Datenstruktur und Validierung.
"""
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Literal


class SystemRules(BaseModel):
    """Model für Systemregeln mit vollständiger Validierung."""
    
    time_budget_without_return: int = Field(
        ge=1, 
        le=120, 
        description="Zeitbudget ohne Rückfahrt (Minuten)"
    )
    time_budget_with_return: int = Field(
        ge=1, 
        le=180, 
        description="Zeitbudget mit Rückfahrt (Minuten)"
    )
    service_time_per_stop: float = Field(
        ge=0.5, 
        le=10.0, 
        description="Service-Zeit pro Stop (Minuten)"
    )
    speed_kmh: float = Field(
        ge=10.0, 
        le=100.0, 
        description="Durchschnittsgeschwindigkeit (km/h)"
    )
    safety_factor: float = Field(
        ge=1.0, 
        le=2.0, 
        description="Sicherheitsfaktor für Stadtverkehr"
    )
    depot_lat: float = Field(
        ge=-90.0, 
        le=90.0, 
        description="Depot-Latitude"
    )
    depot_lon: float = Field(
        ge=-180.0, 
        le=180.0, 
        description="Depot-Longitude"
    )
    rules_version: str = Field(
        default="1.0",
        description="Version der Systemregeln"
    )
    
    # Metadaten (nicht persistiert, nur für Debug/Admin)
    source: Literal["file", "env", "default"] = Field(
        default="default",
        description="Quelle der Systemregeln (nur für Debug)"
    )
    
    @field_validator('service_time_per_stop')
    @classmethod
    def validate_service_time(cls, v: float) -> float:
        """Service-Zeit muss positiv sein."""
        if v <= 0:
            raise ValueError("Service-Zeit pro Stop muss größer als 0 sein")
        return v
    
    @field_validator('speed_kmh')
    @classmethod
    def validate_speed(cls, v: float) -> float:
        """Geschwindigkeit muss positiv sein."""
        if v <= 0:
            raise ValueError("Durchschnittsgeschwindigkeit muss größer als 0 sein")
        return v
    
    @field_validator('safety_factor')
    @classmethod
    def validate_safety_factor(cls, v: float) -> float:
        """Sicherheitsfaktor muss >= 1.0 sein."""
        if v < 1.0:
            raise ValueError("Sicherheitsfaktor muss mindestens 1.0 sein")
        return v
    
    @model_validator(mode='after')
    def validate_time_budgets(self) -> 'SystemRules':
        """Zeitbudget ohne Rückfahrt darf nicht größer sein als mit Rückfahrt."""
        if self.time_budget_without_return > self.time_budget_with_return:
            raise ValueError(
                f"Zeitbudget ohne Rückfahrt ({self.time_budget_without_return} Min) "
                f"darf nicht größer sein als Zeitbudget mit Rückfahrt ({self.time_budget_with_return} Min)"
            )
        return self


class SystemRulesUpdate(BaseModel):
    """Model für Systemregeln-Updates (ohne Metadaten)."""
    
    time_budget_without_return: int = Field(
        ge=1, 
        le=120, 
        description="Zeitbudget ohne Rückfahrt (Minuten)"
    )
    time_budget_with_return: int = Field(
        ge=1, 
        le=180, 
        description="Zeitbudget mit Rückfahrt (Minuten)"
    )
    service_time_per_stop: float = Field(
        ge=0.5, 
        le=10.0, 
        description="Service-Zeit pro Stop (Minuten)"
    )
    speed_kmh: float = Field(
        ge=10.0, 
        le=100.0, 
        description="Durchschnittsgeschwindigkeit (km/h)"
    )
    safety_factor: float = Field(
        ge=1.0, 
        le=2.0, 
        description="Sicherheitsfaktor für Stadtverkehr"
    )
    depot_lat: float = Field(
        ge=-90.0, 
        le=90.0, 
        description="Depot-Latitude"
    )
    depot_lon: float = Field(
        ge=-180.0, 
        le=180.0, 
        description="Depot-Longitude"
    )
    
    @field_validator('service_time_per_stop')
    @classmethod
    def validate_service_time(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Service-Zeit pro Stop muss größer als 0 sein")
        return v
    
    @field_validator('speed_kmh')
    @classmethod
    def validate_speed(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Durchschnittsgeschwindigkeit muss größer als 0 sein")
        return v
    
    @field_validator('safety_factor')
    @classmethod
    def validate_safety_factor(cls, v: float) -> float:
        if v < 1.0:
            raise ValueError("Sicherheitsfaktor muss mindestens 1.0 sein")
        return v
    
    @model_validator(mode='after')
    def validate_time_budgets(self) -> 'SystemRulesUpdate':
        if self.time_budget_without_return > self.time_budget_with_return:
            raise ValueError(
                f"Zeitbudget ohne Rückfahrt ({self.time_budget_without_return} Min) "
                f"darf nicht größer sein als Zeitbudget mit Rückfahrt ({self.time_budget_with_return} Min)"
            )
        return self

