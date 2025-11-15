"""
Haversine-Fallback für Routing (Phase 2 Runbook).
Erzeugt Polyline6 für Fallback-Routen wenn OSRM nicht verfügbar.
"""
from typing import List, Tuple
import math

try:
    import polyline
except ImportError:
    # Fallback: Einfache Polyline-Encoding
    polyline = None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Berechnet Haversine-Distanz zwischen zwei Punkten.
    
    Returns:
        Distanz in Metern
    """
    R = 6371000  # Erdradius in Metern
    
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c


def haversine_polyline6(coords: List[Tuple[float, float]]) -> str:
    """
    Erzeugt Polyline6 für Koordinaten-Liste (gerade Linien).
    
    Args:
        coords: [[lon, lat], [lon, lat], ...]
    
    Returns:
        Polyline6-String (encoded)
    """
    if not coords or len(coords) < 2:
        return ""
    
    # Konvertiere zu (lat, lon) für polyline
    latlon = [(lat, lon) for lon, lat in coords]
    
    if polyline:
        # Verwende polyline-Bibliothek falls verfügbar
        return polyline.encode(latlon, precision=6)
    else:
        # Fallback: Einfache Implementierung (nur für Notfall)
        # In Produktion sollte polyline installiert sein
        logger = __import__('logging').getLogger(__name__)
        logger.warning("polyline-Bibliothek nicht verfügbar, verwende einfachen Fallback")
        # Für jetzt: Leerer String (Frontend zeichnet dann gerade Linien)
        return ""


def haversine_total_distance(coords: List[Tuple[float, float]]) -> int:
    """
    Berechnet Gesamtdistanz für Koordinaten-Liste.
    
    Args:
        coords: [[lon, lat], [lon, lat], ...]
    
    Returns:
        Gesamtdistanz in Metern (gerundet)
    """
    if len(coords) < 2:
        return 0
    
    total = 0.0
    for i in range(len(coords) - 1):
        lon1, lat1 = coords[i]
        lon2, lat2 = coords[i + 1]
        total += haversine_distance(lat1, lon1, lat2, lon2)
    
    return int(round(total))


def haversine_estimated_duration(distance_m: int, speed_kmh: float = 30.0) -> int:
    """
    Schätzt Dauer basierend auf Distanz und Geschwindigkeit.
    
    Args:
        distance_m: Distanz in Metern
        speed_kmh: Geschwindigkeit in km/h (Standard: 30 km/h für Fallback)
    
    Returns:
        Geschätzte Dauer in Sekunden
    """
    if distance_m <= 0:
        return 0
    
    speed_ms = speed_kmh / 3.6  # km/h → m/s
    duration_s = distance_m / speed_ms
    
    return int(round(duration_s))

