"""
Live-Traffic-Daten Service
Holt Baustellen, Unfälle und Sperrungen und integriert sie in die Routen-Optimierung.

Datenquellen:
- OpenStreetMap Overpass API - Autobahn-Baustellen und Sperrungen
- Externe API (konfigurierbar über AUTOBAHN_API_URL und AUTOBAHN_API_KEY)
- Eigene Datenbank für gespeicherte Hindernisse
- Mock-Daten (nur im Test-Modus mit USE_MOCK_TRAFFIC_DATA=true)
"""
import logging
import math
import os
import httpx
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from sqlalchemy import text
from db.core import ENGINE

logger = logging.getLogger(__name__)


@dataclass
class TrafficIncident:
    """Ein Verkehrshindernis (Baustelle, Unfall, Sperrung)"""
    incident_id: str
    type: str  # "construction", "accident", "closure"
    lat: float
    lon: float
    severity: str  # "low", "medium", "high", "critical"
    description: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    affected_roads: List[str] = None  # Liste von Straßennamen/Nummern
    delay_minutes: int = 0  # Geschätzte Verzögerung in Minuten
    radius_km: float = 0.5  # Radius in km, in dem das Hindernis relevant ist


@dataclass
class SpeedCamera:
    """Ein Blitzer/Radar (Warnung, kein Hindernis)"""
    camera_id: str
    lat: float
    lon: float
    type: str  # "fixed", "mobile", "section_control"
    direction: Optional[str] = None  # "north", "south", "east", "west", "both"
    speed_limit: Optional[int] = None  # Geschwindigkeitsbegrenzung in km/h
    description: Optional[str] = None
    verified: bool = False  # Ob Standort verifiziert ist
    last_seen: Optional[datetime] = None


class LiveTrafficDataService:
    """Service für Live-Traffic-Daten"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cache_duration_minutes = 15  # Cache-Dauer für Live-Daten
        self.last_fetch_time = None
        self.cached_incidents = []
        self.cached_cameras = []
        self.camera_cache_duration_minutes = 60  # Blitzer-Daten länger cachen (seltener Änderungen)
        
    def get_incidents_in_area(
        self,
        bounds: Tuple[float, float, float, float],
        incident_types: List[str] = None
    ) -> List[TrafficIncident]:
        """
        Holt Verkehrshindernisse in einem bestimmten Gebiet.
        
        Args:
            bounds: (min_lat, min_lon, max_lat, max_lon)
            incident_types: Liste von Typen ["construction", "accident", "closure"] oder None für alle
        
        Returns:
            Liste von TrafficIncident
        """
        min_lat, min_lon, max_lat, max_lon = bounds
        
        # Prüfe Cache
        if self._is_cache_valid():
            # Filtere nach Bounds
            incidents = [
                inc for inc in self.cached_incidents
                if min_lat <= inc.lat <= max_lat and min_lon <= inc.lon <= max_lon
            ]
            
            # Filtere nach Typen
            if incident_types:
                incidents = [inc for inc in incidents if inc.type in incident_types]
            
            return incidents
        
        # Hole neue Daten
        try:
            incidents = self._fetch_incidents(bounds)
            self.cached_incidents = incidents
            self.last_fetch_time = datetime.now()
            
            # Filtere nach Typen
            if incident_types:
                incidents = [inc for inc in incidents if inc.type in incident_types]
            
            return incidents
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen von Live-Daten: {e}")
            # Fallback: Leere Liste oder gecachte Daten
            return self.cached_incidents if self.cached_incidents else []
    
    def _is_cache_valid(self) -> bool:
        """Prüft ob Cache noch gültig ist"""
        if not self.last_fetch_time or not self.cached_incidents:
            return False
        
        age = datetime.now() - self.last_fetch_time
        return age.total_seconds() < (self.cache_duration_minutes * 60)
    
    def _fetch_incidents(self, bounds: Tuple[float, float, float, float]) -> List[TrafficIncident]:
        """
        Holt Verkehrshindernisse aus verschiedenen Quellen.
        
        Args:
            bounds: (min_lat, min_lon, max_lat, max_lon)
        
        Returns:
            Liste von TrafficIncident
        """
        incidents = []
        min_lat, min_lon, max_lat, max_lon = bounds
        
        # 1. Hole Baustellen von Autobahn API (falls verfügbar)
        try:
            construction_incidents = self._fetch_autobahn_construction(bounds)
            incidents.extend(construction_incidents)
        except Exception as e:
            self.logger.warning(f"Autobahn API Fehler: {e}")
        
        # 2. Hole Sperrungen von OpenStreetMap Overpass API
        try:
            closure_incidents = self._fetch_osm_closures(bounds)
            incidents.extend(closure_incidents)
        except Exception as e:
            self.logger.warning(f"OSM Overpass API Fehler: {e}")
        
        # 3. Hole gespeicherte Hindernisse aus eigener DB
        try:
            db_incidents = self._fetch_db_incidents(bounds)
            incidents.extend(db_incidents)
        except Exception as e:
            self.logger.warning(f"DB-Incidents Fehler: {e}")
        
        return incidents
    
    def _fetch_autobahn_construction(self, bounds: Tuple[float, float, float, float]) -> List[TrafficIncident]:
        """
        Holt Baustellen von der Autobahn API.
        
        Versucht verschiedene Datenquellen:
        1. OpenStreetMap Overpass API (Baustellen auf Autobahnen)
        2. Eigene API-Endpunkte (falls konfiguriert)
        3. Fallback: Mock-Daten für Tests
        
        Args:
            bounds: (min_lat, min_lon, max_lat, max_lon)
        
        Returns:
            Liste von TrafficIncident
        """
        incidents = []
        min_lat, min_lon, max_lat, max_lon = bounds
        
        # 1. Versuche OSM Overpass API für Autobahn-Baustellen
        try:
            osm_incidents = self._fetch_osm_autobahn_construction(bounds)
            incidents.extend(osm_incidents)
            if osm_incidents:
                self.logger.info(f"OSM Overpass: {len(osm_incidents)} Autobahn-Baustellen gefunden")
        except Exception as e:
            self.logger.warning(f"OSM Overpass API Fehler für Autobahn-Baustellen: {e}")
        
        # 2. Versuche externe API (falls konfiguriert)
        api_url = os.getenv("AUTOBAHN_API_URL")
        api_key = os.getenv("AUTOBAHN_API_KEY")
        
        if api_url and api_key:
            try:
                api_incidents = self._fetch_external_api_construction(api_url, api_key, bounds)
                incidents.extend(api_incidents)
                if api_incidents:
                    self.logger.info(f"Externe API: {len(api_incidents)} Baustellen gefunden")
            except Exception as e:
                self.logger.warning(f"Externe Autobahn API Fehler: {e}")
        
        # 3. Fallback: Mock-Daten nur wenn keine echten Daten vorhanden und im Test-Modus
        use_mock = os.getenv("USE_MOCK_TRAFFIC_DATA", "false").lower() == "true"
        if not incidents and use_mock:
            self.logger.debug("Verwende Mock-Daten für Autobahn-Baustellen (Test-Modus)")
            # Beispiel: Baustelle auf A4 bei Dresden
            if 51.0 <= bounds[0] <= 51.2 and 13.6 <= bounds[1] <= 13.8:
                incidents.append(TrafficIncident(
                    incident_id="autobahn_construction_001",
                    type="construction",
                    lat=51.05,
                    lon=13.73,
                    severity="medium",
                    description="Baustelle A4 Richtung Chemnitz, rechte Spur gesperrt",
                    delay_minutes=5,
                    radius_km=2.0,
                    affected_roads=["A4"]
                ))
        
        return incidents
    
    def _fetch_osm_autobahn_construction(self, bounds: Tuple[float, float, float, float]) -> List[TrafficIncident]:
        """
        Holt Autobahn-Baustellen von OpenStreetMap Overpass API.
        
        Sucht nach:
        - way[highway=motorway][construction=yes]
        - way[highway=motorway_link][construction=yes]
        - relation[type=route][route=motorway][construction=yes]
        """
        incidents = []
        min_lat, min_lon, max_lat, max_lon = bounds
        
        # Overpass API Query für Autobahn-Baustellen
        query = f"""
        [out:json][timeout:15];
        (
          way["highway"="motorway"]["construction"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
          way["highway"="motorway_link"]["construction"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
          relation["type"="route"]["route"="motorway"]["construction"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out center;
        """
        
        try:
            url = "https://overpass-api.de/api/interpreter"
            with httpx.Client(timeout=15.0) as client:
                response = client.post(url, data=query)
                response.raise_for_status()
                data = response.json()
                
                for element in data.get("elements", []):
                    center = element.get("center", {})
                    if not center:
                        continue
                    
                    tags = element.get("tags", {})
                    road_name = tags.get("ref", tags.get("name", "Autobahn"))
                    
                    # Bestimme Severity basierend auf Tags
                    severity = "medium"
                    if tags.get("construction") == "major":
                        severity = "high"
                    elif tags.get("construction") == "minor":
                        severity = "low"
                    
                    incidents.append(TrafficIncident(
                        incident_id=f"osm_autobahn_{element.get('id')}",
                        type="construction",
                        lat=center["lat"],
                        lon=center["lon"],
                        severity=severity,
                        description=f"Baustelle auf {road_name}",
                        delay_minutes=5 if severity == "medium" else (10 if severity == "high" else 2),
                        radius_km=2.0,
                        affected_roads=[road_name] if road_name != "Autobahn" else []
                    ))
        except Exception as e:
            self.logger.warning(f"OSM Overpass API Fehler für Autobahn-Baustellen: {e}")
        
        return incidents
    
    def _fetch_external_api_construction(
        self, 
        api_url: str, 
        api_key: str, 
        bounds: Tuple[float, float, float, float]
    ) -> List[TrafficIncident]:
        """
        Holt Baustellen von einer externen API.
        
        Args:
            api_url: URL der API (z.B. https://api.example.com/v1/construction)
            api_key: API-Schlüssel für Authentifizierung
            bounds: (min_lat, min_lon, max_lat, max_lon)
        
        Returns:
            Liste von TrafficIncident
        """
        incidents = []
        min_lat, min_lon, max_lat, max_lon = bounds
        
        try:
            # Standard-API-Format: GET mit bounds-Parameter
            params = {
                "min_lat": min_lat,
                "min_lon": min_lon,
                "max_lat": max_lat,
                "max_lon": max_lon,
                "api_key": api_key
            }
            
            with httpx.Client(timeout=10.0) as client:
                response = client.get(api_url, params=params)
                response.raise_for_status()
                data = response.json()
                
                # Erwartetes Format: {"incidents": [{"id": "...", "lat": ..., "lon": ..., ...}]}
                for item in data.get("incidents", []):
                    incidents.append(TrafficIncident(
                        incident_id=item.get("id", f"api_{item.get('lat')}_{item.get('lon')}"),
                        type=item.get("type", "construction"),
                        lat=float(item.get("lat", 0)),
                        lon=float(item.get("lon", 0)),
                        severity=item.get("severity", "medium"),
                        description=item.get("description", "Baustelle"),
                        delay_minutes=int(item.get("delay_minutes", 5)),
                        radius_km=float(item.get("radius_km", 2.0)),
                        affected_roads=item.get("affected_roads", [])
                    ))
        except Exception as e:
            self.logger.error(f"Externe API Fehler: {e}")
            raise
        
        return incidents
    
    def _fetch_osm_closures(self, bounds: Tuple[float, float, float, float]) -> List[TrafficIncident]:
        """
        Holt Sperrungen von OpenStreetMap Overpass API.
        
        Sucht nach:
        - way[highway][construction=yes]
        - way[highway][access=no]
        - relation[type=route][route=road][construction=yes]
        """
        incidents = []
        min_lat, min_lon, max_lat, max_lon = bounds
        
        # Overpass API Query
        query = f"""
        [out:json][timeout:10];
        (
          way["highway"]["construction"="yes"]({min_lat},{min_lon},{max_lat},{max_lon});
          way["highway"]["access"="no"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        out center;
        """
        
        try:
            url = "https://overpass-api.de/api/interpreter"
            with httpx.Client(timeout=10.0) as client:
                response = client.post(url, data=query)
                response.raise_for_status()
                data = response.json()
                
                for element in data.get("elements", []):
                    if element.get("type") == "way" and "center" in element:
                        center = element["center"]
                        incidents.append(TrafficIncident(
                            incident_id=f"osm_closure_{element.get('id')}",
                            type="closure",
                            lat=center["lat"],
                            lon=center["lon"],
                            severity="high",
                            description=f"Straßensperrung: {element.get('tags', {}).get('name', 'Unbekannt')}",
                            delay_minutes=10,
                            radius_km=1.0,
                            affected_roads=[element.get('tags', {}).get('name', 'Unbekannt')]
                        ))
        except Exception as e:
            self.logger.warning(f"OSM Overpass API Fehler: {e}")
        
        return incidents
    
    def _fetch_db_incidents(self, bounds: Tuple[float, float, float, float]) -> List[TrafficIncident]:
        """
        Holt gespeicherte Hindernisse aus der eigenen Datenbank.
        
        Erwartet Tabelle: traffic_incidents
        """
        incidents = []
        min_lat, min_lon, max_lat, max_lon = bounds
        
        try:
            with ENGINE.connect() as conn:
                # Prüfe ob Tabelle existiert
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='traffic_incidents'
                """))
                if not result.fetchone():
                    # Tabelle existiert nicht - erstelle sie
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS traffic_incidents (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            incident_id TEXT UNIQUE NOT NULL,
                            type TEXT NOT NULL,
                            lat REAL NOT NULL,
                            lon REAL NOT NULL,
                            severity TEXT NOT NULL,
                            description TEXT,
                            start_time TEXT,
                            end_time TEXT,
                            delay_minutes INTEGER DEFAULT 0,
                            radius_km REAL DEFAULT 0.5,
                            created_at TEXT DEFAULT (datetime('now')),
                            updated_at TEXT DEFAULT (datetime('now'))
                        )
                    """))
                    conn.commit()
                    return []
                
                # Hole aktive Hindernisse
                result = conn.execute(text("""
                    SELECT incident_id, type, lat, lon, severity, description,
                           start_time, end_time, delay_minutes, radius_km
                    FROM traffic_incidents
                    WHERE lat >= :min_lat AND lat <= :max_lat
                      AND lon >= :min_lon AND lon <= :max_lon
                      AND (end_time IS NULL OR end_time > datetime('now'))
                """), {
                    "min_lat": min_lat,
                    "max_lat": max_lat,
                    "min_lon": min_lon,
                    "max_lon": max_lon
                })
                
                for row in result.fetchall():
                    incidents.append(TrafficIncident(
                        incident_id=row[0],
                        type=row[1],
                        lat=row[2],
                        lon=row[3],
                        severity=row[4],
                        description=row[5] or "",
                        start_time=datetime.fromisoformat(row[6]) if row[6] else None,
                        end_time=datetime.fromisoformat(row[7]) if row[7] else None,
                        delay_minutes=row[8] or 0,
                        radius_km=row[9] or 0.5
                    ))
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen von DB-Incidents: {e}")
        
        return incidents
    
    def get_incidents_near_route(
        self,
        route_coords: List[Tuple[float, float]],
        max_distance_km: float = 2.0
    ) -> List[TrafficIncident]:
        """
        Findet Verkehrshindernisse in der Nähe einer Route.
        
        Args:
            route_coords: Liste von (lat, lon) Koordinaten der Route
            max_distance_km: Maximale Entfernung zur Route in km
        
        Returns:
            Liste von TrafficIncident die die Route beeinflussen könnten
        """
        if not route_coords:
            return []
        
        # Berechne Bounds der Route
        lats = [coord[0] for coord in route_coords]
        lons = [coord[1] for coord in route_coords]
        
        # Erweitere Bounds um max_distance_km
        min_lat = min(lats) - (max_distance_km / 111.0)  # ~111 km pro Grad
        max_lat = max(lats) + (max_distance_km / 111.0)
        min_lon = min(lons) - (max_distance_km / (111.0 * abs(math.cos(math.radians(min(lats))))))
        max_lon = max(lons) + (max_distance_km / (111.0 * abs(math.cos(math.radians(max(lats))))))
        
        bounds = (min_lat, min_lon, max_lat, max_lon)
        all_incidents = self.get_incidents_in_area(bounds)
        
        # Filtere nach tatsächlicher Entfernung zur Route
        # Berücksichtige auch den radius_km des Hindernisses
        relevant_incidents = []
        for incident in all_incidents:
            # Berechne minimale Distanz zur Route
            min_dist = self._distance_to_route(incident.lat, incident.lon, route_coords)
            
            # Hindernis ist relevant wenn:
            # 1. Distanz zur Route <= max_distance_km ODER
            # 2. Distanz zur Route <= (max_distance_km + radius_km des Hindernisses)
            #    (Hindernis hat eigenen Radius, der berücksichtigt werden sollte)
            incident_radius = incident.radius_km or 0.5  # Default 500m
            effective_max_distance = max(max_distance_km, incident_radius)
            
            if min_dist <= effective_max_distance:
                # Zusätzlich: Nur Hindernisse mit mindestens "medium" Severity
                # (low-severity Hindernisse sind oft nicht relevant)
                if incident.severity in ["medium", "high", "critical"]:
                    relevant_incidents.append(incident)
        
        return relevant_incidents
    
    def _distance_to_route(
        self,
        lat: float,
        lon: float,
        route_coords: List[Tuple[float, float]]
    ) -> float:
        """
        Berechnet minimale Entfernung eines Punktes zur Route.
        
        Args:
            lat, lon: Punkt-Koordinaten
            route_coords: Liste von (lat, lon) Koordinaten der Route
        
        Returns:
            Minimale Entfernung in km
        """
        import math
        
        min_dist = float('inf')
        
        for i in range(len(route_coords) - 1):
            p1 = route_coords[i]
            p2 = route_coords[i + 1]
            
            # Distanz zu Liniensegment
            dist = self._point_to_line_distance(lat, lon, p1[0], p1[1], p2[0], p2[1])
            min_dist = min(min_dist, dist)
        
        return min_dist
    
    def _point_to_line_distance(
        self,
        px: float, py: float,
        x1: float, y1: float,
        x2: float, y2: float
    ) -> float:
        """
        Berechnet Entfernung eines Punktes zu einem Liniensegment (Haversine).
        Verwendet Projektion auf Liniensegment für präzisere Berechnung.
        """
        import math
        
        # Konvertiere zu Radian
        lat1, lon1 = math.radians(x1), math.radians(y1)
        lat2, lon2 = math.radians(x2), math.radians(y2)
        plat, plon = math.radians(px), math.radians(py)
        
        # Berechne Distanz zu beiden Endpunkten
        d1 = self._haversine_distance(plat, plon, lat1, lon1)
        d2 = self._haversine_distance(plat, plon, lat2, lon2)
        
        # Berechne Länge des Liniensegments
        segment_length = self._haversine_distance(lat1, lon1, lat2, lon2)
        
        # Wenn Segment sehr kurz, verwende Minimum der Endpunkte
        if segment_length < 0.001:  # < 1m
            return min(d1, d2)
        
        # Berechne Projektion des Punktes auf das Liniensegment
        # Vektor vom Startpunkt zum Punkt
        # Vektor vom Startpunkt zum Endpunkt
        # Projektion = dot(v1, v2) / |v2|^2
        
        # Vereinfachte Projektion auf Großkreis (für kurze Segmente ausreichend)
        # Für präzisere Berechnung: Verwende Minimum der Endpunkte und Mittelpunkt
        midpoint_lat = (lat1 + lat2) / 2
        midpoint_lon = (lon1 + lon2) / 2
        d_mid = self._haversine_distance(plat, plon, midpoint_lat, midpoint_lon)
        
        # Nimm Minimum von: Endpunkte, Mittelpunkt
        min_dist = min(d1, d2, d_mid)
        
        # Wenn Punkt zwischen den Endpunkten liegt (d1 + d2 ≈ segment_length), 
        # verwende die kleinere Distanz
        if abs(d1 + d2 - segment_length) < 0.01:  # Punkt liegt zwischen Endpunkten
            return min_dist
        
        # Sonst: Punkt liegt außerhalb, verwende Distanz zum nächsten Endpunkt
        return min(d1, d2)
    
    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine-Distanz zwischen zwei Punkten"""
        import math
        
        R = 6371.0  # Erdradius in km
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    def get_speed_cameras_in_area(
        self,
        bounds: Tuple[float, float, float, float],
        camera_types: List[str] = None
    ) -> List[SpeedCamera]:
        """
        Holt Blitzer/Radar-Standorte in einem bestimmten Gebiet.
        
        WICHTIG: Blitzer.de bietet keine öffentliche API. Diese Funktion verwendet:
        - Eigene Datenbank (manuell gepflegte Daten)
        - Optional: Importierte GPX-Dateien
        
        Rechtlicher Hinweis: Nutzung von Blitzer.de-Daten ohne Genehmigung kann
        gegen deren Nutzungsbedingungen verstoßen. Bitte prüfen Sie die rechtlichen
        Aspekte vor Produktivnutzung.
        
        Args:
            bounds: (min_lat, min_lon, max_lat, max_lon)
            camera_types: Liste von Typen ["fixed", "mobile", "section_control"] oder None für alle
        
        Returns:
            Liste von SpeedCamera
        """
        min_lat, min_lon, max_lat, max_lon = bounds
        
        # Prüfe Cache
        if self._is_camera_cache_valid():
            # Cache enthält ALLE Blitzer aus der Datenbank (nicht nur die im ersten Bereich)
            # Filtere nach Bounds
            cameras = [
                cam for cam in self.cached_cameras
                if min_lat <= cam.lat <= max_lat and min_lon <= cam.lon <= max_lon
            ]
            
            if camera_types:
                cameras = [cam for cam in cameras if cam.type in camera_types]
            
            self.logger.debug(f"[BLITZER-CACHE] {len(cameras)} Blitzer aus Cache (Bereich: [{min_lat:.4f}, {min_lon:.4f}] bis [{max_lat:.4f}, {max_lon:.4f}])")
            return cameras
        
        # Cache abgelaufen oder nicht vorhanden - hole ALLE Blitzer aus der DB
        try:
            # WICHTIG: Hole ALLE Blitzer (nicht nur die im aktuellen Bereich)
            # Der Cache speichert dann alle Blitzer, damit beim Zoomen/Pan alle verfügbar sind
            all_cameras = self._fetch_all_speed_cameras()
            self.cached_cameras = all_cameras
            self.last_camera_fetch_time = datetime.now()
            
            # Filtere nach Bounds
            cameras = [
                cam for cam in all_cameras
                if min_lat <= cam.lat <= max_lat and min_lon <= cam.lon <= max_lon
            ]
            
            if camera_types:
                cameras = [cam for cam in cameras if cam.type in camera_types]
            
            self.logger.info(f"[BLITZER] {len(cameras)} Blitzer im Bereich gefunden (von {len(all_cameras)} insgesamt in DB)")
            return cameras
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen von Blitzer-Daten: {e}")
            return self.cached_cameras if self.cached_cameras else []
    
    def _is_camera_cache_valid(self) -> bool:
        """Prüft ob Blitzer-Cache noch gültig ist"""
        if not hasattr(self, 'last_camera_fetch_time') or not self.last_camera_fetch_time:
            return False
        if not self.cached_cameras:
            return False
        
        age = datetime.now() - self.last_camera_fetch_time
        return age.total_seconds() < (self.camera_cache_duration_minutes * 60)
    
    def _fetch_speed_cameras(self, bounds: Tuple[float, float, float, float]) -> List[SpeedCamera]:
        """
        Holt Blitzer-Daten aus der eigenen Datenbank.
        
        WICHTIG: Blitzer.de bietet keine öffentliche API. Diese Funktion erwartet,
        dass Daten manuell in die Datenbank eingetragen werden oder via Import
        (z.B. GPX-Dateien) geladen werden.
        
        Rechtlicher Hinweis: Bitte prüfen Sie die Nutzungsbedingungen von Blitzer.de
        und anderen Datenquellen vor der Nutzung.
        """
        cameras = []
        min_lat, min_lon, max_lat, max_lon = bounds
        
        try:
            with ENGINE.connect() as conn:
                # Prüfe ob Tabelle existiert
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='speed_cameras'
                """))
                if not result.fetchone():
                    # Tabelle existiert nicht - erstelle sie
                    conn.execute(text("""
                        CREATE TABLE IF NOT EXISTS speed_cameras (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            camera_id TEXT UNIQUE NOT NULL,
                            lat REAL NOT NULL,
                            lon REAL NOT NULL,
                            type TEXT NOT NULL,
                            direction TEXT,
                            speed_limit INTEGER,
                            description TEXT,
                            verified INTEGER DEFAULT 0,
                            last_seen TEXT,
                            created_at TEXT DEFAULT (datetime('now')),
                            updated_at TEXT DEFAULT (datetime('now'))
                        )
                    """))
                    conn.commit()
                    logger.info("Tabelle 'speed_cameras' erstellt. Bitte Daten manuell eintragen oder importieren.")
                    return []
                
                # Zähle ALLE Blitzer in der Datenbank (für Debugging)
                total_count_result = conn.execute(text("SELECT COUNT(*) FROM speed_cameras"))
                total_count = total_count_result.fetchone()[0]
                logger.info(f"[BLITZER-DB] Gesamtanzahl Blitzer in DB: {total_count}")
                
                # Hole Blitzer im Gebiet
                result = conn.execute(text("""
                    SELECT camera_id, lat, lon, type, direction, speed_limit, 
                           description, verified, last_seen
                    FROM speed_cameras
                    WHERE lat >= :min_lat AND lat <= :max_lat
                      AND lon >= :min_lon AND lon <= :max_lon
                """), {
                    "min_lat": min_lat,
                    "max_lat": max_lat,
                    "min_lon": min_lon,
                    "max_lon": max_lon
                })
                
                for row in result.fetchall():
                    cameras.append(SpeedCamera(
                        camera_id=row[0],
                        lat=row[1],
                        lon=row[2],
                        type=row[3],
                        direction=row[4],
                        speed_limit=row[5],
                        description=row[6],
                        verified=bool(row[7]),
                        last_seen=datetime.fromisoformat(row[8]) if row[8] else None
                    ))
                
                # Logging für Debugging
                logger.info(f"[BLITZER-DB] Bereich: [{min_lat:.4f}, {min_lon:.4f}] bis [{max_lat:.4f}, {max_lon:.4f}]")
                logger.info(f"[BLITZER-DB] Gefunden: {len(cameras)} Blitzer im Bereich (von {total_count} insgesamt)")
                
                # Warnung wenn nur wenige Blitzer gefunden werden
                if len(cameras) < 10 and total_count < 50:
                    logger.warning(f"[BLITZER-DB] ⚠️ Nur {len(cameras)} Blitzer im Bereich gefunden. Datenbank enthält nur {total_count} Blitzer insgesamt. Bitte mehr Daten importieren!")
                    
        except Exception as e:
            logger.error(f"Fehler beim Abrufen von Blitzer-Daten aus DB: {e}")
        
        return cameras
    
    def _fetch_all_speed_cameras(self) -> List[SpeedCamera]:
        """
        Holt ALLE Blitzer aus der Datenbank (ohne Bereichs-Filterung).
        Wird für Cache verwendet.
        """
        cameras = []
        
        try:
            with ENGINE.connect() as conn:
                # Prüfe ob Tabelle existiert
                result = conn.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='speed_cameras'
                """))
                if not result.fetchone():
                    return []
                
                # Hole ALLE Blitzer (ohne Bereichs-Filterung)
                result = conn.execute(text("""
                    SELECT camera_id, lat, lon, type, direction, speed_limit, 
                           description, verified, last_seen
                    FROM speed_cameras
                """))
                
                for row in result.fetchall():
                    cameras.append(SpeedCamera(
                        camera_id=row[0],
                        lat=row[1],
                        lon=row[2],
                        type=row[3],
                        direction=row[4],
                        speed_limit=row[5],
                        description=row[6],
                        verified=bool(row[7]),
                        last_seen=datetime.fromisoformat(row[8]) if row[8] else None
                    ))
                
                logger.info(f"[BLITZER-DB] Alle Blitzer geladen: {len(cameras)} insgesamt")
                
        except Exception as e:
            logger.error(f"Fehler beim Abrufen aller Blitzer-Daten aus DB: {e}")
        
        return cameras
    
    def get_cameras_near_route(
        self,
        route_coords: List[Tuple[float, float]],
        max_distance_km: float = 1.0
    ) -> List[SpeedCamera]:
        """
        Findet Blitzer in der Nähe einer Route.
        
        Args:
            route_coords: Liste von (lat, lon) Koordinaten der Route
            max_distance_km: Maximale Entfernung zur Route in km
        
        Returns:
            Liste von SpeedCamera die die Route betreffen könnten
        """
        if not route_coords:
            return []
        
        # Berechne Bounds der Route
        lats = [coord[0] for coord in route_coords]
        lons = [coord[1] for coord in route_coords]
        
        # Erweitere Bounds um max_distance_km
        min_lat = min(lats) - (max_distance_km / 111.0)
        max_lat = max(lats) + (max_distance_km / 111.0)
        min_lon = min(lons) - (max_distance_km / (111.0 * abs(math.cos(math.radians(min(lats))))))
        max_lon = max(lons) + (max_distance_km / (111.0 * abs(math.cos(math.radians(max(lats))))))
        
        bounds = (min_lat, min_lon, max_lat, max_lon)
        all_cameras = self.get_speed_cameras_in_area(bounds)
        
        # Filtere nach tatsächlicher Entfernung zur Route
        relevant_cameras = []
        for camera in all_cameras:
            min_dist = self._distance_to_route(camera.lat, camera.lon, route_coords)
            if min_dist <= max_distance_km:
                relevant_cameras.append(camera)
        
        return relevant_cameras


# Globale Instanz
_live_traffic_service = None

def get_live_traffic_service() -> LiveTrafficDataService:
    """Singleton-Instanz des Live-Traffic-Services"""
    global _live_traffic_service
    if _live_traffic_service is None:
        _live_traffic_service = LiveTrafficDataService()
    return _live_traffic_service

