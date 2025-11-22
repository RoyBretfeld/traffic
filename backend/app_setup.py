"""
App-Setup-Module für FastAPI-App.
Teilt die create_app Funktion in logische Module auf.
"""
from pathlib import Path
from typing import Optional
from fastapi import FastAPI, Depends
import logging
import os
from backend.utils.enhanced_logging import get_enhanced_logger

logger = logging.getLogger(__name__)
enhanced_logger = get_enhanced_logger(__name__)


def setup_config_directory() -> None:
    """Stellt sicher, dass das config-Verzeichnis existiert."""
    from pathlib import Path
    config_dir = Path("config")
    config_dir.mkdir(parents=True, exist_ok=True)
    enhanced_logger.success("Config-Verzeichnis sichergestellt", 
                           context={'path': str(config_dir.absolute())})


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
    enhanced_logger.info("=" * 70)
    enhanced_logger.info("App-Factory: Initialisiere TrafficApp")
    enhanced_logger.info("=" * 70)
    enhanced_logger.success("App-State konfiguriert", 
                           context={
                               'db_url': str(ENGINE.url),
                               'db_path': str(app.state.db_path) if app.state.db_path else None,
                               'osrm_url': osrm_settings.OSRM_BASE_URL
                           })


def setup_database_schema() -> None:
    """Sichert DB-Schema."""
    enhanced_logger.operation_start("DB-Schema Verifizierung")
    try:
        from db.schema import ensure_schema
        ensure_schema()
        enhanced_logger.operation_end("DB-Schema Verifizierung", success=True)
        enhanced_logger.success("DB-Schema verifiziert")
    except Exception as e:
        enhanced_logger.operation_end("DB-Schema Verifizierung", success=False, error=e)
        enhanced_logger.error("DB-Schema-Verifizierung fehlgeschlagen", error=e)
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
    
    # Rate-Limiting für Login (SC-04)
    from backend.middlewares.rate_limit import RateLimitMiddleware
    app.add_middleware(RateLimitMiddleware)
    
    # CORS Middleware (SC-06: Kein "*" mit Credentials in Prod)
    # In Development: Erlaube alle Origins für lokale Entwicklung
    # In Production: Nur erlaubte Domains
    is_production = os.getenv("APP_ENV", "development") == "production"
    allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",") if is_production else ["*"]
    
    # Entferne leere Strings aus Liste
    allowed_origins = [origin.strip() for origin in allowed_origins if origin.strip()]
    
    # Fallback: Wenn keine Origins gesetzt, aber Production: Nur localhost
    if is_production and not allowed_origins:
        allowed_origins = ["http://localhost:8111", "https://localhost:8111"]
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins if allowed_origins else ["*"],  # Development: "*", Production: Whitelist
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "X-Requested-With"],
    )


def setup_static_files(app: FastAPI) -> None:
    """Konfiguriert Static Files."""
    from fastapi.staticfiles import StaticFiles
    from fastapi.responses import RedirectResponse
    from pathlib import Path
    import os
    
    # Konfigurierbarer Pfad für Static Files
    frontend_dir = os.getenv("FRONTEND_DIR", "frontend")
    frontend_path = Path(frontend_dir)
    
    if not frontend_path.exists():
        enhanced_logger.warning("Frontend-Verzeichnis nicht gefunden", 
                               context={'path': str(frontend_path)})
        return
    
    # Static Files
    app.mount("/static", StaticFiles(directory=str(frontend_path)), name="static")
    
    # Redirect für favicon.ico zu favicon.svg
    @app.get("/favicon.ico")
    async def favicon_redirect():
        """Redirect favicon.ico zu favicon.svg"""
        return RedirectResponse(url="/static/favicon.svg", status_code=301)
    
    enhanced_logger.success("Static Files konfiguriert", 
                           context={'frontend_dir': str(frontend_path)})


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
    from backend.routes.multi_tour_generator_api import router as multi_tour_generator_router
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
    from backend.routes.tour_import_api import router as tour_import_router
    from backend.routes.live_traffic_api import router as live_traffic_api_router
    from backend.routes.ki_improvements_api import router as ki_improvements_api_router
    from backend.routes.code_checker_api import router as code_checker_api_router
    from backend.routes.code_improvement_job_api import router as code_improvement_job_api_router
    from backend.routes.cost_tracker_api import router as cost_tracker_api_router
    from backend.routes.osrm_metrics_api import router as osrm_metrics_api_router
    from backend.routes.health import router as health_routes
    from backend.routes.debug_health import router as debug_health_router
    from backend.routes.auth_api import router as auth_router
    from backend.routes.system_rules_api import router as system_rules_api_router
    from backend.routes.db_management_api import router as db_management_api_router
    from backend.routes.db_schema_api import router as db_schema_api_router
    from backend.routes.error_logger_api import router as error_logger_api_router
    from backend.routes.error_learning_api import router as error_learning_api_router
    from backend.routes.ki_learning_api import router as ki_learning_api_router
    from backend.routes.ki_activity_api import router as ki_activity_api_router
    from backend.routes.ki_effectiveness_api import router as ki_effectiveness_api_router
    from backend.routes.tour_filter_api import router as tour_filter_api_router
    from backend.routes.tourplan_api import router as tourplan_api_router
    from backend.routes.fuel_price_api import router as fuel_price_api_router
    
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
        multi_tour_generator_router,
        upload_csv_router,
        audit_geocoding_router,
        workflow_api_router,
        audit_status_router,
        health_check_router,
        summary_api_router,
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
        code_improvement_job_api_router,
        cost_tracker_api_router,
        osrm_metrics_api_router,
        health_routes,
        debug_health_router,
        system_rules_api_router,
        tourplan_api_router,  # Muss VOR db_management_api_router sein (gleicher Pfad)
        fuel_price_api_router,
        db_management_api_router,
        db_schema_api_router,
        error_logger_api_router,
        error_learning_api_router,
        ki_learning_api_router,
        ki_activity_api_router,
        ki_effectiveness_api_router,
        tour_filter_api_router,
        tour_import_router
    ]
    
    for router in routers:
        app.include_router(router)
    
    # Optionale Debug-Routen (SC-09: Nur mit Flag + Admin)
    ENABLE_DEBUG_ROUTES = os.getenv("ENABLE_DEBUG_ROUTES", "0") == "1"
    if ENABLE_DEBUG_ROUTES:
        try:
            from backend.debug.routes import router as debug_routes
            from backend.routes.auth_api import require_admin
            app.include_router(
                debug_routes,
                prefix="/_debug",
                tags=["debug"],
                dependencies=[Depends(require_admin)]
            )
            logger.info("Debug-Router aktiviert (nur mit Admin-Auth)")
        except Exception as e:
            logger.warning("Debug-Router nicht verfügbar: %s", e)
    
    # Test-Dashboard und Code-Checker nur mit Flag + Admin (SC-09)
    if ENABLE_DEBUG_ROUTES:
        from backend.routes.auth_api import require_admin
        app.include_router(
            test_dashboard_router,
            dependencies=[Depends(require_admin)]
        )
        app.include_router(
            code_checker_api_router,
            dependencies=[Depends(require_admin)]
        )
        logger.info("Test-Dashboard und Code-Checker aktiviert (nur mit Admin-Auth)")
    else:
        logger.info("Test-Dashboard und Code-Checker deaktiviert (ENABLE_DEBUG_ROUTES=0)")


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
    """Konfiguriert Startup/Shutdown Event-Handler mit Timeout-Schutz."""
    import logging
    import asyncio
    import time
    from datetime import datetime
    from pathlib import Path
    from backend.utils.encoding_guards import setup_utf8_logging, smoke_test_encoding
    from repositories.geo_fail_repo import cleanup_expired
    # from backend.services.code_improvement_job import CodeImprovementJob  # TEMPORÄR DEAKTIVIERT
    
    log = logging.getLogger("startup")
    
    # Startup-Log-Datei
    startup_log_path = Path("logs") / f"startup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    startup_log_path.parent.mkdir(exist_ok=True)
    startup_file_handler = logging.FileHandler(startup_log_path, encoding='utf-8')
    startup_file_handler.setLevel(logging.DEBUG)
    startup_file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    log.addHandler(startup_file_handler)
    
    startup_start_time = None
    
    async def _startup_with_timeout(coro, timeout_seconds: int = 30, task_name: str = "Task"):
        """Führt eine Coroutine mit Timeout aus."""
        task_start = time.time()
        try:
            await asyncio.wait_for(coro, timeout=timeout_seconds)
            elapsed = time.time() - task_start
            log.info(f"[STARTUP] ✅ {task_name} erfolgreich abgeschlossen ({elapsed:.2f}s)")
            return True
        except asyncio.TimeoutError:
            elapsed = time.time() - task_start
            log.error(f"[STARTUP] ❌ TIMEOUT: {task_name} hat {timeout_seconds}s überschritten (nach {elapsed:.2f}s) - wird übersprungen")
            return False
        except Exception as e:
            elapsed = time.time() - task_start
            log.error(f"[STARTUP] ❌ FEHLER bei {task_name} (nach {elapsed:.2f}s): {e}", exc_info=True)
            return False
    
    @app.on_event("startup")
    async def startup_event():
        """Startet Background-Job beim Server-Start und loggt alle registrierten Routen."""
        global startup_start_time
        startup_start_time = time.time()
        
        # Error-Pattern-Aggregator starten (Hintergrund-Job)
        # STATUS: Aggregator sammelt nur Daten (keine KI-Eingriffe), kann aber deaktiviert werden
        # wenn gewünscht. Aktuell aktiv, da er nur Daten sammelt und keine Code-Änderungen macht.
        try:
            from backend.services.error_pattern_aggregator import run_aggregator_loop
            # Starte Aggregator-Loop im Hintergrund (alle 5 Minuten)
            # HINWEIS: Aggregator sammelt nur Fehler-Patterns in DB, greift nicht in Code ein
            asyncio.create_task(run_aggregator_loop(interval_minutes=5))
            log.info("[STARTUP] ✅ Error-Pattern-Aggregator gestartet (nur Daten-Sammlung, keine KI-Eingriffe)")
        except Exception as e:
            log.warning(f"[STARTUP] ⚠️ Error-Pattern-Aggregator konnte nicht gestartet werden: {e}")
        
        # Tour-Vectorizer starten (Hintergrund-Job)
        try:
            from backend.services.tour_vectorizer import run_vectorizer_loop
            # Starte Vectorizer-Loop im Hintergrund (alle 30 Sekunden)
            asyncio.create_task(run_vectorizer_loop(interval_seconds=30))
            log.info("[STARTUP] ✅ Tour-Vectorizer gestartet")
        except Exception as e:
            log.warning(f"[STARTUP] ⚠️ Tour-Vectorizer konnte nicht gestartet werden: {e}")
        
        # Lessons-Updater starten (Hintergrund-Job, täglich)
        try:
            from backend.services.lessons_updater import auto_update_lessons_for_fixed_patterns
            # Starte Lessons-Updater-Loop im Hintergrund (täglich um 01:00 Uhr)
            async def _lessons_updater_loop():
                import asyncio
                while True:
                    # Warte bis 01:00 Uhr
                    await asyncio.sleep(3600)  # Prüfe stündlich
                    now = datetime.now()
                    if now.hour == 1 and now.minute < 5:  # Zwischen 01:00 und 01:05
                        auto_update_lessons_for_fixed_patterns()
                        # Warte bis nächster Tag
                        await asyncio.sleep(3600 * 23)  # 23 Stunden
            asyncio.create_task(_lessons_updater_loop())
            log.info("[STARTUP] ✅ Lessons-Updater gestartet (läuft täglich um 01:00 Uhr)")
        except Exception as e:
            log.warning(f"[STARTUP] ⚠️ Lessons-Updater konnte nicht gestartet werden: {e}")
        
        log.info("=" * 70)
        log.info("[STARTUP] 🚀 Server-Startup beginnt")
        log.info(f"[STARTUP] 📝 Startup-Log: {startup_log_path}")
        log.info("=" * 70)
        
        # 1. Route-Logging (schnell, kein Timeout nötig)
        step_start = time.time()
        log.info(f"[STARTUP] 📋 Schritt 1/5: Route-Logging (Start: +{step_start - startup_start_time:.2f}s)")
        try:
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
            
            elapsed = time.time() - step_start
            log.info("=" * 70)
            log.info(f"[STARTUP] ✅ Schritt 1/5 abgeschlossen: {len(routes_list)} Routen registriert ({elapsed:.2f}s)")
            log.info("=" * 70)
        except Exception as e:
            elapsed = time.time() - step_start
            log.error(f"[STARTUP] ❌ Schritt 1/5 fehlgeschlagen ({elapsed:.2f}s): {e}", exc_info=True)
        
        # 2. Encoding Setup (mit Timeout)
        step_start = time.time()
        log.info(f"[STARTUP] 📋 Schritt 2/5: Encoding Setup (Start: +{step_start - startup_start_time:.2f}s)")
        async def _encoding_setup():
            setup_utf8_logging()
            smoke_test_encoding()
        encoding_ok = await _startup_with_timeout(_encoding_setup(), timeout_seconds=5, task_name="Encoding Setup")
        if encoding_ok:
            elapsed = time.time() - step_start
            log.info(f"[STARTUP] ✅ Schritt 2/5 abgeschlossen: Encoding Setup ({elapsed:.2f}s)")
        
        # 3. Fail-Cache Bereinigung (mit Timeout)
        step_start = time.time()
        log.info(f"[STARTUP] 📋 Schritt 3/5: Fail-Cache Bereinigung (Start: +{step_start - startup_start_time:.2f}s)")
        async def _fail_cache_cleanup():
            cleaned = cleanup_expired()
            if cleaned > 0:
                log.info(f"[STARTUP] {cleaned} abgelaufene Fail-Cache-Einträge bereinigt")
        cleanup_ok = await _startup_with_timeout(_fail_cache_cleanup(), timeout_seconds=10, task_name="Fail-Cache Bereinigung")
        if cleanup_ok:
            elapsed = time.time() - step_start
            log.info(f"[STARTUP] ✅ Schritt 3/5 abgeschlossen: Fail-Cache Bereinigung ({elapsed:.2f}s)")
        
        # 4. Background-Job starten (TEMPORÄR DEAKTIVIERT)
        # STATUS: Code-Improvement-Job ist aktuell deaktiviert, um Server-Startup-Probleme zu vermeiden.
        # GRUND: Die Initialisierung des CodeImprovementJob blockierte den Server-Startup (siehe LESSONS_LOG.md).
        # LÖSUNG: Job kann manuell über API gestartet werden: POST /api/code-improvement-job/start
        # DOKUMENTATION: Siehe docs/STARTUP_BACKGROUND_JOB_PROBLEM_2025-11-16.md
        step_start = time.time()
        log.info(f"[STARTUP] 📋 Schritt 4/5: Background-Job Start (Start: +{step_start - startup_start_time:.2f}s)")
        log.info("[STARTUP] ⚠️ Code-Improvement-Job ist TEMPORÄR DEAKTIVIERT")
        log.info("[STARTUP]    Grund: Verhinderte Server-Startup-Blockierung")
        log.info("[STARTUP]    Alternative: Job kann manuell über API gestartet werden")
        log.info("[STARTUP]    Endpoint: POST /api/code-improvement-job/start")
        log.info("[STARTUP]    Status-Endpoint: GET /api/code-improvement-job/status")
        
        # Code auskommentiert, aber für Referenz behalten:
        # async def _start_background_job():
        #     try:
        #         from backend.services.code_improvement_job import CodeImprovementJob
        #         log.info("[STARTUP] Initialisiere CodeImprovementJob...")
        #         job = CodeImprovementJob()
        #         log.info(f"[STARTUP] Background-Job initialisiert: enabled={job.enabled}, is_running={job.is_running}, ai_checker={'OK' if job.ai_checker else 'FEHLT'}")
        #         
        #         if job.enabled and not job.is_running:
        #             if job.ai_checker:
        #                 # Starte Job als Task (nicht-blockierend)
        #                 log.info("[STARTUP] Erstelle Background-Job Task...")
        #                 task = asyncio.create_task(job.run_continuously())
        #                 log.info("[STARTUP] KI-CodeChecker Background-Job gestartet (Task erstellt)")
        #                 return
        #             else:
        #                 log.info("[STARTUP] KI-CodeChecker nicht verfügbar (OPENAI_API_KEY fehlt)")
        #                 return
        #         else:
        #             log.info(f"[STARTUP] KI-CodeChecker Background-Job deaktiviert (enabled={job.enabled}, is_running={job.is_running})")
        #             return
        #     except Exception as e:
        #         log.error(f"[STARTUP] Fehler beim Initialisieren des Background-Jobs: {e}", exc_info=True)
        #         raise
        
        job_ok = True  # Als erfolgreich markieren, da deaktiviert
        elapsed = time.time() - step_start
        log.info(f"[STARTUP] ✅ Schritt 4/5 abgeschlossen: Background-Job (deaktiviert) ({elapsed:.2f}s)")
        
        # Startup-Zusammenfassung (IMMER ausführen, auch bei Fehlern)
        total_elapsed = time.time() - startup_start_time
        log.info("=" * 70)
        log.info(f"[STARTUP] ✅ Server-Startup abgeschlossen (Gesamt: {total_elapsed:.2f}s)")
        log.info(f"[STARTUP] 📝 Startup-Log gespeichert: {startup_log_path}")
        log.info("=" * 70)
        
        # Status-Übersicht
        log.info("[STARTUP] 📊 Status-Übersicht:")
        log.info(f"  - Route-Logging: ✅")
        log.info(f"  - Encoding Setup: {'✅' if encoding_ok else '❌'}")
        log.info(f"  - Fail-Cache Bereinigung: {'✅' if cleanup_ok else '❌'}")
        log.info(f"  - Background-Job: {'✅' if job_ok else '❌'}")
        log.info("=" * 70)
        
        # WICHTIG: Explizit signalisieren, dass Startup abgeschlossen ist
        log.info("[STARTUP] 🎯 Startup-Event beendet - Server sollte jetzt bereit sein")

