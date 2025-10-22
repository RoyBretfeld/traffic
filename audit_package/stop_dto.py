# services/stop_dto.py
from __future__ import annotations
from typing import Optional, Dict, Any

def build_stop_dto(*, stop_id: str, display_name: str, resolved_address: str,
                   lat: Optional[float], lon: Optional[float], geo_source: str,
                   extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Baut das API-DTO für Stop-Objekte mit Guards für valide Koordinaten.
    
    Args:
        stop_id: Eindeutige ID des Stops
        display_name: Anzeigename (z.B. Firmenname) für UI-Titel
        resolved_address: Bereinigte Adresse für UI-Rendering
        lat: Breitengrad (kann None sein)
        lon: Längengrad (kann None sein)
        geo_source: Quelle der Geocoding-Daten (synonym|cache|geocoder)
        extra: Zusätzliche Felder die dem DTO hinzugefügt werden sollen
        
    Returns:
        Dict mit allen Stop-Daten und valid-Flag für Koordinaten
    """
    dto = {
        "id": stop_id,
        "display_name": display_name,            # z.B. Firmenname (UI Titel)
        "resolved_address": resolved_address,    # fürs UI rendern
        "lat": lat,
        "lon": lon,
        "geo_source": geo_source,                # synonym|cache|geocoder
        "valid": isinstance(lat, (int, float)) and isinstance(lon, (int, float)),
    }
    if extra:
        dto.update(extra)
    # Harte Guard: an die UI nur valid==True routen lassen
    return dto

def build_stop_dto_from_stop(stop_obj: Any) -> Dict[str, Any]:
    """
    Convenience-Funktion um ein Stop-Objekt direkt in ein DTO zu konvertieren.
    
    Args:
        stop_obj: Stop-Objekt mit Attributen id, name, address, lat, lon, geo_source
        
    Returns:
        DTO-Dict mit allen Stop-Daten
    """
    return build_stop_dto(
        stop_id=getattr(stop_obj, 'id', ''),
        display_name=getattr(stop_obj, 'name', getattr(stop_obj, 'id', '')),
        resolved_address=getattr(stop_obj, 'address', ''),
        lat=getattr(stop_obj, 'lat', None),
        lon=getattr(stop_obj, 'lon', None),
        geo_source=getattr(stop_obj, 'geo_source', 'cache'),
        extra=getattr(stop_obj, 'extra', None)
    )