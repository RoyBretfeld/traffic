"""
Echte Straßenrouting mit Mapbox Directions API für FAMO TrafficApp
"""

from __future__ import annotations
import logging
import os
from typing import List, Optional
from dataclasses import dataclass
import httpx


@dataclass
class RoutePoint:
    lat: float
    lon: float
    address: str
    name: str = ""


@dataclass
class RouteSegment:
    distance_km: float
    duration_minutes: int
    traffic_delay_minutes: int
    construction_avoided: bool
    route_geometry: List[tuple[float, float]]


@dataclass
class FullRoute:
    total_distance_km: float
    total_duration_minutes: int
    total_traffic_delay: int
    segments: List[RouteSegment]
    avoided_issues: List[str]


class RealRoutingService:
    """Routenservice mit OSRM-Priorität und Mapbox-Fallback."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        self.osrm_base = os.environ.get("OSRM_BASE_URL")
        self.osrm_profile = os.environ.get("OSRM_PROFILE", "driving")
        self.osrm_timeout = float(os.environ.get("OSRM_TIMEOUT", "20"))

        self.mapbox_token = os.environ.get("MAPBOX_ACCESS_TOKEN")
        self.mapbox_base_url = "https://api.mapbox.com/directions/v5/mapbox/driving"
        if not self.osrm_base and not self.mapbox_token:
            self.logger.warning(
                "Weder OSRM_BASE_URL noch MAPBOX_ACCESS_TOKEN gesetzt – verwende Fallback-Routing."
            )

    async def calculate_route(self, points: List[RoutePoint]) -> FullRoute:
        if len(points) < 2:
            raise ValueError("Mindestens zwei Punkte erforderlich")

        if self.osrm_base:
            osrm_route = await self._calculate_osrm(points)
            if osrm_route:
                return osrm_route

        if self.mapbox_token:
            mapbox_route = await self._calculate_mapbox(points)
            if mapbox_route:
                return mapbox_route

        return self._fallback(points)

    async def _calculate_osrm(self, points: List[RoutePoint]) -> Optional[FullRoute]:
        coords = ";".join(f"{p.lon},{p.lat}" for p in points)
        base = self.osrm_base.rstrip("/")
        url = f"{base}/route/v1/{self.osrm_profile}/{coords}"
        params = {
            "overview": "full",
            "geometries": "polyline",
            "steps": "false",
        }
        try:
            async with httpx.AsyncClient(timeout=self.osrm_timeout) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            self.logger.warning("OSRM Anfrage fehlgeschlagen: %s", exc)
            return None

        routes = data.get("routes") or []
        if not routes:
            self.logger.warning("OSRM: Keine Route gefunden")
            return None

        route = routes[0]
        distance_km = route.get("distance", 0.0) / 1000.0
        duration_min = route.get("duration", 0.0) / 60.0
        geometry = self._decode_polyline(route.get("geometry", ""))

        segments = [
            RouteSegment(
                distance_km=distance_km,
                duration_minutes=int(duration_min),
                traffic_delay_minutes=0,
                construction_avoided=False,
                route_geometry=geometry,
            )
        ]

        return FullRoute(
            total_distance_km=distance_km,
            total_duration_minutes=int(duration_min),
            total_traffic_delay=0,
            segments=segments,
            avoided_issues=[],
        )

    async def _calculate_mapbox(self, points: List[RoutePoint]) -> Optional[FullRoute]:
        coords = ";".join(f"{p.lon},{p.lat}" for p in points)
        url = f"{self.mapbox_base_url}/{coords}"
        params = {
            "access_token": self.mapbox_token,
            "geometries": "polyline",
            "annotations": "duration,distance",
            "overview": "full",
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(url, params=params)
                resp.raise_for_status()
                data = resp.json()
        except Exception as exc:
            self.logger.warning("Mapbox Anfrage fehlgeschlagen: %s", exc)
            return None

        routes = data.get("routes") or []
        if not routes:
            self.logger.warning("Mapbox: Keine Route gefunden")
            return None

        route = routes[0]
        distance_km = route.get("distance", 0) / 1000.0
        duration_min = route.get("duration", 0) / 60.0
        geometry = self._decode_polyline(route.get("geometry", ""))

        segments = [
            RouteSegment(
                distance_km=distance_km,
                duration_minutes=int(duration_min),
                traffic_delay_minutes=0,
                construction_avoided=False,
                route_geometry=geometry,
            )
        ]

        return FullRoute(
            total_distance_km=distance_km,
            total_duration_minutes=int(duration_min),
            total_traffic_delay=0,
            segments=segments,
            avoided_issues=[],
        )

    def _fallback(self, points: List[RoutePoint]) -> FullRoute:
        total_distance = 0.0
        segments: List[RouteSegment] = []
        for i in range(len(points) - 1):
            p1, p2 = points[i], points[i + 1]
            air = self._haversine(p1.lat, p1.lon, p2.lat, p2.lon)
            road = air * 1.3
            duration_min = (road / 25.0) * 60
            segments.append(
                RouteSegment(
                    distance_km=road,
                    duration_minutes=int(duration_min),
                    traffic_delay_minutes=0,
                    construction_avoided=False,
                    route_geometry=[],
                )
            )
            total_distance += road

        return FullRoute(
            total_distance_km=total_distance,
            total_duration_minutes=int((total_distance / 25.0) * 60),
            total_traffic_delay=0,
            segments=segments,
            avoided_issues=["Fallback ohne aktiven Routingdienst"],
        )

    def _decode_polyline(self, encoded: str) -> List[tuple[float, float]]:
        # Polyline-Decoder (Mapbox / Google kompatibel)
        coords: List[tuple[float, float]] = []
        index = lat = lon = 0
        length = len(encoded)
        while index < length:
            result = shift = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            dlat = ~(result >> 1) if result & 1 else (result >> 1)
            lat += dlat

            result = shift = 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1F) << shift
                shift += 5
                if b < 0x20:
                    break
            dlng = ~(result >> 1) if result & 1 else (result >> 1)
            lon += dlng

            coords.append((lat / 1e5, lon / 1e5))
        return coords

    def _haversine(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        from math import radians, sin, cos, sqrt, atan2
        R = 6371.0
        dlat = radians(lat2 - lat1)
        dlon = radians(lon2 - lon1)
        a = (
            sin(dlat / 2) ** 2
            + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon / 2) ** 2
        )
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return R * c
