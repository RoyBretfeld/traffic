"""
Robuster OSRM Client mit Timeouts, Retry, Circuit-Breaker und Validierung

Ersetzt services/osrm_client.py mit gehärteter Implementierung.
"""

from __future__ import annotations
import os
import logging
import time
from typing import List, Dict, Optional, Tuple
import math
from dataclasses import dataclass
from enum import Enum

try:
    import httpx
    HTTPX_AVAILABLE = True
except ImportError:
    HTTPX_AVAILABLE = False
    try:
        import requests
        REQUESTS_AVAILABLE = True
    except ImportError:
        REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)


class CircuitBreakerState(Enum):
    CLOSED = "closed"  # Normal
    OPEN = "open"      # Fehler, Requests blockiert
    HALF_OPEN = "half_open"  # Test-Request erlaubt


@dataclass
class CircuitBreaker:
    """Einfacher Circuit-Breaker für OSRM-Requests"""
    failure_threshold: int = 5  # Nach 5 Fehlern → OPEN
    failure_window_seconds: int = 60  # Zeitfenster für Fehler
    half_open_timeout_seconds: int = 30  # Wartezeit bis HALF_OPEN
    
    def __init__(self):
        self.state = CircuitBreakerState.CLOSED
        self.failures = []
        self.last_failure_time = 0.0
    
    def record_success(self):
        """Erfolgreicher Request → CLOSED"""
        if self.state == CircuitBreakerState.HALF_OPEN:
            self.state = CircuitBreakerState.CLOSED
            self.failures.clear()
        elif self.state == CircuitBreakerState.CLOSED:
            # Alte Fehler entfernen
            now = time.time()
            self.failures = [f for f in self.failures if now - f < self.failure_window_seconds]
    
    def record_failure(self):
        """Fehlgeschlagener Request → Prüfe ob OPEN"""
        now = time.time()
        self.last_failure_time = now
        self.failures.append(now)
        
        # Alte Fehler entfernen
        self.failures = [f for f in self.failures if now - f < self.failure_window_seconds]
        
        # Prüfe ob Schwellwert erreicht
        if len(self.failures) >= self.failure_threshold:
            self.state = CircuitBreakerState.OPEN
            logger.warning(f"[OSRM-CB] Circuit-Breaker OPEN nach {len(self.failures)} Fehlern")
    
    def is_open(self) -> bool:
        """Prüft ob Requests erlaubt sind"""
        now = time.time()
        
        if self.state == CircuitBreakerState.CLOSED:
            return False
        
        if self.state == CircuitBreakerState.OPEN:
            # Prüfe ob HALF_OPEN erlaubt
            if now - self.last_failure_time >= self.half_open_timeout_seconds:
                self.state = CircuitBreakerState.HALF_OPEN
                logger.info("[OSRM-CB] Circuit-Breaker HALF_OPEN (Test-Request erlaubt)")
                return False
            return True
        
        # HALF_OPEN: Erlaube einen Request
        return False


def format_coord(lon: float, lat: float) -> str:
    """
    Formatiert Koordinaten für OSRM-URL (lon,lat Format).
    
    Args:
        lon: Längengrad (-180 bis 180)
        lat: Breitengrad (-90 bis 90)
        
    Returns:
        Formatierter String: "lon,lat" (z.B. "13.70161,51.01127")
        
    Raises:
        ValueError: Wenn Koordinaten außerhalb des gültigen Bereichs
    """
    if not (-180 <= lon <= 180):
        raise ValueError(f"Längengrad außerhalb des gültigen Bereichs: {lon}")
    if not (-90 <= lat <= 90):
        raise ValueError(f"Breitengrad außerhalb des gültigen Bereichs: {lat}")
    
    return f"{lon:.6f},{lat:.6f}"


class OSRMClientRobust:
    """
    Robuster OSRM Client mit:
    - Expliziten Timeouts (connect + read)
    - Retry-Mechanismus (2 Versuche)
    - Circuit-Breaker (5 Fehler/60s → OPEN, 30s → HALF_OPEN)
    - Pydantic-Validierung der Responses
    - Telemetrie-Metriken
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        connect_timeout: float = 1.5,
        read_timeout: float = 8.0,
        retries: int = 2,
        breaker: Optional[CircuitBreaker] = None
    ):
        """
        Initialisiert den robusten OSRM Client.
        
        Args:
            base_url: OSRM Server URL
            connect_timeout: Timeout für Verbindungsaufbau (Sekunden)
            read_timeout: Timeout für Lese-Operation (Sekunden)
            retries: Anzahl Retry-Versuche (Standard: 2)
            breaker: Circuit-Breaker (optional, wird erstellt wenn None)
        """
        # OSRM-URL aus .env (OSRM_URL oder OSRM_HOST:OSRM_PORT)
        env_url = os.getenv("OSRM_URL")
        if not env_url:
            osrm_host = os.getenv("OSRM_HOST", "127.0.0.1")
            osrm_port = os.getenv("OSRM_PORT", "5011")
            env_url = f"http://{osrm_host}:{osrm_port}"
        
        self.base_url = (base_url or env_url or "http://router.project-osrm.org").rstrip("/")
        
        # Fallback-URL für OSRM (Public OSRM wenn primärer Server nicht verfügbar)
        self.fallback_url = os.getenv("OSRM_FALLBACK", "https://router.project-osrm.org").rstrip("/")
        self.fallback_enabled = True
        
        # Timeouts aus .env (falls nicht explizit übergeben)
        env_timeout = os.getenv("OSRM_TIMEOUT")
        if env_timeout:
            timeout_float = float(env_timeout)
            if connect_timeout == 1.5:  # Default-Wert
                self.connect_timeout = min(timeout_float * 0.3, 2.0)
            else:
                self.connect_timeout = connect_timeout
            if read_timeout == 8.0:  # Default-Wert
                self.read_timeout = timeout_float
            else:
                self.read_timeout = read_timeout
        else:
            self.connect_timeout = connect_timeout
            self.read_timeout = read_timeout
        self.retries = retries
        self.breaker = breaker or CircuitBreaker()
        self.logger = logger
        
        # Telemetrie
        self.metrics = {
            "osrm_table_latency_ms": [],
            "osrm_unavailable": 0,
            "osrm_retry_total": 0,
            "osrm_circuit_breaker_trips": 0,
            "osrm_unreachable_null": 0
        }
        
        # HTTP Client (httpx bevorzugt, sonst requests)
        self._client = None
        self._use_httpx = HTTPX_AVAILABLE
        
        # Verfügbarkeitsprüfung
        self._available = self._check_availability()
    
    def _get_client(self):
        """Erstellt HTTP Client (httpx oder requests)"""
        if self._client is None:
            if self._use_httpx:
                self._client = httpx.Client(
                    timeout=httpx.Timeout(
                        connect=self.connect_timeout,
                        read=self.read_timeout,
                        write=None,  # Kein Write-Timeout
                        pool=None    # Kein Pool-Timeout
                    )
                )
            elif REQUESTS_AVAILABLE:
                self._client = requests  # requests-Modul direkt verwenden
            else:
                raise ImportError("Weder httpx noch requests verfügbar")
        return self._client
    
    def _check_availability(self) -> bool:
        """Prüft ob OSRM verfügbar ist"""
        try:
            test_coords = format_coord(13.388860, 52.517037) + ";" + format_coord(13.397634, 52.529407)
            test_url = f"{self.base_url}/route/v1/driving/{test_coords}?overview=false"
            
            if self._use_httpx:
                # Verwende temporären Client für Verfügbarkeitsprüfung
                with httpx.Client(
                    timeout=httpx.Timeout(
                        connect=self.connect_timeout,
                        read=self.read_timeout,
                        write=None,
                        pool=None
                    )
                ) as client:
                    response = client.get(test_url)
                    status = response.status_code
            elif REQUESTS_AVAILABLE:
                response = requests.get(test_url, timeout=self.read_timeout)
                status = response.status_code
            else:
                return False
            
            if status == 200:
                self.logger.info(f"[OSRM] Server verfügbar: {self.base_url}")
                return True
            else:
                self.logger.warning(f"[OSRM] Server antwortet mit Status {status}")
                return False
        except Exception as e:
            self.logger.warning(f"[OSRM] Verfügbarkeitsprüfung fehlgeschlagen: {e}")
            return False
    
    @property
    def available(self) -> bool:
        """Gibt zurück ob OSRM verfügbar ist"""
        return self._available
    
    def _get(self, url: str, params: Optional[Dict] = None) -> Dict:
        """
        HTTP GET mit Retry und Circuit-Breaker.
        
        Args:
            url: URL für Request
            params: Query-Parameter
            
        Returns:
            JSON Response als Dict
            
        Raises:
            RuntimeError: Wenn Circuit-Breaker OPEN ist
            httpx/requests Exception: Bei Netzwerk-Fehlern
        """
        # Circuit-Breaker prüfen
        if self.breaker.is_open():
            self.metrics["osrm_circuit_breaker_trips"] += 1
            raise RuntimeError(f"OSRM Circuit-Breaker OPEN (Server {self.base_url} nicht verfügbar)")
        
        client = self._get_client()
        
        # Retry-Loop
        last_exception = None
        for attempt in range(self.retries + 1):
            try:
                start_time = time.time()
                
                if self._use_httpx:
                    response = client.get(url, params=params)
                    response.raise_for_status()
                    data = response.json()
                else:
                    response = client.get(url, params=params, timeout=self.read_timeout)
                    response.raise_for_status()
                    data = response.json()
                
                # Erfolg
                elapsed_ms = (time.time() - start_time) * 1000
                self.metrics["osrm_table_latency_ms"].append(elapsed_ms)
                self.breaker.record_success()
                
                if attempt > 0:
                    self.logger.info(f"[OSRM] Request erfolgreich nach {attempt} Retry(s)")
                    self.metrics["osrm_retry_total"] += attempt
                
                return data
                
            except Exception as e:
                last_exception = e
                self.logger.warning(f"[OSRM] Request fehlgeschlagen (Versuch {attempt + 1}/{self.retries + 1}): {e}")
                
                if attempt < self.retries:
                    # Warte kurz vor Retry
                    time.sleep(0.1 * (attempt + 1))
                else:
                    # Alle Versuche fehlgeschlagen
                    self.breaker.record_failure()
                    self.metrics["osrm_unavailable"] += 1
                    raise
        
        # Sollte nie erreicht werden
        raise last_exception
    
    def get_route(self, coords: List[Tuple[float, float]]) -> Optional[Dict]:
        """
        Berechnet eine Route zwischen Koordinaten (robust).
        
        Args:
            coords: Liste von (lat, lon) Tupeln (min. 2 Punkte)
            
        Returns:
            Dict mit geometry, distance_km, duration_min, source
            Oder None wenn Route nicht berechnet werden kann
        """
        if len(coords) < 2:
            return None
        
        # Versuche OSRM wenn verfügbar
        if self._available:
            try:
                # Koordinaten formatieren (lon,lat)
                coords_str = ";".join([format_coord(lon, lat) for lat, lon in coords])
                route_url = f"{self.base_url}/route/v1/driving/{coords_str}"
                params = {
                    "overview": "full",
                    "geometries": "polyline",
                    "alternatives": "false"
                }
                
                data = self._get(route_url, params)
                
                # Validierung
                if not self._validate_route_response(data):
                    self.logger.warning("[OSRM] Route-Response ungültig, versuche OSRM-Fallback")
                    # Versuche Fallback-OSRM
                    if self.fallback_enabled and self.base_url != self.fallback_url:
                        return self._try_fallback_osrm(coords)
                    return None
                
                route = data.get("routes", [])[0]
                distance_m = route.get("distance", 0)
                duration_s = route.get("duration", 0)
                geometry = route.get("geometry", "")
                
                # Prüfe auf null/None
                if distance_m is None or duration_s is None:
                    self.metrics["osrm_unreachable_null"] += 1
                    self.logger.warning("[OSRM] Route enthält null-Werte, versuche OSRM-Fallback")
                    # Versuche Fallback-OSRM
                    if self.fallback_enabled and self.base_url != self.fallback_url:
                        return self._try_fallback_osrm(coords)
                    return None
                
                return {
                    "geometry": geometry if geometry else None,
                    "distance_km": round(distance_m / 1000.0, 2),
                    "duration_min": round(duration_s / 60.0, 2),
                    "source": "osrm"
                }
                
            except Exception as e:
                self.logger.warning(f"[OSRM] Route-Request fehlgeschlagen: {e}, versuche OSRM-Fallback")
                # Versuche Fallback-OSRM
                if self.fallback_enabled and self.base_url != self.fallback_url:
                    result = self._try_fallback_osrm(coords)
                    if result:
                        return result
        
        # Fallback: Haversine (wenn auch OSRM-Fallback fehlschlägt)
        return self._haversine_fallback(coords)
    
    def _try_fallback_osrm(self, coords: List[Tuple[float, float]]) -> Optional[Dict]:
        """
        Versucht Route über Fallback-OSRM zu berechnen.
        
        Args:
            coords: Liste von (lat, lon) Tupeln
            
        Returns:
            Route-Dict oder None
        """
        try:
            self.logger.info(f"[OSRM] Versuche Fallback-OSRM: {self.fallback_url}")
            coords_str = ";".join([format_coord(lon, lat) for lat, lon in coords])
            route_url = f"{self.fallback_url}/route/v1/driving/{coords_str}"
            params = {
                "overview": "full",
                "geometries": "polyline",
                "alternatives": "false"
            }
            
            data = self._get(route_url, params)
            
            if not self._validate_route_response(data):
                return None
            
            route = data.get("routes", [])[0]
            distance_m = route.get("distance", 0)
            duration_s = route.get("duration", 0)
            geometry = route.get("geometry", "")
            
            if distance_m is None or duration_s is None:
                return None
            
            self.logger.info(f"[OSRM] Fallback-OSRM erfolgreich")
            return {
                "geometry": geometry if geometry else None,
                "distance_km": round(distance_m / 1000.0, 2),
                "duration_min": round(duration_s / 60.0, 2),
                "source": "osrm_fallback"
            }
        except Exception as e:
            self.logger.warning(f"[OSRM] Fallback-OSRM fehlgeschlagen: {e}")
            return None
    
    def get_distance_matrix(
        self,
        coords: List[Tuple[float, float]],
        sources: Optional[List[int]] = None,
        destinations: Optional[List[int]] = None
    ) -> Optional[Dict[Tuple[int, int], Dict[str, float]]]:
        """
        Berechnet Distanzmatrix (robust mit Validierung).
        
        Args:
            coords: Liste von (lat, lon) Tupeln
            sources: Indizes für Quellen (wenn None: alle)
            destinations: Indizes für Ziele (wenn None: alle)
            
        Returns:
            Dict mit Keys (i, j) -> {"km": float, "minutes": float}
            Oder None wenn Matrix nicht berechnet werden kann
        """
        if len(coords) < 2:
            return None
        
        # Versuche OSRM wenn verfügbar
        if self._available:
            try:
                if sources is None:
                    sources = list(range(len(coords)))
                if destinations is None:
                    destinations = list(range(len(coords)))
                
                # Koordinaten formatieren (lon,lat)
                coords_str = ";".join([format_coord(lon, lat) for lat, lon in coords])
                sources_str = ",".join(map(str, sources))
                destinations_str = ",".join(map(str, destinations))
                
                table_url = f"{self.base_url}/table/v1/driving/{coords_str}"
                params = {
                    "sources": sources_str,
                    "destinations": destinations_str,
                    "annotations": "duration,distance"
                }
                
                data = self._get(table_url, params)
                
                # Validierung
                if not self._validate_table_response(data):
                    self.logger.warning("[OSRM] Table-Response ungültig, verwende Fallback")
                    return None
                
                durations = data.get("durations", [])
                distances = data.get("distances", [])
                
                # Prüfe auf null-Werte
                has_null = False
                for row in durations:
                    if any(x is None for x in row):
                        has_null = True
                        break
                
                if has_null:
                    self.metrics["osrm_unreachable_null"] += 1
                    self.logger.warning("[OSRM] Table enthält null-Werte (unreachable), verwende Fallback")
                    return None
                
                # Matrix erstellen
                matrix = {}
                for i, src_idx in enumerate(sources):
                    for j, dst_idx in enumerate(destinations):
                        if src_idx == dst_idx:
                            matrix[(src_idx, dst_idx)] = {"km": 0.0, "minutes": 0.0}
                            continue
                        
                        distance_m = distances[i][j] if i < len(distances) and j < len(distances[i]) else 0
                        duration_s = durations[i][j] if i < len(durations) and j < len(durations[i]) else 0
                        
                        matrix[(src_idx, dst_idx)] = {
                            "km": round(distance_m / 1000.0, 2),
                            "minutes": round(duration_s / 60.0, 2)
                        }
                
                self.logger.info(f"[OSRM] Table API erfolgreich: {len(sources)}×{len(destinations)} Matrix")
                return matrix
                
            except Exception as e:
                self.logger.warning(f"[OSRM] Table API Fehler: {e}, verwende Fallback")
        
        # Fallback: Haversine
        return self._haversine_matrix_fallback(coords, sources, destinations)
    
    def _validate_route_response(self, data: Dict) -> bool:
        """Validiert OSRM Route-Response mit Pydantic (F3)"""
        try:
            from services.osrm_models import RouteResponse
            RouteResponse.model_validate(data)
            return True
        except Exception as e:
            self.logger.warning(f"[OSRM] Route-Response Validierung fehlgeschlagen: {e}")
            return False
    
    def _validate_table_response(self, data: Dict) -> bool:
        """Validiert OSRM Table-Response mit Pydantic (F3)"""
        try:
            from services.osrm_models import TableResponse
            TableResponse.model_validate(data)
            return True
        except Exception as e:
            self.logger.warning(f"[OSRM] Table-Response Validierung fehlgeschlagen: {e}")
            return False
    
    def _haversine_fallback(self, coords: List[Tuple[float, float]]) -> Dict:
        """Haversine-Fallback für Route"""
        total_distance_km = 0.0
        total_duration_min = 0.0
        
        for i in range(len(coords) - 1):
            lat1, lon1 = coords[i]
            lat2, lon2 = coords[i + 1]
            
            distance_km = self._haversine_distance(lat1, lon1, lat2, lon2) * 1.3
            duration_min = (distance_km / 50.0) * 60
            
            total_distance_km += distance_km
            total_duration_min += duration_min
        
        return {
            "geometry": None,
            "distance_km": round(total_distance_km, 2),
            "duration_min": round(total_duration_min, 2),
            "source": "haversine"
        }
    
    def _haversine_matrix_fallback(
        self,
        coords: List[Tuple[float, float]],
        sources: Optional[List[int]],
        destinations: Optional[List[int]]
    ) -> Dict[Tuple[int, int], Dict[str, float]]:
        """Haversine-Fallback für Matrix"""
        if sources is None:
            sources = list(range(len(coords)))
        if destinations is None:
            destinations = list(range(len(coords)))
        
        matrix = {}
        for src_idx in sources:
            for dst_idx in destinations:
                if src_idx == dst_idx:
                    matrix[(src_idx, dst_idx)] = {"km": 0.0, "minutes": 0.0}
                    continue
                
                lat1, lon1 = coords[src_idx]
                lat2, lon2 = coords[dst_idx]
                
                distance_km = self._haversine_distance(lat1, lon1, lat2, lon2) * 1.3
                duration_min = (distance_km / 50.0) * 60
                
                matrix[(src_idx, dst_idx)] = {
                    "km": round(distance_km, 2),
                    "minutes": round(duration_min, 2)
                }
        
        return matrix
    
    @staticmethod
    def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Haversine-Distanz in Kilometern"""
        R = 6371.0
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (
            math.sin(delta_lat / 2) ** 2 +
            math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
        )
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        return R * c
    
    def get_metrics(self) -> Dict:
        """Gibt Telemetrie-Metriken zurück"""
        latency_avg = (
            sum(self.metrics["osrm_table_latency_ms"]) / len(self.metrics["osrm_table_latency_ms"])
            if self.metrics["osrm_table_latency_ms"] else 0
        )
        
        return {
            **self.metrics,
            "osrm_table_latency_avg_ms": latency_avg,
            "circuit_breaker_state": self.breaker.state.value
        }

