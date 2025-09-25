"""Distance utilities."""

from __future__ import annotations

import math

from .models import Location


EARTH_RADIUS_KM = 6371.0


def haversine_km(a: Location, b: Location) -> float:
    """Compute the great-circle distance between two points in kilometres."""

    lat1 = math.radians(a.latitude)
    lon1 = math.radians(a.longitude)
    lat2 = math.radians(b.latitude)
    lon2 = math.radians(b.longitude)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(h))
