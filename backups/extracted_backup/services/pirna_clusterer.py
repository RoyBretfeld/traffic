"""
Pirna-Route Clustering

Problem: PIR-Touren haben meist > 4 Stopps und werden oft in zu viele 
kleine Routen aufgeteilt (z.B. 3 Personen mit je 3 Stopps).

Lösung: Gruppierung innerhalb der Pirna-Richtung nach geografischer Nähe,
damit weniger Routen mit mehr Stopps entstehen.
"""
import math
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass

from services.osrm_client import OSRMClient
from services.uid_service import generate_stop_uid

logger = logging.getLogger(__name__)


@dataclass
class PirnaClusterParams:
    """Parameter für Pirna-Clustering"""
    depot_uid: str
    depot_lat: float
    depot_lon: float
    max_stops_per_cluster: int = 15  # Max. Stopps pro Cluster (erhöht, damit nicht zu früh aufgeteilt wird)
    max_time_per_cluster_minutes: int = 120  # Max. Zeit pro Cluster (erhöht, damit mehr Stationen zusammen bleiben)
    service_time_default: float = 2.0
    service_time_per_stop: Dict[str, float] = None
    include_return_to_depot: bool = True
    
    def __post_init__(self):
        if self.service_time_per_stop is None:
            self.service_time_per_stop = {}


@dataclass
class PirnaCluster:
    """Ein Cluster von Stopps in Richtung Pirna"""
    cluster_id: int
    stops: List[Dict]  # Liste von Stopp-Dicts mit stop_uid, lat, lon
    center_lat: float
    center_lon: float
    estimated_stops_count: int
    estimated_time_minutes: float


class PirnaClusterer:
    """
    Clustering für PIR-Touren: Gruppiert Stopps nach geografischer Nähe,
    damit nicht zu viele kleine Routen entstehen.
    """
    
    def __init__(self, osrm_client: Optional[OSRMClient] = None):
        self.osrm_client = osrm_client or OSRMClient()
        self.logger = logging.getLogger(__name__)
    
    def _haversine_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine-Distanz in km"""
        R = 6371.0
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = lat2_rad - lat1_rad
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    
    def _calculate_center(self, stops: List[Dict]) -> Tuple[float, float]:
        """Berechnet geografisches Zentrum einer Stopp-Liste"""
        if not stops:
            return 0.0, 0.0
        
        total_lat = sum(s.get("lat", 0) for s in stops if s.get("lat"))
        total_lon = sum(s.get("lon", 0) for s in stops if s.get("lon"))
        count = len([s for s in stops if s.get("lat") and s.get("lon")])
        
        if count == 0:
            return 0.0, 0.0
        
        return total_lat / count, total_lon / count
    
    def _estimate_time_for_stops(
        self,
        stops: List[Dict],
        depot_lat: float,
        depot_lon: float,
        params: PirnaClusterParams
    ) -> float:
        """
        Schätzt Gesamtzeit für eine Liste von Stopps.
        Vereinfacht: Haversine-Distanzen × 1.3 (Stadtverkehr) + Service-Zeiten.
        """
        if not stops:
            return 0.0
        
        # Sortiere Stopps nach Entfernung vom Depot (vereinfacht)
        stops_with_coords = [(s, s.get("lat"), s.get("lon")) for s in stops if s.get("lat") and s.get("lon")]
        if not stops_with_coords:
            return len(stops) * params.service_time_default
        
        # Berechne Route: Depot → Stopps → Depot
        total_distance = 0.0
        
        # Depot → Erster Stop
        first_stop = stops_with_coords[0]
        dist_to_first = self._haversine_distance_km(
            depot_lat, depot_lon,
            first_stop[1], first_stop[2]
        )
        total_distance += dist_to_first
        
        # Stop → Stop
        for i in range(1, len(stops_with_coords)):
            prev = stops_with_coords[i-1]
            curr = stops_with_coords[i]
            dist = self._haversine_distance_km(prev[1], prev[2], curr[1], curr[2])
            total_distance += dist
        
        # Letzter Stop → Depot
        last_stop = stops_with_coords[-1]
        dist_from_last = self._haversine_distance_km(
            last_stop[1], last_stop[2],
            depot_lat, depot_lon
        )
        total_distance += dist_from_last
        
        # Fahrzeit (50 km/h Durchschnitt, × 1.3 für Stadtverkehr)
        adjusted_distance = total_distance * 1.3
        driving_time = (adjusted_distance / 50.0) * 60
        
        # Service-Zeit
        service_time = sum(
            params.service_time_per_stop.get(s[0].get("stop_uid"), params.service_time_default)
            for s in stops_with_coords
        )
        
        return driving_time + service_time
    
    def cluster_stops(
        self,
        stops: List[Dict],
        params: PirnaClusterParams
    ) -> List[PirnaCluster]:
        """
        Gruppiert Stopps in Richtung Pirna nach geografischer Nähe.
        
        Algorithmus:
        1. Sortiere Stopps nach Entfernung vom Depot (nähere zuerst)
        2. Erstelle Cluster: Füge Stopps hinzu bis max_stops oder max_time erreicht
        3. Neuer Cluster nur wenn Limit ERREICHT ist (nicht vorher aufteilen!)
        
        Ziel: Weniger Routen, mehr Stopps pro Route (verhindert 3 Personen mit je 3 Stopps)
        WICHTIG: Wenn 6 Stationen zusammen in die Zeit passen (z.B. 30 Min mehr), bleiben sie zusammen!
        """
        # Filtere Stopps mit Koordinaten
        stops_with_coords = [
            s for s in stops 
            if s.get("lat") and s.get("lon")
        ]
        
        if not stops_with_coords:
            self.logger.warning("Keine Stopps mit Koordinaten für Clustering")
            return []
        
        # Sortiere nach Entfernung vom Depot (nähere zuerst)
        def distance_from_depot(stop):
            lat = stop.get("lat")
            lon = stop.get("lon")
            return self._haversine_distance_km(
                params.depot_lat, params.depot_lon,
                lat, lon
            )
        
        sorted_stops = sorted(stops_with_coords, key=distance_from_depot)
        
        clusters = []
        current_cluster_stops = []
        cluster_id = 1
        
        for stop in sorted_stops:
            # Test: Würde dieser Stop in den aktuellen Cluster passen?
            test_cluster = current_cluster_stops + [stop]
            
            # Prüfe max_stops
            if len(test_cluster) > params.max_stops_per_cluster:
                # Aktueller Cluster voll → speichere und starte neuen
                if current_cluster_stops:
                    center_lat, center_lon = self._calculate_center(current_cluster_stops)
                    estimated_time = self._estimate_time_for_stops(
                        current_cluster_stops,
                        params.depot_lat,
                        params.depot_lon,
                        params
                    )
                    
                    cluster = PirnaCluster(
                        cluster_id=cluster_id,
                        stops=current_cluster_stops,
                        center_lat=center_lat,
                        center_lon=center_lon,
                        estimated_stops_count=len(current_cluster_stops),
                        estimated_time_minutes=estimated_time
                    )
                    clusters.append(cluster)
                    cluster_id += 1
                
                # Neuer Cluster mit diesem Stop
                current_cluster_stops = [stop]
                continue
            
            # Prüfe max_time
            estimated_time = self._estimate_time_for_stops(
                test_cluster,
                params.depot_lat,
                params.depot_lon,
                params
            )
            
            if estimated_time > params.max_time_per_cluster_minutes:
                # Zeit überschritten → speichere aktuellen Cluster
                if current_cluster_stops:
                    center_lat, center_lon = self._calculate_center(current_cluster_stops)
                    estimated_time_old = self._estimate_time_for_stops(
                        current_cluster_stops,
                        params.depot_lat,
                        params.depot_lon,
                        params
                    )
                    
                    cluster = PirnaCluster(
                        cluster_id=cluster_id,
                        stops=current_cluster_stops,
                        center_lat=center_lat,
                        center_lon=center_lon,
                        estimated_stops_count=len(current_cluster_stops),
                        estimated_time_minutes=estimated_time_old
                    )
                    clusters.append(cluster)
                    cluster_id += 1
                
                # Neuer Cluster mit diesem Stop
                current_cluster_stops = [stop]
                continue
            
            # Stop passt in aktuellen Cluster
            current_cluster_stops.append(stop)
        
        # Letzter Cluster (falls vorhanden)
        if current_cluster_stops:
            center_lat, center_lon = self._calculate_center(current_cluster_stops)
            estimated_time = self._estimate_time_for_stops(
                current_cluster_stops,
                params.depot_lat,
                params.depot_lon,
                params
            )
            
            cluster = PirnaCluster(
                cluster_id=cluster_id,
                stops=current_cluster_stops,
                center_lat=center_lat,
                center_lon=center_lon,
                estimated_stops_count=len(current_cluster_stops),
                estimated_time_minutes=estimated_time
            )
            clusters.append(cluster)
        
        self.logger.info(
            f"PIR-Tour: {len(stops_with_coords)} Stopps → {len(clusters)} Cluster "
            f"(Ø {sum(c.estimated_stops_count for c in clusters) / len(clusters):.1f} Stopps/Cluster)"
        )
        
        return clusters

