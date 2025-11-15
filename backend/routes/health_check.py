from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from db.core import ENGINE

router = APIRouter()  # Kein prefix - Endpoints werden direkt registriert


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
    Einfach & robust: Nur SELECT 1, keine komplexe Prüflogik.
    """
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            result.fetchone()
        
        # Zusätzlich: Tabellen-Liste für Frontend
        try:
            tables_result = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
            tables = [row[0] for row in tables_result.fetchall()]
        except Exception as table_err:
            logger.debug(f"Failed to fetch table list: {table_err}")
            tables = []
        
        return JSONResponse({
            "ok": True,
            "status": "online",
            "tables": tables
        }, status_code=200)
    except Exception as e:
        return JSONResponse({
            "ok": False,
            "status": "offline",
            "error": str(e)
        }, status_code=503)

@router.get("/health/osrm")
async def health_osrm():
    """
    Prüft ob OSRM-Endpunkt erreichbar ist.
    Einfach & robust: Kurzer Health-Call mit Timeout.
    Erweitert: Latenz-Messung, Circuit-Breaker-Status, Retry-Info.
    """
    import httpx
    import os
    import time
    
    # Verwende OSRM-Client für korrekte URL
    try:
        from .workflow_api import get_osrm_client
        osrm_client = get_osrm_client()
        url = osrm_client.base_url
    except Exception as osrm_err:
        # Fallback: Prüfe env und config
        logger.debug(f"Failed to get OSRM client: {osrm_err}")
        url = os.getenv("OSRM_BASE_URL", "")
        if not url:
            from backend.config import cfg
            url = cfg("osrm:base_url", "http://127.0.0.1:5000")
    
    if not url:
        return JSONResponse({
            "ok": False,
            "reason": "no_osrm_url",
            "status": "unconfigured"
        }, status_code=503)
    
    # Versuche OSRM-Client zu nutzen (für Circuit-Breaker-Status)
    try:
        from .workflow_api import get_osrm_client
        osrm_client = get_osrm_client()
        circuit_state = osrm_client.circuit_state.value if hasattr(osrm_client, 'circuit_state') else "unknown"
    except Exception as circuit_err:
        logger.debug(f"Failed to get circuit breaker state: {circuit_err}")
        circuit_state = "unknown"
    
    start_time = time.time()
    try:
        # Kurzer Health-Call (billig) - nearest endpoint
        # Timeout erhöht auf 3s für langsamere Systeme
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{url}/nearest/v1/driving/13.7373,51.0504?number=1")
            latency_ms = int((time.time() - start_time) * 1000)
            
            is_ok = r.status_code == 200
            return JSONResponse({
                "ok": is_ok,
                "status": "up" if is_ok else "degraded",
                "url": url,
                "latency_ms": latency_ms,
                "circuit_breaker": circuit_state,
                "http_status": r.status_code
            }, status_code=200)
    except httpx.TimeoutException:
        latency_ms = int((time.time() - start_time) * 1000)
        return JSONResponse({
            "ok": False,
            "status": "timeout",
            "url": url,
            "latency_ms": latency_ms,
            "circuit_breaker": circuit_state,
            "error": "OSRM timeout (>3s)"
        }, status_code=503)
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        return JSONResponse({
            "ok": False,
            "status": "error",
            "url": url,
            "latency_ms": latency_ms,
            "circuit_breaker": circuit_state,
            "error": str(e)[:200]
        }, status_code=503)

@router.get("/health/osrm/sample-route")
async def health_osrm_sample():
    """Prüft ob OSRM Polyline6 zurückgibt."""
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        import httpx
        import time
        from .workflow_api import get_osrm_client
        from backend.config import cfg
        
        # Versuche OSRM-Client zu holen
        try:
            osrm_client = get_osrm_client()
            base_url = osrm_client.base_url if hasattr(osrm_client, 'base_url') else None
        except Exception as client_err:
            logger.warning(f"OSRM-Client konnte nicht initialisiert werden: {client_err}")
            base_url = None
        
        # Fallback auf Config
        if not base_url:
            base_url = cfg("osrm:base_url", "http://127.0.0.1:5000")
        
        profile = cfg("osrm:profile", "driving")
        
        # Probe-Koordinaten (Dresden)
        probe_a = "13.7373,51.0504"
        probe_b = "13.7283,51.0615"
        url = f"{base_url}/route/v1/{profile}/{probe_a};{probe_b}?overview=full&geometries=polyline6&steps=false"
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=5.0, follow_redirects=True) as client:
                r = await client.get(url)
                latency_ms = int((time.time() - start_time) * 1000)
                
                if r.status_code == 200:
                    try:
                        data = r.json()
                        poly = None
                        try:
                            poly = data["routes"][0]["geometry"]
                        except (KeyError, IndexError):
                            logger.warning(f"OSRM Response hat keine routes[0].geometry: {data}")
                        
                        return JSONResponse({
                            "ok": isinstance(poly, str) and len(poly) > 0,
                            "status": r.status_code,
                            "polyline6_len": len(poly) if isinstance(poly, str) else 0,
                            "latency_ms": latency_ms,
                            "url": url
                        }, status_code=200)
                    except Exception as json_err:
                        logger.error(f"Fehler beim Parsen der OSRM-Response: {json_err}")
                        return JSONResponse({
                            "ok": False,
                            "status": r.status_code,
                            "polyline6_len": 0,
                            "latency_ms": latency_ms,
                            "url": url,
                            "error": f"JSON-Parse-Fehler: {str(json_err)}"
                        }, status_code=503)
                else:
                    return JSONResponse({
                        "ok": False,
                        "status": r.status_code,
                        "polyline6_len": 0,
                        "latency_ms": latency_ms,
                        "url": url,
                        "error": f"HTTP {r.status_code}: {r.text[:200]}"
                    }, status_code=503)
        except httpx.TimeoutException:
            logger.warning(f"OSRM Timeout bei {url}")
            return JSONResponse({
                "ok": False,
                "status": 0,
                "polyline6_len": 0,
                "latency_ms": int((time.time() - start_time) * 1000),
                "url": url,
                "error": "Timeout: OSRM antwortet nicht"
            }, status_code=503)
        except httpx.ConnectError as conn_err:
            logger.warning(f"OSRM Verbindungsfehler: {conn_err}")
            return JSONResponse({
                "ok": False,
                "status": 0,
                "polyline6_len": 0,
                "latency_ms": int((time.time() - start_time) * 1000),
                "url": url,
                "error": f"Verbindungsfehler: OSRM nicht erreichbar ({base_url})"
            }, status_code=503)
    except Exception as e:
        logger.error(f"Unerwarteter Fehler in health_osrm_sample: {e}", exc_info=True)
        return JSONResponse({
            "ok": False,
            "status": 0,
            "polyline6_len": 0,
            "error": f"Interner Fehler: {str(e)}"
        }, status_code=500)

@router.get("/health/status")
async def health_status():
    """Kombinierter Status-Endpoint für Server, DB, OSRM und Systemregeln."""
    status = {
        "server": {"status": "ok", "message": "Server online"},
        "database": {"status": "unknown", "message": "Prüfe..."},
        "osrm": {"status": "unknown", "message": "Prüfe..."},
        "system_rules": {"status": "unknown", "message": "Prüfe..."}
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
        from .workflow_api import get_osrm_client
        osrm_client = get_osrm_client()
        health_result = osrm_client.check_health()
        # health_result ist ein OSRMHealth Pydantic-Model, nicht ein Dict
        if hasattr(health_result, 'reachable') and hasattr(health_result, 'sample_ok'):
            osrm_status = "ok" if (health_result.reachable and health_result.sample_ok) else "error"
            status["osrm"] = {
                "status": osrm_status,
                "message": f"OSRM {'erreichbar' if health_result.reachable else 'nicht erreichbar'}",
                "url": health_result.base_url
            }
        else:
            # Fallback: als Dict behandeln (für Kompatibilität)
            status["osrm"] = {
                "status": "ok" if health_result.get("reachable", False) else "error",
                "message": health_result.get("message", "OSRM-Status unbekannt"),
                "url": health_result.get("base_url", "unknown")
            }
    except Exception as e:
        status["osrm"] = {"status": "error", "message": f"OSRM-Prüfung fehlgeschlagen: {str(e)}", "url": "unknown"}
    
    # Systemregeln-Status
    try:
        from backend.services.system_rules_service import get_effective_system_rules
        rules = get_effective_system_rules()
        status["system_rules"] = {
            "status": "ok",
            "message": f"Systemregeln verfügbar (Quelle: {rules.source})",
            "source": rules.source
        }
    except Exception as e:
        status["system_rules"] = {
            "status": "error",
            "message": f"Systemregeln-Prüfung fehlgeschlagen: {str(e)}",
            "source": "unknown"
        }
    
    # Gesamt-Status: ok nur wenn alle ok sind
    all_ok = (
        status["server"]["status"] == "ok" and
        status["database"]["status"] == "ok" and
        status["osrm"]["status"] == "ok" and
        status["system_rules"]["status"] == "ok"
    )
    
    http_status = 200 if all_ok else 503
    
    return JSONResponse({
        "status": "ok" if all_ok else "degraded",
        "services": status
    }, status_code=http_status)
