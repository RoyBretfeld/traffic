"""
App-Setup-Module für FastAPI-App.
Teilt die create_app Funktion in logische Module auf.
"""
from pathlib import Path
from typing import Optional
from fastapi import FastAPI
import logging
import os

logger = logging.getLogger(__name__)


def setup_config_directory() -> None:
    """Stellt sicher, dass das config-Verzeichnis existiert."""
    from pathlib import Path
    config_dir = Path("config")
    config_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Config-Verzeichnis sichergestellt: {config_dir.absolute()}")


def setup_app_state(app: FastAPI) -> None:
    """Konfiguriert app.state mit Settings und DB-Pfad."""
    from backend.config import get_osrm_settings
    from db.core import ENGINE
    
    # Settings laden
    osrm_settings = get_osrm_settings()
    
    # Settings in app.state speichern
    app.state.osrm_settings = osrm_settings
    try:
        app.state.db_path = Path(ENGINE.url.database or "app.db").resolve()
    except Exception:
        app.state.db_path = None
    
    # Boot-Log
    logger.info("=" * 70)
    logger.info("App-Factory: Initialisiere TrafficApp")
    logger.info("=" * 70)
    logger.info("DB URL: %s", ENGINE.url)
    if app.state.db_path:
        logger.info("DB Pfad: %s", app.state.db_path)
    logger.info("OSRM URL: %s", osrm_settings.OSRM_BASE_URL)


def setup_database_schema() -> None:
    """Sichert DB-Schema."""
    try:
        from db.schema import ensure_schema
        ensure_schema()
        logger.info("DB-Schema verifiziert")
    except Exception as e:
        logger.error("DB-Schema-Verifizierung fehlgeschlagen: %s", e)
        # Start nicht abbrechen, aber warnen


def setup_middleware(app: FastAPI) -> None:
    """Konfiguriert Middleware."""
    from backend.core.error_handlers import http_exception_handler, RequestIdMiddleware
    from backend.middlewares.trace_id import TraceIDMiddleware
    from backend.middlewares.error_tally import error_tally
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.exceptions import HTTPException
    
    # Exception Handler
    app.add_exception_handler(HTTPException, http_exception_handler)
    
    # Middleware (Reihenfolge wichtig!)
    # Error-Tally muss VOR anderen Middlewares sein, um alle Responses zu erfassen
    app.middleware("http")(error_tally)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(TraceIDMiddleware)
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def setup_static_files(app: FastAPI) -> None:
    """Konfiguriert Static Files."""
    from fastapi.staticfiles import StaticFiles
    from pathlib import Path
    import os
    
    # Konfigurierbarer Pfad für Static Files
    frontend_dir = os.getenv("FRONTEND_DIR", "frontend")
    frontend_path = Path(frontend_dir)
    
    if not frontend_path.exists():
        logger.warning(f"Frontend-Verzeichnis nicht gefunden: {frontend_path}")
        return
    
    # Static Files
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")


def setup_routers(app: FastAPI) -> None:
    """Registriert alle Router."""
    # Importiere alle Router
    from backend.routes.tourplan_match import router as tourplan_match_router
    from backend.routes.tourplan_geofill import router as tourplan_geofill_router
    from backend.routes.tourplaene_list import router as tourplaene_list_router
    from backend.routes.tourplan_status import router as tourplan_status_router
    from backend.routes.tourplan_suggest import router as tourplan_suggest_router
    from backend.routes.tourplan_accept import router as tourplan_accept_router
    from backend.routes.audit_geo import router as audit_geo_router
    from backend.routes.failcache_api import router as failcache_api_router
    from backend.routes.failcache_clear import router as failcache_clear_router
    from backend.routes.failcache_improved import router as failcache_improved_router
    from backend.routes.tourplan_manual_geo import router as tourplan_manual_geo_router
    from backend.routes.debug_geo import router as debug_geo_router
    from backend.routes.manual_api import router as manual_api_router
    from backend.routes.tourplan_bulk_analysis import router as tourplan_bulk_analysis_router
    from backend.routes.tourplan_triage import router as tourplan_triage_router
    from backend.routes.tourplan_bulk_process import router as tourplan_bulk_process_router
    from backend.routes.upload_csv import router as upload_csv_router
    from backend.routes.audit_geocoding import router as audit_geocoding_router
    from backend.routes.workflow_api import router as workflow_api_router
    from backend.routes.audit_status import router as audit_status_router
    from backend.routes.health_check import router as health_check_router
    from backend.routes.summary_api import router as summary_api_router
    from backend.routes.test_dashboard_api import router as test_dashboard_router
    from backend.routes.address_recognition_api import router as address_recognition_router
    from backend.routes.endpoint_flow_api import router as endpoint_flow_router
    from backend.routes.ai_test_api import router as ai_test_router
    from backend.routes.backup_api import router as backup_api_router
    from backend.routes.engine_api import router as engine_api_router
    from backend.routes.coordinate_verify_api import router as coordinate_verify_router
    from backend.routes.stats_api import router as stats_api_router
    from backend.routes.live_traffic_api import router as live_traffic_api_router
    from backend.routes.ki_improvements_api import router as ki_improvements_api_router
    from backend.routes.code_checker_api import router as code_checker_api_router
    from backend.routes.code_improvement_job_api import router as code_improvement_job_api_router
    from backend.routes.osrm_metrics_api import router as osrm_metrics_api_router
    from backend.routes.health import router as health_routes
    from backend.routes.debug_health import router as debug_health_router
    from backend.routes.auth_api import router as auth_router
    from backend.routes.system_rules_api import router as system_rules_api_router
    from backend.routes.db_management_api import router as db_management_api_router
    
    # Registriere alle Router
    routers = [
        tourplan_match_router,
        tourplan_geofill_router,
        tourplaene_list_router,
        tourplan_status_router,
        tourplan_suggest_router,
        tourplan_accept_router,
        audit_geo_router,
        failcache_api_router,
        failcache_clear_router,
        failcache_improved_router,
        tourplan_manual_geo_router,
        debug_geo_router,
        manual_api_router,
        tourplan_bulk_analysis_router,
        tourplan_triage_router,
        tourplan_bulk_process_router,
        upload_csv_router,
        audit_geocoding_router,
        workflow_api_router,
        audit_status_router,
        health_check_router,
        summary_api_router,
        test_dashboard_router,
        address_recognition_router,
        endpoint_flow_router,
        ai_test_router,
        backup_api_router,
        engine_api_router,
        auth_router,
        coordinate_verify_router,
        stats_api_router,
        live_traffic_api_router,
        ki_improvements_api_router,
        code_checker_api_router,
        code_improvement_job_api_router,
        osrm_metrics_api_router,
        health_routes,
        debug_health_router,
        system_rules_api_router,
        db_management_api_router
    ]
    
    for router in routers:
        app.include_router(router)
    
    # Optionale Debug-Routen
    ENABLE_DEBUG_ROUTES = os.getenv("ENABLE_DEBUG_ROUTES", "0") == "1"
    if ENABLE_DEBUG_ROUTES:
        try:
            from backend.debug.routes import router as debug_routes
            app.include_router(debug_routes, prefix="/_debug", tags=["debug"])
            logger.info("Debug-Router aktiviert")
        except Exception as e:
            logger.warning("Debug-Router nicht verfügbar: %s", e)


def setup_health_routes(app: FastAPI) -> None:
    """Registriert Health/Debug-Routen direkt in der App."""
    from fastapi import HTTPException
    from db.core import ENGINE
    from sqlalchemy import text
    from backend.config import get_osrm_settings
    from backend.middlewares.error_tally import get_metrics
    from pathlib import Path
    import logging
    import os
    
    log = logging.getLogger(__name__)
    
    @app.get("/healthz")
    async def healthz():
        """Kubernetes/Docker Health Check - einfach OK wenn App läuft."""
        return {"status": "ok"}
    
    @app.get("/readyz")
    async def readyz():
        """Kubernetes/Docker Readiness Check - prüft ob App bereit ist."""
        try:
            # Leichtgewichtige Checks: DB erreichbar?
            with ENGINE.connect() as conn:
                conn.execute(text("SELECT 1"))
            return {"ready": True}
        except Exception as e:
            log.warning(f"Readiness check failed: {e}")
            return {"ready": False, "error": str(e)}, 503
    
    @app.get("/metrics/simple")
    async def metrics_simple():
        """
        Gibt einfache Metriken zurück: 4xx und 5xx Zähler.
        """
        return get_metrics()
    
    @app.get("/debug/info")
    async def debug_info():
        """Debug-Info: Konfiguration und Status."""
        osrm_settings = get_osrm_settings()
        try:
            db_path = Path(ENGINE.url.database or "app.db").resolve()
        except Exception:
            db_path = "unknown"
        
        return {
            "db_url": str(ENGINE.url),
            "db_path": str(db_path),
            "osrm_url": osrm_settings.OSRM_BASE_URL,
            "osrm_timeout": osrm_settings.OSRM_TIMEOUT_S,
            "env": os.getenv("APP_ENV", "dev"),
            "debug_routes_enabled": os.getenv("ENABLE_DEBUG_ROUTES", "0") == "1",
        }


def setup_startup_handlers(app: FastAPI) -> None:
    """Konfiguriert Startup/Shutdown Event-Handler."""
    import logging
    from backend.utils.encoding_guards import setup_utf8_logging, smoke_test_encoding
    from repositories.geo_fail_repo import cleanup_expired
    from backend.services.code_improvement_job import CodeImprovementJob
    
    log = logging.getLogger("startup")
    
    @app.on_event("startup")
    async def startup_event():
        """Startet Background-Job beim Server-Start und loggt alle registrierten Routen."""
        # Logge alle registrierten Routen (Runbook-Format)
        log.info("=" * 70)
        log.info("ROUTE-MAP: Registrierte API-Endpoints")
        log.info("=" * 70)
        
        routes_list = []
        for route in app.routes:
            try:
                name = getattr(route, 'name', '?')
                path = getattr(route, 'path', '?')
                methods = getattr(route, 'methods', {})
                if methods:
                    methods_str = ', '.join(sorted(methods))
                    routes_list.append(f"{methods_str:20} {path:50} [{name}]")
            except Exception:
                pass
        
        for route_line in sorted(routes_list):
            log.info(route_line)
        
        log.info("=" * 70)
        log.info(f"Gesamt: {len(routes_list)} Routen registriert")
        log.info("=" * 70)
        
        # Encoding Setup
        try:
            setup_utf8_logging()
            smoke_test_encoding()
        except Exception as e:
            log.warning(f"Encoding setup failed: {e}")
        
        # Fail-Cache Bereinigung beim Start
        try:
            cleaned = cleanup_expired()
            if cleaned > 0:
                log.info(f"[STARTUP] {cleaned} abgelaufene Fail-Cache-Einträge bereinigt - werden erneut versucht")
        except Exception as e:
            log.warning(f"[WARNING] Fail-Cache Bereinigung beim Start fehlgeschlagen: {e}")
        
        # Background-Job für KI-CodeChecker beim Start starten
        try:
            job = CodeImprovementJob()
            if job.enabled:
                import asyncio
                asyncio.create_task(job.run_continuously())
                log.info("[STARTUP] KI-CodeChecker Background-Job gestartet")
            else:
                log.info("[STARTUP] KI-CodeChecker Background-Job deaktiviert")
        except Exception as e:
            log.warning(f"[STARTUP] KI-CodeChecker nicht verfügbar: {e}")

