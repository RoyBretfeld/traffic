"""
Dresden-Quadranten & Zeitbox Planer

Ziel: Touren in Dresden vorstrukturieren durch Sektorisierung (N/O/S/W) 
und Zeitbox-Erzwingung (07:00 Start, 09:00 Rückkehr).
"""
import math
import logging
from typing import List, Dict, Optional, Tuple, Set
from dataclasses import dataclass
from enum import Enum

from services.osrm_client import OSRMClient
from services.uid_service import generate_stop_uid

logger = logging.getLogger(__name__)

# Optional: LLM-Import
try:
    from services.llm_optimizer import LLMOptimizer
    LLM_AVAILABLE = True
except ImportError:
    LLM_AVAILABLE = False
    logger.warning("LLMOptimizer nicht verfügbar, LLM-Integration deaktiviert")


def should_use_sector_planning(tour_id: str) -> bool:
    """
    Prüft, ob eine Tour die Sektor-Planung verwenden soll.
    
    Regel: Sektor-Planung gilt NUR für W-Touren, weil sie über das ganze 
    Dresden-Kreuz verteilt sind und in mehrere Richtungen (N/O/S/W) gehen.
    
    CB (Cottbus), BZ (Bautzen), PIR (Pirna) gehen in eine Richtung raus 
    aus Dresden und brauchen KEINE Sektorisierung.
    
    Args:
        tour_id: Tour-ID (z.B. "W-07.00 Uhr Tour")
    
    Returns:
        True wenn Sektor-Planung verwendet werden soll (nur W-Touren), sonst False
    """
    if not tour_id:
        return False
    
    tour_id_upper = tour_id.upper()
    
    # Prüfe auf W-Touren (über ganz Dresden-Kreuz verteilt)
    # Pattern: W-XX.XX oder W-XX.XX Uhr Tour
    import re
    if re.match(r'^W-\d+\.\d+', tour_id_upper):
        return True
    
    # CB, BZ, PIR brauchen KEINE Sektor-Planung
    # Sie gehen in eine Richtung raus aus Dresden
    
    return False


class Sector(Enum):
    """Himmelsrichtungen (4er-Kreuz oder 8er-Richtungen)"""
    N = "N"   # Norden: 315°-360° ∪ 0°-45°
    O = "O"   # Osten: 45°-135°
    S = "S"   # Süden: 135°-225°
    W = "W"   # Westen: 225°-315°
    
    # Optional: 8er-Richtungen
    NO = "NO"  # Nordost: 0°-45° (bereits N)
    SO = "SO"  # Südost: 135°-180°
    SW = "SW"  # Südwest: 225°-270°
    NW = "NW"  # Nordwest: 315°-360° (bereits N)


@dataclass
class SectorPlanParams:
    """Parameter für Sektor-Planung"""
    depot_uid: str
    depot_lat: float
    depot_lon: float
    start_time: str = "07:00"
    hard_deadline: str = "09:00"
    # Harte Timebox ohne Rückfahrt (DoD): 65 Minuten
    time_budget_minutes: int = 65
    # Depot‑Puffer bleibt 30 Min
    reload_buffer_minutes: int = 30
    service_time_default: float = 2.0
    service_time_per_stop: Dict[str, float] = None
    sectors: int = 4  # 4 oder 8
    include_return_to_depot: bool = True
    round: int = 2
    
    def __post_init__(self):
        if self.service_time_per_stop is None:
            self.service_time_per_stop = {}


@dataclass
class StopWithSector:
    """Stop mit Sektor-Zuordnung"""
    stop_uid: str
    lat: float
    lon: float
    sector: Sector
    bearing_deg: float
    distance_from_depot_km: Optional[float] = None


@dataclass
class RouteSegment:
    """Segment zwischen zwei Stopps"""
    from_uid: str
    to_uid: str
    km: float
    minutes: float
    source: str = "osrm"  # "osrm" oder "fallback_haversine"


@dataclass
class SectorRoute:
    """Eine Route in einem Sektor"""
    name: str  # z.B. "West A"
    sector: Sector
    route_uids: List[str]  # Depot → ... → Depot
    segments: List[RouteSegment]
    service_time_minutes: float
    driving_time_minutes: float
    total_time_minutes: float
    meta: Dict = None
    
    def __post_init__(self):
        if self.meta is None:
            self.meta = {}


class SectorPlanner:
    """
    Planer für Dresden-Quadranten & Zeitbox.
    
    Prinzipien:
    - OSRM-First (exakte Distanzen/Zeiten)
    - Deterministische Sektorzuordnung
    - Greedy-Routenbauung pro Sektor
    - Zeitbox-Validierung (07:00 → 09:00)
    """
    
    def __init__(self, osrm_client: Optional[OSRMClient] = None, llm_optimizer=None):
        self.osrm_client = osrm_client or OSRMClient()
        self.logger = logging.getLogger(__name__)
        
        # LLM-Integration (optional)
        if llm_optimizer is None and LLM_AVAILABLE:
            try:
                self.llm_optimizer = LLMOptimizer()
                self.llm_enabled = self.llm_optimizer.enabled if hasattr(self.llm_optimizer, 'enabled') else False
            except Exception as e:
                self.logger.warning(f"LLM-Optimizer konnte nicht initialisiert werden: {e}")
                self.llm_optimizer = None
                self.llm_enabled = False
        else:
            self.llm_optimizer = llm_optimizer
            self.llm_enabled = self.llm_optimizer.enabled if (llm_optimizer and hasattr(llm_optimizer, 'enabled')) else False
        
        # Telemetrie
        self.metrics = {
            "osrm_calls": 0,
            "osrm_unavailable": 0,
            "fallback_haversine": 0,
            "timebox_violations": 0,
            "llm_calls": 0,
            "llm_invalid_schema": 0,
            "llm_decision_usage": {"llm": 0, "heuristic": 0},
            "routes_by_sector": {}
        }
    
    def calculate_bearing(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Berechnet Bearing/Azimut vom ersten Punkt zum zweiten Punkt.
        
        Formel:
        θ = atan2( sin(Δλ)*cos(φ2), cos(φ1)*sin(φ2) − sin(φ1)*cos(φ2)*cos(Δλ) )
        θ_deg = (θ * 180/π + 360) mod 360
        
        Returns:
            Bearing in Grad (0° = Norden, 90° = Osten, 180° = Süden, 270° = Westen)
        """
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlon_rad = math.radians(lon2 - lon1)
        
        y = math.sin(dlon_rad) * math.cos(lat2_rad)
        x = (math.cos(lat1_rad) * math.sin(lat2_rad) - 
             math.sin(lat1_rad) * math.cos(lat2_rad) * math.cos(dlon_rad))
        
        bearing_rad = math.atan2(y, x)
        bearing_deg = math.degrees(bearing_rad)
        
        # Normalisiere auf 0-360°
        bearing_deg = (bearing_deg + 360) % 360
        
        return bearing_deg
    
    def assign_sector(self, bearing_deg: float, sectors: int = 4) -> Sector:
        """
        Ordnet einen Bearing einem Sektor zu.
        
        Für 4er-Kreuz:
        - N: 315°-360° ∪ 0°-45°
        - O: 45°-135°
        - S: 135°-225°
        - W: 225°-315°
        
        Kantenfall: Liegt θ exakt auf Achse (z.B. 45°), ordne deterministisch 
        zum links folgenden Sektor zu (O→N).
        """
        if sectors == 4:
            # 4er-Kreuz
            if bearing_deg >= 315 or bearing_deg < 45:
                return Sector.N
            elif bearing_deg >= 45 and bearing_deg < 135:
                # Kantenfall 45°: O → N (links)
                if bearing_deg == 45:
                    return Sector.N
                # Kantenfall 135°: O → S (links)
                if bearing_deg == 135:
                    return Sector.S
                return Sector.O
            elif bearing_deg >= 135 and bearing_deg < 225:
                # Kantenfall 225°: S → W (links)
                if bearing_deg == 225:
                    return Sector.W
                return Sector.S
            elif bearing_deg >= 225 and bearing_deg < 315:
                # Kantenfall 315°: W → N (links)
                if bearing_deg == 315:
                    return Sector.N
                return Sector.W
            else:
                # Fallback: N
                return Sector.N
        elif sectors == 8:
            # 8er-Richtungen (45° Breite)
            # TODO: Implementierung für 8er-Sektoren
            sector_idx = int(bearing_deg / 45) % 8
            sectors_8 = [Sector.N, Sector.NO, Sector.O, Sector.SO, Sector.S, Sector.SW, Sector.W, Sector.NW]
            return sectors_8[sector_idx]
        else:
            raise ValueError(f"Unsupported sectors count: {sectors}")
    
    def sectorize_stops(
        self,
        stops: List[Dict],
        depot_lat: float,
        depot_lon: float,
        sectors: int = 4
    ) -> List[StopWithSector]:
        """
        Weist allen Stopps Sektoren zu (Sektorisierung).
        
        Args:
            stops: Liste von Stop-Dicts mit stop_uid, lat, lon
            depot_lat: Depot-Breitengrad
            depot_lon: Depot-Längengrad
            sectors: Anzahl Sektoren (4 oder 8)
        
        Returns:
            Liste von StopWithSector mit Sektor-Zuordnung
        """
        stop_with_sectors = []
        
        for stop in stops:
            stop_uid = stop.get("stop_uid")
            lat = stop.get("lat")
            lon = stop.get("lon")
            
            if not (lat and lon):
                self.logger.warning(f"Stop {stop_uid} hat keine Koordinaten, überspringe")
                continue
            
            # Berechne Bearing vom Depot zum Stop
            bearing_deg = self.calculate_bearing(depot_lat, depot_lon, lat, lon)
            
            # Ordne Sektor zu
            sector = self.assign_sector(bearing_deg, sectors)
            
            # Berechne Distanz vom Depot (Haversine als Näherung)
            distance_km = self._haversine_distance_km(depot_lat, depot_lon, lat, lon)
            
            stop_with_sector = StopWithSector(
                stop_uid=stop_uid,
                lat=lat,
                lon=lon,
                sector=sector,
                bearing_deg=bearing_deg,
                distance_from_depot_km=distance_km
            )
            
            stop_with_sectors.append(stop_with_sector)
        
        return stop_with_sectors
    
    def _haversine_distance_km(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine-Distanz in km (Fallback)"""
        R = 6371.0
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        dlat = lat2_rad - lat1_rad
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    
    def _get_service_time(self, stop_uid: str, params: SectorPlanParams) -> float:
        """Holt Service-Zeit für einen Stop (override oder default)"""
        return params.service_time_per_stop.get(stop_uid, params.service_time_default)
    
    def _get_osrm_table_for_candidates(
        self,
        current_lat: float,
        current_lon: float,
        candidates: List[StopWithSector]
    ) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Holt OSRM Table für Kandidaten vom aktuellen Punkt.
        
        Betriebsordnung §4: 
        GET /table/v1/driving/{coords}?annotations=duration&sources=0&destinations=1;2;3;...
        
        Returns:
            Dict mit {stop_uid: {"minutes": ..., "km": ...}} oder None
        """
        if not candidates:
            return None
        
        # Erstelle Koordinaten-Liste: [current, candidate1, candidate2, ...]
        coords = [(current_lat, current_lon)]
        for cand in candidates:
            coords.append((cand.lat, cand.lon))
        
        # OSRM Table API: sources=0 (nur aktueller Punkt), destinations=1,2,3,... (alle Kandidaten)
        try:
            sources = [0]  # Nur vom aktuellen Punkt
            destinations = list(range(1, len(coords)))  # Alle Kandidaten
            
            distance_matrix = self.osrm_client.get_distance_matrix(
                coords,
                sources=sources,
                destinations=destinations
            )
            
            if not distance_matrix:
                self.metrics["osrm_unavailable"] += 1
                return None
            
            self.metrics["osrm_calls"] += 1
            
            # Konvertiere Matrix-Format zu Dict
            result = {}
            for i, cand in enumerate(candidates):
                # Matrix-Index: (0, i+1) weil current=0 (source), cand1=1, cand2=2, ... (destinations)
                key = (0, i + 1)
                seg_data = distance_matrix.get(key)
                
                if seg_data:
                    result[cand.stop_uid] = {
                        "km": seg_data.get("km", 0),
                        "minutes": seg_data.get("minutes", 0)
                    }
            
            return result
            
        except Exception as e:
            self.logger.warning(f"OSRM Table API Fehler: {e}")
            self.metrics["osrm_unavailable"] += 1
            return None
    
    def _get_distance_fallback(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float
    ) -> Tuple[float, float]:
        """Fallback: Haversine × 1.3 für Distanz und Zeit"""
        distance_km = self._haversine_distance_km(lat1, lon1, lat2, lon2) * 1.3
        minutes = (distance_km / 50.0) * 60
        return round(distance_km, 2), round(minutes, 2)
    
    def plan_by_sector(
        self,
        stops_with_sectors: List[StopWithSector],
        params: SectorPlanParams
    ) -> List[SectorRoute]:
        """
        Plant Routen pro Sektor mit Greedy-Algorithmus und Zeitbox.
        
        Args:
            stops_with_sectors: Stopps mit Sektor-Zuordnung
            params: Planungs-Parameter
        
        Returns:
            Liste von SectorRoute (mehrere Routen pro Sektor möglich)
        """
        # Gruppiere Stopps nach Sektor
        stops_by_sector: Dict[Sector, List[StopWithSector]] = {}
        for stop in stops_with_sectors:
            sector = stop.sector
            if sector not in stops_by_sector:
                stops_by_sector[sector] = []
            stops_by_sector[sector].append(stop)
        
        all_routes = []
        
        # Plane jeden Sektor
        for sector, sector_stops in stops_by_sector.items():
            # Sortier-Seed: Primär Entfernung, sekundär Winkel, tertiär stop_uid
            sorted_stops = sorted(
                sector_stops,
                key=lambda s: (
                    s.distance_from_depot_km or float('inf'),
                    s.bearing_deg,
                    s.stop_uid
                )
            )
            
            # Plane Routen in diesem Sektor
            sector_routes = self._plan_sector_greedy(
                sorted_stops,
                params,
                sector
            )
            
            all_routes.extend(sector_routes)
            
            # Telemetrie
            self.metrics["routes_by_sector"][sector.value] = len(sector_routes)
        
        return all_routes
    
    def _plan_sector_greedy(
        self,
        stops: List[StopWithSector],
        params: SectorPlanParams,
        sector: Sector
    ) -> List[SectorRoute]:
        """
        Greedy-Planung für einen Sektor.
        
        Pseudocode:
        - Start: Depot
        - Wähle nächsten Kandidaten per OSRM-Table
        - Addiere Segment + Service-Zeit
        - Cut wenn Zeitbox überschritten → neue Route
        """
        routes = []
        remaining = stops.copy()
        route_counter = 0
        
        while remaining:
            # Neue Route starten
            route_counter += 1
            route_name = f"{sector.value} {chr(64 + route_counter)}"  # A, B, C, ...
            
            current_lat = params.depot_lat
            current_lon = params.depot_lon
            current_uid = params.depot_uid
            
            route_uids = [params.depot_uid]
            segments = []
            driving_time = 0.0
            service_time = 0.0
            
            while remaining:
                # Hole OSRM Table für alle verbleibenden Kandidaten
                osrm_table = self._get_osrm_table_for_candidates(
                    current_lat,
                    current_lon,
                    remaining
                )
                
                # Finde besten Kandidaten (Greedy: kürzeste Fahrzeit)
                candidates_with_data = []
                
                for cand in remaining:
                    # Hole Distanz/Minuten
                    if osrm_table and cand.stop_uid in osrm_table:
                        seg_data = osrm_table[cand.stop_uid]
                        seg_minutes = seg_data["minutes"]
                        seg_km = seg_data["km"]
                        source = "osrm"
                    else:
                        # Fallback: Haversine
                        seg_km, seg_minutes = self._get_distance_fallback(
                            current_lat, current_lon,
                            cand.lat, cand.lon
                        )
                        source = "fallback_haversine"
                        self.metrics["fallback_haversine"] += 1
                    
                    candidates_with_data.append({
                        "candidate": cand,
                        "km": seg_km,
                        "minutes": seg_minutes,
                        "source": source
                    })
                
                # Optional: LLM für Entscheidung zwischen mehreren guten Kandidaten
                # Betriebsordnung §6: LLM nur für Entscheidung, strikt validiert
                best_candidate = None
                best_segment = None
                
                if len(candidates_with_data) > 1:
                    # Sortiere nach Fahrzeit (kürzeste zuerst)
                    candidates_with_data.sort(key=lambda x: x["minutes"])
                    
                    # LLM-Integration: Nur wenn mehrere ähnlich gute Kandidaten vorhanden
                    # (z.B. wenn Top-3 alle innerhalb von 2 Minuten liegen)
                    use_llm = False
                    if self.llm_enabled and len(candidates_with_data) >= 2:
                        top_minutes = candidates_with_data[0]["minutes"]
                        # Wenn mehrere Kandidaten sehr nah beieinander sind (innerhalb 2 Min), frage LLM
                        similar_candidates = [
                            c for c in candidates_with_data[:3]  # Top 3
                            if abs(c["minutes"] - top_minutes) <= 2.0  # Innerhalb 2 Minuten
                        ]
                        if len(similar_candidates) >= 2:
                            use_llm = True
                    
                    if use_llm:
                        try:
                            # LLM-Entscheidung zwischen ähnlich guten Kandidaten
                            self.metrics["llm_calls"] += 1
                            best_data = self._llm_choose_best_candidate(
                                current_uid, candidates_with_data[:3], route_uids
                            )
                            if best_data:
                                self.metrics["llm_decision_usage"]["llm"] += 1
                            else:
                                # Fallback bei LLM-Fehler
                                best_data = candidates_with_data[0]
                                self.metrics["llm_invalid_schema"] += 1
                                self.metrics["llm_decision_usage"]["heuristic"] += 1
                        except Exception as e:
                            self.logger.warning(f"LLM-Entscheidung fehlgeschlagen: {e}, verwende Heuristik")
                            best_data = candidates_with_data[0]
                            self.metrics["llm_invalid_schema"] += 1
                            self.metrics["llm_decision_usage"]["heuristic"] += 1
                    else:
                        # Heuristik: Wähle kürzesten
                        best_data = candidates_with_data[0]
                        self.metrics["llm_decision_usage"]["heuristic"] += 1
                else:
                    best_data = candidates_with_data[0] if candidates_with_data else None
                    if best_data:
                        self.metrics["llm_decision_usage"]["heuristic"] += 1
                
                if best_data:
                    best_candidate = best_data["candidate"]
                    best_segment = {
                        "from_uid": current_uid,
                        "to_uid": best_candidate.stop_uid,
                        "km": best_data["km"],
                        "minutes": best_data["minutes"],
                        "source": best_data["source"]
                    }
                
                if not best_candidate:
                    break
                
                # Prüfe Zeitbox
                # WICHTIG: Regel ist OHNE Rückfahrt ≤ 65 Min (nicht 90 Min mit Rückfahrt!)
                # Die Zeitbox (90 Min) ist für Gesamtzeit INKL. Rückfahrt gedacht
                # Aber die eigentliche Regel ist: Fahrzeit + Servicezeit ≤ 65 Min (OHNE Rückfahrt)
                cand_service_time = self._get_service_time(best_candidate.stop_uid, params)
                
                # Zeit OHNE Rückfahrt (für die eigentliche Regel)
                time_without_return = (driving_time + best_segment["minutes"] + service_time + cand_service_time)
                
                # Rückfahrt (nur für Zeitbox-Prüfung)
                if params.include_return_to_depot:
                    return_km, return_minutes = self._get_distance_fallback(
                        best_candidate.lat, best_candidate.lon,
                        params.depot_lat, params.depot_lon
                    )
                else:
                    return_minutes = 0.0
                
                # Gesamtzeit INKL. Rückfahrt (für Zeitbox)
                total_with_return = time_without_return + return_minutes
                
                # KRITISCH: Prüfe zuerst die eigentliche Regel (OHNE Rückfahrt ≤ 65 Min)
                MAX_TIME_WITHOUT_RETURN = 65.0  # Minuten OHNE Rückfahrt (Hard Limit)
                if time_without_return >= MAX_TIME_WITHOUT_RETURN:  # ✅ >= statt > (strengere Prüfung)
                    # Regel überschritten → Cut (auch bei genau 65.0 Min stoppen)
                    self.metrics["timebox_violations"] += 1
                    break
                
                # Dann prüfe Zeitbox (INKL. Rückfahrt ≤ 90 Min)
                RECOMMENDED_MAX_WITH_RETURN = 80.0  # Empfohlenes Maximum (Puffer für andere Routen)
                MAX_TIME_WITH_RETURN = params.time_budget_minutes  # Hard Limit: 90 Min
                
                if total_with_return >= MAX_TIME_WITH_RETURN:  # ✅ >= statt > (strengere Prüfung)
                    # Zeitbox überschritten → Cut (auch bei genau 90.0 Min stoppen)
                    self.metrics["timebox_violations"] += 1
                    break
                
                # ⚠️ Warnung wenn Route >80 Min (empfohlenes Maximum)
                if total_with_return > RECOMMENDED_MAX_WITH_RETURN:
                    self.logger.debug(
                        f"⚠️ Route '{route_name}' würde empfohlenes Maximum von 80 Min überschreiten: "
                        f"{total_with_return:.1f} Min (wird aber noch akzeptiert, Limit: 90 Min)"
                    )
                
                # Akzeptiere Kandidaten
                route_uids.append(best_candidate.stop_uid)
                segments.append(RouteSegment(**best_segment))
                driving_time += best_segment["minutes"]
                service_time += cand_service_time
                
                # ✅ WICHTIG: Prüfe AKTUELLE Route nach jedem hinzugefügten Stop!
                # Berechne aktuelle Route-Zeit OHNE Rückfahrt
                current_time_without_return = driving_time + service_time
                
                # Berechne geschätzte Rückfahrt vom aktuellen Stop
                if params.include_return_to_depot:
                    current_return_km, current_return_minutes = self._get_distance_fallback(
                        best_candidate.lat, best_candidate.lon,
                        params.depot_lat, params.depot_lon
                    )
                else:
                    current_return_minutes = 0.0
                
                current_total_with_return = current_time_without_return + current_return_minutes
                
                # KRITISCH: Prüfe AKTUELLE Route (nicht nur nächsten Kandidaten)!
                MAX_TIME_WITHOUT_RETURN = 65.0  # Hard Limit: OHNE Rückfahrt
                RECOMMENDED_MAX_WITH_RETURN = 80.0  # Empfohlenes Maximum: INKL. Rückfahrt (Puffer für andere Routen)
                MAX_TIME_WITH_RETURN = params.time_budget_minutes  # Hard Limit: INKL. Rückfahrt (90 Min)
                
                if current_time_without_return > MAX_TIME_WITHOUT_RETURN:
                    # Aktuelle Route ist bereits zu lang OHNE Rückfahrt!
                    # Entferne letzten Stop und stoppe Route
                    self.logger.warning(
                        f"⚠️ Route '{route_name}' überschreitet 65 Min OHNE Rückfahrt "
                        f"nach Hinzufügen von Stop {best_candidate.stop_uid}: "
                        f"{current_time_without_return:.1f} Min. Stop wird entfernt und Route gestoppt."
                    )
                    route_uids.pop()
                    segments.pop()
                    driving_time -= best_segment["minutes"]
                    service_time -= cand_service_time
                    remaining.append(best_candidate)  # Stop zurück in Warteschlange
                    self.metrics["timebox_violations"] += 1
                    break  # Route ist voll - stoppe diese Route
                
                if current_total_with_return > MAX_TIME_WITH_RETURN:
                    # Aktuelle Route ist bereits zu lang INKL. Rückfahrt (>90 Min)!
                    # Entferne letzten Stop und stoppe Route
                    self.logger.warning(
                        f"⚠️ Route '{route_name}' überschreitet 90 Min INKL. Rückfahrt "
                        f"nach Hinzufügen von Stop {best_candidate.stop_uid}: "
                        f"{current_total_with_return:.1f} Min. Stop wird entfernt und Route gestoppt."
                    )
                    route_uids.pop()
                    segments.pop()
                    driving_time -= best_segment["minutes"]
                    service_time -= cand_service_time
                    remaining.append(best_candidate)  # Stop zurück in Warteschlange
                    self.metrics["timebox_violations"] += 1
                    break  # Route ist voll - stoppe diese Route
                
                # ⚠️ Warnung wenn Route >80 Min (empfohlenes Maximum für Puffer)
                if current_total_with_return > RECOMMENDED_MAX_WITH_RETURN:
                    self.logger.warning(
                        f"⚠️ Route '{route_name}' überschreitet empfohlenes Maximum von 80 Min: "
                        f"{current_total_with_return:.1f} Min. Route wird erstellt, aber Puffer für andere Routen fehlt."
                    )
                
                # Aktualisiere aktuellen Punkt
                current_lat = best_candidate.lat
                current_lon = best_candidate.lon
                current_uid = best_candidate.stop_uid
                
                remaining.remove(best_candidate)
            
            # Rückfahrt zum Depot
            if params.include_return_to_depot and route_uids[-1] != params.depot_uid:
                # Berechne Rückfahrt
                if segments:
                    last_stop = next((s for s in stops if s.stop_uid == route_uids[-1]), None)
                    if last_stop:
                        return_km, return_minutes = self._get_distance_fallback(
                            last_stop.lat, last_stop.lon,
                            params.depot_lat, params.depot_lon
                        )
                        
                        segments.append(RouteSegment(
                            from_uid=route_uids[-1],
                            to_uid=params.depot_uid,
                            km=return_km,
                            minutes=return_minutes,
                            source="fallback_haversine"
                        ))
                        driving_time += return_minutes
                        route_uids.append(params.depot_uid)
            
            # WICHTIG: Berechne finale Zeiten korrekt
            # driving_time enthält alle Segmente (inkl. Rückfahrt wenn vorhanden)
            # Für total_time_minutes: Fahrzeit OHNE Rückfahrt + Servicezeit (für Anzeige)
            
            # Trenne Rückfahrt von Fahrzeit für korrekte Berechnung
            driving_time_without_return = driving_time
            return_time_final = 0.0
            if params.include_return_to_depot and segments and route_uids and route_uids[-1] == params.depot_uid:
                # Rückfahrt wurde bereits zu driving_time addiert (Zeile 631)
                # Subtrahiere sie wieder für korrekte Berechnung
                last_segment = segments[-1]
                if last_segment.to_uid == params.depot_uid:
                    return_time_final = last_segment.minutes
                    driving_time_without_return = driving_time - return_time_final
            elif params.include_return_to_depot and route_uids and len(route_uids) > 1:
                # WICHTIG: Wenn keine Rückfahrt in segments, berechne sie vom letzten tatsächlichen Stop
                # (nicht vom Kandidaten während der Planung!)
                last_stop_uid = route_uids[-1]
                if last_stop_uid != params.depot_uid:
                    # Finde letzten Stop in stops-Liste
                    last_stop = next((s for s in stops if s.stop_uid == last_stop_uid), None)
                    if last_stop:
                        return_km, return_minutes = self._get_distance_fallback(
                            last_stop.lat, last_stop.lon,
                            params.depot_lat, params.depot_lon
                        )
                        return_time_final = return_minutes
                        # Füge Rückfahrt-Segment hinzu
                        if segments:
                            segments.append(RouteSegment(
                                from_uid=last_stop_uid,
                                to_uid=params.depot_uid,
                                km=return_km,
                                minutes=return_minutes,
                                source="fallback_haversine"
                            ))
                            route_uids.append(params.depot_uid)
            
            # Berechne finale Zeiten
            time_without_return_final = driving_time_without_return + service_time
            total_with_return_final = time_without_return_final + return_time_final
            
            # ✅ VALIDIERUNG: Prüfe ob Route Constraints erfüllt (nach Erstellung)
            MAX_TIME_WITHOUT_RETURN = 65.0  # Hard Limit: OHNE Rückfahrt
            RECOMMENDED_MAX_WITH_RETURN = 80.0  # Empfohlenes Maximum: INKL. Rückfahrt (Puffer für andere Routen)
            MAX_TIME_WITH_RETURN = params.time_budget_minutes  # Hard Limit: INKL. Rückfahrt (90 Min)
            route_exceeds_limits = False
            
            if time_without_return_final > MAX_TIME_WITHOUT_RETURN:
                self.logger.error(
                    f"❌ KRITISCH: Route '{route_name}' überschreitet 65 Min OHNE Rückfahrt: "
                    f"{time_without_return_final:.1f} Min (Limit: {MAX_TIME_WITHOUT_RETURN} Min)"
                )
                route_exceeds_limits = True
            
            if total_with_return_final > MAX_TIME_WITH_RETURN:
                self.logger.error(
                    f"❌ KRITISCH: Route '{route_name}' überschreitet 90 Min INKL. Rückfahrt: "
                    f"{total_with_return_final:.1f} Min (Limit: {MAX_TIME_WITH_RETURN} Min)"
                )
                route_exceeds_limits = True
            
            # ⚠️ Warnung wenn Route >80 Min (empfohlenes Maximum für Puffer)
            exceeds_recommended = total_with_return_final > RECOMMENDED_MAX_WITH_RETURN
            if exceeds_recommended and total_with_return_final <= MAX_TIME_WITH_RETURN:
                self.logger.warning(
                    f"⚠️ Route '{route_name}' überschreitet empfohlenes Maximum von 80 Min: "
                    f"{total_with_return_final:.1f} Min. Route wird erstellt, aber Puffer für andere Routen fehlt."
                )
            
            # ❌ WICHTIG: Route NICHT erstellen wenn Limits überschritten!
            # Stopps zurück in remaining geben und Route aufteilen
            if route_exceeds_limits:
                self.logger.warning(
                    f"⚠️ Route '{route_name}' überschreitet Limits - Route wird NICHT erstellt. "
                    f"Stopps werden zurück in Warteschlange gegeben für Aufteilung."
                )
                
                # Stopps zurück in remaining geben (außer Depot)
                for uid in route_uids:
                    if uid != params.depot_uid:
                        stop = next((s for s in stops if s.stop_uid == uid), None)
                        if stop and stop not in remaining:
                            remaining.append(stop)
                
                # Route nicht erstellen - überspringe diese Iteration
                # Wenn keine Route erstellt werden kann → Endlosschleife vermeiden
                if len(route_uids) <= 1:  # Nur Depot oder gar keine Stopps
                    self.logger.error(
                        f"❌ FEHLER: Route kann nicht erstellt werden - einzelner Stop überschreitet Limits. "
                        f"Stop wird trotzdem hinzugefügt, aber mit Warnung."
                    )
                    # Fallback: Erstelle Route trotzdem (besser als Endlosschleife)
                    route = SectorRoute(
                        name=route_name,
                        sector=sector,
                        route_uids=route_uids,
                        segments=segments,
                        service_time_minutes=service_time,
                        driving_time_minutes=round(driving_time_without_return, params.round),
                        total_time_minutes=round(time_without_return_final, params.round),
                        meta={
                            "source": "osrm" if segments and segments[0].source == "osrm" else "fallback_haversine",
                            "llm_choices": self.metrics["llm_decision_usage"]["llm"],
                            "return_time_minutes": round(return_time_final, params.round),
                            "total_time_with_return": round(total_with_return_final, params.round),
                            "validated": False,  # NICHT validiert
                            "exceeds_limits": True,  # Flag: Route überschreitet Limits
                            "exceeds_recommended": total_with_return_final > 80.0
                        }
                    )
                    routes.append(route)
                    if not remaining:
                        break
                    continue
                
                # Versuche Route erneut mit weniger Stopps (Rückwärts durchgehen)
                # Entferne letzten Stop und versuche es nochmal
                if len(route_uids) > 1:
                    last_uid = route_uids[-1]
                    if last_uid != params.depot_uid:
                        stop = next((s for s in stops if s.stop_uid == last_uid), None)
                        if stop and stop not in remaining:
                            remaining.append(stop)
                            route_uids.pop()
                            if segments:
                                removed_segment = segments.pop()
                                driving_time -= removed_segment.minutes
                                # Service-Zeit des entfernten Stopps abziehen
                                removed_service_time = self._get_service_time(last_uid, params)
                                service_time -= removed_service_time
                                # Rekalkuliere Zeiten ohne letzten Stop
                                driving_time_without_return = driving_time
                                # Rückfahrt neu berechnen vom neuen letzten Stop
                                if route_uids and len(route_uids) > 1:
                                    new_last_uid = route_uids[-1]
                                    if new_last_uid != params.depot_uid:
                                        new_last_stop = next((s for s in stops if s.stop_uid == new_last_uid), None)
                                        if new_last_stop:
                                            return_km, return_minutes_new = self._get_distance_fallback(
                                                new_last_stop.lat, new_last_stop.lon,
                                                params.depot_lat, params.depot_lon
                                            )
                                            return_time_final = return_minutes_new
                                else:
                                    return_time_final = 0.0
                                
                                time_without_return_final = driving_time_without_return + service_time
                                total_with_return_final = time_without_return_final + return_time_final
                                
                                # Prüfe nochmal ob jetzt OK
                                if time_without_return_final <= MAX_TIME_WITHOUT_RETURN and total_with_return_final <= params.time_budget_minutes:
                                    # Jetzt OK → erstelle Route
                                    route = SectorRoute(
                                        name=route_name,
                                        sector=sector,
                                        route_uids=route_uids,
                                        segments=segments,
                                        service_time_minutes=service_time,
                                        driving_time_minutes=round(driving_time_without_return, params.round),
                                        total_time_minutes=round(time_without_return_final, params.round),
                                        meta={
                                            "source": "osrm" if segments and segments[0].source == "osrm" else "fallback_haversine",
                                            "llm_choices": self.metrics["llm_decision_usage"]["llm"],
                                            "return_time_minutes": round(return_time_final, params.round),
                                            "total_time_with_return": round(total_with_return_final, params.round),
                                            "validated": True,
                                            "exceeds_recommended": total_with_return_final > 80.0
                                        }
                                    )
                                    routes.append(route)
                                    if not remaining:
                                        break
                                    continue
                
                # Wenn auch nach Entfernen noch zu lang → überspringe diese Route komplett
                # Neue Route wird in nächster Iteration versucht
                continue
            
            # Route ist OK → erstelle sie
            route = SectorRoute(
                name=route_name,
                sector=sector,
                route_uids=route_uids,
                segments=segments,
                service_time_minutes=service_time,
                driving_time_minutes=round(driving_time_without_return, params.round),  # OHNE Rückfahrt
                total_time_minutes=round(time_without_return_final, params.round),  # OHNE Rückfahrt
                meta={
                    "source": "osrm" if segments and segments[0].source == "osrm" else "fallback_haversine",
                    "llm_choices": self.metrics["llm_decision_usage"]["llm"],
                    "return_time_minutes": round(return_time_final, params.round),  # Rückfahrt separat
                    "total_time_with_return": round(total_with_return_final, params.round),  # INKL. Rückfahrt
                    "validated": True,  # ✅ Route ist validiert
                    "exceeds_recommended": total_with_return_final > 80.0  # Flag: Überschreitet empfohlenes Maximum (80 Min)
                }
            )
            
            routes.append(route)
            
            if not remaining:
                break
        
        return routes
    
    def _llm_choose_best_candidate(
        self,
        current_uid: str,
        candidates_with_data: List[Dict],
        route_so_far: List[str]
    ) -> Optional[Dict]:
        """
        LLM-Entscheidung zwischen mehreren ähnlich guten Kandidaten.
        
        Betriebsordnung §6: Strikt validiert, nur aus Kandidatenliste wählen.
        
        Args:
            current_uid: UID des aktuellen Stopps
            candidates_with_data: Liste mit {candidate, km, minutes, source}
            route_so_far: Liste der bereits besuchten stop_uid's
        
        Returns:
            Bestes candidate_data Dict oder None bei Fehler
        """
        if not self.llm_optimizer or not self.llm_enabled:
            return None
        
        try:
            # Baue Prompt für LLM
            candidates_info = []
            for i, cand_data in enumerate(candidates_with_data):
                cand = cand_data["candidate"]
                candidates_info.append({
                    "index": i,
                    "stop_uid": cand.stop_uid,
                    "km": cand_data["km"],
                    "minutes": cand_data["minutes"],
                    "address": f"{cand.street}, {cand.postal_code} {cand.city}" if cand.street else f"{cand.postal_code} {cand.city}"
                })
            
            prompt = f"""Du wählst den nächsten Stopp für eine Route in Dresden.

Aktueller Punkt: {current_uid}
Bereits besuchte Stopps: {len(route_so_far)} Stopps

Kandidaten (alle ähnlich schnell, ~2 Min Unterschied):
{chr(10).join([f"{i+1}. {c['stop_uid']}: {c['km']} km, {c['minutes']} Min → {c['address']}" for i, c in enumerate(candidates_info)])}

Wähle den BESTEN nächsten Stopp basierend auf:
1. Logische Reihenfolge (keine Rückwege)
2. Minimale Gesamt-Fahrzeit
3. Geografische Nähe zu Depot-Richtung

Antworte NUR mit JSON:
{{
  "choose": "<stop_uid>",
  "reasoning": "Kurze Begründung (1 Satz)"
}}"""

            # LLM-Call
            response = self.llm_optimizer.client.chat.completions.create(
                model=self.llm_optimizer.model,
                messages=[
                    {"role": "system", "content": "Du bist ein Routenplanungs-Experte. Antworte nur mit gültigem JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=200,
                response_format={"type": "json_object"}
            )
            
            response_text = response.choices[0].message.content
            import json
            result = json.loads(response_text)
            
            chosen_uid = result.get("choose", "").strip()
            
            # VALIDIERUNG: chosen_uid muss in candidates_with_data sein
            for cand_data in candidates_with_data:
                if cand_data["candidate"].stop_uid == chosen_uid:
                    self.logger.debug(f"LLM wählte: {chosen_uid} (Reasoning: {result.get('reasoning', 'N/A')})")
                    return cand_data
            
            # Invalid: chosen_uid nicht in Liste
            self.logger.warning(f"LLM wählte ungültigen stop_uid: {chosen_uid}, nicht in Kandidatenliste")
            return None
            
        except Exception as e:
            self.logger.warning(f"LLM-Entscheidung Fehler: {e}")
            return None

