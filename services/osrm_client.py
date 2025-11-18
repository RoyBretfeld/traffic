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
from pydantic import BaseModel

from backend.config import cfg # Importiere cfg
from backend.utils.circuit_breaker import CircuitBreaker, breaker_osrm
from backend.utils.rate_limit import TokenBucket, rate_limiter_osrm
from backend.cache.osrm_cache import OsrmCache
from backend.services.osrm_metrics import get_osrm_metrics
from backend.utils.errors import TransientError, QuotaError

logger = logging.getLogger(__name__)

class OSRMHealth(BaseModel):
    base_url: str
    reachable: bool
    sample_ok: bool
    status_code: int | None = None
    message: str | None = None
    circuit_breaker_state: str
    circuit_breaker_failures: int
    circuit_breaker_open_since: float | None = None
    

class OSRMClient:
    """
    OSRM-Client mit Timeouts, Retry, Circuit-Breaker, Rate-Limiting und Cache-Integration.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Verwende OSRMSettings für Konfiguration (priorisiert OSRM_BASE_URL aus ENV/config.env)
        from backend.config import get_osrm_settings
        osrm_settings = get_osrm_settings()
        
        # Fallback auf cfg() wenn OSRMSettings nicht verfügbar
        self.base_url = osrm_settings.OSRM_BASE_URL
        self.profile = cfg("osrm:profile", "driving")
        self.connect_timeout = osrm_settings.OSRM_TIMEOUT_S * 0.3  # 30% für Connect
        self.read_timeout = osrm_settings.OSRM_TIMEOUT_S
        self.max_retries = osrm_settings.OSRM_RETRIES
        self.fallback_enabled = osrm_settings.FEATURE_OSRM_FALLBACK
        self.fallback_url = "https://router.project-osrm.org"
        
        self.logger.info(f"OSRM-Client initialisiert: {self.base_url} (Profil: {self.profile})")

        # Verfügbarkeits-Tracking (Kompatibilität zu älteren Aufrufern)
        self._available: bool | None = None
        self._last_health_check: float = 0.0
        self._health_check_interval: float = 60.0  # Sekunden

    def _refresh_availability(self) -> bool:
        """Führt einen Health-Check durch und cached das Ergebnis."""
        try:
            health = self.check_health()
            self._available = bool(health.reachable and health.sample_ok)
        except Exception:
            self._available = False
        self._last_health_check = time.time()
        return self._available

    @property
    def available(self) -> bool:
        """
        Kompatible Schnittstelle zu älteren Aufrufern.
        Führt höchstens alle `self._health_check_interval` Sekunden einen Health-Check aus.
        """
        if self._available is None:
            return self._refresh_availability()
        if (time.time() - self._last_health_check) > self._health_check_interval:
            return self._refresh_availability()
        return bool(self._available)

    def _make_request(
        self,
        url: str,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Optional[httpx.Response]:
        """
        Führt HTTP-Request mit Retry-Logik aus.
        """
        
        # Phase 2: Circuit Breaker Check
        if not breaker_osrm.allow():
            self.logger.warning("Circuit-Breaker: Request blockiert (OPEN)")
            get_osrm_metrics().record_request(
                latency_ms=0.0,
                success=False,
                error_type="circuit_breaker_open",
                circuit_state=breaker_osrm.get_state()
            )
            raise TransientError("OSRM Circuit Breaker ist OPEN")
            
        start_time = time.time()
        try:
            timeout = httpx.Timeout(
                connect=self.connect_timeout,
                read=self.read_timeout,
                write=30.0,
                pool=5.0
            )
            
            with httpx.Client(timeout=timeout) as client:
                response = client.get(url, params=params)
                latency_ms = (time.time() - start_time) * 1000
                response.raise_for_status()
                
                # Erfolg -> Circuit-Status aktualisieren
                breaker_osrm.record_success()
                get_osrm_metrics().record_request(
                    latency_ms=latency_ms,
                    success=True,
                    circuit_state=breaker_osrm.get_state()
                )
                self._available = True
                self._last_health_check = time.time()

                return response
                
        except httpx.TimeoutException as e:
            latency_ms = (time.time() - start_time) * 1000
            self.logger.warning(f"OSRM Timeout: {e}")
            breaker_osrm.record_failure()
            get_osrm_metrics().record_request(
                latency_ms=latency_ms,
                success=False,
                error_type="timeout",
                circuit_state=breaker_osrm.get_state()
            )
            
            if retry_count < self.max_retries:
                self.logger.info(f"Retry {retry_count + 1}/{self.max_retries}")
                time.sleep(0.3 * (retry_count + 1))  # Exponential Backoff
                return self._make_request(url, params, retry_count + 1)
            raise TransientError("OSRM Timeout nach Retries")
            
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            latency_ms = (time.time() - start_time) * 1000
            
            if status_code == 402:
                self.logger.warning(f"OSRM Quota-Fehler (402) -> Mappe zu QuotaError: {e}")
                breaker_osrm.record_failure()
                get_osrm_metrics().record_request(
                    latency_ms=latency_ms,
                    success=False,
                    error_type="quota",
                    circuit_state=breaker_osrm.get_state()
                )
                self._available = False
                self._last_health_check = time.time()
                raise QuotaError("OSRM quota exceeded (402)")
            elif status_code in (502, 503, 504):
                self.logger.warning(f"OSRM Transient-Fehler ({status_code}): {e}")
                breaker_osrm.record_failure()
                get_osrm_metrics().record_request(
                    latency_ms=latency_ms,
                    success=False,
                    error_type="transient",
                    circuit_state=breaker_osrm.get_state()
                )
                self._available = False
                self._last_health_check = time.time()
                if retry_count < self.max_retries:
                    self.logger.info(f"Retry {retry_count + 1}/{self.max_retries}")
                    time.sleep(0.3 * (retry_count + 1))  # Exponential Backoff
                    return self._make_request(url, params, retry_count + 1)
                raise TransientError(f"OSRM transient error ({status_code}) nach Retries")
            else:
                self.logger.warning(f"OSRM HTTP-Fehler {status_code}: {e}")
                breaker_osrm.record_failure()
                get_osrm_metrics().record_request(
                    latency_ms=latency_ms,
                    success=False,
                    error_type=f"http_{status_code}",
                    circuit_state=breaker_osrm.get_state()
                )
                self._available = False
                self._last_health_check = time.time()
                raise RuntimeError(f"OSRM unerwarteter HTTP-Fehler ({status_code})")
            
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000
            self.logger.error(f"OSRM unerwarteter Fehler: {e}", exc_info=True)
            breaker_osrm.record_failure()
            get_osrm_metrics().record_request(
                latency_ms=latency_ms,
                success=False,
                error_type="unexpected",
                circuit_state=breaker_osrm.get_state()
            )
            self._available = False
            self._last_health_check = time.time()
            raise RuntimeError("OSRM unerwarteter Fehler")
    
    def get_distance_matrix(
        self,
        coords: List[Tuple[float, float]],
        sources: Optional[List[int]] = None,
        destinations: Optional[List[int]] = None
    ) -> Optional[Dict[Tuple[int, int], Dict[str, float]]]:
        """
        Berechnet Distanz-Matrix mit OSRM Table API.
        """
        if len(coords) < 2:
            return None
        
        coord_string = ";".join(f"{lon},{lat}" for lat, lon in coords)
        
        base = self.base_url.rstrip("/")
        url = f"{base}/table/v1/{self.profile}/{coord_string}"
        params = {"annotations": "distance,duration"}
        
        if sources is not None:
            params["sources"] = ";".join(str(i) for i in sources)
        if destinations is not None:
            params["destinations"] = ";".join(str(i) for i in destinations)
        
        try:
            response = self._make_request(url, params)
            if not response:
                return None
            
            data = response.json()
            distances = data.get("distances", [])
            durations = data.get("durations", [])
            
            if not distances or not durations:
                self.logger.warning("OSRM Table API: Keine Distanzen/Dauern zurückgegeben")
                return None
            
            matrix = {}
            
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
                        distance_km = distances[idx_i][idx_j] / 1000.0
                        duration_min = durations[idx_i][idx_j] / 60.0
                        matrix[(i, j)] = {
                            "km": round(distance_km, 2),
                            "minutes": round(duration_min, 2)
                        }
            
            return matrix
            
        except (TransientError, QuotaError, RuntimeError) as e:
            self.logger.warning(f"OSRM Table API Fehler: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen von OSRM Table API Response: {e}")
            return None
    
    def get_route(
        self,
        coords: List[Tuple[float, float]],
        use_polyline6: bool = False,
        avoid_incidents: bool = True,
        timeout: Optional[float] = None
    ) -> Optional[Dict]:
        """
        Berechnet Route mit OSRM Route API (für Visualisierung).
        
        Phase 2: Mit Cache-Integration und Rate Limiting.
        """
        if len(coords) < 2:
            return None
        
        # Phase 2: Rate Limiter-Check
        try:
            if rate_limiter_osrm and not rate_limiter_osrm.allow():
                wait_time = rate_limiter_osrm.wait_time()
                self.logger.warning(f"Rate Limit erreicht, warte {wait_time:.2f}s")
                time.sleep(wait_time)
        except Exception as e:
            self.logger.debug(f"Rate Limiter nicht verfügbar: {e}")
        
        # Phase 2: Cache-Check
        try:
            import hashlib
            import json
            
            cache_params = {
                "coords": coords,
                "profile": self.profile,
                "overview": "full",
                "geometries": "polyline6" if use_polyline6 else "polyline"
            }
            cache_key = hashlib.sha256(
                json.dumps(cache_params, sort_keys=True).encode()
            ).hexdigest()
            
            cached = OsrmCache.get(cache_key)
            if cached:
                self.logger.debug(f"OSRM-Cache-Hit für {len(coords)} Koordinaten")
                return {
                    "geometry": cached["geometry_polyline6"],
                    "distance_m": cached["distance_m"],
                    "duration_s": cached["duration_s"],
                    "distance_km": cached["distance_m"] / 1000.0,
                    "duration_min": cached["duration_s"] / 60.0,
                    "cached": True
                }
        except Exception as e:
            self.logger.debug(f"Cache-Check fehlgeschlagen: {e}")
        
        coord_string = ";".join(f"{lon},{lat}" for lat, lon in coords)
        
        base = self.base_url.rstrip("/")
        url = f"{base}/route/v1/{self.profile}/{coord_string}"
        params = {
            "overview": "full",
            "steps": "false",
            "geometries": "polyline6" if use_polyline6 else "polyline"
        }
        
        response = None
        try:
            # Wenn timeout übergeben wurde, verwende es für diesen Request
            # Ansonsten verwendet _make_request() das Standard-Timeout
            if timeout is not None:
                # Temporär Timeout überschreiben (für diesen Request)
                original_read_timeout = self.read_timeout
                self.read_timeout = timeout
                try:
                    response = self._make_request(url, params)
                finally:
                    self.read_timeout = original_read_timeout
            else:
                response = self._make_request(url, params)
        except (TransientError, QuotaError, RuntimeError) as e:
            self.logger.warning(f"Primärer OSRM-Server Fehler: {e}")
            
        if not response and self.fallback_enabled and self.base_url != self.fallback_url:
            self.logger.info(f"Primärer OSRM-Server nicht verfügbar, versuche Fallback: {self.fallback_url}")
            base = self.fallback_url.rstrip("/")
            url = f"{base}/route/v1/{self.profile}/{coord_string}"
            try:
                # Fallback auch mit Timeout (wenn gesetzt)
                if timeout is not None:
                    original_read_timeout = self.read_timeout
                    self.read_timeout = timeout
                    try:
                        response = self._make_request(url, params)
                    finally:
                        self.read_timeout = original_read_timeout
                else:
                    response = self._make_request(url, params)
            except (TransientError, QuotaError, RuntimeError) as e:
                self.logger.warning(f"Fallback OSRM-Server Fehler: {e}")
        
        if not response:
            return None
        
        try:
            data = response.json()
            routes = data.get("routes", [])
            if not routes:
                return None
            
            route = routes[0]
            result = {
                "geometry": route.get("geometry"),
                "distance_m": route.get("distance"),
                "duration_s": route.get("duration"),
                "distance_km": route.get("distance", 0) / 1000.0,
                "duration_min": route.get("duration", 0) / 60.0,
                "cached": False
            }
            
            try:
                cache_params = {
                    "coords": coords,
                    "profile": self.profile,
                    "overview": "full",
                    "geometries": "polyline6" if use_polyline6 else "polyline"
                }
                cache_key = hashlib.sha256(
                    json.dumps(cache_params, sort_keys=True).encode()
                ).hexdigest()
                
                OsrmCache.put(cache_key, {
                    "geometry_polyline6": result["geometry"],
                    "distance_m": result["distance_m"],
                    "duration_s": result["duration_s"]
                })
            except Exception as e:
                self.logger.debug(f"Cache-Speichern fehlgeschlagen: {e}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen von OSRM Route API Response: {e}")
            return None
    
    def check_health(self) -> OSRMHealth:
        """
        Prüft ob OSRM tatsächlich erreichbar ist durch einen Test-Request und gibt OSRMHealth zurück.
        """
        test_coords = [
            (51.0493, 13.7381),
            (51.0639, 13.7522)
        ]
        
        # Versuche primären Server
        result = self._test_health_for_url(self.base_url, test_coords)
        if result.reachable and result.sample_ok:
            return result
        
        # Wenn primärer Server nicht verfügbar und Fallback aktiviert
        if self.fallback_enabled and self.base_url != self.fallback_url:
            self.logger.info(f"Primärer OSRM-Server nicht verfügbar, teste Fallback: {self.fallback_url}")
            result_fallback = self._test_health_for_url(self.fallback_url, test_coords)
            if result_fallback.reachable and result_fallback.sample_ok:
                result_fallback.message = f"OSRM erreichbar (Fallback: {self.fallback_url})"
                result_fallback.base_url = f"{self.base_url} (Fallback: {self.fallback_url})"
            return result_fallback
        
        return result
    
    def _test_health_for_url(self, base_url: str, test_coords: List[Tuple[float, float]]) -> OSRMHealth:
        """
        Testet einen spezifischen OSRM-URL und gibt OSRMHealth zurück.
        """
        try:
            coord_string = ";".join(f"{lon},{lat}" for lat, lon in test_coords)
            base = base_url.rstrip("/")
            
            # Test mit /nearest
            nearest_url = f"{base}/nearest/v1/{self.profile}/{coord_string.split(';')[0]}?number=1"
            timeout_obj = httpx.Timeout(connect=2.0, read=5.0)
            
            with httpx.Client(timeout=timeout_obj) as client:
                nearest_response = client.get(nearest_url)
                
                if 200 <= nearest_response.status_code < 300:
                    return OSRMHealth(
                        base_url=base_url,
                        reachable=True,
                        sample_ok=True,
                        status_code=nearest_response.status_code,
                        message="OSRM erreichbar",
                        circuit_breaker_state=breaker_osrm.get_state(),
                        circuit_breaker_failures=breaker_osrm.fail_count,
                        circuit_breaker_open_since=breaker_osrm.open_since
                    )
                else:
                    # Fallback auf Route-API
                    route_url = f"{base}/route/v1/{self.profile}/{coord_string}"
                    route_response = client.get(route_url, timeout=timeout_obj)
                    if 200 <= route_response.status_code < 300:
                        data = route_response.json()
                        if data.get("code") == "Ok" and data.get("routes"):
                            return OSRMHealth(
                                base_url=base_url,
                                reachable=True,
                                sample_ok=True,
                                status_code=route_response.status_code,
                                message="OSRM erreichbar",
                                circuit_breaker_state=breaker_osrm.get_state(),
                                circuit_breaker_failures=breaker_osrm.fail_count,
                                circuit_breaker_open_since=breaker_osrm.open_since
                            )
                            
                    return OSRMHealth(
                        base_url=base_url,
                        reachable=True,
                        sample_ok=False,
                        status_code=nearest_response.status_code,
                        message=f"OSRM antwortet mit Status {nearest_response.status_code}",
                        circuit_breaker_state=breaker_osrm.get_state(),
                        circuit_breaker_failures=breaker_osrm.fail_count,
                        circuit_breaker_open_since=breaker_osrm.open_since
                    )
        except httpx.TimeoutException:
            return OSRMHealth(
                base_url=base_url,
                reachable=False,
                sample_ok=False,
                message="OSRM Timeout - nicht erreichbar",
                circuit_breaker_state=breaker_osrm.get_state(),
                circuit_breaker_failures=breaker_osrm.fail_count,
                circuit_breaker_open_since=breaker_osrm.open_since
            )
        except httpx.ConnectError:
            return OSRMHealth(
                base_url=base_url,
                reachable=False,
                sample_ok=False,
                message="OSRM Verbindungsfehler - Server nicht erreichbar",
                circuit_breaker_state=breaker_osrm.get_state(),
                circuit_breaker_failures=breaker_osrm.fail_count,
                circuit_breaker_open_since=breaker_osrm.open_since
            )
        except Exception as e:
            return OSRMHealth(
                base_url=base_url,
                reachable=False,
                sample_ok=False,
                message=f"OSRM Fehler: {str(e)}",
                circuit_breaker_state=breaker_osrm.get_state(),
                circuit_breaker_failures=breaker_osrm.fail_count,
                circuit_breaker_open_since=breaker_osrm.open_since
            )

