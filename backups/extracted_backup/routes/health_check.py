from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from db.core import ENGINE

router = APIRouter()


@router.get("/health")
async def health_root():
    """Einfache Health-Route als Liveness-Probe."""

    return JSONResponse({"status": "ok"}, status_code=200)

@router.get("/health/app")
async def health_app():
    """App-Health mit Feature-Flags und Konfiguration."""
    try:
        from backend.config import cfg
        return JSONResponse({
            "status": "ok",
            "env": cfg("app:env", "development"),
            "feature_flags": {
                "stats_box_enabled": cfg("app:feature_flags:stats_box_enabled", True),
                "ai_ops_enabled": cfg("app:feature_flags:ai_ops_enabled", False)
            },
            "osrm": {
                "base_url": cfg("osrm:base_url", "http://localhost:5000"),
                "fallback_enabled": cfg("osrm:fallback_enabled", True)
            }
        }, status_code=200)
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "error": str(e)
        }, status_code=500)

@router.get("/health/db")
async def health_db():
    try:
        # Verwende connect() statt begin() für einfacheren Health-Check
        with ENGINE.connect() as conn:
            # Einfacher Query zur Prüfung der Verbindung
            result = conn.execute(text("SELECT 1"))
            result.fetchone()  # Result abrufen

        return JSONResponse({"status": "online"}, status_code=200)
    except Exception as e:
        error_details = str(e)
        return JSONResponse({"status": "offline", "error": error_details}, status_code=500)

@router.get("/health/osrm")
async def health_osrm():
    """Prüft ob OSRM-Endpunkt erreichbar ist."""
    try:
        from routes.workflow_api import get_osrm_client
        osrm_client = get_osrm_client()
        health_result = osrm_client.check_health()
        
        if health_result["status"] == "ok":
            return JSONResponse(health_result, status_code=200)
        else:
            return JSONResponse(health_result, status_code=503)
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "url": "unknown",
            "message": f"Fehler beim Prüfen von OSRM: {str(e)}",
            "circuit_state": "unknown"
        }, status_code=500)

@router.get("/health/status")
async def health_status():
    """Kombinierter Status-Endpoint für Server, DB und OSRM."""
    status = {
        "server": {"status": "ok", "message": "Server online"},
        "database": {"status": "unknown", "message": "Prüfe..."},
        "osrm": {"status": "unknown", "message": "Prüfe..."}
    }
    
    # Datenbank-Status
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        status["database"] = {"status": "ok", "message": "Datenbank online"}
    except Exception as e:
        status["database"] = {"status": "error", "message": f"Datenbank-Fehler: {str(e)}"}
    
    # OSRM-Status
    try:
        from routes.workflow_api import get_osrm_client
        osrm_client = get_osrm_client()
        health_result = osrm_client.check_health()
        status["osrm"] = {
            "status": health_result["status"],
            "message": health_result["message"],
            "url": health_result.get("url", "unknown")
        }
    except Exception as e:
        status["osrm"] = {"status": "error", "message": f"OSRM-Prüfung fehlgeschlagen: {str(e)}", "url": "unknown"}
    
    # Gesamt-Status: ok nur wenn alle ok sind
    all_ok = (
        status["server"]["status"] == "ok" and
        status["database"]["status"] == "ok" and
        status["osrm"]["status"] == "ok"
    )
    
    http_status = 200 if all_ok else 503
    
    return JSONResponse({
        "status": "ok" if all_ok else "degraded",
        "services": status
    }, status_code=http_status)
