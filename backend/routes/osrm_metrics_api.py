"""
API-Endpoints für OSRM-Metriken.
"""
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from backend.services.osrm_metrics import get_osrm_metrics

router = APIRouter()


@router.get("/api/osrm/metrics")
async def get_osrm_metrics_endpoint():
    """
    Gibt aktuelle OSRM-Metriken zurück.
    
    Response:
    {
        "total_requests": 100,
        "successful_requests": 95,
        "failed_requests": 5,
        "success_rate_pct": 95.0,
        "error_rate_pct": 5.0,
        "avg_latency_ms": 123.45,
        "p95_latency_ms": 200.0,
        "p99_latency_ms": 300.0,
        "timeout_requests": 2,
        "quota_errors": 1,
        "transient_errors": 2,
        "circuit_breaker_state": "closed",
        "circuit_breaker_trips": 0,
        "last_request_time": 1234567890.0,
        "last_success_time": 1234567890.0,
        "last_error_time": 1234567880.0,
        "samples_count": 100
    }
    """
    metrics = get_osrm_metrics()
    stats = metrics.get_stats()
    return JSONResponse(stats)


@router.get("/api/osrm/metrics/errors")
async def get_osrm_errors(limit: int = 10):
    """
    Gibt letzte OSRM-Fehler zurück.
    
    Args:
        limit: Maximale Anzahl Fehler (Standard: 10)
    
    Response:
    {
        "errors": [
            {
                "timestamp": 1234567890.0,
                "latency_ms": 5000.0,
                "error_type": "timeout"
            },
            ...
        ],
        "count": 10
    }
    """
    metrics = get_osrm_metrics()
    errors = metrics.get_recent_errors(limit=limit)
    return JSONResponse({
        "errors": errors,
        "count": len(errors)
    })


@router.post("/api/osrm/metrics/reset")
async def reset_osrm_metrics():
    """
    Setzt alle OSRM-Metriken zurück.
    
    Response:
    {
        "success": true,
        "message": "Metriken zurückgesetzt"
    }
    """
    metrics = get_osrm_metrics()
    metrics.reset()
    return JSONResponse({
        "success": True,
        "message": "Metriken zurückgesetzt"
    })

