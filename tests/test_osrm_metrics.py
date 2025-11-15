"""
Tests für OSRM-Metriken.
"""
import pytest
import time
from backend.services.osrm_metrics import OSRMMetrics, get_osrm_metrics


def test_osrm_metrics_initialization():
    """Test: Metriken-Initialisierung."""
    metrics = OSRMMetrics()
    assert metrics.total_requests == 0
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 0
    assert metrics.circuit_breaker_state == "closed"


def test_osrm_metrics_record_success():
    """Test: Erfolgreiche Requests aufzeichnen."""
    metrics = OSRMMetrics()
    
    metrics.record_request(latency_ms=100.0, success=True)
    metrics.record_request(latency_ms=200.0, success=True)
    metrics.record_request(latency_ms=150.0, success=True)
    
    assert metrics.total_requests == 3
    assert metrics.successful_requests == 3
    assert metrics.failed_requests == 0
    assert len(metrics.latency_history) == 3
    assert metrics.last_success_time is not None


def test_osrm_metrics_record_failure():
    """Test: Fehlgeschlagene Requests aufzeichnen."""
    metrics = OSRMMetrics()
    
    metrics.record_request(latency_ms=5000.0, success=False, error_type="timeout")
    metrics.record_request(latency_ms=100.0, success=False, error_type="quota")
    
    assert metrics.total_requests == 2
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 2
    assert metrics.timeout_requests == 1
    assert metrics.quota_errors == 1
    assert len(metrics.error_history) == 2
    assert metrics.last_error_time is not None


def test_osrm_metrics_stats():
    """Test: Statistiken berechnen."""
    metrics = OSRMMetrics()
    
    # 10 erfolgreiche Requests
    for i in range(10):
        metrics.record_request(latency_ms=100.0 + i * 10, success=True)
    
    # 2 fehlgeschlagene Requests
    metrics.record_request(latency_ms=5000.0, success=False, error_type="timeout")
    metrics.record_request(latency_ms=100.0, success=False, error_type="quota")
    
    stats = metrics.get_stats()
    
    assert stats["total_requests"] == 12
    assert stats["successful_requests"] == 10
    assert stats["failed_requests"] == 2
    assert stats["success_rate_pct"] == pytest.approx(83.33, abs=0.1)
    assert stats["error_rate_pct"] == pytest.approx(16.67, abs=0.1)
    assert stats["avg_latency_ms"] > 0
    assert stats["p95_latency_ms"] > 0
    assert stats["p99_latency_ms"] > 0
    assert stats["timeout_requests"] == 1
    assert stats["quota_errors"] == 1


def test_osrm_metrics_circuit_breaker():
    """Test: Circuit-Breaker-Status tracken."""
    metrics = OSRMMetrics()
    
    metrics.record_request(latency_ms=100.0, success=True, circuit_state="closed")
    metrics.record_request(latency_ms=200.0, success=False, error_type="timeout", circuit_state="open")
    
    stats = metrics.get_stats()
    assert stats["circuit_breaker_state"] == "open"
    assert stats["circuit_breaker_trips"] == 1


def test_osrm_metrics_recent_errors():
    """Test: Letzte Fehler abrufen."""
    metrics = OSRMMetrics()
    
    # 5 Fehler aufzeichnen
    for i in range(5):
        metrics.record_request(latency_ms=100.0 * i, success=False, error_type=f"error_{i}")
    
    recent_errors = metrics.get_recent_errors(limit=3)
    assert len(recent_errors) == 3
    assert recent_errors[0]["error_type"] == "error_2"  # Ältester der letzten 3
    assert recent_errors[-1]["error_type"] == "error_4"  # Neuester


def test_osrm_metrics_reset():
    """Test: Metriken zurücksetzen."""
    metrics = OSRMMetrics()
    
    metrics.record_request(latency_ms=100.0, success=True)
    metrics.record_request(latency_ms=200.0, success=False, error_type="timeout")
    
    metrics.reset()
    
    assert metrics.total_requests == 0
    assert metrics.successful_requests == 0
    assert metrics.failed_requests == 0
    assert len(metrics.latency_history) == 0
    assert len(metrics.error_history) == 0


def test_osrm_metrics_singleton():
    """Test: Singleton-Pattern für globale Instanz."""
    metrics1 = get_osrm_metrics()
    metrics2 = get_osrm_metrics()
    
    assert metrics1 is metrics2  # Gleiche Instanz


def test_osrm_metrics_max_samples():
    """Test: Maximale Anzahl Samples begrenzen."""
    metrics = OSRMMetrics(max_samples=10)
    
    # 20 Requests aufzeichnen
    for i in range(20):
        metrics.record_request(latency_ms=100.0, success=True)
    
    # Nur die letzten 10 sollten gespeichert sein
    assert len(metrics.latency_history) == 10
    assert metrics.total_requests == 20

