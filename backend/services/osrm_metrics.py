"""
Metriken-Service für OSRM-Performance-Tracking.
Trackt Latenz, Fehlerrate, Circuit-Breaker-Status.
"""
import time
from typing import Dict, List, Optional
from collections import deque
from pathlib import Path
import json
from datetime import datetime


class OSRMMetrics:
    """Trackt OSRM-Performance-Metriken."""
    
    def __init__(self, max_samples: int = 1000):
        """
        Initialisiert Metriken-Service.
        
        Args:
            max_samples: Maximale Anzahl gespeicherter Samples
        """
        self.max_samples = max_samples
        
        # Latenz-Historie (in ms)
        self.latency_history: deque = deque(maxlen=max_samples)
        
        # Fehler-Historie
        self.error_history: deque = deque(maxlen=max_samples)
        
        # Zähler
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.timeout_requests = 0
        self.quota_errors = 0
        self.transient_errors = 0
        
        # Circuit-Breaker-Status
        self.circuit_breaker_state = "closed"
        self.circuit_breaker_trips = 0
        
        # Metadaten
        self.last_request_time: Optional[float] = None
        self.last_error_time: Optional[float] = None
        self.last_success_time: Optional[float] = None
    
    def record_request(
        self,
        latency_ms: float,
        success: bool = True,
        error_type: Optional[str] = None,
        circuit_state: Optional[str] = None
    ) -> None:
        """
        Zeichnet einen Request auf.
        
        Args:
            latency_ms: Latenz in Millisekunden
            success: Ob Request erfolgreich war
            error_type: Typ des Fehlers (timeout, quota, transient, etc.)
            circuit_state: Circuit-Breaker-Status
        """
        self.total_requests += 1
        self.last_request_time = time.time()
        
        if success:
            self.successful_requests += 1
            self.last_success_time = time.time()
            self.latency_history.append(latency_ms)
        else:
            self.failed_requests += 1
            self.last_error_time = time.time()
            self.error_history.append({
                "timestamp": time.time(),
                "latency_ms": latency_ms,
                "error_type": error_type or "unknown"
            })
            
            # Fehler-Typ-spezifische Zähler
            if error_type == "timeout":
                self.timeout_requests += 1
            elif error_type == "quota" or error_type == "402":
                self.quota_errors += 1
            elif error_type in ("transient", "502", "503", "504"):
                self.transient_errors += 1
        
        # Circuit-Breaker-Status aktualisieren
        if circuit_state:
            if circuit_state != self.circuit_breaker_state:
                if circuit_state == "open":
                    self.circuit_breaker_trips += 1
                self.circuit_breaker_state = circuit_state
    
    def get_stats(self) -> Dict[str, any]:
        """
        Gibt aktuelle Statistiken zurück.
        
        Returns:
            Dict mit Metriken
        """
        # Berechne Durchschnitts-Latenz
        avg_latency_ms = 0.0
        if self.latency_history:
            avg_latency_ms = sum(self.latency_history) / len(self.latency_history)
        
        # Berechne P95/P99 Latenz
        p95_latency_ms = 0.0
        p99_latency_ms = 0.0
        if self.latency_history:
            sorted_latencies = sorted(self.latency_history)
            p95_idx = int(len(sorted_latencies) * 0.95)
            p99_idx = int(len(sorted_latencies) * 0.99)
            p95_latency_ms = sorted_latencies[min(p95_idx, len(sorted_latencies) - 1)]
            p99_latency_ms = sorted_latencies[min(p99_idx, len(sorted_latencies) - 1)]
        
        # Fehlerrate berechnen
        error_rate = 0.0
        if self.total_requests > 0:
            error_rate = (self.failed_requests / self.total_requests) * 100
        
        # Erfolgsrate berechnen
        success_rate = 0.0
        if self.total_requests > 0:
            success_rate = (self.successful_requests / self.total_requests) * 100
        
        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "success_rate_pct": round(success_rate, 2),
            "error_rate_pct": round(error_rate, 2),
            "avg_latency_ms": round(avg_latency_ms, 2),
            "p95_latency_ms": round(p95_latency_ms, 2),
            "p99_latency_ms": round(p99_latency_ms, 2),
            "timeout_requests": self.timeout_requests,
            "quota_errors": self.quota_errors,
            "transient_errors": self.transient_errors,
            "circuit_breaker_state": self.circuit_breaker_state,
            "circuit_breaker_trips": self.circuit_breaker_trips,
            "last_request_time": self.last_request_time,
            "last_success_time": self.last_success_time,
            "last_error_time": self.last_error_time,
            "samples_count": len(self.latency_history)
        }
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict]:
        """
        Gibt letzte Fehler zurück.
        
        Args:
            limit: Maximale Anzahl Fehler
        
        Returns:
            Liste von Fehler-Dicts
        """
        return list(self.error_history)[-limit:]
    
    def reset(self) -> None:
        """Setzt alle Metriken zurück."""
        self.latency_history.clear()
        self.error_history.clear()
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.timeout_requests = 0
        self.quota_errors = 0
        self.transient_errors = 0
        self.circuit_breaker_trips = 0
        self.circuit_breaker_state = "closed"
        self.last_request_time = None
        self.last_error_time = None
        self.last_success_time = None


# Globale Instanz
_osrm_metrics_instance: Optional[OSRMMetrics] = None


def get_osrm_metrics() -> OSRMMetrics:
    """Gibt globale OSRM-Metriken-Instanz zurück."""
    global _osrm_metrics_instance
    if _osrm_metrics_instance is None:
        _osrm_metrics_instance = OSRMMetrics()
    return _osrm_metrics_instance

