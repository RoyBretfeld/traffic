from fastapi import FastAPI, HTTPException, UploadFile, File, Request
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Optional
import pandas as pd
import tempfile
import os
import unicodedata
import uuid
from backend.utils.encoding_guards import trace_text, assert_no_mojibake, setup_utf8_logging, smoke_test_encoding
from backend.core.error_handlers import http_exception_handler, RequestIdMiddleware
from backend.middlewares.trace_id import TraceIDMiddleware
from fastapi.exceptions import HTTPException
import logging

logger = logging.getLogger(__name__)

# Importiere neue Routen
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
from backend.routes.tourplan_bulk_process import router as tourplan_bulk_process_router
from backend.routes.tourplan_triage import router as tourplan_triage_router
from backend.routes.upload_csv import router as upload_csv_router
from backend.routes.audit_geocoding import router as audit_geocoding_router
from backend.routes.workflow_api import router as workflow_api_router
from backend.routes.audit_status import router as audit_status_router
from backend.routes.health_check import router as health_check_router # Importiere neuen Health Check Router
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
from backend.routes.cost_tracker_api import router as cost_tracker_api_router
from backend.routes.osrm_metrics_api import router as osrm_metrics_api_router
from backend.routes.health import router as health_routes # Korrekter Import für Health Routes
from backend.routes.debug_health import router as debug_health_router  # Korrekter Import für Debug Health Router
from backend.routes.auth_api import router as auth_router

def create_app() -> FastAPI:
    """
    App-Factory: Erstellt und konfiguriert die FastAPI-App.
    Nutzt modulare Setup-Funktionen aus app_setup.py.
    """
    from backend.app_setup import (
        setup_app_state,
        setup_database_schema,
        setup_middleware,
        setup_static_files,
        setup_routers,
        setup_health_routes,
        setup_startup_handlers,
    )
    
    # App erstellen
    app = FastAPI(title="TrafficApp API", version="1.0.0")
    
    # Modulare Setup-Funktionen aufrufen
    from backend.app_setup import setup_config_directory
    setup_config_directory()  # Config-Verzeichnis sicherstellen
    setup_app_state(app)
    setup_database_schema()
    setup_middleware(app)
    setup_static_files(app)
    setup_routers(app)
    setup_health_routes(app)
    setup_startup_handlers(app)
    
    # Encoding Setup (optional)
    try:
        setup_utf8_logging()
        smoke_test_encoding()
    except Exception as e:
        print(f"[WARNING] Encoding setup failed: {e}")
    
    # ENTFERNT: Startup-Event wurde nach app_setup.py verschoben
    # Alle Startup-Logik ist jetzt in setup_startup_handlers() konsolidiert
    # Dies verhindert doppelte Startup-Events und Race Conditions

    # --- Start der verschobenen Routen und Helferfunktionen ---
    def read_tourplan_csv_internal(csv_file):
        """Liest Tourplan-CSV direkt (für temporäre Dateien)."""
        import pandas as pd
        from pathlib import Path

        # Für temporäre Dateien direkt lesen (ohne Staging)
        csv_path = Path(csv_file)

        # Versuche verschiedene Encodings
        encodings = ['cp850', 'utf-8', 'latin-1', 'iso-8859-1']

        for encoding in encodings:
            try:
                df = pd.read_csv(csv_path, sep=';', header=None, dtype=str, encoding=encoding)
                print(f"[CSV READ] {csv_path.name} mit {encoding} ({len(df)} Zeilen)")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                print(f"[CSV READ] Fehler mit {encoding}: {e}")
                continue

        # Fallback: mit Fehlerbehandlung
        try:
            df = pd.read_csv(csv_path, sep=';', header=None, dtype=str, encoding='cp850', errors='replace')
            print(f"[CSV READ] {csv_path.name} mit cp850+replace ({len(df)} Zeilen)")
            return df
        except Exception as e:
            raise Exception(f"CSV konnte nicht gelesen werden: {e}")
    
    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Hauptseite"""
        try:
            from ingest.http_responses import create_utf8_html_response
            from fastapi.responses import Response

            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("index.html")

            # Cache-Control Header setzen um Browser-Cache zu verhindern
            response = Response(content=content, media_type="text/html; charset=utf-8")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Hauptseite nicht gefunden")

    @app.get("/admin/ki-improvements", response_class=HTMLResponse)
    async def ki_improvements_dashboard(request: Request):
        """KI-CodeChecker Dashboard (geschützt)."""
        # Auth-Check
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            # Redirect zu Login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/ki-improvements", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/ki-improvements.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="KI-Improvements Dashboard nicht gefunden")
    
    @app.get("/admin/ki-kosten", response_class=HTMLResponse)
    async def ki_kosten_dashboard(request: Request):
        """KI-Kosten & Modelle Dashboard (geschützt)."""
        # Auth-Check
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            # Redirect zu Login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/ki-kosten", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/ki-kosten.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="KI-Kosten Dashboard nicht gefunden")
    
    @app.get("/admin/ki-verhalten", response_class=HTMLResponse)
    async def ki_verhalten_dashboard(request: Request):
        """KI-Verhalten Dashboard (geschützt)."""
        # Auth-Check
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            # Redirect zu Login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/ki-verhalten", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/ki-verhalten.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="KI-Verhalten Dashboard nicht gefunden")
    
    @app.get("/admin/tour-filter", response_class=HTMLResponse)
    async def tour_filter_page(request: Request):
        """Tour-Filter Verwaltung (geschützt)."""
        # Auth-Check
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            # Redirect zu Login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/tour-filter", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/tour-filter.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Tour-Filter Seite nicht gefunden")
    
    @app.get("/admin/dataflow.html", response_class=HTMLResponse)
    async def dataflow_page(request: Request):
        """Datenfluss-Visualisierung (geschützt)."""
        # Auth-Check
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            # Redirect zu Login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/dataflow.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/dataflow.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Datenfluss-Seite nicht gefunden")
    
    @app.get("/admin/tour-import.html", response_class=HTMLResponse)
    async def tour_import_page(request: Request):
        """Tour-Import & Vorladen Seite (geschützt)."""
        # Auth-Check
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            # Redirect zu Login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/tour-import.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/tour-import.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Tour-Import-Seite nicht gefunden")
    
    @app.get("/admin/tour-filter.html", response_class=HTMLResponse)
    async def tour_filter_page(request: Request):
        """Tour-Filter Seite (geschützt)."""
        # Auth-Check
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            # Redirect zu Login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/tour-filter.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/tour-filter.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Tour-Filter-Seite nicht gefunden")
    
    @app.get("/admin/system.html", response_class=HTMLResponse)
    async def admin_system_page(request: Request):
        """System/Health Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/system.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/system.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="System-Seite nicht gefunden")
    
    @app.get("/admin/statistik.html", response_class=HTMLResponse)
    async def admin_statistik_page(request: Request):
        """Statistik-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/statistik.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/statistik.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Statistik-Seite nicht gefunden")
    
    @app.get("/admin/systemregeln.html", response_class=HTMLResponse)
    async def admin_systemregeln_page(request: Request):
        """Systemregeln-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/systemregeln.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/systemregeln.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Systemregeln-Seite nicht gefunden")
    
    @app.get("/admin/ki-integration.html", response_class=HTMLResponse)
    async def admin_ki_integration_page(request: Request):
        """KI-Integration-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/ki-integration.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/ki-integration.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="KI-Integration-Seite nicht gefunden")
    
    @app.get("/admin/ki-improvements.html", response_class=HTMLResponse)
    async def admin_ki_improvements_page(request: Request):
        """KI-CodeChecker-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/ki-improvements.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/ki-improvements.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="KI-CodeChecker-Seite nicht gefunden")
    
    @app.get("/admin/ki-kosten.html", response_class=HTMLResponse)
    async def admin_ki_kosten_page(request: Request):
        """KI-Kosten-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/ki-kosten.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/ki-kosten.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="KI-Kosten-Seite nicht gefunden")
    
    @app.get("/admin/ki-verhalten.html", response_class=HTMLResponse)
    async def admin_ki_verhalten_page(request: Request):
        """KI-Verhalten-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/ki-verhalten.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/ki-verhalten.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="KI-Verhalten-Seite nicht gefunden")
    
    @app.get("/admin/db-verwaltung.html", response_class=HTMLResponse)
    async def admin_db_verwaltung_page(request: Request):
        """DB-Verwaltung-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/db-verwaltung.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/db-verwaltung.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="DB-Verwaltung-Seite nicht gefunden")
    
    @app.get("/admin/tourplan-uebersicht.html", response_class=HTMLResponse)
    async def admin_tourplan_uebersicht_page(request: Request):
        """Tourplan-Übersicht-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/tourplan-uebersicht.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/tourplan-uebersicht.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Tourplan-Übersicht-Seite nicht gefunden")

    @app.get("/admin/geo-cache-vorverarbeitung.html", response_class=HTMLResponse)
    async def admin_geo_cache_vorverarbeitung_page(request: Request):
        """Geo-Cache Vorverarbeitung-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/geo-cache-vorverarbeitung.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/geo-cache-vorverarbeitung.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Geo-Cache Vorverarbeitung-Seite nicht gefunden")
    
    @app.get("/admin/tankpreise.html", response_class=HTMLResponse)
    async def admin_tankpreise_page(request: Request):
        """Tank- und Strompreise-Seite (geschützt)."""
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin/tankpreise.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/tankpreise.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Tank- und Strompreise-Seite nicht gefunden")
    
    @app.get("/admin.html", response_class=HTMLResponse)
    async def admin_page(request: Request):
        """Admin-Hauptseite (geschützt)."""
        # Auth-Check
        from backend.routes.auth_api import get_session_from_request
        session_id = get_session_from_request(request)
        if not session_id:
            # Redirect zu Login
            from fastapi.responses import RedirectResponse
            return RedirectResponse(url="/admin/login.html?redirect=/admin.html", status_code=302)
        
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Admin-Seite nicht gefunden")
    
    @app.get("/admin/login.html", response_class=HTMLResponse)
    async def admin_login_page():
        """Login-Seite für Admin-Bereich."""
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("admin/login.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Login-Seite nicht gefunden")

    @app.get("/ui/", response_class=HTMLResponse)
    async def ui_root():
        """UI Hauptseite"""
        try:
            from ingest.http_responses import create_utf8_html_response
            from fastapi.responses import Response

            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("index.html")

            # Cache-Control Header setzen um Browser-Cache zu verhindern
            response = Response(content=content, media_type="text/html; charset=utf-8")
            response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"
            return response
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="UI Hauptseite nicht gefunden")

    @app.post("/api/tourplan-analysis", tags=["csv"], summary="Tourplan CSV analysieren")
    async def tourplan_analysis(file: UploadFile = File(...)) -> JSONResponse:
        """Analysiert eine CSV-Datei und gibt die Adressen zurück."""
        from ingest.guards import trace_text, assert_no_mojibake
        import tempfile
        import pandas as pd
        from pathlib import Path
        from fastapi import HTTPException

        try:
            # Datei temporär speichern
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                    content = await file.read()
                    tmp_file.write(content)
                    tmp_file_path = tmp_file.name
            except (IOError, OSError) as e:
                raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der temporären Datei: {e}")

            try:
                # CSV mit gehärteter Funktion lesen
                csv_path = Path(tmp_file_path)
                df = read_tourplan_csv_internal(csv_path)

                addresses = []
                total_rows = len(df)
                recognized_count = 0
                coordinates_count = 0

                # Adressen extrahieren und validieren
                for idx, row in df.iterrows():
                    if len(row) >= 5:
                        # Korrekte Spalten-Indizes für Tourplan-CSV
                        # Spalte 0: Kdnr, Spalte 1: Name, Spalte 2: Straße, Spalte 3: PLZ, Spalte 4: Ort
                        customer_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                        customer_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                        street = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                        postal_code = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
                        city = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""

                        # Nur verarbeiten wenn alle wichtigen Felder vorhanden sind
                        if customer_id and customer_name and street and city and street != 'nan' and city != 'nan':
                            # Adresse zusammenstellen
                            full_address = f"{street}, {postal_code} {city}".strip()

                            # Echte Datenbankabfrage
                            try:
                                customer_id_found = get_kunde_id_by_name_adresse(customer_name, street, city)
                                if customer_id_found:
                                    customer_data = get_kunde_by_id(customer_id_found)
                                    if customer_data and customer_data.get('latitude') and customer_data.get('longitude'):
                                        recognized_count += 1
                                        coordinates_count += 1
                                        coordinates = {
                                            "lat": float(customer_data['latitude']),
                                            "lon": float(customer_data['longitude'])
                                        }
                                    else:
                                        coordinates = None
                                else:
                                    coordinates = None
                            except Exception as e:
                                print(f"[DB ERROR] {e}")
                                coordinates = None

                            addresses.append({
                                "customer_id": customer_id,
                                "street": street,
                                "postal_code": postal_code,
                                "city": city,
                                "customer_name": customer_name,
                                "full_address": full_address,
                                "recognized": coordinates is not None,
                                "coordinates": coordinates,
                                "row": idx + 1
                            })

                # UTF-8 JSON Response mit zentraler Konfiguration
                from ingest.http_responses import create_utf8_json_response

                return create_utf8_json_response({
                    "success": True,
                    "file_name": file.filename,
                    "total_rows": total_rows,
                    "addresses": addresses,
                    "summary": {
                        "total_addresses": len(addresses),
                        "recognized": recognized_count,
                        "unrecognized": len(addresses) - recognized_count,
                        "with_coordinates": coordinates_count
                    }
                })

            finally:
                # Temporäre Datei löschen
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass

        except Exception as e:
            # Unicode-sichere Fehlerbehandlung
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            print(f"[ERROR] Upload failed: {error_msg}")
            raise HTTPException(status_code=500, detail=f"Fehler beim Verarbeiten der CSV-Datei: {error_msg}")

    @app.post("/api/tourplan-visual-test", tags=["csv"], summary="Tourplan CSV hochladen und visuell testen")
    async def tourplan_visual_test(file: UploadFile = File(...)) -> JSONResponse:
        """Lädt eine CSV-Datei hoch und testet die Mojibake-Reparatur visuell."""
        import logging
        logging.basicConfig(level=logging.INFO)

        try:
            print(f"[VISUAL-TEST] Upload gestartet: {file.filename}")

            # Datei temporär speichern
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
                    content = await file.read()
                    tmp_file.write(content)
                    tmp_file_path = tmp_file.name
            except (IOError, OSError) as e:
                raise HTTPException(status_code=500, detail=f"Fehler beim Speichern der temporären Datei: {e}")

            try:
                # CSV mit gehärteter Funktion lesen
                csv_path = Path(tmp_file_path)
                print(f"[VISUAL-TEST] Starte CSV-Parsing...")
                df = read_tourplan_csv_internal(csv_path)
                print(f"[VISUAL-TEST] CSV geparst: {len(df)} Zeilen, {len(df.columns)} Spalten")

                addresses = []
                total_rows = len(df)

                # Adressen extrahieren und validieren
                for idx, row in df.iterrows():
                    if len(row) >= 5:
                        # Korrekte Spalten-Indizes für Tourplan-CSV
                        # Spalte 0: Kdnr, Spalte 1: Name, Spalte 2: Straße, Spalte 3: PLZ, Spalte 4: Ort
                        customer_id = str(row.iloc[0]).strip() if pd.notna(row.iloc[0]) else ""
                        customer_name = str(row.iloc[1]).strip() if pd.notna(row.iloc[1]) else ""
                        street = str(row.iloc[2]).strip() if pd.notna(row.iloc[2]) else ""
                        postal_code = str(row.iloc[3]).strip() if pd.notna(row.iloc[3]) else ""
                        city = str(row.iloc[4]).strip() if pd.notna(row.iloc[4]) else ""

                        # Nur verarbeiten wenn alle wichtigen Felder vorhanden sind
                        if customer_id and customer_name and street and city and street != 'nan' and city != 'nan':
                            # Prüfe ob OT (Ortsteil) in der Straße ist
                            from repositories.geo_repo import has_ot_part
                            has_ot = has_ot_part(street)

                            # Adresse zusammenstellen
                            full_address = f"{street}, {postal_code} {city}".strip()

                            # ECHTE DATENBANK-SUCHE
                            kunde_id = get_kunde_id_by_name_adresse(customer_name, street, city)
                            recognized = kunde_id is not None
                            coordinates = None

                            # OT-Adressen sind nicht erkannt (Mitarbeiter-Bearbeitung nötig)
                            if has_ot:
                                recognized = False

                            if recognized:
                                # Lade Kunde-Details mit Koordinaten
                                kunde = get_kunde_by_id(kunde_id)
                                if kunde and 'latitude' in kunde and 'longitude' in kunde:
                                    coordinates = {
                                        "lat": float(kunde['latitude']),
                                        "lon": float(kunde['longitude'])
                                    }
                            addresses.append({
                                "customer_id": customer_id,
                                "street": street,
                                "postal_code": postal_code,
                                "city": city,
                                "customer_name": customer_name,
                                "full_address": full_address,
                                "recognized": recognized,
                                "coordinates": coordinates,
                                "has_ot": has_ot,
                                "row": idx + 1
                            })

                # UTF-8 JSON Response mit zentraler Konfiguration
                from ingest.http_responses import create_utf8_json_response

                # Berechne echte Statistiken
                recognized_count = sum(1 for addr in addresses if addr["recognized"])
                with_coords_count = sum(1 for addr in addresses if addr["coordinates"])

                print(f"[VISUAL-TEST] Verarbeitet: {len(addresses)} Adressen, {recognized_count} erkannt")

                result = {
                    "success": True,
                    "file_name": file.filename,
                    "total_rows": total_rows,
                    "addresses": addresses,
                    "summary": {
                        "total_addresses": len(addresses),
                        "recognized": recognized_count,
                        "unrecognized": len(addresses) - recognized_count,
                        "with_coordinates": with_coords_count
                    }
                }

                print(f"[VISUAL-TEST] Sende Response mit {len(addresses)} Adressen")
                return create_utf8_json_response(result)

            finally:
                # Temporäre Datei löschen
                try:
                    os.unlink(tmp_file_path)
                except:
                    pass

        except Exception as e:
            # Unicode-sichere Fehlerbehandlung
            import traceback
            error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
            error_trace = traceback.format_exc()
            print(f"[ERROR] Upload failed: {error_msg}")
            print(f"[ERROR] Traceback:\n{error_trace}")

            from ingest.http_responses import create_utf8_json_response
            return create_utf8_json_response({
                "success": False,
                "error": error_msg,
                "file_name": file.filename if hasattr(file, 'filename') else 'unknown'
            }, status_code=500)

    @app.post("/api/csv-tour-process", tags=["csv"], summary="CSV Tour verarbeiten")
    async def csv_tour_process(file: UploadFile = File(...)):
        """CSV Tour-Verarbeitung für Frontend"""
        return await tourplan_analysis(file)

    @app.get("/api/geocode", tags=["geocoding"], summary="Adresse geocodieren")
    async def geocode_address(address: str):
        """Geocodiert eine einzelne Adresse"""
        try:
            from ingest.http_responses import create_utf8_json_response
            import requests
            import urllib.parse

            # URL-Encoding der Adresse
            encoded_address = urllib.parse.quote(address, safe='')
            url = f"https://nominatim.openstreetmap.org/search?q={encoded_address}&format=jsonv2"

            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()  # Wirft Exception bei HTTP-Fehlern
                data = response.json()
            except requests.exceptions.RequestException as e:
                raise HTTPException(status_code=503, detail=f"Fehler beim Abrufen von Nominatim: {e}")
            except (ValueError, KeyError) as e:
                raise HTTPException(status_code=500, detail=f"Fehler beim Parsen der Nominatim-Antwort: {e}")

            if data:
                result = data[0]
                return create_utf8_json_response({
                    "success": True,
                    "address": address,
                    "coordinates": {
                        "lat": float(result["lat"]),
                        "lon": float(result["lon"])
                    },
                    "display_name": result["display_name"]
                })
            else:
                return create_utf8_json_response({
                    "success": False,
                    "address": address,
                    "error": "Keine Ergebnisse gefunden"
                })

        except Exception as e:
            from ingest.http_responses import create_utf8_json_response
            return create_utf8_json_response({
                "success": False,
                "address": address,
                "error": str(e)
            })

    # ENTFERNT: /health/db ist jetzt in routes/health_check.py (Router)
    # Der Router-Endpunkt wird über app.include_router(health_check_router) registriert

    @app.get("/audit/orig-integrity", tags=["audit"], summary="Original-CSV Integrität prüfen")
    async def audit_integrity():
        """Prüft die Integrität der Original-CSV-Dateien"""
        try:
            from tools.orig_integrity import verify
            probs = verify()
            body = {"ok": len(probs)==0, "problems": probs}
            from ingest.http_responses import create_utf8_json_response
            return create_utf8_json_response(body)
        except Exception as e:
            from ingest.http_responses import create_utf8_json_response
            return create_utf8_json_response({
                "ok": False,
                "error": str(e)
            })

    @app.get("/export/tourplan", tags=["export"], summary="Tourplan als CSV exportieren")
    async def export_tourplan(excel: bool = False):
        """Exportiert Tourplan-Daten als CSV (mit Excel-Kompatibilität)"""
        try:
            from fastapi.responses import FileResponse
            from pathlib import Path
            import pandas as pd
            import os

            # Beispiel-Daten (in echter Implementierung würde das aus der DB kommen)
            df = pd.DataFrame({
                "Kunde": ["Müller GmbH", "Schmidt & Co", "Weiß AG"],
                "Adresse": ["Löbtauer Straße 1", "Hauptstraße 42", "Dresdner Platz 5"],
                "PLZ": ["01809", "01067", "01069"],
                "Ort": ["Heidenau", "Dresden", "Dresden"]
            })

            # Output-Pfad
            filename = "tourplan_export_excel.csv" if excel else "tourplan_export.csv"
            output_dir = Path(os.getenv("OUTPUT_DIR", "./data/output"))
            output_dir.mkdir(parents=True, exist_ok=True)
            out_path = output_dir / filename

            # CSV direkt schreiben (ohne PathPolicy für Tests)
            enc = 'utf-8-sig' if excel else 'utf-8'
            df.to_csv(out_path, encoding=enc, sep=';', index=False)

            # FileResponse mit korrektem Charset
            return FileResponse(
                out_path,
                media_type="text/csv; charset=utf-8",
                filename=filename
            )

        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"Export fehlgeschlagen: {str(e)}")

    # Echte Datenbank-Funktionen für Kunden-Suche
    def _normalize_string(s: str) -> str:
        """Normalisiert einen String für die DB-Suche"""
        return s.lower().strip()

    def get_kunde_id_by_name_adresse(name: str, street: str, city: str) -> Optional[int]:
        """Sucht Kunde-ID nach Name und Adresse in der echten Datenbank."""
        from backend.utils.customer_db_helpers import get_kunde_id_by_name_adresse as db_search
        return db_search(name, street, city)

    def get_kunde_by_id(kunde_id: int):
        """Lädt Kunde aus DB nach ID"""
        try:
            import sqlite3
            import os

            # Prüfe beide Datenbanken
            db_paths = ['data/customers.db', 'data/traffic.db']

            for db_path in db_paths:
                if os.path.exists(db_path):
                    conn = sqlite3.connect(db_path)
                    cursor = conn.cursor()

                    # Prüfe Tabellen
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                    tables = cursor.fetchall()

                    for table in tables:
                        table_name = table[0]
                        if 'customer' in table_name.lower() or 'kunde' in table_name.lower():
                            try:
                                cursor.execute(f"SELECT * FROM {table_name} WHERE id = ?", (kunde_id,))
                                result = cursor.fetchone()
                                if result:
                                    # Hole Spaltennamen
                                    cursor.execute(f"PRAGMA table_info({table_name})")
                                    columns = [col[1] for col in cursor.fetchall()]

                                    # Erstelle Dictionary
                                    kunde = dict(zip(columns, result))
                                    conn.close()
                                    return kunde
                            except sqlite3.OperationalError:
                                continue

                    conn.close()

            return None

        except Exception as e:
            print(f"[DB-ERROR] Fehler beim Laden des Kunden {kunde_id}: {e}")
            return None

    @app.get("/ui/tourplan-management", response_class=HTMLResponse)
    async def tourplan_management():
        """Tourplan Management Seite"""
        try:
            from ingest.http_responses import create_utf8_html_response

            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("tourplan-management.html")

            return create_utf8_html_response(content)

        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Seite: {str(e)}")

    @app.get("/ui/ai-test", response_class=HTMLResponse, tags=["ui"])
    async def ai_test_page():
        """AI Test-Seite für Adress-Analyse"""
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("ai-test.html")

            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")

        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="AI Test-Seite nicht gefunden")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Seite: {str(e)}")

    @app.get("/ui/test-dashboard", response_class=HTMLResponse)
    async def test_dashboard():
        """Test-Dashboard Seite"""
        try:
            from ingest.http_responses import create_utf8_html_response

            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("test-dashboard.html")

            return create_utf8_html_response(content)

        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Seite: {str(e)}")

    @app.get("/panel-map.html", response_class=HTMLResponse, tags=["ui"])
    async def panel_map():
        """Karten-Panel (abdockbares Fenster)"""
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("panel-map.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Karten-Panel nicht gefunden")

    @app.get("/panel-tours.html", response_class=HTMLResponse, tags=["ui"])
    async def panel_tours():
        """Tour-Übersicht-Panel (abdockbares Fenster)"""
        try:
            from backend.utils.path_helpers import read_frontend_file
            content = read_frontend_file("panel-tours.html")
            return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
        except FileNotFoundError:
            raise HTTPException(status_code=404, detail="Tour-Panel nicht gefunden")

    # --- Ende der verschobenen Routen und Helferfunktionen ---

    return app

# Exportiere read_tourplan_csv für Tests (nutzt gleiche Logik wie interne Funktion)
def read_tourplan_csv(csv_file):
    """Liest Tourplan-CSV direkt (für temporäre Dateien)."""
    import pandas as pd
    from pathlib import Path

    # Für temporäre Dateien direkt lesen (ohne Staging)
    csv_path = Path(csv_file)

    # Versuche verschiedene Encodings
    encodings = ['cp850', 'utf-8', 'latin-1', 'iso-8859-1']

    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, sep=';', header=None, dtype=str, encoding=encoding)
            print(f"[CSV READ] {csv_path.name} mit {encoding} ({len(df)} Zeilen)")
            return df
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"[CSV READ] Fehler mit {encoding}: {e}")
            continue

    # Fallback: mit Fehlerbehandlung
    try:
        df = pd.read_csv(csv_path, sep=';', header=None, dtype=str, encoding='cp850', errors='replace')
        print(f"[CSV READ] {csv_path.name} mit cp850+replace ({len(df)} Zeilen)")
        return df
    except Exception as e:
        raise Exception(f"CSV konnte nicht gelesen werden: {e}")

# Erstelle App-Instanz für direkten Import (z.B. in Tests)
app = create_app()
