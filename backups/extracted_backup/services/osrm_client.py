"""
OSRM-Client gemäß Betriebsordnung §4.

- connect_timeout=1.5s, read_timeout=8s
- Retry 2× (idempotente GETs)
- Circuit-Breaker (Trip 5/60s, Half-Open 30s)
- OSRM Table API für Distanz-Matrix
- OSRM Route API für Visualisierung
"""
import os
import time
import logging
from typing import List, Dict, Tuple, Optional
from enum import Enum
import httpx


class CircuitState(Enum):
    """Circuit-Breaker Zustände"""
    CLOSED = "closed"      # Normal
    OPEN = "open"          # Fehler → blockiert
    HALF_OPEN = "half_open"  # Test-Phase


class OSRMClient:
    """
    OSRM-Client mit Circuit-Breaker, Retry und Timeouts.
    
    Betriebsordnung §4:
    - ROUTER_URL (Router-Service vor OSRM)
    - connect_timeout=1.5s, read_timeout=8s
    - Retry 2× (idempotente GETs)
    - Circuit-Breaker (Trip 5/60s, Half-Open 30s)
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Konfiguration: Zuerst app.yaml, dann ENV, dann Default
        try:
            from backend.config import cfg
            config_base_url = cfg("osrm:base_url")
            config_timeout = cfg("osrm:timeout_seconds", 6)
            self.fallback_enabled = cfg("osrm:fallback_enabled", True)
            self.fallback_url = "https://router.project-osrm.org"
        except Exception:
            config_base_url = None
            config_timeout = None
            self.fallback_enabled = True
            self.fallback_url = "https://router.project-osrm.org"
        
        # Base URL: Config > ENV > Default
        self.base_url = (
            config_base_url or 
            os.getenv("ROUTER_URL") or 
            os.getenv("OSRM_BASE_URL") or 
            "http://localhost:5000"
        )
        self.profile = os.getenv("OSRM_PROFILE", "driving")
        
        # Timeout: Config > Default
        if config_timeout:
            self.connect_timeout = min(config_timeout * 0.3, 2.0)  # 30% für Connect
            self.read_timeout = config_timeout
        else:
            self.connect_timeout = 1.5
            self.read_timeout = 8.0
        
        self.max_retries = 2
        
        # Circuit-Breaker
        self.circuit_state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.trip_threshold = 5  # Fehler innerhalb 60s → OPEN
        self.trip_window = 60   # 60 Sekunden
        self.half_open_timeout = 30  # 30 Sekunden in HALF_OPEN
        self.half_open_start = None
        
        self.logger.info(f"OSRM-Client initialisiert: {self.base_url} (Profil: {self.profile})")
    
    def _check_circuit_breaker(self) -> bool:
        """
        Prüft Circuit-Breaker Zustand.
        
        Returns:
            True wenn Request erlaubt, False wenn blockiert
        """
        now = time.time()
        
        if self.circuit_state == CircuitState.CLOSED:
            return True
        
        elif self.circuit_state == CircuitState.OPEN:
            # Prüfe ob wir zu HALF_OPEN wechseln können
            if self.last_failure_time and (now - self.last_failure_time) >= self.half_open_timeout:
                self.circuit_state = CircuitState.HALF_OPEN
                self.half_open_start = now
                self.logger.info("Circuit-Breaker: OPEN → HALF_OPEN (Test-Phase)")
                return True
            return False
        
        elif self.circuit_state == CircuitState.HALF_OPEN:
            # In HALF_OPEN erlauben wir einen Test-Request
            return True
        
        return False
    
    def _record_success(self):
        """Zeichnet Erfolg auf → Circuit schließen"""
        if self.circuit_state == CircuitState.HALF_OPEN:
            self.circuit_state = CircuitState.CLOSED
            self.failure_count = 0
            self.logger.info("Circuit-Breaker: HALF_OPEN → CLOSED (Erfolg)")
        elif self.circuit_state == CircuitState.CLOSED:
            # Reset failure count nach erfolgreichem Request
            if self.last_failure_time and (time.time() - self.last_failure_time) > self.trip_window:
                self.failure_count = 0
    
    def _record_failure(self):
        """Zeichnet Fehler auf → Circuit möglicherweise öffnen"""
        self.failure_count += 1
        self.last_failure_time = time.time()
        
        if self.circuit_state == CircuitState.HALF_OPEN:
            # HALF_OPEN → OPEN (Test fehlgeschlagen)
            self.circuit_state = CircuitState.OPEN
            self.logger.warning("Circuit-Breaker: HALF_OPEN → OPEN (Test fehlgeschlagen)")
        elif self.circuit_state == CircuitState.CLOSED:
            # Prüfe ob wir zu OPEN wechseln müssen
            now = time.time()
            # Reset failure_count wenn außerhalb Zeitfenster
            if self.last_failure_time:
                window_start = now - self.trip_window
                # Vereinfacht: Wenn 5 Fehler innerhalb 60s → OPEN
                if self.failure_count >= self.trip_threshold:
                    self.circuit_state = CircuitState.OPEN
                    self.logger.warning(f"Circuit-Breaker: CLOSED → OPEN ({self.failure_count} Fehler)")
    
    def _make_request(
        self,
        url: str,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Optional[httpx.Response]:
        """
        Führt HTTP-Request mit Retry-Logik aus.
        
        Args:
            url: Vollständige URL
            params: Query-Parameter
            retry_count: Aktuelle Retry-Anzahl
        
        Returns:
            Response oder None bei Fehler
        """
        if not self._check_circuit_breaker():
            self.logger.warning("Circuit-Breaker: Request blockiert (OPEN)")
            return None
        
        try:
            timeout = httpx.Timeout(
                connect=self.connect_timeout,
                read=self.read_timeout,
                write=30.0,
                pool=5.0
            )
            
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)
                response.raise_for_status()
                
                # Erfolg → Circuit-Status aktualisieren
                self._record_success()
                return response
                
        except httpx.TimeoutException as e:
            self.logger.warning(f"OSRM Timeout: {e}")
            self._record_failure()
            
            # Retry bei Timeout
            if retry_count < self.max_retries:
                self.logger.info(f"Retry {retry_count + 1}/{self.max_retries}")
                return self._make_request(url, params, retry_count + 1)
            return None
            
        except httpx.HTTPStatusError as e:
            self.logger.warning(f"OSRM HTTP-Fehler {e.response.status_code}: {e}")
            self._record_failure()
            return None
            
        except Exception as e:
            self.logger.error(f"OSRM unerwarteter Fehler: {e}")
            self._record_failure()
            return None
    
    def get_distance_matrix(
        self,
        coords: List[Tuple[float, float]],
        sources: Optional[List[int]] = None,
        destinations: Optional[List[int]] = None
    ) -> Optional[Dict[Tuple[int, int], Dict[str, float]]]:
        """
        Berechnet Distanz-Matrix mit OSRM Table API.
        
        Betriebsordnung §4: GET /table/v1/driving/{coords}?annotations=duration&sources=...&destinations=...
        
        Args:
            coords: Liste von (lat, lon) Tupeln
            sources: Liste von Indizes (Standard: alle, 0..n-1)
            destinations: Liste von Indizes (Standard: alle, 0..n-1)
        
        Returns:
            Dict mit {(i, j): {"km": distance_km, "minutes": duration_min}} oder None bei Fehler
        """
        if len(coords) < 2:
            return None
        
        # OSRM Table API Format: lon,lat;lon,lat;...
        coord_string = ";".join(f"{lon},{lat}" for lat, lon in coords)
        
        base = self.base_url.rstrip("/")
        url = f"{base}/table/v1/{self.profile}/{coord_string}"
        params = {"annotations": "distance,duration"}
        
        # Sources/Destinations Parameter (optional)
        if sources is not None:
            params["sources"] = ";".join(str(i) for i in sources)
        if destinations is not None:
            params["destinations"] = ";".join(str(i) for i in destinations)
        
        response = self._make_request(url, params)
        if not response:
            return None
        
        try:
            data = response.json()
            distances = data.get("distances", [])
            durations = data.get("durations", [])
            
            if not distances or not durations:
                self.logger.warning("OSRM Table API: Keine Distanzen/Dauern zurückgegeben")
                return None
            
            # Konvertiere in Dict: {(i, j): {"km": ..., "minutes": ...}}
            matrix = {}
            
            # Wenn sources/destinations angegeben, müssen wir die Indizes mappen
            if sources is not None:
                source_indices = sources
            else:
                source_indices = list(range(len(coords)))
            
            if destinations is not None:
                dest_indices = destinations
            else:
                dest_indices = list(range(len(coords)))
            
            for idx_i, i in enumerate(source_indices):
                for idx_j, j in enumerate(dest_indices):
                    if i != j or (sources is None and destinations is None):
                        # OSRM gibt Distanz in Metern, Dauer in Sekunden zurück
                        distance_km = distances[idx_i][idx_j] / 1000.0
                        duration_min = durations[idx_i][idx_j] / 60.0
                        matrix[(i, j)] = {
                            "km": round(distance_km, 2),
                            "minutes": round(duration_min, 2)
                        }
            
            return matrix
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen von OSRM Table API Response: {e}")
            return None
    
    def get_route(
        self,
        coords: List[Tuple[float, float]],
        use_polyline6: bool = False
    ) -> Optional[Dict]:
        """
        Berechnet Route mit OSRM Route API (für Visualisierung).
        
        Betriebsordnung §4: GET /route/v1/driving/{coords}?overview=false&steps=false
        
        Args:
            coords: Liste von (lat, lon) Tupeln
            use_polyline6: Wenn True, verwendet polyline6 statt polyline
        
        Returns:
            Route-Dict mit geometry, distance, duration oder None
        """
        if len(coords) < 2:
            return None
        
        # OSRM Route API Format: lon,lat;lon,lat;...
        coord_string = ";".join(f"{lon},{lat}" for lat, lon in coords)
        
        # Versuche zuerst primären OSRM-Server
        base = self.base_url.rstrip("/")
        url = f"{base}/route/v1/{self.profile}/{coord_string}"
        params = {
            "overview": "full",
            "steps": "false",
            "geometries": "polyline6" if use_polyline6 else "polyline"
        }
        
        response = self._make_request(url, params)
        
        # Fallback auf router.project-osrm.org wenn primärer Server nicht verfügbar
        if not response and self.fallback_enabled and self.base_url != self.fallback_url:
            self.logger.info(f"Primärer OSRM-Server nicht verfügbar, versuche Fallback: {self.fallback_url}")
            base = self.fallback_url.rstrip("/")
            url = f"{base}/route/v1/{self.profile}/{coord_string}"
            response = self._make_request(url, params)
        
        if not response:
            return None
        
        try:
            data = response.json()
            routes = data.get("routes", [])
            if not routes:
                return None
            
            route = routes[0]
            return {
                "geometry": route.get("geometry"),
                "distance_m": route.get("distance"),
                "duration_s": route.get("duration"),
                "distance_km": route.get("distance", 0) / 1000.0,
                "duration_min": route.get("duration", 0) / 60.0
            }
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen von OSRM Route API Response: {e}")
            return None
    
    @property
    def available(self) -> bool:
        """
        Prüft ob OSRM verfügbar ist (Circuit nicht OPEN).
        """
        return self.circuit_state != CircuitState.OPEN or self._check_circuit_breaker()
    
    def check_health(self) -> Dict[str, any]:
        """
        Prüft ob OSRM tatsächlich erreichbar ist durch einen Test-Request.
        Testet primären Server, bei Fehler auch Fallback.
        
        Returns:
            Dict mit status (ok/error), url, message
        """
        # Test-Request: Route zwischen zwei bekannten Punkten (Dresden)
        # Koordinaten: Dresden Hauptbahnhof → Dresden Neustadt
        test_coords = [
            (51.0493, 13.7381),  # Dresden Hauptbahnhof
            (51.0639, 13.7522)   # Dresden Neustadt
        ]
        
        # Versuche zuerst primären Server
        result = self._test_health_for_url(self.base_url, test_coords)
        if result["status"] == "ok":
            return result
        
        # Wenn primärer Server nicht verfügbar und Fallback aktiviert
        if self.fallback_enabled and self.base_url != self.fallback_url:
            self.logger.info(f"Primärer OSRM-Server nicht verfügbar, teste Fallback: {self.fallback_url}")
            result_fallback = self._test_health_for_url(self.fallback_url, test_coords)
            if result_fallback["status"] == "ok":
                result_fallback["message"] = f"OSRM erreichbar (Fallback: {self.fallback_url})"
                result_fallback["url"] = f"{self.base_url} → {self.fallback_url}"
            return result_fallback
        
        return result
    
    def _test_health_for_url(self, base_url: str, test_coords: List[Tuple[float, float]]) -> Dict[str, any]:
        """Testet einen spezifischen OSRM-URL."""
        try:
            coord_string = ";".join(f"{lon},{lat}" for lat, lon in test_coords)
            base = base_url.rstrip("/")
            # Viele OSRM-Knoten haben keinen /health Endpoint, testen wir mit /nearest
            url = f"{base}/nearest/v1/{self.profile}/{coord_string.split(';')[0]}?number=1"
            params = {}
            
            timeout = httpx.Timeout(connect=2.0, read=5.0, write=30.0, pool=5.0)
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)
                if 200 <= response.status_code < 300:
                    return {
                        "status": "ok",
                        "url": base_url,
                        "message": "OSRM erreichbar",
                        "circuit_state": self.circuit_state.value
                    }
                else:
                    # Versuche Route-API als Fallback-Test
                    route_url = f"{base}/route/v1/{self.profile}/{coord_string}"
                    route_params = {"overview": "false", "steps": "false"}
                    route_response = client.get(route_url, params=route_params, timeout=timeout)
                    if 200 <= route_response.status_code < 300:
                        data = route_response.json()
                        if data.get("code") == "Ok" and data.get("routes"):
                            return {
                                "status": "ok",
                                "url": base_url,
                                "message": "OSRM erreichbar",
                                "circuit_state": self.circuit_state.value
                            }
                    
                    return {
                        "status": "error",
                        "url": base_url,
                        "message": f"OSRM antwortet mit Status {response.status_code}",
                        "circuit_state": self.circuit_state.value
                    }
        except httpx.TimeoutException:
            return {
                "status": "error",
                "url": base_url,
                "message": "OSRM Timeout - nicht erreichbar",
                "circuit_state": self.circuit_state.value
            }
        except httpx.ConnectError:
            return {
                "status": "error",
                "url": base_url,
                "message": "OSRM Verbindungsfehler - Server nicht erreichbar",
                "circuit_state": self.circuit_state.value
            }
        except Exception as e:
            return {
                "status": "error",
                "url": base_url,
                "message": f"OSRM Fehler: {str(e)}",
                "circuit_state": self.circuit_state.value
            }

