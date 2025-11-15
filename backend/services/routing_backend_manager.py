"""
Routing-Backend-Manager mit Circuit Breaker

Verwaltet mehrere Routing-Backends (OSRM, Valhalla, GraphHopper, lokale Haversine)
mit Circuit Breaker-Pattern für robuste Backend-Auswahl.
"""

import time
import logging
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum
from dataclasses import dataclass
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit-Breaker Zustände"""
    CLOSED = "closed"      # Normal - Requests erlaubt
    OPEN = "open"          # Fehler → blockiert
    HALF_OPEN = "half_open"  # Test-Phase


@dataclass
class BackendStatus:
    """Status eines Routing-Backends"""
    name: str
    url: Optional[str]
    circuit_state: CircuitState
    failure_count: int
    last_failure_time: Optional[float]
    last_success_time: Optional[float]
    latency_ms: Optional[float]
    enabled: bool = True


class RoutingBackendManager:
    """
    Verwaltet mehrere Routing-Backends mit Circuit Breaker.
    
    Circuit Breaker Logik:
    - 3 Fehler in 60s → OPEN (2 min gesperrt)
    - Nach 2 min → HALF_OPEN (Test-Phase)
    - Erfolg in HALF_OPEN → CLOSED
    - Fehler in HALF_OPEN → OPEN (weitere 2 min)
    """
    
    def __init__(self):
        self.backends: Dict[str, BackendStatus] = {}
        self.trip_threshold = 3  # Fehler innerhalb 60s → OPEN
        self.trip_window = 60   # 60 Sekunden
        self.open_timeout = 120  # 2 Minuten in OPEN
        self.half_open_timeout = 30  # 30 Sekunden in HALF_OPEN
        
    def register_backend(
        self,
        name: str,
        url: Optional[str] = None,
        enabled: bool = True
    ):
        """Registriert ein Routing-Backend"""
        self.backends[name] = BackendStatus(
            name=name,
            url=url,
            circuit_state=CircuitState.CLOSED,
            failure_count=0,
            last_failure_time=None,
            last_success_time=None,
            latency_ms=None,
            enabled=enabled
        )
        logger.info(f"Backend registriert: {name} (URL: {url}, enabled: {enabled})")
    
    def _check_circuit_breaker(self, backend_name: str) -> bool:
        """
        Prüft Circuit-Breaker Zustand.
        
        Returns:
            True wenn Request erlaubt, False wenn blockiert
        """
        if backend_name not in self.backends:
            return False
        
        backend = self.backends[backend_name]
        now = time.time()
        
        if backend.circuit_state == CircuitState.CLOSED:
            # Reset failure_count wenn außerhalb Zeitfenster
            if backend.last_failure_time:
                if (now - backend.last_failure_time) > self.trip_window:
                    backend.failure_count = 0
            return True
        
        elif backend.circuit_state == CircuitState.OPEN:
            # Prüfe ob wir zu HALF_OPEN wechseln können
            if backend.last_failure_time:
                if (now - backend.last_failure_time) >= self.open_timeout:
                    backend.circuit_state = CircuitState.HALF_OPEN
                    logger.info(f"Circuit-Breaker {backend_name}: OPEN → HALF_OPEN (Test-Phase)")
                    return True
            return False
        
        elif backend.circuit_state == CircuitState.HALF_OPEN:
            # In HALF_OPEN erlauben wir einen Test-Request
            return True
        
        return False
    
    def _record_success(self, backend_name: str, latency_ms: Optional[float] = None):
        """Zeichnet Erfolg auf → Circuit schließen"""
        if backend_name not in self.backends:
            return
        
        backend = self.backends[backend_name]
        backend.last_success_time = time.time()
        backend.latency_ms = latency_ms
        
        if backend.circuit_state == CircuitState.HALF_OPEN:
            backend.circuit_state = CircuitState.CLOSED
            backend.failure_count = 0
            logger.info(f"Circuit-Breaker {backend_name}: HALF_OPEN → CLOSED (Erfolg)")
        elif backend.circuit_state == CircuitState.CLOSED:
            # Reset failure_count nach erfolgreichem Request
            if backend.last_failure_time:
                if (time.time() - backend.last_failure_time) > self.trip_window:
                    backend.failure_count = 0
    
    def _record_failure(self, backend_name: str):
        """Zeichnet Fehler auf → Circuit möglicherweise öffnen"""
        if backend_name not in self.backends:
            return
        
        backend = self.backends[backend_name]
        backend.failure_count += 1
        backend.last_failure_time = time.time()
        
        if backend.circuit_state == CircuitState.HALF_OPEN:
            # HALF_OPEN → OPEN (Test fehlgeschlagen)
            backend.circuit_state = CircuitState.OPEN
            logger.warning(f"Circuit-Breaker {backend_name}: HALF_OPEN → OPEN (Test fehlgeschlagen)")
        elif backend.circuit_state == CircuitState.CLOSED:
            # Prüfe ob wir zu OPEN wechseln müssen
            now = time.time()
            if backend.last_failure_time:
                # Reset failure_count wenn außerhalb Zeitfenster
                window_start = now - self.trip_window
                if backend.last_failure_time < window_start:
                    backend.failure_count = 1
                
                # Wenn 3 Fehler innerhalb 60s → OPEN
                if backend.failure_count >= self.trip_threshold:
                    backend.circuit_state = CircuitState.OPEN
                    logger.warning(f"Circuit-Breaker {backend_name}: CLOSED → OPEN ({backend.failure_count} Fehler)")
    
    def get_available_backend(self, priority: List[str]) -> Optional[str]:
        """
        Gibt das erste verfügbare Backend zurück (basierend auf Priorität und Circuit Breaker).
        
        Args:
            priority: Liste von Backend-Namen in Prioritätsreihenfolge
        
        Returns:
            Backend-Name oder None wenn keines verfügbar
        """
        for backend_name in priority:
            if backend_name not in self.backends:
                continue
            
            backend = self.backends[backend_name]
            
            # Prüfe ob Backend enabled ist
            if not backend.enabled:
                continue
            
            # Prüfe Circuit Breaker
            if self._check_circuit_breaker(backend_name):
                return backend_name
        
        return None
    
    def get_backend_status(self, backend_name: str) -> Optional[Dict[str, Any]]:
        """Gibt Status eines Backends zurück"""
        if backend_name not in self.backends:
            return None
        
        backend = self.backends[backend_name]
        return {
            "name": backend.name,
            "url": backend.url,
            "circuit_state": backend.circuit_state.value,
            "failure_count": backend.failure_count,
            "last_failure_time": backend.last_failure_time,
            "last_success_time": backend.last_success_time,
            "latency_ms": backend.latency_ms,
            "enabled": backend.enabled,
            "available": self._check_circuit_breaker(backend_name)
        }
    
    def get_all_backend_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Gibt Status aller Backends zurück"""
        return {
            name: self.get_backend_status(name)
            for name in self.backends.keys()
        }


# Globale Instanz
_backend_manager = None

def get_backend_manager() -> RoutingBackendManager:
    """Lazy-Initialisierung des Backend-Managers"""
    global _backend_manager
    if _backend_manager is None:
        _backend_manager = RoutingBackendManager()
    return _backend_manager

