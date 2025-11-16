"""
Routing-Optimizer Service
Bietet verschiedene Routing-Optimierungs-Algorithmen mit Fallback-Mechanismen
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import math
import time


@dataclass
class OptimizationMetrics:
    """Metriken für Routing-Optimierung"""
    total_duration_minutes: float
    gain_vs_nearest_neighbor_pct: float
    backend_used: str
    solver_used: str
    time_ms: int
    quality: str


@dataclass
class OptimizationResult:
    """Ergebnis einer Routing-Optimierung"""
    optimized_order: List[int]
    metrics: OptimizationMetrics
    warnings: Optional[List[str]] = None


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Berechnet Haversine-Distanz zwischen zwei Koordinaten (in km)"""
    R = 6371.0  # Erdradius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    return 2 * R * math.asin(math.sqrt(a))


def compute_local_haversine_matrix(
    points: List[Tuple[float, float]], 
    profile: str = "urban"
) -> List[List[float]]:
    """
    Berechnet Haversine-Distanz-Matrix für eine Liste von Punkten.
    
    Args:
        points: Liste von (lat, lon) Tupeln
        profile: Profil (wird aktuell ignoriert, für zukünftige Erweiterungen)
        
    Returns:
        2D-Liste mit Distanzen in km
    """
    n = len(points)
    matrix = [[0.0] * n for _ in range(n)]
    
    for i in range(n):
        for j in range(i + 1, n):
            dist = haversine_distance(points[i][0], points[i][1], points[j][0], points[j][1])
            matrix[i][j] = dist
            matrix[j][i] = dist
    
    return matrix


def nearest_neighbor(matrix: List[List[float]], start: int = 0) -> List[int]:
    """
    Nearest-Neighbor-Heuristik für TSP.
    
    Args:
        matrix: Distanz-Matrix (2D-Liste)
        start: Start-Index (Standard: 0)
        
    Returns:
        Liste von Indizes in optimierter Reihenfolge
    """
    n = len(matrix)
    if n <= 1:
        return [0] if n == 1 else []
    
    visited = {start}
    route = [start]
    current = start
    
    while len(visited) < n:
        nearest = None
        min_dist = float('inf')
        
        for j in range(n):
            if j not in visited:
                dist = matrix[current][j]
                if dist < min_dist:
                    min_dist = dist
                    nearest = j
        
        if nearest is not None:
            route.append(nearest)
            visited.add(nearest)
            current = nearest
        else:
            break
    
    return route


def optimize_route(
    stops: List[Dict],
    backend_priority: List[str] = ["osrm", "local_haversine"],
    osrm_client: Optional[object] = None,
    valhalla_url: Optional[str] = None,
    graphhopper_url: Optional[str] = None
) -> Optional[OptimizationResult]:
    """
    Optimiert Route mit verschiedenen Backends (OSRM, Valhalla, GraphHopper, Haversine).
    
    Args:
        stops: Liste von Stop-Dicts mit 'lat' und 'lon'
        backend_priority: Liste von Backend-Namen in Prioritätsreihenfolge
        osrm_client: OSRM-Client-Instanz (optional)
        valhalla_url: Valhalla-URL (optional, TODO)
        graphhopper_url: GraphHopper-URL (optional, TODO)
        
    Returns:
        OptimizationResult oder None bei Fehler
    """
    if not stops or len(stops) <= 1:
        return OptimizationResult(
            optimized_order=list(range(len(stops))),
            metrics=OptimizationMetrics(
                total_duration_minutes=0.0,
                gain_vs_nearest_neighbor_pct=0.0,
                backend_used="none",
                solver_used="identity",
                time_ms=0,
                quality="trivial"
            )
        )
    
    start_time = time.time()
    
    # Extrahiere Koordinaten
    points = []
    valid_indices = []
    for i, stop in enumerate(stops):
        lat = stop.get('lat')
        lon = stop.get('lon')
        if lat is not None and lon is not None:
            points.append((lat, lon))
            valid_indices.append(i)
    
    if len(points) <= 1:
        return OptimizationResult(
            optimized_order=list(range(len(stops))),
            metrics=OptimizationMetrics(
                total_duration_minutes=0.0,
                gain_vs_nearest_neighbor_pct=0.0,
                backend_used="none",
                solver_used="identity",
                time_ms=int((time.time() - start_time) * 1000),
                quality="trivial"
            )
        )
    
    # Versuche Backends in Prioritätsreihenfolge
    for backend in backend_priority:
        try:
            if backend == "osrm" and osrm_client:
                # TODO: OSRM-Matrix-basierte Optimierung
                # Für jetzt: Fallback auf Haversine
                pass
            elif backend == "local_haversine":
                # Haversine-basierte Nearest-Neighbor-Optimierung
                matrix = compute_local_haversine_matrix(points)
                optimized_indices = nearest_neighbor(matrix, start=0)
                
                # Berechne Metriken
                total_distance = 0.0
                for i in range(len(optimized_indices) - 1):
                    total_distance += matrix[optimized_indices[i]][optimized_indices[i + 1]]
                
                # Geschätzte Fahrzeit (50 km/h Durchschnitt)
                estimated_duration_minutes = (total_distance / 50.0) * 60.0
                
                # Mappe zurück auf ursprüngliche Indizes
                mapped_indices = [valid_indices[i] for i in optimized_indices if i < len(valid_indices)]
                
                return OptimizationResult(
                    optimized_order=mapped_indices,
                    metrics=OptimizationMetrics(
                        total_duration_minutes=estimated_duration_minutes,
                        gain_vs_nearest_neighbor_pct=0.0,  # NN ist bereits der Baseline
                        backend_used="local_haversine",
                        solver_used="nearest_neighbor",
                        time_ms=int((time.time() - start_time) * 1000),
                        quality="good"
                    )
                )
        except Exception as e:
            print(f"[ROUTING-OPTIMIZER] Backend {backend} fehlgeschlagen: {e}")
            continue
    
    # Fallback: Identität (keine Optimierung)
    return OptimizationResult(
        optimized_order=list(range(len(stops))),
        metrics=OptimizationMetrics(
            total_duration_minutes=0.0,
            gain_vs_nearest_neighbor_pct=0.0,
            backend_used="none",
            solver_used="identity",
            time_ms=int((time.time() - start_time) * 1000),
            quality="fallback"
        )
    )

