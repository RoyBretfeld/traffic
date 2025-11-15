"""
Circuit Breaker (leichtgewichtig, in-proc) für Phase 2 Runbook.
"""
import os
import time
from typing import Callable, Type


class CircuitBreaker:
    """
    Circuit Breaker für robuste Fehlerbehandlung.
    
    States:
    - CLOSED: Normal, Requests erlaubt
    - OPEN: Zu viele Fehler → Requests blockiert
    - HALF_OPEN: Test-Phase nach Timeout
    """
    
    def __init__(self, max_failures: int = 5, reset_timeout: int = 60):
        """
        Initialisiert Circuit Breaker.
        
        Args:
            max_failures: Maximale Fehleranzahl bevor OPEN
            reset_timeout: Sekunden bis HALF_OPEN (Standard: 60)
        """
        self.max_failures = max_failures
        self.reset_timeout = reset_timeout
        self.fail_count = 0
        self.state = "CLOSED"  # CLOSED | OPEN | HALF_OPEN
        self.open_since = 0.0
        self.last_failure_time = None
    
    def _trip(self):
        """Öffnet den Circuit Breaker."""
        self.state = "OPEN"
        self.open_since = time.time()
        self.last_failure_time = time.time()
    
    def _can_half_open(self) -> bool:
        """Prüft ob HALF_OPEN möglich ist (nach Timeout)."""
        return (time.time() - self.open_since) >= self.reset_timeout
    
    def allow(self) -> bool:
        """
        Prüft ob Request erlaubt ist.
        
        Returns:
            True wenn Request erlaubt, False wenn blockiert
        """
        if self.state == "OPEN":
            if self._can_half_open():
                self.state = "HALF_OPEN"
                return True
            return False
        return True  # CLOSED oder HALF_OPEN
    
    def record_success(self):
        """Zeichnet Erfolg auf → Circuit schließen."""
        self.fail_count = 0
        self.state = "CLOSED"
        self.open_since = 0.0
        self.last_failure_time = None
    
    def record_failure(self):
        """Zeichnet Fehler auf → Circuit möglicherweise öffnen."""
        self.fail_count += 1
        self.last_failure_time = time.time()
        
        if self.state == "HALF_OPEN":
            # HALF_OPEN → OPEN (Test fehlgeschlagen)
            self._trip()
        elif self.state == "CLOSED":
            if self.fail_count >= self.max_failures:
                self._trip()
    
    def get_state(self) -> str:
        """Gibt aktuellen Zustand zurück."""
        return self.state
    
    def reset(self):
        """Setzt Circuit Breaker zurück (für Tests)."""
        self.fail_count = 0
        self.state = "CLOSED"
        self.open_since = 0.0
        self.last_failure_time = None


# Globale Instanz für OSRM
breaker_osrm = CircuitBreaker(
    max_failures=int(os.getenv("OSRM_BREAKER_MAX_FAILS", "5")),
    reset_timeout=int(os.getenv("OSRM_BREAKER_RESET_SEC", "60"))
)

