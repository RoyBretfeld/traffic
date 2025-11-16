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
    """
    Prüft den Status der Datenbankverbindung.
    Gibt 503 zurück bei DB-Fehlern (nicht 500), damit klar ist dass es ein Service-Problem ist.
    """
    try:
        # Verwende connect() statt begin() für einfacheren Health-Check
        with ENGINE.connect() as conn:
            # Einfacher Query zur Prüfung der Verbindung
            result = conn.execute(text("SELECT 1"))
            result.fetchone()  # Result abrufen

        return JSONResponse({"status": "online"}, status_code=200)
    except Exception as e:
        error_details = str(e)
        # WICHTIG: 503 statt 500 - DB ist ein Service, nicht ein Server-Fehler
        return JSONResponse({"status": "offline", "error": error_details}, status_code=503)

@router.get("/health/osrm")
async def health_osrm():
    """
    Prüft ob OSRM-Endpunkt erreichbar ist.
    Testet mit einer echten Route-Anfrage (13.7373,51.0504 → 13.7283,51.0615).
    """
    try:
        import httpx
        import time
        from routes.workflow_api import get_osrm_client
        from backend.config import cfg
        
        osrm_client = get_osrm_client()
        base_url = cfg("osrm:base_url", "https://router.project-osrm.org")
        profile = cfg("osrm:profile", "driving")
        
        # Test-Route (Dresden)
        test_coords = "13.7373,51.0504;13.7283,51.0615"
        test_url = f"{base_url}/route/v1/{profile}/{test_coords}?overview=false"
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                r = await client.get(test_url)
                latency_ms = int((time.time() - start_time) * 1000)
                
                if r.status_code == 200:
                    return JSONResponse({
                        "status": "ok",
                        "url": base_url,
                        "router": "ok",
                        "profile": profile,
                        "latency_ms": latency_ms,
                        "mode": "remote" if "router.project-osrm.org" in base_url else "local",
                        "test_route_status": 200
                    }, status_code=200)
                else:
                    return JSONResponse({
                        "status": "down",
                        "url": base_url,
                        "router": "error",
                        "profile": profile,
                        "latency_ms": latency_ms,
                        "test_route_status": r.status_code,
                        "message": f"OSRM antwortet mit HTTP {r.status_code}"
                    }, status_code=503)
        except httpx.TimeoutException:
            return JSONResponse({
                "status": "down",
                "url": base_url,
                "router": "timeout",
                "profile": profile,
                "latency_ms": int((time.time() - start_time) * 1000),
                "message": "OSRM Timeout (>5s)"
            }, status_code=503)
        except Exception as req_error:
            return JSONResponse({
                "status": "down",
                "url": base_url,
                "router": "error",
                "profile": profile,
                "message": f"OSRM Request fehlgeschlagen: {str(req_error)}"
            }, status_code=503)
    except Exception as e:
        return JSONResponse({
            "status": "error",
            "url": "unknown",
            "message": f"Fehler beim Prüfen von OSRM: {str(e)}",
            "circuit_state": "unknown"
        }, status_code=500)

@router.get("/health/osrm/sample-route")
async def health_osrm_sample():
    """Prüft ob OSRM Polyline6 zurückgibt."""
    try:
        import httpx
        import time
        from routes.workflow_api import get_osrm_client
        from backend.config import cfg
        
        osrm_client = get_osrm_client()
        base_url = cfg("osrm:base_url", "https://router.project-osrm.org")
        profile = cfg("osrm:profile", "driving")
        
        # Probe-Koordinaten (Dresden)
        probe_a = "13.7373,51.0504"
        probe_b = "13.7283,51.0615"
        url = f"{base_url}/route/v1/{profile}/{probe_a};{probe_b}?overview=full&geometries=polyline6&steps=false"
        
        start_time = time.time()
        async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
            r = await client.get(url)
            latency_ms = int((time.time() - start_time) * 1000)
            
            if r.status_code == 200:
                data = r.json()
                poly = None
                try:
                    poly = data["routes"][0]["geometry"]
                except (KeyError, IndexError):
                    pass
                
                return JSONResponse({
                    "ok": isinstance(poly, str) and len(poly) > 0,
                    "status": r.status_code,
                    "polyline6_len": len(poly) if isinstance(poly, str) else 0,
                    "latency_ms": latency_ms,
                    "url": url
                }, status_code=200)
            else:
                return JSONResponse({
                    "ok": False,
                    "status": r.status_code,
                    "polyline6_len": 0,
                    "latency_ms": latency_ms,
                    "url": url,
                    "error": f"HTTP {r.status_code}"
                }, status_code=503)
    except Exception as e:
        return JSONResponse({
            "ok": False,
            "status": 0,
            "polyline6_len": 0,
            "error": str(e)
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
