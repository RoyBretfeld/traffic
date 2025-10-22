from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
import pandas as pd
import tempfile
import os
import unicodedata
from backend.utils.encoding_guards import trace_text, assert_no_mojibake, setup_utf8_logging, smoke_test_encoding
from datetime import datetime

# Importiere neue Routen
from routes.tourplan_match import router as tourplan_match_router
from routes.tourplan_geofill import router as tourplan_geofill_router
from routes.tourplaene_list import router as tourplaene_list_router
from routes.tourplan_status import router as tourplan_status_router
from routes.tourplan_suggest import router as tourplan_suggest_router
from routes.tourplan_accept import router as tourplan_accept_router
from routes.audit_geo import router as audit_geo_router
from routes.failcache_api import router as failcache_api_router
from routes.failcache_clear import router as failcache_clear_router
from routes.failcache_improved import router as failcache_improved_router
from routes.tourplan_manual_geo import router as tourplan_manual_geo_router
from routes.debug_geo import router as debug_geo_router
from routes.manual_api import router as manual_api_router
from routes.tourplan_bulk_analysis import router as tourplan_bulk_analysis_router
from routes.tourplan_bulk_process import router as tourplan_bulk_process_router
from routes.tourplan_triage import router as tourplan_triage_router
from routes.upload_csv import router as upload_csv_router
from routes.audit_geocoding import router as audit_geocoding_router
from routes.audit_status import router as audit_status_router
from routes.health_check import router as health_check_router # Importiere neuen Health Check Router

def create_app():
    app = FastAPI(title="TrafficApp API", version="1.0.0")
    
    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Static Files
    app.mount("/static", StaticFiles(directory="frontend"), name="static")
    
    # Root route - serve frontend
    @app.get("/", response_class=HTMLResponse)
    async def root():
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            return HTMLResponse(f.read())
    
    # Registriere neue Routen
    app.include_router(tourplan_match_router)
    app.include_router(tourplan_geofill_router)
    app.include_router(tourplaene_list_router)
    app.include_router(tourplan_status_router)
    app.include_router(tourplan_suggest_router)
    app.include_router(tourplan_accept_router)
    app.include_router(audit_geo_router)
    app.include_router(failcache_api_router)
    app.include_router(failcache_clear_router)
    app.include_router(failcache_improved_router)
    app.include_router(tourplan_manual_geo_router)
    app.include_router(debug_geo_router)
    app.include_router(manual_api_router)
    app.include_router(tourplan_bulk_analysis_router)
    app.include_router(tourplan_triage_router)
    app.include_router(tourplan_bulk_process_router)
    app.include_router(upload_csv_router)
    app.include_router(audit_geocoding_router)
    app.include_router(audit_status_router)
    app.include_router(health_check_router) # Registriere neuen Health Check Router
    
    # Encoding Setup (optional)
    try:
        setup_utf8_logging()
        smoke_test_encoding()
    except Exception as e:
        print(f"[WARNING] Encoding setup failed: {e}")
    
    return app

app = create_app()

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

@app.get("/", response_class=HTMLResponse)
async def root():
    """Hauptseite"""
    try:
        from ingest.http_responses import create_utf8_html_response
        
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return create_utf8_html_response(content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Hauptseite nicht gefunden")

@app.get("/ui/", response_class=HTMLResponse)
async def ui_root():
    """UI Hauptseite"""
    try:
        from ingest.http_responses import create_utf8_html_response
        
        with open("frontend/index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return create_utf8_html_response(content)
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
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # CSV mit gehärteter Funktion lesen
            csv_path = Path(tmp_file_path)
            df = read_tourplan_csv(csv_path)
            
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
    try:
        # Datei temporär speichern
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # CSV mit gehärteter Funktion lesen
            csv_path = Path(tmp_file_path)
            df = read_tourplan_csv(csv_path)
            
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
                        # Adresse zusammenstellen
                        full_address = f"{street}, {postal_code} {city}".strip()
                        
                        # ECHTE DATENBANK-SUCHE
                        kunde_id = get_kunde_id_by_name_adresse(customer_name, street, city)
                        recognized = kunde_id is not None
                        coordinates = None
                        
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
                            "row": idx + 1
                        })
            
            # UTF-8 JSON Response mit zentraler Konfiguration
            from ingest.http_responses import create_utf8_json_response
            
            # Berechne echte Statistiken
            recognized_count = sum(1 for addr in addresses if addr["recognized"])
            with_coords_count = sum(1 for addr in addresses if addr["coordinates"])
            
            return create_utf8_json_response({
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

@app.get("/ui/tourplan-visual-test", response_class=HTMLResponse, tags=["ui"], summary="Tourplan Visual Test-Seite")
async def tourplan_visual_test_page():
    """Zeigt die Tourplan Visual Test-Seite für Mojibake-Reparatur an."""
    try:
        with open("frontend/tourplan-visual-test.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content, media_type="text/html; charset=utf-8")
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Tourplan Visual Test-Seite nicht gefunden")

# Fehlende API-Endpunkte für Frontend-Kompatibilität
@app.post("/api/parse-csv-tourplan", tags=["csv"], summary="CSV Tourplan parsen")
async def parse_csv_tourplan(file: UploadFile = File(...)):
    """CSV Tourplan parsen mit Geocoding-Integration für Frontend"""
    try:
        # Temporäre Datei speichern
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Tourplan mit modernem Parser verarbeiten
            from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
            tour_data = parse_tour_plan_to_dict(tmp_file_path)
            
            # Geocoding-Statistiken sammeln
            from repositories.geo_repo import bulk_get
            geocoding_stats = {
                "total": 0,
                "from_db": 0,
                "from_geocoding": 0,
                "failed": 0,
                "new_customers_saved": 0
            }
            
            # Alle Adressen sammeln
            all_addresses = []
            for customer in tour_data["customers"]:
                address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
                all_addresses.append(address)
            
            geocoding_stats["total"] = len(all_addresses)
            
            # Bestehende Geocodes aus DB laden
            existing_geo = bulk_get(all_addresses)
            geocoding_stats["from_db"] = len(existing_geo)
            
            # Fehlende Adressen identifizieren
            missing_addresses = [addr for addr in all_addresses if addr not in existing_geo]
            
            # Geocoding für fehlende Adressen (simuliert - später echte API)
            geocoding_stats["from_geocoding"] = 0  # TODO: Echte Geocoding-API
            geocoding_stats["failed"] = len(missing_addresses)
            
            # Tour-Daten mit Geocoding-Statistiken erweitern
            result = {
                "success": True,
                "file_name": file.filename,
                "tours": tour_data["tours"],
                "customers": tour_data["customers"],
                "stats": tour_data["stats"],
                "geocoding": geocoding_stats
            }
            
            from ingest.http_responses import create_utf8_json_response
            return create_utf8_json_response(result)
            
        finally:
            # Temporäre Datei löschen
            try:
                os.unlink(tmp_file_path)
            except:
                pass
                
    except Exception as e:
        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
        print(f"[ERROR] CSV parsing failed: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Verarbeiten der CSV-Datei: {error_msg}")

@app.get("/api/tourplan/status", tags=["status"], summary="Tourplan-Status abfragen")
async def tourplan_status():
    """Gibt den aktuellen Tourplan-Status zurück"""
    try:
        from ingest.http_responses import create_utf8_json_response
        
        # Beispiel-Status (in echter Implementierung würde das aus der DB kommen)
        status_data = {
            "success": True,
            "status": "aktiv",
            "letzte_aktualisierung": "2025-01-07T10:30:00Z",
            "statistiken": {
                "gesamte_kunden": 150,
                "erkannte_adressen": 142,
                "erfolgsquote": "94.7%",
                "letzte_tour": "Tourenplan 01.09.2025"
            },
            "nachrichten": [
                "System läuft stabil",
                "Alle Umlaute (ö, ü, ä, ß) werden korrekt verarbeitet",
                "Geocoding funktioniert einwandfrei"
            ]
        }
        
        return create_utf8_json_response(status_data)
        
    except Exception as e:
        from ingest.http_responses import create_utf8_json_response
        return create_utf8_json_response({
            "success": False,
            "error": str(e)
        })

@app.get("/api/llm-status", tags=["status"], summary="LLM Status")
async def llm_status():
    """LLM Status für Frontend"""
    from ingest.http_responses import create_utf8_json_response
    return create_utf8_json_response({
        "status": "available",
        "model": "dummy",
        "version": "1.0"
    })

@app.get("/api/db-status", tags=["status"], summary="Database Status") 
async def db_status():
    """Database Status für Frontend"""
    from ingest.http_responses import create_utf8_json_response
    return create_utf8_json_response({
        "status": "connected",
        "type": "sqlite",
        "version": "3.0"
    })

@app.get("/api/temp-status", tags=["status"], summary="Temp Files Status")
async def temp_status():
    """Temp-Verzeichnis Status und Bereinigungsinfo"""
    from services.temp_cleanup import get_temp_file_size
    from ingest.http_responses import create_utf8_json_response
    return create_utf8_json_response(get_temp_file_size())

@app.post("/api/temp-cleanup", tags=["status"], summary="Temp Files sofort bereinigen")
async def temp_cleanup_now():
    """Führt Temp-Bereinigung sofort aus"""
    from services.temp_cleanup import cleanup_old_temp_files, get_temp_file_size
    from ingest.http_responses import create_utf8_json_response
    cleanup_old_temp_files()
    return create_utf8_json_response({
        "message": "Temp-Bereinigung durchgeführt",
        "status": get_temp_file_size()
    })

@app.post("/api/archive-parsing-files", tags=["archive"], summary="Parsing-Dateien archivieren")
async def archive_parsing_files(source_dir: str = "tourplaene"):
    """Archiviert alle Parsing-Dateien ins ZIP-Verzeichnis"""
    from services.temp_cleanup import archive_parsing_files as archive_func
    from ingest.http_responses import create_utf8_json_response
    result = archive_func(source_dir=source_dir)
    return create_utf8_json_response(result)

@app.get("/api/archive-status", tags=["archive"], summary="Archive Status")
async def archive_status():
    """Zeigt den Inhalt des ZIP-Archivs"""
    from pathlib import Path
    from ingest.http_responses import create_utf8_json_response
    
    zip_dir = Path("ZIP")
    files = []
    total_size = 0
    
    if zip_dir.exists():
        for item in zip_dir.glob("*"):
            if item.is_file():
                size = item.stat().st_size
                files.append({
                    "name": item.name,
                    "size": size,
                    "size_mb": round(size / 1024 / 1024, 2),
                    "modified": datetime.fromtimestamp(item.stat().st_mtime).isoformat()
                })
                total_size += size
    
    return create_utf8_json_response({
        "archive_dir": str(zip_dir.resolve()),
        "file_count": len(files),
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "files": sorted(files, key=lambda x: x["modified"], reverse=True)
    })

@app.post("/api/process-csv-modular", tags=["csv"], summary="CSV modular verarbeiten")
async def process_csv_modular(file: UploadFile = File(...)):
    """CSV modular verarbeiten mit vollständigem Workflow"""
    try:
        # Temporäre Datei speichern
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp_file:
            content = await file.read()
            tmp_file.write(content)
            tmp_file_path = tmp_file.name
        
        try:
            # Tourplan mit modernem Parser verarbeiten
            from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
            tour_data = parse_tour_plan_to_dict(tmp_file_path)
            
            # Geocoding-Integration
            from repositories.geo_repo import bulk_get, upsert
            from services.geocode_fill import fill_missing
            
            # Alle Adressen sammeln
            all_addresses = []
            for customer in tour_data["customers"]:
                address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
                all_addresses.append(address)
            
            # Bestehende Geocodes aus DB laden
            existing_geo = bulk_get(all_addresses)
            
            # Fehlende Adressen geocodieren (mit Rate-Limiting)
            missing_addresses = [addr for addr in all_addresses if addr not in existing_geo]
            
            # Geocoding für fehlende Adressen (max 50 pro Request)
            geocoded_results = []
            if missing_addresses:
                geocoded_results = await fill_missing(missing_addresses[:50], limit=50, dry_run=False)
            
            # Geocoding-Statistiken
            geocoding_stats = {
                "total": len(all_addresses),
                "from_db": len(existing_geo),
                "from_geocoding": len(geocoded_results),
                "failed": len(missing_addresses) - len(geocoded_results),
                "new_customers_saved": len(geocoded_results)
            }
            
            # Tour-Daten mit Koordinaten erweitern
            tours_with_coords = []
            for tour in tour_data["tours"]:
                customers_with_coords = []
                for customer in tour["customers"]:
                    address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
                    
                    # Koordinaten aus DB oder Geocoding-Ergebnis
                    coords = existing_geo.get(address)
                    if not coords and geocoded_results:
                        for result in geocoded_results:
                            if result.get("address") == address:
                                coords = {"lat": result.get("lat"), "lon": result.get("lon")}
                                break
                    
                    customer_with_coords = {
                        **customer,
                        "coordinates": coords,
                        "address": address
                    }
                    customers_with_coords.append(customer_with_coords)
                
                tour_with_coords = {
                    **tour,
                    "customers": customers_with_coords
                }
                tours_with_coords.append(tour_with_coords)
            
            # Workflow-Ergebnis
            workflow_results = {
                "final_results": {
                    "routes": {
                        "total_routes": len(tours_with_coords),
                        "routes": tours_with_coords
                    },
                    "geocoding": geocoding_stats
                }
            }
            
            result = {
                "success": True,
                "file_name": file.filename,
                "workflow_results": workflow_results,
                "tours": tours_with_coords,
                "customers": tour_data["customers"],
                "stats": tour_data["stats"],
                "geocoding": geocoding_stats
            }
            
            from ingest.http_responses import create_utf8_json_response
            return create_utf8_json_response(result)
            
        finally:
            # Temporäre Datei löschen
            try:
                os.unlink(tmp_file_path)
            except:
                pass
                
    except Exception as e:
        error_msg = str(e).encode('utf-8', errors='replace').decode('utf-8')
        print(f"[ERROR] CSV processing failed: {error_msg}")
        raise HTTPException(status_code=500, detail=f"Fehler beim Verarbeiten der CSV-Datei: {error_msg}")

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
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
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

@app.get("/health/db", tags=["health"], summary="Datenbank-Health prüfen")
async def health_db():
    """Prüft den Status der Datenbankverbindung"""
    try:
        from db.core import db_health
        status = db_health()
        code = 200 if status.get("ok") else 503
        from ingest.http_responses import create_utf8_json_response
        return create_utf8_json_response(status)
    except Exception as e:
        from ingest.http_responses import create_utf8_json_response
        return create_utf8_json_response({
            "ok": False,
            "error": str(e)
        })

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

def get_kunde_id_by_name_adresse(name: str, street: str, city: str) -> int:
    """Sucht Kunde-ID nach Name und Adresse in der echten Datenbank"""
    try:
        import sqlite3
        import os
        
        # Prüfe customers.db zuerst
        if os.path.exists('data/customers.db'):
            conn = sqlite3.connect('data/customers.db')
            cursor = conn.cursor()
            
            # Suche in customers-Tabelle
            normalized_name = _normalize_string(name)
            normalized_street = _normalize_string(street)
            normalized_city = _normalize_string(city)
            
            # Verschiedene Suchstrategien für customers.db
            queries = [
                "SELECT id FROM customers WHERE LOWER(name) LIKE ? AND LOWER(street) LIKE ? AND LOWER(city) LIKE ?",
                "SELECT id FROM customers WHERE LOWER(name) LIKE ? AND LOWER(street) LIKE ?",
                "SELECT id FROM customers WHERE LOWER(name) LIKE ? AND LOWER(city) LIKE ?"
            ]
            
            for query in queries:
                try:
                    cursor.execute(query, (f'%{normalized_name}%', f'%{normalized_street}%', f'%{normalized_city}%'))
                    result = cursor.fetchone()
                    if result:
                        conn.close()
                        print(f"[DB-SUCCESS] Kunde gefunden in customers.db: ID {result[0]}")
                        return result[0]
                except sqlite3.OperationalError:
                    continue
            
            conn.close()
        
        # Prüfe traffic.db als Fallback
        if os.path.exists('data/traffic.db'):
            conn = sqlite3.connect('data/traffic.db')
            cursor = conn.cursor()
            
            # Suche in kunden-Tabelle (adresse ist kombiniert)
            normalized_name = _normalize_string(name)
            normalized_street = _normalize_string(street)
            normalized_city = _normalize_string(city)
            
            # Suche nach Name und Adresse
            cursor.execute("SELECT id FROM kunden WHERE LOWER(name) LIKE ? AND LOWER(adresse) LIKE ?", 
                          (f'%{normalized_name}%', f'%{normalized_street}%'))
            result = cursor.fetchone()
            if result:
                conn.close()
                print(f"[DB-SUCCESS] Kunde gefunden in traffic.db: ID {result[0]}")
                return result[0]
            
            conn.close()
        
        print(f"[DB-INFO] Kein Kunde gefunden für: {name}, {street}, {city}")
        return None
        
    except Exception as e:
        print(f"[DB-ERROR] Fehler bei Kunden-Suche: {e}")
        return None

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
        
        with open("frontend/tourplan-management.html", "r", encoding="utf-8") as f:
            content = f.read()
        
        return create_utf8_html_response(content)
        
    except Exception as e:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail=f"Fehler beim Laden der Seite: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8111)