"""
Touren Engine API gemäß Betriebsordnung §3.

Endpoints:
- POST /engine/tours/ingest - Akzeptiert Erkennungsformat, erzeugt UIDs
- GET  /engine/tours/{tour_uid}/status - Status abfragen
- POST /engine/tours/optimize - Optimiert nur vollständige Touren
- POST /engine/tours/split - Subtourenbildung mit OSRM Table
"""
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from typing import List, Dict, Optional, Set, Tuple
from pydantic import BaseModel, Field
import logging

from services.uid_service import generate_tour_uid, generate_stop_uid, validate_tour_uid, validate_stop_uid
from services.osrm_client import OSRMClient
from common.normalize import normalize_address

router = APIRouter()
logger = logging.getLogger(__name__)

# Globale Services
osrm_client = OSRMClient()

# In-Memory Store für Touren (später in DB)
_tour_store: Dict[str, Dict] = {}


# Request/Response Models
class StopInput(BaseModel):
    """Input-Format von Erkennung (Betriebsordnung §1)"""
    source_id: str = Field(..., description="Quell-ID (z.B. 'ROW-12345')")
    label: Optional[str] = Field(None, description="Kunden-Label")
    address: Optional[str] = Field(None, description="Adresse")
    lat: Optional[float] = Field(None, description="Breitengrad")
    lon: Optional[float] = Field(None, description="Längengrad")
    time_window: Optional[Dict[str, str]] = Field(None, description="Zeitfenster")
    attrs: Optional[Dict] = Field(default_factory=dict, description="Zusätzliche Attribute")


class TourInput(BaseModel):
    """Tour-Input-Format von Erkennung (Betriebsordnung §1)"""
    tour_id: str = Field(..., description="Tour-ID (z.B. 'ext-2025-11-01-A')")
    label: Optional[str] = Field(None, description="Tour-Label")
    stops: List[StopInput] = Field(default_factory=list, description="Stopps")


class IngestRequest(BaseModel):
    """Request für /engine/tours/ingest"""
    tours: List[TourInput] = Field(default_factory=list, description="Touren")


class IngestResponse(BaseModel):
    """Response für /engine/tours/ingest"""
    success: bool
    tours_ingested: int
    tour_uids: List[str]
    stops_with_uid: int
    stops_pending_geo: int
    warnings: List[str] = Field(default_factory=list)


class TourStatusResponse(BaseModel):
    """Response für /engine/tours/{tour_uid}/status"""
    tour_uid: str
    tour_id: str
    status: str  # pending_geo|ready|optimized|failed
    stop_count: int
    stops_with_geo: int
    stops_pending_geo: int
    optimized: bool
    error: Optional[str] = None


class OptimizeRequest(BaseModel):
    """Request für /engine/tours/optimize"""
    tour_uid: str = Field(..., description="Tour-UID")


class OptimizeResponse(BaseModel):
    """Response für /engine/tours/optimize (Betriebsordnung §3)"""
    tour_uid: str
    route: List[str] = Field(..., description="Liste von stop_uids in optimierter Reihenfolge")
    meta: Dict = Field(default_factory=lambda: {"objective": "time"})


class SplitRequest(BaseModel):
    """Request für /engine/tours/split"""
    tour_uid: str = Field(..., description="Tour-UID")
    max_duration_minutes: int = Field(60, description="Maximale Dauer pro Sub-Route")
    max_stops_per_route: Optional[int] = Field(None, description="Max. Stopps pro Route")


class SplitResponse(BaseModel):
    """Response für /engine/tours/split"""
    tour_uid: str
    sub_routes: List[Dict] = Field(..., description="Liste von Sub-Routen mit stop_uids")


@router.post("/engine/tours/ingest", response_model=IngestResponse)
async def ingest_tours(request: IngestRequest):
    """
    Akzeptiert Erkennungsformat, erzeugt UIDs, normalisiert, plant Geo.
    
    Betriebsordnung §3: POST /engine/tours/ingest
    """
    try:
        tour_uids = []
        stops_with_uid = 0
        stops_pending_geo = 0
        warnings = []
        
        for tour_input in request.tours:
            # Generiere tour_uid
            tour_uid = generate_tour_uid(tour_input.tour_id)
            tour_uids.append(tour_uid)
            
            # Erstelle interne Tour-Repräsentation
            tour_data = {
                "tour_id": tour_input.tour_id,
                "tour_uid": tour_uid,
                "label": tour_input.label,
                "stops": [],
                "status": "pending_geo",
                "optimized": False
            }
            
            # Verarbeite Stopps
            stops_with_geo_count = 0
            for stop_input in tour_input.stops:
                # Generiere stop_uid
                # Betriebsordnung §2: stop_uid = sha256(source_id | norm(address) | plz | ort)
                # Extrahieren PLZ/Ort aus address (vereinfacht)
                plz = None
                ort = None
                if stop_input.address:
                    # Versuche PLZ/Ort zu extrahieren (vereinfacht)
                    parts = stop_input.address.split(',')
                    if len(parts) >= 2:
                        # Annahme: Letzter Teil enthält PLZ und Ort
                        last_part = parts[-1].strip()
                        # PLZ: 5-stellige Zahl am Anfang
                        import re
                        plz_match = re.search(r'\b(\d{5})\b', last_part)
                        if plz_match:
                            plz = plz_match.group(1)
                            ort = last_part.replace(plz, '').strip()
                
                stop_uid = generate_stop_uid(
                    source_id=stop_input.source_id,
                    address=stop_input.address or "",
                    postal_code=plz,
                    city=ort
                )
                
                # Normalisiere Adresse (Repair-Layer)
                norm_address = normalize_address(stop_input.address) if stop_input.address else ""
                
                stop_data = {
                    "stop_uid": stop_uid,
                    "source_id": stop_input.source_id,
                    "label": stop_input.label,
                    "address": norm_address,
                    "original_address": stop_input.address,
                    "lat": stop_input.lat,
                    "lon": stop_input.lon,
                    "time_window": stop_input.time_window,
                    "attrs": stop_input.attrs or {}
                }
                
                tour_data["stops"].append(stop_data)
                stops_with_uid += 1
                
                # Prüfe Geo-Status
                if stop_input.lat is None or stop_input.lon is None:
                    stops_pending_geo += 1
                else:
                    stops_with_geo_count += 1
            
            # Status bestimmen
            if stops_with_geo_count == len(tour_input.stops):
                tour_data["status"] = "ready"
            elif stops_with_geo_count > 0:
                tour_data["status"] = "pending_geo"
                warnings.append(f"Tour {tour_input.tour_id}: {len(tour_input.stops) - stops_with_geo_count} Stopps ohne Koordinaten")
            else:
                tour_data["status"] = "pending_geo"
                warnings.append(f"Tour {tour_input.tour_id}: Keine Koordinaten für Stopps")
            
            # Speichere Tour
            _tour_store[tour_uid] = tour_data
            
            logger.info(f"Ingest: Tour {tour_input.tour_id} → {tour_uid} ({stops_with_geo_count}/{len(tour_input.stops)} mit Geo)")
        
        return IngestResponse(
            success=True,
            tours_ingested=len(request.tours),
            tour_uids=tour_uids,
            stops_with_uid=stops_with_uid,
            stops_pending_geo=stops_pending_geo,
            warnings=warnings
        )
        
    except Exception as e:
        logger.error(f"Fehler bei ingest: {e}", exc_info=True)
        raise HTTPException(500, detail=f"Ingest fehlgeschlagen: {str(e)}")


@router.get("/engine/tours/{tour_uid}/status", response_model=TourStatusResponse)
async def get_tour_status(tour_uid: str):
    """
    Status abfragen: pending_geo|ready|optimized|failed
    
    Betriebsordnung §3: GET /engine/tours/{tour_uid}/status
    """
    if not validate_tour_uid(tour_uid):
        raise HTTPException(400, detail="Ungültige tour_uid")
    
    if tour_uid not in _tour_store:
        raise HTTPException(404, detail="Tour nicht gefunden")
    
    tour_data = _tour_store[tour_uid]
    stops = tour_data["stops"]
    
    stops_with_geo = sum(1 for s in stops if s.get("lat") and s.get("lon"))
    stops_pending_geo = len(stops) - stops_with_geo
    
    return TourStatusResponse(
        tour_uid=tour_uid,
        tour_id=tour_data["tour_id"],
        status=tour_data["status"],
        stop_count=len(stops),
        stops_with_geo=stops_with_geo,
        stops_pending_geo=stops_pending_geo,
        optimized=tour_data.get("optimized", False),
        error=tour_data.get("error")
    )


@router.post("/engine/tours/optimize", response_model=OptimizeResponse)
async def optimize_tour(request: OptimizeRequest):
    """
    Optimiert nur vollständige Touren (alle Stops mit lat/lon).
    
    Betriebsordnung §3: POST /engine/tours/optimize
    
    Strategie (Betriebsordnung §4, §5):
    1. OSRM (wenn verfügbar)
    2. Heuristik (Nearest-Neighbor)
    3. LLM (nur als Fallback)
    
    Validierung: set(route) == set(valid_stop_uids) and len(route) == n
    """
    tour_uid = request.tour_uid
    
    if not validate_tour_uid(tour_uid):
        raise HTTPException(400, detail="Ungültige tour_uid")
    
    if tour_uid not in _tour_store:
        raise HTTPException(404, detail="Tour nicht gefunden")
    
    tour_data = _tour_store[tour_uid]
    stops = tour_data["stops"]
    
    # Prüfe ob alle Stopps Koordinaten haben
    valid_stops = [s for s in stops if s.get("lat") and s.get("lon")]
    if len(valid_stops) != len(stops):
        missing = len(stops) - len(valid_stops)
        raise HTTPException(
            400,
            detail=f"Tour nicht vollständig: {missing} Stopps ohne Koordinaten (Status: {tour_data['status']})"
        )
    
    valid_stop_uids: Set[str] = {s["stop_uid"] for s in valid_stops}
    
    # WICHTIG: Prüfe OSRM-Verfügbarkeit BEVOR optimiert wird
    from .workflow_api import get_osrm_client
    osrm_client_check = get_osrm_client()
    osrm_health = osrm_client_check.check_health()
    
    if osrm_health["status"] != "ok":
        raise HTTPException(
            503,
            detail=f"OSRM nicht verfügbar: {osrm_health['message']}. Optimierung ohne OSRM nicht möglich."
        )
    
    # OSRM-First Strategie (Betriebsordnung §4)
    optimized_route: Optional[List[str]] = None
    method = "unknown"
    
    try:
        # 1. Versuche OSRM-basierte Optimierung
        if osrm_client.available:
            try:
                # Erstelle Koordinaten-Liste
                coords = [(s["lat"], s["lon"]) for s in valid_stops]
                
                # Hole Distanz-Matrix mit OSRM Table API (alle zu allen)
                distance_matrix_raw = osrm_client.get_distance_matrix(coords)
                
                if distance_matrix_raw:
                    # Konvertiere zu altem Format für Kompatibilität {(i,j): km}
                    distance_matrix = {}
                    for key, value in distance_matrix_raw.items():
                        if isinstance(value, dict):
                            distance_matrix[key] = value.get("km", 0)
                        else:
                            distance_matrix[key] = value
                    
                    # Optimierung mit OSRM-Distanzen (vereinfacht: Nearest-Neighbor)
                    optimized_route = _optimize_with_osrm_matrix(valid_stops, distance_matrix)
                    method = "osrm"
                    logger.info(f"Tour {tour_uid}: OSRM-Optimierung erfolgreich")
            except Exception as e:
                logger.warning(f"OSRM-Optimierung fehlgeschlagen: {e}")
        
        # 2. Fallback: Heuristik (Nearest-Neighbor mit Haversine)
        if not optimized_route:
            optimized_route = _optimize_with_heuristic(valid_stops)
            method = "heuristic"
            logger.info(f"Tour {tour_uid}: Heuristik-Optimierung verwendet")
        
        # 3. Fallback: LLM (nur wenn nötig - Betriebsordnung §5)
        # TODO: LLM-Integration (nur wenn OSRM/Heuristik nicht eindeutig)
        
    except Exception as e:
        logger.error(f"Optimierung fehlgeschlagen für Tour {tour_uid}: {e}", exc_info=True)
        # Quarantäne (Betriebsordnung §0)
        tour_data["status"] = "failed"
        tour_data["error"] = str(e)
        raise HTTPException(500, detail=f"Optimierung fehlgeschlagen: {str(e)}")
    
    # Harte Set-Validierung (Betriebsordnung §3)
    route_set = set(optimized_route)
    if route_set != valid_stop_uids or len(optimized_route) != len(valid_stop_uids):
        logger.error(
            f"Validierungsfehler: route_set={len(route_set)}, valid_set={len(valid_stop_uids)}, "
            f"route_len={len(optimized_route)}, valid_len={len(valid_stop_uids)}"
        )
        # Quarantäne (Betriebsordnung §0)
        tour_data["status"] = "failed"
        tour_data["error"] = "Set-Validierung fehlgeschlagen"
        raise HTTPException(
            400,
            detail=f"Route ungültig: {len(route_set)}/{len(valid_stop_uids)} Stopps (Set-Validierung fehlgeschlagen)"
        )
    
    # Erfolgreich optimiert
    tour_data["optimized"] = True
    tour_data["status"] = "optimized"
    tour_data["optimized_route"] = optimized_route
    tour_data["optimization_method"] = method
    
    return OptimizeResponse(
        tour_uid=tour_uid,
        route=optimized_route,
        meta={"objective": "time", "method": method}
    )


def _optimize_with_osrm_matrix(
    stops: List[Dict],
    distance_matrix: Dict[Tuple[int, int], float]
) -> List[str]:
    """
    Optimiert Route mit OSRM-Distanz-Matrix (Nearest-Neighbor).
    
    Args:
        stops: Liste von Stop-Dicts (mit stop_uid, lat, lon)
        distance_matrix: Dict mit {(i, j): distance_km}
    
    Returns:
        Liste von stop_uids in optimierter Reihenfolge
    """
    if len(stops) <= 1:
        return [s["stop_uid"] for s in stops]
    
    # Nearest-Neighbor mit OSRM-Distanzen
    optimized = [stops[0]]
    remaining_indices = set(range(1, len(stops)))
    
    while remaining_indices:
        last_idx = stops.index(optimized[-1])
        nearest_idx = None
        min_distance = float('inf')
        
        for idx in remaining_indices:
            distance = distance_matrix.get((last_idx, idx))
            if distance is not None and distance < min_distance:
                min_distance = distance
                nearest_idx = idx
        
        if nearest_idx is None:
            # Fallback: Wähle ersten verbleibenden
            nearest_idx = next(iter(remaining_indices))
        
        optimized.append(stops[nearest_idx])
        remaining_indices.remove(nearest_idx)
    
    return [s["stop_uid"] for s in optimized]


def _optimize_with_heuristic(stops: List[Dict]) -> List[str]:
    """
    Optimiert Route mit Haversine-Heuristik (Nearest-Neighbor).
    
    Args:
        stops: Liste von Stop-Dicts (mit stop_uid, lat, lon)
    
    Returns:
        Liste von stop_uids in optimierter Reihenfolge
    """
    if len(stops) <= 1:
        return [s["stop_uid"] for s in stops]
    
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371.0  # Erdradius in km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    
    optimized = [stops[0]]
    remaining = stops[1:]
    
    while remaining:
        last_stop = optimized[-1]
        nearest = min(
            remaining,
            key=lambda s: haversine_distance(
                last_stop["lat"], last_stop["lon"],
                s["lat"], s["lon"]
            )
        )
        optimized.append(nearest)
        remaining.remove(nearest)
    
    return [s["stop_uid"] for s in optimized]


@router.post("/engine/tours/split", response_model=SplitResponse)
async def split_tour(request: SplitRequest):
    """
    Subtourenbildung mit OSRM Table (Fahrzeiten).
    
    Betriebsordnung §3: POST /engine/tours/split
    
    Args:
        tour_uid: Tour-UID
        max_duration_minutes: Maximale Dauer pro Sub-Route (Standard: 60)
        max_stops_per_route: Maximale Stopps pro Route (optional)
    """
    tour_uid = request.tour_uid
    
    if not validate_tour_uid(tour_uid):
        raise HTTPException(400, detail="Ungültige tour_uid")
    
    if tour_uid not in _tour_store:
        raise HTTPException(404, detail="Tour nicht gefunden")
    
    tour_data = _tour_store[tour_uid]
    
    # Prüfe ob Tour optimiert wurde
    if not tour_data.get("optimized"):
        raise HTTPException(400, detail="Tour muss erst optimiert werden (POST /engine/tours/optimize)")
    
    optimized_route = tour_data.get("optimized_route", [])
    if not optimized_route:
        raise HTTPException(400, detail="Keine optimierte Route vorhanden")
    
    # Mappe stop_uids zurück zu Stop-Daten
    stop_dict = {s["stop_uid"]: s for s in tour_data["stops"]}
    route_stops = [stop_dict[uid] for uid in optimized_route if uid in stop_dict]
    
    if not route_stops:
        raise HTTPException(400, detail="Route enthält ungültige stop_uids")
    
    # Splitting-Logik mit OSRM Table API
    sub_routes = []
    
    try:
        # Erstelle Koordinaten-Liste
        coords = [(s["lat"], s["lon"]) for s in route_stops]
        
        if osrm_client.available:
            # Hole Distanz-Matrix mit OSRM Table API
            distance_matrix = osrm_client.get_distance_matrix(coords)
            if distance_matrix:
                # Splitting mit OSRM-Distanzen
                sub_routes = _split_tour_with_osrm(
                    route_stops,
                    distance_matrix,
                    request.max_duration_minutes,
                    request.max_stops_per_route
                )
            else:
                # Fallback: Haversine × 1.3 (Betriebsordnung §4)
                sub_routes = _split_tour_with_heuristic(
                    route_stops,
                    request.max_duration_minutes,
                    request.max_stops_per_route
                )
        else:
            # Fallback: Haversine × 1.3
            sub_routes = _split_tour_with_heuristic(
                route_stops,
                request.max_duration_minutes,
                request.max_stops_per_route
            )
        
    except Exception as e:
        logger.error(f"Splitting fehlgeschlagen für Tour {tour_uid}: {e}", exc_info=True)
        raise HTTPException(500, detail=f"Splitting fehlgeschlagen: {str(e)}")
    
    return SplitResponse(
        tour_uid=tour_uid,
        sub_routes=[
            {
                "route": [s["stop_uid"] for s in sub_route],
                "stop_count": len(sub_route),
                "estimated_duration_minutes": _estimate_duration(sub_route)
            }
            for sub_route in sub_routes
        ]
    )


def _split_tour_with_osrm(
    stops: List[Dict],
    distance_matrix: Dict[Tuple[int, int], float],
    max_duration_minutes: int,
    max_stops_per_route: Optional[int]
) -> List[List[Dict]]:
    """Splitting mit OSRM-Distanzen"""
    sub_routes = []
    current_route = []
    current_duration = 0.0
    
    # Durchschnittsgeschwindigkeit: 50 km/h
    speed_kmh = 50.0
    
    for i, stop in enumerate(stops):
        # Berechne Distanz zum vorherigen Stop
        if current_route:
            prev_idx = stops.index(current_route[-1])
            distance_km = distance_matrix.get((prev_idx, i))
            if distance_km:
                travel_time = (distance_km / speed_kmh) * 60  # Minuten
            else:
                travel_time = 5.0  # Fallback: 5 Minuten
        else:
            travel_time = 0.0
        
        service_time = 2.0  # 2 Minuten pro Stop
        
        # Prüfe ob Stop in aktuelle Route passt
        if (current_duration + travel_time + service_time <= max_duration_minutes and
            (max_stops_per_route is None or len(current_route) < max_stops_per_route)):
            current_route.append(stop)
            current_duration += travel_time + service_time
        else:
            # Neue Sub-Route starten
            if current_route:
                sub_routes.append(current_route)
            current_route = [stop]
            current_duration = service_time
    
    # Letzte Route hinzufügen
    if current_route:
        sub_routes.append(current_route)
    
    return sub_routes


def _split_tour_with_heuristic(
    stops: List[Dict],
    max_duration_minutes: int,
    max_stops_per_route: Optional[int]
) -> List[List[Dict]]:
    """Splitting mit Haversine × 1.3 (Betriebsordnung §4)"""
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    
    sub_routes = []
    current_route = []
    current_duration = 0.0
    
    speed_kmh = 50.0
    safety_factor = 1.3  # Betriebsordnung §4
    
    for i, stop in enumerate(stops):
        if current_route:
            prev_stop = current_route[-1]
            distance_km = haversine_distance(
                prev_stop["lat"], prev_stop["lon"],
                stop["lat"], stop["lon"]
            ) * safety_factor
            travel_time = (distance_km / speed_kmh) * 60
        else:
            travel_time = 0.0
        
        service_time = 2.0
        
        if (current_duration + travel_time + service_time <= max_duration_minutes and
            (max_stops_per_route is None or len(current_route) < max_stops_per_route)):
            current_route.append(stop)
            current_duration += travel_time + service_time
        else:
            if current_route:
                sub_routes.append(current_route)
            current_route = [stop]
            current_duration = service_time
    
    if current_route:
        sub_routes.append(current_route)
    
    return sub_routes


def _estimate_duration(stops: List[Dict]) -> float:
    """Schätzt Dauer für eine Route (vereinfacht)"""
    if len(stops) <= 1:
        return 2.0  # Service-Zeit
    
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371.0
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    
    total_distance = 0.0
    for i in range(1, len(stops)):
        dist = haversine_distance(
            stops[i-1]["lat"], stops[i-1]["lon"],
            stops[i]["lat"], stops[i]["lon"]
        )
        total_distance += dist
    
    travel_time = (total_distance / 50.0) * 60  # 50 km/h
    service_time = len(stops) * 2.0
    
    return travel_time + service_time


# ============================================================
# DRESDEN-QUADRANTEN & ZEITBOX ENDPOINTS
# ============================================================

from services.sector_planner import (
    SectorPlanner, SectorPlanParams, SectorRoute, StopWithSector, RouteSegment
)
from services.pirna_clusterer import (
    PirnaClusterer, PirnaClusterParams, PirnaCluster
)


class SectorizeRequest(BaseModel):
    """Request für /engine/tours/sectorize"""
    tour_uid: str
    depot_lat: float = Field(51.0111988, description="Depot-Breitengrad")
    depot_lon: float = Field(13.7016485, description="Depot-Längengrad")
    sectors: int = Field(4, description="Anzahl Sektoren (4 oder 8)")


class SectorizeResponse(BaseModel):
    """Response für /engine/tours/sectorize"""
    tour_uid: str
    stops_with_sectors: List[Dict] = Field(..., description="Stopps mit Sektor-Zuordnung")


class PlanBySectorRequest(BaseModel):
    """Request für /engine/tours/plan_by_sector"""
    tour_uid: str
    depot_uid: str = Field("depot_uid", description="Depot-UID")
    depot_lat: float = Field(51.0111988, description="Depot-Breitengrad")
    depot_lon: float = Field(13.7016485, description="Depot-Längengrad")
    start_time: str = Field("07:00", description="Start-Zeit")
    hard_deadline: str = Field("09:00", description="Rückkehr-Zeit")
    time_budget_minutes: int = Field(90, description="Zeitbudget pro Route")
    reload_buffer_minutes: int = Field(30, description="Puffer am Depot")
    service_time_default: float = Field(2.0, description="Standard Service-Zeit")
    service_time_per_stop: Dict[str, float] = Field(default_factory=dict, description="Service-Zeit Overrides")
    sectors: int = Field(4, description="Anzahl Sektoren")
    include_return_to_depot: bool = Field(True, description="Rückfahrt zum Depot")
    round: int = Field(2, description="Rundung")


class PlanBySectorResponse(BaseModel):
    """Response für /engine/tours/plan_by_sector"""
    tour_uid: str
    params: Dict
    sub_routes: List[Dict] = Field(..., description="Sub-Routen pro Sektor")
    totals: Dict = Field(..., description="Gesamt-KM und Minuten")


@router.post("/engine/tours/sectorize", response_model=SectorizeResponse)
async def sectorize_tour(request: SectorizeRequest):
    """
    Weist allen Stopps einer Tour Sektoren zu (N/O/S/W).
    
    Betriebsordnung: Deterministische Zuordnung basierend auf Bearing/Azimut.
    
    WICHTIG: Sektor-Planung gilt NUR für W-Touren (z.B. "W-07.00"), 
    weil sie über das ganze Dresden-Kreuz verteilt sind.
    
    CB (Cottbus), BZ (Bautzen), PIR (Pirna) gehen in eine Richtung raus 
    aus Dresden und brauchen KEINE Sektorisierung.
    """
    from services.sector_planner import should_use_sector_planning
    
    tour_uid = request.tour_uid
    
    if not validate_tour_uid(tour_uid):
        raise HTTPException(400, detail="Ungültige tour_uid")
    
    if tour_uid not in _tour_store:
        raise HTTPException(404, detail="Tour nicht gefunden")
    
    tour_data = _tour_store[tour_uid]
    tour_id = tour_data.get("tour_id", "")
    
    # Prüfe ob Tour Sektor-Planung verwenden soll
    if not should_use_sector_planning(tour_id):
        raise HTTPException(
            400,
            detail=f"Sektor-Planung gilt nur für W-Touren (z.B. 'W-07.00'), die über das ganze Dresden-Kreuz verteilt sind. "
                   f"Tour '{tour_id}' ist keine W-Tour."
        )
    stops = tour_data["stops"]
    
    # Prüfe ob alle Stopps Koordinaten haben
    stops_with_coords = [s for s in stops if s.get("lat") and s.get("lon")]
    if len(stops_with_coords) != len(stops):
        missing = len(stops) - len(stops_with_coords)
        raise HTTPException(
            400,
            detail=f"Tour nicht vollständig: {missing} Stopps ohne Koordinaten"
        )
    
    # Sektorisierung
    planner = SectorPlanner(osrm_client)
    stops_with_sectors = planner.sectorize_stops(
        stops_with_coords,
        request.depot_lat,
        request.depot_lon,
        request.sectors
    )
    
    # Konvertiere zu Dict für Response
    result_stops = []
    for stop_ws in stops_with_sectors:
        result_stops.append({
            "stop_uid": stop_ws.stop_uid,
            "lat": stop_ws.lat,
            "lon": stop_ws.lon,
            "sector": stop_ws.sector.value,
            "bearing_deg": round(stop_ws.bearing_deg, 2),
            "distance_from_depot_km": round(stop_ws.distance_from_depot_km or 0, 2)
        })
    
    return SectorizeResponse(
        tour_uid=tour_uid,
        stops_with_sectors=result_stops
    )


@router.post("/engine/tours/plan_by_sector", response_model=PlanBySectorResponse)
async def plan_by_sector(request: PlanBySectorRequest):
    """
    Plant Routen pro Sektor mit Greedy-Algorithmus und Zeitbox.
    
    Betriebsordnung:
    - OSRM-First (exakte Distanzen/Zeiten)
    - Deterministische Sektorzuordnung
    - Zeitbox: Start 07:00, Rückkehr 09:00 (time_budget_minutes)
    - Frontend rechnet nichts
    
    WICHTIG: Sektor-Planung gilt NUR für W-Touren (z.B. "W-07.00"), 
    weil sie über das ganze Dresden-Kreuz verteilt sind.
    
    CB (Cottbus), BZ (Bautzen), PIR (Pirna) gehen in eine Richtung raus 
    aus Dresden und brauchen KEINE Sektorisierung.
    """
    from services.sector_planner import should_use_sector_planning
    
    tour_uid = request.tour_uid
    
    if not validate_tour_uid(tour_uid):
        raise HTTPException(400, detail="Ungültige tour_uid")
    
    if tour_uid not in _tour_store:
        raise HTTPException(404, detail="Tour nicht gefunden")
    
    tour_data = _tour_store[tour_uid]
    tour_id = tour_data.get("tour_id", "")
    
    # Prüfe ob Tour Sektor-Planung verwenden soll
    if not should_use_sector_planning(tour_id):
        raise HTTPException(
            400,
            detail=f"Sektor-Planung gilt nur für W-Touren (z.B. 'W-07.00'), die über das ganze Dresden-Kreuz verteilt sind. "
                   f"Tour '{tour_id}' ist keine W-Tour."
        )
    stops = tour_data["stops"]
    
    # Prüfe ob alle Stopps Koordinaten haben
    stops_with_coords = [s for s in stops if s.get("lat") and s.get("lon")]
    if len(stops_with_coords) != len(stops):
        missing = len(stops) - len(stops_with_coords)
        raise HTTPException(
            400,
            detail=f"Tour nicht vollständig: {missing} Stopps ohne Koordinaten"
        )
    
    # Erstelle Parameter
    params = SectorPlanParams(
        depot_uid=request.depot_uid,
        depot_lat=request.depot_lat,
        depot_lon=request.depot_lon,
        start_time=request.start_time,
        hard_deadline=request.hard_deadline,
        time_budget_minutes=request.time_budget_minutes,
        reload_buffer_minutes=request.reload_buffer_minutes,
        service_time_default=request.service_time_default,
        service_time_per_stop=request.service_time_per_stop,
        sectors=request.sectors,
        include_return_to_depot=request.include_return_to_depot,
        round=request.round
    )
    
    # Sektorisierung
    planner = SectorPlanner(osrm_client)
    stops_with_sectors = planner.sectorize_stops(
        stops_with_coords,
        params.depot_lat,
        params.depot_lon,
        params.sectors
    )
    
    # Planung pro Sektor
    routes = planner.plan_by_sector(stops_with_sectors, params)
    
    # Konvertiere zu Dict für Response
    sub_routes = []
    total_km = 0.0
    total_minutes = 0.0
    
    for route in routes:
        # Konvertiere Segmente
        segments = [
            {
                "from_uid": seg.from_uid,
                "to_uid": seg.to_uid,
                "km": seg.km,
                "minutes": seg.minutes
            }
            for seg in route.segments
        ]
        
        route_km = sum(seg.km for seg in route.segments)
        total_km += route_km
        
        sub_routes.append({
            "name": route.name,
            "sector": route.sector.value,
            "route_uids": route.route_uids,
            "segments": segments,
            "service_time_minutes": route.service_time_minutes,
            "driving_time_minutes": route.driving_time_minutes,
            "total_time_minutes": route.total_time_minutes,
            "meta": route.meta
        })
        
        total_minutes += route.total_time_minutes
    
    # Telemetrie
    metrics = planner.metrics
    
    return PlanBySectorResponse(
        tour_uid=tour_uid,
        params={
            "time_budget_minutes": params.time_budget_minutes,
            "include_return_to_depot": params.include_return_to_depot,
            "sectors": params.sectors,
            "start_time": params.start_time,
            "hard_deadline": params.hard_deadline
        },
        sub_routes=sub_routes,
        totals={
            "km": round(total_km, params.round),
            "minutes": round(total_minutes, params.round),
            "routes_count": len(sub_routes),
            "metrics": metrics
        }
    )


# PIRNA CLUSTERING

# ============================================================
# PIRNA-ROUTE CLUSTERING ENDPOINT
# ============================================================

class PirnaClusterRequest(BaseModel):
    """Request für /engine/tours/pirna/cluster"""
    tour_uid: str
    depot_uid: str = Field("depot_uid", description="Depot-UID")
    depot_lat: float = Field(51.0111988, description="Depot-Breitengrad")
    depot_lon: float = Field(13.7016485, description="Depot-Längengrad")
    max_stops_per_cluster: int = Field(8, description="Max. Stopps pro Cluster")
    max_time_per_cluster_minutes: int = Field(90, description="Max. Zeit pro Cluster")
    service_time_default: float = Field(2.0, description="Standard Service-Zeit")
    service_time_per_stop: Dict[str, float] = Field(default_factory=dict, description="Service-Zeit Overrides")
    include_return_to_depot: bool = Field(True, description="Rückfahrt zum Depot")


class PirnaClusterResponse(BaseModel):
    """Response für /engine/tours/pirna/cluster"""
    tour_uid: str
    clusters: List[Dict] = Field(..., description="Cluster von Stopps")
    params: Dict
    totals: Dict = Field(..., description="Gesamt-Statistiken")


@router.post("/engine/tours/pirna/cluster", response_model=PirnaClusterResponse)
async def cluster_pirna_tour(request: PirnaClusterRequest):
    """
    Gruppiert Stopps einer PIR-Tour nach geografischer Nähe.
    
    Problem: PIR-Touren haben meist > 4 Stopps und werden oft in zu viele 
    kleine Routen aufgeteilt (z.B. 3 Personen mit je 3 Stopps).
    
    Lösung: Clustering nach geografischer Nähe, damit weniger Routen mit 
    mehr Stopps entstehen (z.B. 1-2 Personen mit 5-8 Stopps statt 3×3).
    
    WICHTIG: Nur für PIR-Touren (Tour-ID beginnt mit "PIR").
    """
    tour_uid = request.tour_uid
    
    if not validate_tour_uid(tour_uid):
        raise HTTPException(400, detail="Ungültige tour_uid")
    
    if tour_uid not in _tour_store:
        raise HTTPException(404, detail="Tour nicht gefunden")
    
    tour_data = _tour_store[tour_uid]
    tour_id = tour_data.get("tour_id", "")
    
    # Prüfe ob Tour eine PIR-Tour ist
    if not tour_id.upper().startswith("PIR"):
        raise HTTPException(
            400,
            detail=f"Clustering gilt nur für PIR-Touren (Pirna). "
                   f"Tour '{tour_id}' ist keine PIR-Tour."
        )
    
    stops = tour_data["stops"]
    
    # Erstelle Parameter
    params_obj = PirnaClusterParams(
        depot_uid=request.depot_uid,
        depot_lat=request.depot_lat,
        depot_lon=request.depot_lon,
        max_stops_per_cluster=request.max_stops_per_cluster,
        max_time_per_cluster_minutes=request.max_time_per_cluster_minutes,
        service_time_default=request.service_time_default,
        service_time_per_stop=request.service_time_per_stop,
        include_return_to_depot=request.include_return_to_depot
    )
    
    # Clustering
    clusterer = PirnaClusterer(osrm_client)
    clusters = clusterer.cluster_stops(stops, params_obj)
    
    # Konvertiere zu Dict für Response
    cluster_dicts = []
    total_stops = 0
    total_time = 0.0
    
    for cluster in clusters:
        cluster_dicts.append({
            "cluster_id": cluster.cluster_id,
            "stops": cluster.stops,
            "center_lat": cluster.center_lat,
            "center_lon": cluster.center_lon,
            "estimated_stops_count": cluster.estimated_stops_count,
            "estimated_time_minutes": round(cluster.estimated_time_minutes, 2)
        })
        
        total_stops += cluster.estimated_stops_count
        total_time += cluster.estimated_time_minutes
    
    avg_stops_per_cluster = total_stops / len(clusters) if clusters else 0
    
    return PirnaClusterResponse(
        tour_uid=tour_uid,
        clusters=cluster_dicts,
        params={
            "max_stops_per_cluster": params_obj.max_stops_per_cluster,
            "max_time_per_cluster_minutes": params_obj.max_time_per_cluster_minutes,
            "service_time_default": params_obj.service_time_default
        },
        totals={
            "total_clusters": len(clusters),
            "total_stops": total_stops,
            "avg_stops_per_cluster": round(avg_stops_per_cluster, 1),
            "total_estimated_time_minutes": round(total_time, 2)
        }
    )

