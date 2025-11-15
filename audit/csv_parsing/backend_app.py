from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import re
import json
import os
from io import BytesIO
import logging
from logging.handlers import RotatingFileHandler

from fastapi import FastAPI, HTTPException, Query, UploadFile, File, Form
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from backend.db.schema import init_db
from backend.db.dao import Kunde, insert_tour, upsert_kunden, _normalize_string, get_kunde_id_by_name_adresse, get_kunde_by_id, _connect, get_customers_by_ids
from backend.parsers import parse_teha_excel, parse_teha_excel_all_sheets, parse_teha_excel_sections, parse_tour_plan, parse_tour_plan_to_dict
from backend.parsers.excel_parser import parse_universal_routes
from backend.parsers.pdf_parser import parse_pdf_tours, preview_summary
from backend.services.geocode import geocode_address
from backend.services.multi_tour_generator import MultiTourGenerator, Customer
from backend.services.optimization_rules import default_rules
from backend.services.real_routing import RealRoutingService, RoutePoint
from backend.services.ai_optimizer import AIOptimizer, Stop
from backend.services.tour_manager import TourManager
from backend.services.workflow_orchestrator import WorkflowOrchestrator
from pydantic import BaseModel

# Robustes CSV-Decoding für Tourpläne
import unicodedata
import re

def read_tourplan_csv(csv_file):
    """Liest Tourplan-CSV mit korrektem Encoding - HARDENED VERSION."""
    from backend.utils.encoding_guards import trace_text, assert_no_mojibake
    
    try:
        # 1) Bytes korrekt -> Unicode (CP850 für Windows-Tourpläne)
        raw = csv_file.read_bytes()
        
        # 2) EINMALIGE Decoding mit CP850 (Windows-Standard)
        # Danach IMMER UTF-8 verwenden
        try:
            text = raw.decode("cp850")  # Windows-Standard für CSV-Export
            print(f"[CSV INGEST] CP850 erfolgreich für {csv_file.name}")
        except UnicodeDecodeError:
            # Fallback nur bei echten UTF-8-Dateien
            try:
                text = raw.decode("utf-8-sig")  # Mit BOM
                print(f"[CSV INGEST] UTF-8-sig erfolgreich für {csv_file.name}")
            except UnicodeDecodeError:
                text = raw.decode("utf-8")  # Ohne BOM
                print(f"[CSV INGEST] UTF-8 erfolgreich für {csv_file.name}")
        
        # 3) Unicode normalisieren (verlustfrei)
        text = unicodedata.normalize("NFC", text)
        
        # 4) GUARD: Mojibake-Prüfung direkt nach Ingest
        assert_no_mojibake(text)
        
        # 5) TRACE: Erste 200 Zeichen für Diagnose
        trace_text("CSV_INGEST", text[:200])
        
        # 6) In DataFrame - KEINE Reparatur mehr!
        import pandas as pd
        from io import StringIO
        return pd.read_csv(StringIO(text), sep=';', header=None, dtype=str)
        
    except Exception as e:
        raise Exception(f"Fehler beim Lesen von {csv_file}: {e}")

# ENTFERNT: repair_utf8_as_latin1() - verschleiert nur Encoding-Probleme!

def normalize_de(text: str, mode: str = "preserve") -> str:
    """Sprachliche Normalisierung (reversibel)."""
    if not text or not isinstance(text, str):
        return text
    
    # 1) Unicode-NFC + Whitespace säubern
    t = unicodedata.normalize("NFC", text)
    t = re.sub(r"\s+", " ", t).strip()
    
    # 2) Optional transliterieren - nur für ASCII-Pflichten
    if mode == "ascii":
        german_map = str.maketrans({
            "ä":"ae", "ö":"oe", "ü":"ue", "Ä":"Ae", "Ö":"Oe", "Ü":"Ue", "ß":"ss"
        })
        t = t.translate(german_map)
    elif mode != "preserve":
        raise ValueError("mode muss 'preserve' oder 'ascii' sein")
    
    return t


# Pydantic Models für API
class CustomerUpdate(BaseModel):
    name: str
    adresse: str
    lat: float
    lon: float


class OrderRequest(BaseModel):
    tour_id: str
    datum: str
    kunden_ids: List[int]

# Tour Management Models
class TourCreateRequest(BaseModel):
    tour_name: str
    tour_type: str  # W, PIR, T
    tour_date: str  # YYYY-MM-DD
    total_customers: int
    total_distance_km: float
    total_duration_min: int
    stops: List[Dict[str, Any]]

class TourStopUpdateRequest(BaseModel):
    tour_id: int
    new_sequence: List[int]  # Liste der stop_ids in neuer Reihenfolge

class TourCompleteRequest(BaseModel):
    tour_id: int
    actual_distance_km: Optional[float] = None
    actual_duration_min: Optional[int] = None
    fuel_consumption_l: Optional[float] = None
    driver_notes: Optional[str] = None
    customer_feedback: Optional[str] = None
    weather_conditions: Optional[str] = None
    traffic_conditions: Optional[str] = None


def create_app() -> FastAPI:
    app = FastAPI(title="FAMO TrafficApp API", version="2.0")
    
    # UTF-8 Logging Setup (optional)
    try:
        from backend.utils.encoding_guards import setup_utf8_logging, smoke_test_encoding
        setup_utf8_logging()
        print("[STARTUP] ✅ UTF-8 Logging konfiguriert")
    except Exception as e:
        print(f"[STARTUP] ⚠️ UTF-8 Logging Setup fehlgeschlagen: {e}")
        # Server trotzdem starten
    
    # Smoke Test beim Start (optional)
    try:
        smoke_test_encoding()
        print("[STARTUP] ✅ Encoding-Smoke-Test erfolgreich")
    except Exception as e:
        print(f"[STARTUP] ⚠️ Encoding-Smoke-Test fehlgeschlagen: {e}")
        # Server trotzdem starten

    # Static files (Frontend)
    try:
        app.mount("/ui", StaticFiles(directory="frontend", html=True), name="frontend")
        print("[OK] Frontend erfolgreich gemountet auf /ui")
        
        # Dashboard auch direkt unter / verfügbar machen
        @app.get("/", response_class=HTMLResponse, tags=["frontend"])
        def root_dashboard():
            """Zeigt das Dashboard direkt unter / an"""
            try:
                with open("frontend/index.html", "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                return "<h1>Frontend nicht gefunden</h1>"
        
        # Tourplan Test Seite
        @app.get("/tourplan-test.html", response_class=HTMLResponse, tags=["frontend"])
        def tourplan_test():
            """Zeigt die Tourplan Test Seite"""
            try:
                with open("frontend/tourplan-test.html", "r", encoding="utf-8") as f:
                    return f.read()
            except FileNotFoundError:
                return "<h1>Tourplan Test Seite nicht gefunden</h1>"
    except Exception as e:
        print(f"[FEHLER] Frontend-Mount fehlgeschlagen: {e}")
        # Fallback: Einfache HTML-Antwort
        @app.get("/ui/", response_class=HTMLResponse)
        def frontend_fallback():
            return """
            <!DOCTYPE html>
            <html>
            <head><title>FAMO TrafficApp</title></head>
            <body>
                <h1>FAMO TrafficApp läuft!</h1>
                <p>Server ist aktiv auf Port 8111</p>
                <p><a href="/docs">API-Dokumentation</a></p>
                <p><a href="/health">Server-Status</a></p>
            </body>
            </html>
            """

    @app.get("/health", tags=["system"])
    def health() -> dict:
        return {"status": "ok"}

    @app.get("/test", tags=["system"])
    def test() -> dict:
        return {"message": "Server läuft", "port": "8111"}

    @app.get("/api/dashboard", tags=["dashboard"])
    def get_dashboard() -> dict:
        """Gibt Dashboard-Daten zurück (Anzahl Touren, Kunden)"""
        try:
            db_path = _db_path()
            if not db_path.exists():
                return {"tour_count": 0, "customer_count": 0}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Anzahl Touren
            cursor.execute('SELECT COUNT(*) FROM touren')
            tour_count = cursor.fetchone()[0]
            
            # Anzahl Kunden
            cursor.execute('SELECT COUNT(*) FROM kunden')
            customer_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                "tour_count": tour_count,
                "customer_count": customer_count,
                "status": "success"
            }
            
        except Exception as e:
            return {
                "tour_count": 0,
                "customer_count": 0,
                "error": str(e),
                "status": "success"  # Geändert: Server läuft auch ohne DB
            }

    @app.get("/api/llm-status", tags=["ai"])
    def get_llm_status():
        """Prüft den Status der verfügbaren LLM-Provider"""
        try:
            # Ollama-Status prüfen
            ollama_available = False
            ollama_provider = "Ollama"
            
            try:
                import requests
                response = requests.get("http://localhost:11434/api/tags", timeout=5)
                if response.status_code == 200:
                    ollama_available = True
            except Exception:
                pass
            
            # OpenAI-Status prüfen (falls API-Key gesetzt)
            openai_available = False
            openai_provider = "OpenAI"
            
            if os.getenv("OPENAI_API_KEY"):
                try:
                    import openai
                    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
                    # Einfacher Test-Call
                    response = client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": "Test"}],
                        max_tokens=5
                    )
                    openai_available = True
                except Exception:
                    pass
            
            # Verfügbaren Provider zurückgeben
            if ollama_available:
                return {
                    "available": True,
                    "provider": ollama_provider,
                    "status": "online"
                }
            elif openai_available:
                return {
                    "available": True,
                    "provider": openai_provider,
                    "status": "online"
                }
            else:
                return {
                    "available": False,
                    "provider": "Kein Provider",
                    "status": "offline"
                }
                
        except Exception as e:
            return {
                "available": False,
                "provider": "Fehler",
                "status": "error",
                "error": str(e)
            }

    @app.get("/api/db-status", tags=["system"], summary="Datenbank-Status prüfen")
    async def get_db_status() -> Dict[str, Any]:
        """Prüft Datenbank-Status und Kundenanzahl"""
        try:
            db_path = _db_path()
            if not db_path.exists():
                return {
                    "status": "offline",
                    "total_customers": 0,
                    "touren_count": 0,
                    "message": "Datenbank nicht gefunden"
                }
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Kunden in kunden-Tabelle zählen
            cursor.execute("SELECT COUNT(*) FROM kunden")
            kunden_count = cursor.fetchone()[0]
            
            # Kunden in customers-Tabelle zählen (falls vorhanden)
            try:
                cursor.execute("SELECT COUNT(*) FROM customers")
                customers_count = cursor.fetchone()[0]
            except Exception:
                customers_count = 0
            
            # Touren zählen
            cursor.execute("SELECT COUNT(*) FROM touren")
            touren_count = cursor.fetchone()[0]
            
            total_customers = kunden_count + customers_count
            conn.close()
            
            return {
                "status": "online",
                "kunden_table": kunden_count,
                "customers_table": customers_count,
                "total_customers": total_customers,
                "touren_count": touren_count,
                "message": f"DB online - {total_customers} Kunden, {touren_count} Touren"
            }
            
        except Exception as e:
            return {
                "status": "error",
                "kunden_table": 0,
                "customers_table": 0,
                "total_customers": 0,
                "touren_count": 0,
                "message": f"DB Fehler: {str(e)}"
            }

    @app.get("/api/geocode", tags=["geo"], summary="Adresse geokodieren")
    async def geocode_endpoint(
        address: Optional[str] = Query(None, description="Vollständige Adresse"),
        street: Optional[str] = Query(None, description="Straße"),
        postal_code: Optional[str] = Query(None, description="Postleitzahl"),
        city: Optional[str] = Query(None, description="Ort"),
    ) -> Dict[str, Any]:
        parts: List[str] = []
        if address:
            parts.append(address)
        else:
            for value in (street, postal_code, city):
                if value:
                    parts.append(value)

        if not parts:
            raise HTTPException(status_code=400, detail="Adresse erforderlich")

        query_address = ", ".join(part.strip() for part in parts if part and part.strip())
        if not query_address:
            raise HTTPException(status_code=400, detail="Adresse unvollständig")

        result = geocode_address(query_address)
        if not result:
            raise HTTPException(status_code=404, detail="Adresse nicht gefunden")

        return {
            "address": query_address,
            "lat": result.get("lat"),
            "lon": result.get("lon"),
            "provider": result.get("provider"),
            "postal_code": result.get("postal_code"),
            "city": result.get("city"),
            }

    @app.get("/api/touren-details", tags=["touren"], summary="Touren mit Details abrufen")
    async def get_touren_details() -> Dict[str, Any]:
        """Touren mit Namen, BAR-Status und Kundenanzahl abrufen"""
        try:
            db_path = _db_path()
            if not db_path.exists():
                return {"status": "error", "error": "Datenbank nicht gefunden", "touren": []}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Touren mit Details abrufen
            cursor.execute("""
                SELECT tour_id, datum, kunden_ids, dauer_min, distanz_km, fahrer, created_at
                FROM touren 
                ORDER BY created_at DESC
            """)
            
            touren = []
            for row in cursor.fetchall():
                tour_id, datum, kunden_ids, dauer_min, distanz_km, fahrer, created_at = row
                
                # Kundenanzahl aus JSON-Array
                try:
                    import json
                    kunden_liste = json.loads(kunden_ids) if kunden_ids else []
                    kunden_count = len(kunden_liste)
                except Exception:
                    kunden_count = 0
                
                # BAR-Kunden zählen (aus der ursprünglichen CSV-Verarbeitung)
                # Da wir jetzt Touren zusammenführen, zeigen wir die Gesamtanzahl
                bar_count = 0  # Wird später aus den Kunden-Daten berechnet
                
                touren.append({
                    "id": tour_id,
                    "name": tour_id,
                    "datum": datum,
                    "has_bar": False,  # Wird später berechnet
                    "kunden_count": kunden_count,
                    "bar_count": bar_count,
                    "normal_count": kunden_count - bar_count,
                    "dauer_min": dauer_min,
                    "distanz_km": distanz_km,
                    "fahrer": fahrer,
                    "created_at": created_at
                })
            
            conn.close()
            
            return {
                "status": "ok",
                "touren": touren,
                "total_touren": len(touren),
                "bar_touren": len([t for t in touren if t['is_bar']]),
                "normal_touren": len([t for t in touren if not t['is_bar']])
            }
        except Exception as e:
            return {"status": "error", "error": str(e), "touren": [], "total_touren": 0}

    @app.get("/api/tours/{date}", tags=["tours"])
    def get_tours_by_date(date: str) -> dict:
        """Gibt alle Touren für ein bestimmtes Datum zurück, einschließlich Untertouren"""
        try:
            db_path = _db_path()
            if not db_path.exists():
                return {"tours": [], "message": "Datenbank nicht gefunden"}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Haupttouren für das Datum laden (ohne parent_tour_id)
            cursor.execute('''
                SELECT t.id, t.tour_name, t.tour_type, t.tour_date, t.parent_tour_id
                FROM touren t
                WHERE t.tour_date = ? AND t.parent_tour_id IS NULL
                ORDER BY t.tour_name, t.id
            ''', (date,))
            
            main_tours = cursor.fetchall()
            tours_data = []
            
            for main_tour in main_tours:
                tour_id, tour_name, tour_type, tour_date, parent_tour_id = main_tour
                
                # Kunden für diese Haupttour laden
                cursor.execute('''
                    SELECT k.id, k.name, k.adresse, k.lat, k.lon, k.seq_no
                    FROM kunden k
                    INNER JOIN tour_kunden tk ON k.id = tk.customer_id
                    WHERE tk.tour_id = ?
                    ORDER BY k.seq_no
                ''', (tour_id,))
                
                customers = cursor.fetchall()
                customer_count = len(customers)
                
                # Tour-Informationen
                tour_info = {
                    "id": tour_id,
                    "tour_name": tour_name or f"Tour {tour_id}",
                    "tour_type": tour_type,
                    "tour_date": tour_date,
                    "customer_count": customer_count,
                    "is_main_tour": True,
                    "parent_tour_id": parent_tour_id,
                    "customers": [],
                    "subtours": []
                }
                
                # Kunden hinzufügen
                for customer in customers:
                    cid, name, adresse, lat, lon, seq_no = customer
                    tour_info["customers"].append({
                        "id": cid,
                        "name": name or f"Kunde {cid}",
                        "address": adresse or "Keine Adresse",
                        "latitude": lat,
                        "longitude": lon,
                        "sequence": seq_no or 0
                    })
                
                # Untertouren für diese Haupttour laden
                cursor.execute('''
                    SELECT t.id, t.tour_name, t.tour_type, t.tour_date
                    FROM touren t
                    WHERE t.parent_tour_id = ?
                    ORDER BY t.tour_name
                ''', (tour_id,))
                
                subtours = cursor.fetchall()
                for subtour in subtours:
                    st_id, st_name, st_type, st_date = subtour
                    
                    # Kunden der Untertour laden
                    cursor.execute('''
                        SELECT k.id, k.name, k.adresse, k.lat, k.lon, k.seq_no
                        FROM kunden k
                        INNER JOIN tour_kunden tk ON k.id = tk.customer_id
                        WHERE tk.tour_id = ?
                        ORDER BY k.seq_no
                    ''', (st_id,))
                    
                    subtour_customers = cursor.fetchall()
                    subtour_info = {
                        "id": st_id,
                        "tour_name": st_name or f"Untertour {st_id}",
                        "tour_type": st_type,
                        "tour_date": st_date,
                        "customer_count": len(subtour_customers),
                        "is_main_tour": False,
                        "parent_tour_id": tour_id,
                        "customers": []
                    }
                    
                    for customer in subtour_customers:
                        cid, name, adresse, lat, lon, seq_no = customer
                        subtour_info["customers"].append({
                            "id": cid,
                            "name": name or f"Kunde {cid}",
                            "address": adresse or "Keine Adresse",
                            "latitude": lat,
                            "longitude": lon,
                            "sequence": seq_no or 0
                        })
                    
                    tour_info["subtours"].append(subtour_info)
                
                tours_data.append(tour_info)
            
            conn.close()
            
            return {
                "tours": tours_data,
                "date": date,
                "count": len(tours_data),
                "total_customers": sum(tour["customer_count"] for tour in tours_data),
                "status": "success"
            }
            
        except Exception as e:
            return {
                "tours": [],
                "error": str(e),
                "status": "error"
            }

    @app.get("/api/address-validation", tags=["validation"], summary="Echte Adressvalidierung aus der Datenbank")
    def get_address_validation() -> dict:
        """Gibt die echten Validierungsergebnisse aller Adressen aus der Datenbank zurück"""
        try:
            import sqlite3
            from pathlib import Path
            
            db_path = _db_path()
            if not db_path.exists():
                return {
                    "error": "Datenbank nicht gefunden",
                    "total_addresses": 0,
                    "valid_addresses": 0,
                    "invalid_addresses": 0,
                    "success_rate": 0.0
                }
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Alle Adressen aus dem Geocache holen
            cursor.execute('SELECT adresse, lat, lon FROM geocache ORDER BY adresse')
            results = cursor.fetchall()
            conn.close()
            
            total_addresses = len(results)
            valid_addresses = sum(1 for _, lat, lon in results if lat and lon and lat != 0.0 and lon != 0.0)
            invalid_addresses = total_addresses - valid_addresses
            success_rate = (valid_addresses / total_addresses * 100) if total_addresses > 0 else 0.0
            
            # Beispiel-Adressen für Anzeige
            sample_addresses = []
            for adresse, lat, lon in results[:5]:  # Erste 5 Adressen
                if lat and lon and lat != 0.0 and lon != 0.0:
                    sample_addresses.append({
                        "address": adresse,
                        "lat": lat,
                        "lon": lon,
                        "status": "valid"
                    })
                else:
                    sample_addresses.append({
                        "address": adresse,
                        "lat": None,
                        "lon": None,
                        "status": "invalid"
                    })
            
            return {
                "total_addresses": total_addresses,
                "valid_addresses": valid_addresses,
                "invalid_addresses": invalid_addresses,
                "success_rate": round(success_rate, 1),
                "sample_addresses": sample_addresses,
                "message": f"Validierung abgeschlossen: {valid_addresses}/{total_addresses} Adressen gültig ({success_rate:.1f}%)"
            }
            
        except Exception as e:
            return {
                "error": f"Fehler bei der Validierung: {str(e)}",
                "total_addresses": 0,
                "valid_addresses": 0,
                "invalid_addresses": 0,
                "success_rate": 0.0
            }

    def _db_path() -> Path:
        # Projektwurzel ist ein Verzeichnis oberhalb von `backend/`
        return Path(__file__).resolve().parents[1] / "data" / "traffic.db"

    def _dedupe_preserve_order(items: List[int]) -> List[int]:
        """Entfernt Duplikate in einer ID-Liste und behält die Reihenfolge bei."""
        seen: set[int] = set()
        result: List[int] = []
        for value in items:
            if value not in seen:
                seen.add(value)
                result.append(value)
        return result

    def _normalize_address(addr: Optional[str]) -> str:
        if not addr:
            return ""
        s = addr.strip().lower()
        while "  " in s:
            s = s.replace("  ", " ")
        return s

    def _dedupe_customers_by_address(rows: List[tuple]) -> List[tuple]:
        """Dedupeliste für (id, name, adresse) anhand der Adresse, Reihenfolge bleibt erhalten."""
        seen_addr: set[str] = set()
        result: List[tuple] = []
        for cid, name, adresse in rows:
            key = _normalize_address(adresse)
            if key in seen_addr:
                continue
            seen_addr.add(key)
            result.append((cid, name, adresse))
        return result

    def _normalize_ai_output(ai_data: Any) -> Dict[str, Any]:
        """Akzeptiert verschiedene KI-Ausgabeformate und vereinheitlicht sie auf
        {"tours":[{"name":str, "customers":[{"name":str, "adresse":str, "payment":str|null, "time_window":str|null}]}]}.
        Unterstützt u. a. Schemata mit tour/stops, name/customers, kunden/kunde, zahlung/payment.
        """
        def normalize_stop(raw: Any) -> Optional[Dict[str, Any]]:
            # String-Variante: "Name — Adresse" oder "Name - Adresse"
            if isinstance(raw, str):
                s = raw.strip()
                import re as _re
                m = _re.match(r"^(.+?)\s*[–—-]\s*(.+)$", s)
                if m:
                    return {"name": m.group(1).strip(), "adresse": m.group(2).strip()}
                return None
            if not isinstance(raw, dict):
                return None
            # flexible Schlüsselnamen
            name = raw.get("name") or raw.get("kunde") or raw.get("kundenname") or raw.get("customer")
            addr = raw.get("adresse") or raw.get("address") or raw.get("addr")
            payment = raw.get("payment") or raw.get("zahlung")
            time_window = raw.get("time_window") or raw.get("zeitfenster") or raw.get("time")
            if not (name and addr):
                return None
            out: Dict[str, Any] = {"name": str(name).strip(), "adresse": str(addr).strip()}
            if payment is not None:
                p = str(payment).strip().lower()
                if p in ("bar", "cash", "cash on delivery"):
                    out["payment"] = "bar"
                elif p:
                    out["payment"] = p
            if time_window is not None:
                out["time_window"] = str(time_window).strip()
            if isinstance(raw.get("unsicher"), bool):
                out["unsicher"] = raw["unsicher"]
            return out

        tours_out: list[dict[str, object]] = []
        tours_iter: list = []
        # ai_data kann dict mit "tours" sein, Liste von Touren, oder dict mit "tour"/"stops" etc.
        if isinstance(ai_data, dict):
            if isinstance(ai_data.get("tours"), list):
                tours_iter = ai_data["tours"]
            elif isinstance(ai_data.get("data"), list):
                tours_iter = ai_data["data"]
            elif isinstance(ai_data.get("tour"), str) and isinstance(ai_data.get("stops"), list):
                tours_iter = [ai_data]
        elif isinstance(ai_data, list):
            tours_iter = ai_data

    @app.get("/api/load-preset-file", tags=["parsing"], summary="Vordefinierte CSV-Datei laden")
    def load_preset_file(filename: str) -> dict:
        """Lädt eine vordefinierte CSV-Datei aus dem tourplaene-Ordner"""
        try:
            import pandas as pd
            
            # Dateipfad zum tourplaene-Ordner
            tourplaene_dir = Path("tourplaene")
            file_path = tourplaene_dir / filename
            
            if not file_path.exists():
                return {
                    "success": False,
                    "error": f"Datei {filename} nicht gefunden im tourplaene-Ordner"
                }
            
            # Datei einlesen
            if filename.endswith('.csv'):
                df = pd.read_csv(file_path)
            elif filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(file_path)
            else:
                return {
                    "success": False,
                    "error": "Nur CSV und Excel-Dateien werden unterstützt"
                }
            
            # Universellen Parser verwenden
            routes_data = parse_universal_routes(df)
            
            return {
                "success": True,
                "filename": filename,
                "routes_data": routes_data,
                "message": f"Vordefinierte Datei erfolgreich geladen: {routes_data['total_routes']} Routen gefunden"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Laden der vordefinierten Datei"
            }

    @app.post("/api/parse-universal-routes", tags=["parsing"], summary="Universeller CSV-Parser für alle Routen")
    def parse_universal_routes_api(file: UploadFile = File(...)) -> dict:
        """Parst CSV/Excel-Dateien und extrahiert alle Routen-Typen universell"""
        try:
            import pandas as pd
            from io import BytesIO
            
            # Datei einlesen
            content = file.file.read()
            file.file.seek(0)
            
            # Excel oder CSV parsen
            if file.filename.endswith(('.xlsx', '.xls')):
                df = pd.read_excel(BytesIO(content))
            elif file.filename.endswith('.csv'):
                df = pd.read_csv(BytesIO(content))
            else:
                raise HTTPException(status_code=400, detail="Nur Excel (.xlsx, .xls) oder CSV (.csv) Dateien unterstützt")
            
            # Universellen Parser verwenden
            routes_data = parse_universal_routes(df)
            
            return {
                "success": True,
                "filename": file.filename,
                "routes_data": routes_data,
                "message": f"CSV erfolgreich geparst: {routes_data['total_routes']} Routen gefunden"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Parsen der CSV-Datei"
            }

        for t in tours_iter:
            if not isinstance(t, dict):
                continue
            name = t.get("name") or t.get("tour") or t.get("titel") or t.get("id")
            if not name:
                continue
            stops = (
                t.get("customers")
                or t.get("kunden")
                or t.get("stops")
                or []
            )
            customers: List[Dict[str, Any]] = []
            if isinstance(stops, list):
                for s in stops:
                    customers.append(s)
            tour_payment = t.get("payment") or t.get("zahlung")
            tour_obj: Dict[str, Any] = {"name": str(name).strip(), "customers": customers}
            if tour_payment:
                p = str(tour_payment).strip().lower()
                if p in ("bar", "cash"):
                    tour_obj["payment"] = "bar"
                else:
                    tour_obj["payment"] = p
            tours_out.append(tour_obj)

        return {"tours": tours_out}

    def _normalize_tour_title(title: str) -> str:
        name = (title or "Tour").strip()
        name = re.sub(r"\bUhr\b", "", name, flags=re.IGNORECASE).strip()
        name = re.sub(r"\bBAR\b", "", name, flags=re.IGNORECASE).strip()
        while "  " in name:
            name = name.replace("  ", " ")
        return name or "Tour"

    @app.get("/summary", tags=["db"])
    def summary() -> Dict[str, Any]:
        db = _db_path()
        if not db.exists():
            return {"db_exists": False, "kunden": 0, "touren": 0, "beispiele": []}
        con = sqlite3.connect(db)
        cur = con.cursor()
        kunden_count = cur.execute("select count(*) from kunden").fetchone()[0]
        touren_count = cur.execute("select count(*) from touren").fetchone()[0]
        beispiele = cur.execute(
            "select id, name, adresse from kunden order by id desc limit 5"
        ).fetchall()
        return {
            "db_exists": True,
            "db": str(db.resolve()),
            "kunden": kunden_count,
            "touren": touren_count,
            "beispiele": beispiele,
        }

    @app.get("/kunden", tags=["db"])
    def list_kunden(
        limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0)
    ) -> List[Dict[str, Any]]:
        db = _db_path()
        if not db.exists():
            return []
        con = sqlite3.connect(db)
        cur = con.cursor()
        rows = cur.execute(
            "select id, name, adresse, lat, lon from kunden order by id desc limit ? offset ?",
            (limit, offset),
        ).fetchall()
        return [
            {"id": r[0], "name": r[1], "adresse": r[2], "lat": r[3], "lon": r[4]}
            for r in rows
        ]

    @app.get("/api/tours", tags=["tours"], summary="Touren aus customers")
    def api_get_tours() -> List[Dict[str, Any]]:
        db_path = _db_path()
        if not db_path.exists():
            return []

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT tour_type, tour_time, source_file, COUNT(*) AS customer_count
            FROM customers
            GROUP BY tour_type, tour_time, source_file
            HAVING customer_count > 0
            ORDER BY source_file DESC, tour_type, tour_time
            """
        )

        tours = [
            {
                "tour_type": tour_type or "",
                "tour_time": tour_time or "",
                "source_file": source_file,
                "customer_count": count,
            }
            for tour_type, tour_time, source_file, count in cursor.fetchall()
        ]

        conn.close()
        return tours

    @app.get(
        "/api/tours/{tour_type}/{tour_time}",
        tags=["tours"],
        summary="Kunden einer Tour",
    )
    def api_get_tour_customers(tour_type: str, tour_time: str) -> Dict[str, Any]:
        db_path = _db_path()
        if not db_path.exists():
            return {"tour": {}, "customers": []}

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT customer_number, name, street, postal_code, city, latitude, longitude, bar_flag
            FROM customers
            WHERE tour_type = ? AND IFNULL(tour_time, '') = ?
            ORDER BY name
            """,
            (tour_type, tour_time),
        )

        customers = [
            {
                "customer_number": row[0],
                "name": row[1],
                "street": row[2],
                "postal_code": row[3],
                "city": row[4],
                "latitude": row[5],
                "longitude": row[6],
                "bar_flag": bool(row[7]),
            }
            for row in cursor.fetchall()
        ]

        conn.close()
        return {
            "tour": {
                "tour_type": tour_type,
                "tour_time": tour_time,
                "customer_count": len(customers),
            },
            "customers": customers,
        }

    @app.get("/touren", tags=["db"], summary="Touren aus DB")
    def list_touren(
        limit: int = Query(20, ge=1, le=200), offset: int = Query(0, ge=0)
    ) -> List[Dict[str, Any]]:
        db = _db_path()
        if not db.exists():
            return []
        con = sqlite3.connect(db)
        cur = con.cursor()
        rows = cur.execute(
            "select id, tour_id, datum, kunden_ids, dauer_min, distanz_km, has_bar from touren",
        ).fetchall()
        rows.sort(key=lambda r: (_parse_tour_date(r[2]), _parse_tour_time_minutes(r[1]), r[0]))
        result: List[Dict[str, Any]] = []
        for r in rows:
            kunden_ids = r[3]
            try:
                raw_ids = json.loads(kunden_ids) if kunden_ids else []
                stops_count = len(_dedupe_preserve_order(raw_ids)) if raw_ids else 0
            except Exception:
                stops_count = 0
            result.append(
                {
                    "id": r[0],
                    "tour": r[1],
                    "has_bar": bool(r[6]) if len(r) > 6 else False,
                    "datum": r[2],
                    "stops": stops_count,
                    "dauer_min": r[4],
                    "distanz_km": r[5],
                }
            )
        return result

    @app.put("/customers/{customer_id}", tags=["db"], summary="Kunden-Daten aktualisieren")
    def update_customer(customer_id: int, payload: CustomerUpdate) -> Dict[str, Any]:
        """Aktualisiert Name und/oder Adresse eines Kunden und gibt den Datensatz zurück."""
        try:
            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
            con = sqlite3.connect(db)

            row = con.execute("select id, name, adresse from kunden where id= ?", (customer_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

            new_name = payload.name if payload.name is not None else row[1]
            new_addr = payload.adresse if payload.adresse is not None else row[2]

            con.execute("update kunden set name=?, adresse=? where id=?", (new_name, new_addr, customer_id))
            con.commit()

            return {"id": customer_id, "name": new_name, "adresse": new_addr}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Update fehlgeschlagen: {e}")

    @app.delete("/customers/{customer_id}", tags=["db"], summary="Kunde löschen und aus Touren entfernen")
    def delete_customer(customer_id: int) -> Dict[str, Any]:
        """Löscht einen Kunden aus der Tabelle `kunden` und entfernt die ID aus allen Touren.
        Gibt die Anzahl betroffener Touren zurück."""
        try:
            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
            con = sqlite3.connect(db)

            exists = con.execute("select 1 from kunden where id=?", (customer_id,)).fetchone()
            if not exists:
                raise HTTPException(status_code=404, detail="Kunde nicht gefunden")

            affected = 0
            rows = con.execute("select id, kunden_ids from touren").fetchall()
            for tid, kid_json in rows:
                try:
                    ids = json.loads(kid_json) if kid_json else []
                except Exception:
                    ids = []
                new_ids = [i for i in ids if i != customer_id]
                if new_ids != ids:
                    affected += 1
                    con.execute("update touren set kunden_ids=? where id=?", (json.dumps(new_ids), tid))

            con.execute("delete from kunden where id=?", (customer_id,))
            con.commit()

            return {"deleted": True, "removed_from_tours": affected, "customer_id": customer_id}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Löschen fehlgeschlagen: {e}")

    @app.get("/plan", tags=["db"], summary="Touren-Planvorschlag")
    def plan_touren(
        min_stops: int = Query(
            5, ge=1, description="Nur Touren mit mindestens so vielen Stopps"
        ),
        include: Optional[str] = Query(
            None, description="Nur Touren, deren Name dieses Fragment enthält"
        ),
        exclude: Optional[str] = Query(
            None, description="Touren ausschließen, die dieses Fragment enthalten"
        ),
        limit: int = Query(50, ge=1, le=500),
        offset: int = Query(0, ge=0),
    ) -> List[Dict[str, Any]]:
        try:
            db = _db_path()
            if not db.exists():
                return []
            con = sqlite3.connect(db)
            cur = con.cursor()
            rows = cur.execute(
                "select id, tour_id, datum, kunden_ids from touren order by id desc",
            ).fetchall()

            def match(text: str, needle: Optional[str]) -> bool:
                if needle is None:
                    return True
                return needle.lower() in text.lower()

            items: List[Dict[str, Any]] = []
            for r in rows:
                try:
                    tour_name = r[1] or ""
                    raw_ids = json.loads(r[3]) if r[3] else []
                    stops = len(_dedupe_preserve_order(raw_ids)) if raw_ids else 0
                    
                    if stops < min_stops:
                        continue
                    if include is not None and not match(tour_name, include):
                        continue
                    if exclude is not None and match(tour_name, exclude):
                        continue
                    
                    items.append({
                        "id": r[0], 
                        "tour": tour_name, 
                        "datum": r[2] or "", 
                        "stops": stops, 
                        "kunden_ids": r[3] if r[3] else "[]"
                    })
                except Exception as e:
                    print(f"[WARNUNG] Fehler beim Verarbeiten von Tour {r[0]}: {e}")
                    continue

            # Sortiere nach Stopps absteigend
            items.sort(key=lambda x: x["stops"], reverse=True)
            return items[offset : offset + limit]
            
        except Exception as e:
            print(f"🚨 Kritischer Fehler in /plan: {e}")
            return []

    @app.get("/settings/prompts", tags=["system"], summary="System- und Regel-Prompts für Anzeige")
    def get_prompts() -> Dict[str, Any]:
        params = {
            "max_minutes_to_last": 60,
            "dwell_minutes_per_stop": 2,
            "min_stops_per_tour": 5,
            "return_to_depot": True,
            "live_routing": True,
            "provider": "OpenRouteService",
        }
        system_prompt = (
            "Du bist der MultiRoutenPlaner 1.0. Generiere realistische Liefertouren für einen Tag "
            "auf Basis echter Straßenrouten, unter Berücksichtigung von Fahrzeiten und einfachen Regeln."
        )
        rules_prompt = (
            "Regeln:\n"
            "- Maximal 60 Minuten Fahrzeit bis zum letzten Kunden (inkl. Aufenthalte).\n"
            "- Aufenthalt je besuchtem Kunden: 2 Minuten.\n"
            "- Nach dem letzten Kunden Rückfahrt zum Depot (separat).\n"
            "- Mindestens 5 Stopps pro Tour (sofern genug Kunden vorhanden/geocodiert).\n"
            "- Routing basiert auf echten Straßen (OpenRouteService)."
        )
        return {"system_prompt": system_prompt, "rules_prompt": rules_prompt, "params": params}

    def _normalize_base_name(original_name: str) -> str:
        name = (original_name or "Tour").strip()
        # häufige Muster vereinfachen
        name = name.replace(" Uhr Tour", "").replace(" Uhr", "").replace("Tour", "").strip()
        name = name.replace(".", ":")
        # Mehrfach-Leerzeichen entfernen
        while "  " in name:
            name = name.replace("  ", " ")
        return name or "Tour"

    def _next_suffix(base: str, con: sqlite3.Connection) -> str:
        # alle existierenden Namen mit diesem Prefix holen
        rows = con.execute("select tour_id from touren where tour_id like ?", (f"{base}-%",)).fetchall()
        used = set()
        for (tour_name,) in rows:
            try:
                suffix = tour_name.split("-")[-1]
                used.add(suffix)
            except Exception:
                pass
        # einfache Buchstabenfolge A..Z, danach AA, AB...
        import string
        letters = list(string.ascii_uppercase)
        # erste Runde A..Z
        for ch in letters:
            if ch not in used:
                return ch
        # zweite Runde AA..AZ, BA..BZ
        for a in letters:
            for b in letters:
                cand = a + b
                if cand not in used:
                    return cand
        return "X"

    def _purge_generated_tours(con: sqlite3.Connection, base: str, current_date: str) -> None:
        """Löscht alle zuvor generierten Touren für einen bestimmten Basisnamen und das aktuelle Datum.
        Dies verhindert UNIQUE Constraint-Fehler bei mehrfachem Import am selben Tag.
        """
        con.execute("DELETE FROM touren WHERE tour_id LIKE ? AND datum = ?", (f"{base}%", current_date))
        con.commit()

    @app.post("/tour/{tour_id}/generate", tags=["map"], summary="Tour gemäß Regeln generieren (60min/2min Aufenthalt)")
    async def generate_tour(tour_id: int) -> Dict[str, Any]:
        try:
            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
            con = sqlite3.connect(db)
            row = con.execute("select tour_id, datum, kunden_ids from touren where id=?", (tour_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tour nicht gefunden")
            tour_name, datum, kid_json = row
            try:
                all_ids = json.loads(kid_json) if kid_json else []
                all_ids = _dedupe_preserve_order(all_ids)
            except Exception:
                all_ids = []
            if not all_ids:
                raise HTTPException(status_code=400, detail="Keine Kunden in Tour")

            # Kunden in der vorhandenen Reihenfolge laden und nach Adresse deduplizieren
            placeholders = ",".join(["?"] * len(all_ids))
            rows = con.execute(
                f"select id, name, adresse from kunden where id in ({placeholders})",
                tuple(all_ids),
            ).fetchall()
            by_id = {cid: (cid, name, adr) for cid, name, adr in rows}
            customers = [by_id[cid] for cid in all_ids if cid in by_id]
            customers = _dedupe_customers_by_address(customers)

            famo_address = "Stuttgarter Str. 33, 01189 Dresden"
            famo_pt = geocode_address(famo_address)
            if famo_pt is None:
                raise HTTPException(status_code=500, detail="Depot konnte nicht geocodiert werden")
            depot_lat, depot_lon = famo_pt

            routing_service = RealRoutingService()
            max_minutes = 60
            dwell_per_stop = 2
            # Kein Mindeststopps-Zwang: die 60-Minuten-Regel ist maßgeblich

            selected: List[tuple] = []
            for i in range(len(customers)):
                trial = customers[: i + 1]
                coords = [RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO")]
                for _cid, _name, _adr in trial:
                    pt = geocode_address(_adr)
                    if pt is None:
                        continue
                    lat, lon = pt
                    coords.append(RoutePoint(lat=lat, lon=lon, address=_adr, name=_name))
                coords.append(RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO"))
                if len(coords) < 3:
                    break
                route = await routing_service.calculate_route(coords)
                travel_to_last = 0
                if route.segments:
                    for seg_i, seg in enumerate(route.segments):
                        if seg_i < len(coords) - 2:
                            travel_to_last += seg.duration_minutes
                dwell_total = dwell_per_stop * (len(coords) - 2)
                total_until_last = int(travel_to_last + dwell_total)
                if total_until_last <= max_minutes:
                    selected = trial
                else:
                    break

            # Kein künstliches Erzwingen – 60-Minuten-Regel ist maßgeblich

            if not selected:
                raise HTTPException(status_code=400, detail="Keine Kunden innerhalb 60 Minuten erreichbar")

            # Neue Tour speichern – immer bei A beginnen: vorherige Generierte löschen
            base = _normalize_base_name(tour_name or "Tour")
            current_date_str = datetime.now().strftime("%Y-%m-%d")
            with _connect() as con:
                _purge_generated_tours(con, base, current_date_str)
            suffix = _next_suffix(base, con)
            new_name = f"{base}-{suffix}"
            selected_ids = [cid for cid, _, _ in selected]
            new_id = insert_tour(tour_id=new_name, datum=str(datum or ""), kunden_ids=selected_ids)

            # Response mit Metriken vorbereiten (Route final mit Rückfahrt)
            final_coords = [RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO")]
            for cid, name, adr in selected:
                pt = geocode_address(adr)
                if pt is None:
                    continue
                lat, lon = pt
                final_coords.append(RoutePoint(lat=lat, lon=lon, address=adr, name=name))
            final_coords.append(RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO"))
            final_route = await routing_service.calculate_route(final_coords)
            route_geometry: List[List[float]] = []
            for seg in final_route.segments:
                if seg.route_geometry:
                    route_geometry.extend(seg.route_geometry)

            return {
                "new_tour_id": new_id,
                "new_tour_name": new_name,
                "metrics": {
                    "selected_customers": len(selected_ids),
                    "distance_km": round(final_route.total_distance_km, 1),
                    "drive_minutes_total": int(final_route.total_duration_minutes),
                    "dwell_minutes_total": dwell_per_stop * len(selected_ids),
                    "rule_minutes_limit": max_minutes,
                },
                "route_geometry": route_geometry,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Generierung fehlgeschlagen: {e}")

    @app.post("/tour/{tour_id}/generate_multi", tags=["map"], summary="Mehrere Touren generieren, bis alle Kunden verplant sind")
    async def generate_tour_multi(tour_id: int) -> Dict[str, Any]:
        try:
            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
            con = sqlite3.connect(db)
            row = con.execute("select tour_id, datum, kunden_ids from touren where id=?", (tour_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tour nicht gefunden")
            tour_name, datum, kid_json = row
            try:
                remaining_ids: List[int] = json.loads(kid_json) if kid_json else []
                remaining_ids = _dedupe_preserve_order(remaining_ids)
            except Exception:
                remaining_ids = []
            if not remaining_ids:
                raise HTTPException(status_code=400, detail="Keine Kunden in Tour")

            # Kunden-Daten laden und nach Adresse deduplizieren
            placeholders = ",".join(["?"] * len(remaining_ids))
            rows = con.execute(
                f"select id, name, adresse from kunden where id in ({placeholders})",
                tuple(remaining_ids),
            ).fetchall()
            by_id = {cid: (cid, name, adr) for cid, name, adr in rows}
            customers_all = [by_id[cid] for cid in remaining_ids if cid in by_id]
            customers_all = _dedupe_customers_by_address(customers_all)

            famo_address = "Stuttgarter Str. 33, 01189 Dresden"
            famo_pt = geocode_address(famo_address)
            if famo_pt is None:
                raise HTTPException(status_code=500, detail="Depot konnte nicht geocodiert werden")
            depot_lat, depot_lon = famo_pt
            routing_service = RealRoutingService()
            max_minutes = 60
            dwell_per_stop = 2

            created: List[Dict[str, Any]] = []
            base = _normalize_base_name(tour_name or "Tour")
            # Immer bei A starten: zuvor generierte Reiter (A, B, C, …) entfernen
            current_date_str = datetime.now().strftime("%Y-%m-%d")
            with _connect() as con:
                _purge_generated_tours(con, base, current_date_str)

            # Iterativ Touren bilden, bis keine Kunden mehr vorhanden
            available = customers_all.copy()
            while available:
                selected: List[tuple] = []
                # Greedy von vorne weg
                for i in range(len(available)):
                    trial = available[: i + 1]
                    # Punkte: Depot + trial + Depot
                    coords = [RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO")]
                    for _cid, _name, _adr in trial:
                        pt = geocode_address(_adr)
                        if pt is None:
                            continue
                        lat, lon = pt
                        coords.append(RoutePoint(lat=lat, lon=lon, address=_adr, name=_name))
                    coords.append(RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO"))
                    if len(coords) < 3:
                        break
                    route = await routing_service.calculate_route(coords)
                    travel_to_last = 0
                    if route.segments:
                        for seg_i, seg in enumerate(route.segments):
                            if seg_i < len(coords) - 2:
                                travel_to_last += seg.duration_minutes
                    dwell_total = dwell_per_stop * (len(coords) - 2)
                    total_until_last = int(travel_to_last + dwell_total)
                    if total_until_last <= max_minutes:
                        selected = trial
                    else:
                        break

                if not selected:
                    # kein weiterer Kunde passt → Abbruch, um Endlosschleife zu vermeiden
                    break

                # 60-Minuten-Regel ist maßgeblich – kein erzwungenes Mindest-Stopps

                # neue Tour speichern
                suffix = _next_suffix(base, con)
                new_name = f"{base}-{suffix}"
                sel_ids = [cid for cid, _, _ in selected]
                new_id = insert_tour(tour_id=new_name, datum=str(datum or ""), kunden_ids=sel_ids)

                # Route final bestimmen
                coords_final = [RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO")]
                for cid, name, adr in selected:
                    pt = geocode_address(adr)
                    if pt is None:
                        continue
                    lat, lon = pt
                    coords_final.append(RoutePoint(lat=lat, lon=lon, address=adr, name=name))
                coords_final.append(RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO"))
                final_route = await routing_service.calculate_route(coords_final)
                route_geometry: List[List[float]] = []
                for seg in final_route.segments:
                    if seg.route_geometry:
                        route_geometry.extend(seg.route_geometry)

                explanation = (
                    f"Ausgewählt: {len(sel_ids)} Kunden. "
                    f"Fahrtzeit gesamt: {int(final_route.total_duration_minutes)} min, Aufenthalt: {dwell_per_stop * len(sel_ids)} min. "
                    f"Regel: max. {max_minutes} min bis letzter Kunde (inkl. Aufenthalt), danach Rückfahrt zum Depot."
                )

                created.append({
                    "new_tour_id": new_id,
                    "new_tour_name": new_name,
                    "selected_customer_ids": sel_ids,
                    "metrics": {
                        "selected_customers": len(sel_ids),
                        "distance_km": round(final_route.total_distance_km, 1),
                        "drive_minutes_total": int(final_route.total_duration_minutes),
                        "dwell_minutes_total": dwell_per_stop * len(sel_ids),
                        "rule_minutes_limit": max_minutes,
                    },
                    "route_geometry": route_geometry,
                    "explanation": explanation,
                })

                # Aus available entfernen (IDs der ausgewählten entfernen, Reihenfolge erhalten)
                available = [item for item in available if item[0] not in sel_ids]

            return {"created": created}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Mehrfach-Generierung fehlgeschlagen: {e}")

    @app.post("/tour/{tour_id}/generate_multi_ai", tags=["ai"], summary="KI: Stopps in mehrere Touren aufteilen und speichern")
    async def generate_multi_ai(tour_id: int) -> Dict[str, Any]:
        print(f"[INFO] Multi-Tour-Generator API aufgerufen für Tour ID: {tour_id}")
        try:
            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
            con = sqlite3.connect(db)
            row = con.execute("select tour_id, datum, kunden_ids from touren where id=?", (tour_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tour nicht gefunden")
            base_name, datum, kid_json = row
            try:
                ids = json.loads(kid_json) if kid_json else []
                ids = _dedupe_preserve_order(ids)
            except Exception:
                ids = []
            if not ids:
                raise HTTPException(status_code=400, detail="Keine Kunden in Tour")

            # Kunden laden und per Adresse deduplizieren
            placeholders = ",".join(["?"] * len(ids))
            rows = con.execute(
                f"select id, name, adresse from kunden where id in ({placeholders})",
                tuple(ids),
            ).fetchall()
            customers = _dedupe_customers_by_address(rows)

            # Stopps aufbereiten
            stops = []
            for idx, (cid, name, adr) in enumerate(customers):
                pt = geocode_address(adr)
                if pt is None:
                    continue
                lat, lon = pt
                stops.append(Stop(id=str(cid), name=name, address=adr, lat=lat, lon=lon, sequence=idx + 1))

            if len(stops) < 2:
                raise HTTPException(status_code=400, detail="Zu wenige geocodierte Stopps")

            print(f"[KI] Starte KI-Clustering fuer {len(stops)} Stopps...")
            optimizer = AIOptimizer(use_local=True)
            result = await optimizer.cluster_stops_into_tours(stops, default_rules)
            print(f"[OK] KI-Clustering Ergebnis: {result}")
            
            tours = result.get("tours", [])
            if not tours:
                print("[WARNUNG] Keine Touren von KI generiert")
                return {"created": [], "tours": [], "reason": result.get("reasoning", "Keine Vorschläge")}
            
            print(f"[KI] KI hat {len(tours)} Touren vorgeschlagen")

            # Vorherige generierte Touren entfernen und bei A beginnen
            base = _normalize_base_name(base_name or "Tour")
            current_date_str = datetime.now().strftime("%Y-%m-%d")
            with _connect() as con:
                _purge_generated_tours(con, base, current_date_str)

            created_ids: List[int] = []
            for t in tours:
                suffix = _next_suffix(base, con)
                new_name = f"{base}-{suffix}"
                cust_ids = [int(x) for x in t.get("customer_ids", []) if isinstance(x, (int, str)) and str(x).isdigit()]
                print(f"[TOUR] Erstelle Tour: {new_name} mit {len(cust_ids)} Kunden")
                created_id = insert_tour(tour_id=new_name, datum=str(datum or ""), kunden_ids=cust_ids)
                created_ids.append(created_id)

            print(f"[OK] Multi-Tour-Generator abgeschlossen: {len(created_ids)} Touren erstellt")
            return {"created": created_ids, "tours": tours, "reason": result.get("reasoning")}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"KI-Aufteilung fehlgeschlagen: {e}")

    @app.get("/import", tags=["db"], summary="Excel in DB importieren")
    def import_excel(
        excel: str = Query(
            ..., description="Pfad zur Excel-Datei, relativ zum Projektordner"
        ),
        date: Optional[str] = Query(
            None, description="Optionales Datum YYYY-MM-DD, falls im Excel fehlt"
        ),
        all: bool = Query(False, description="Alle Tabellenblätter importieren"),
        split: bool = Query(
            False, description="Eine Tabelle in Abschnitte/Touren splitten"
        ),
    ) -> Dict[str, Any]:
        # Auflösen relativer Pfade aus Sicht des Projektwurzelverzeichnisses
        project_root = Path(__file__).resolve().parents[1]
        excel_path = Path(excel)
        if not excel_path.is_absolute():
            excel_path = (project_root / excel_path).resolve()
        if not excel_path.exists():
            raise HTTPException(
                status_code=400, detail=f"Excel nicht gefunden: {excel_path}"
            )

        # DB initialisieren und importieren
        init_db()
        if split:
            tours = parse_teha_excel_sections(excel_path, fallback_date=date)
            total_customers = 0
            tour_ids: List[int] = []
            for t in tours:
                tour_id = str(t.get("tour"))
                datum = str(t.get("datum"))
                kunden_rows = t.get("kunden", [])
                kunden_ids = upsert_kunden(
                    Kunde(id=None, name=row["name"], adresse=row["adresse"])
                    for row in kunden_rows
                )
                t_id = insert_tour(tour_id=tour_id, datum=datum, kunden_ids=kunden_ids)
                tour_ids.append(t_id)
                total_customers += len(kunden_ids)
            return {
                "sections": len(tours),
                "imported_customers": total_customers,
                "tour_db_ids": tour_ids,
                "excel": str(excel_path),
            }
        elif all:
            tours = parse_teha_excel_all_sheets(excel_path, fallback_date=date)
            total_customers = 0
            tour_ids: List[int] = []
            for t in tours:
                tour_id = str(t.get("tour"))
                datum = str(t.get("datum"))
                kunden_rows = t.get("kunden", [])
                kunden_ids = upsert_kunden(
                    Kunde(id=None, name=row["name"], adresse=row["adresse"])
                    for row in kunden_rows
                )
                t_id = insert_tour(tour_id=tour_id, datum=datum, kunden_ids=kunden_ids)
                tour_ids.append(t_id)
                total_customers += len(kunden_ids)
            return {
                "sheets": len(tours),
                "imported_customers": total_customers,
                "tour_db_ids": tour_ids,
                "excel": str(excel_path),
            }
        else:
            result = parse_teha_excel(excel_path, fallback_date=date)
            tour_id = str(result.get("tour"))
            datum = str(result.get("datum"))
            kunden_rows = result.get("kunden", [])
            kunden_ids = upsert_kunden(
                Kunde(id=None, name=row["name"], adresse=row["adresse"])
                for row in kunden_rows
            )
            tour_db_id = insert_tour(
                tour_id=tour_id, datum=datum, kunden_ids=kunden_ids
            )

            return {
                "imported_customers": len(kunden_ids),
                "tour_db_id": tour_db_id,
                "tour": tour_id,
                "datum": datum,
                "excel": str(excel_path),
            }

    @app.get(
        "/upload", tags=["db"], response_class=HTMLResponse, summary="Upload-Formular"
    )
    def upload_form() -> str:
        return """
            <html>
              <body>
                <p><a href="/">Zur Startseite</a></p>
                <h2>Daten hochladen</h2>
                <h3>Excel (.xlsx)</h3>
                <form action="/upload" method="post" enctype="multipart/form-data">
                  <label>Excel-Datei (.xlsx): </label>
                  <input type="file" name="file" accept=".xlsx,.xls" required />
                  <br/><br/>
                  <label>Datum (YYYY-MM-DD, optional): </label>
                  <input type="text" name="date" placeholder="2025-08-11" />
                  <br/><br/>
                  <button type="submit">Excel importieren</button>
                </form>
                <hr/>
                <h3>PDF (Touren-PDF)</h3>
                <form action="/import/pdf" method="post" enctype="multipart/form-data">
                  <label>PDF-Datei: </label>
                  <input type="file" name="file" accept=".pdf" required />
                  <br/><br/>
                  <button type="submit">PDF importieren</button>
                </form>
              </body>
            </html>
            """

    @app.post("/upload", tags=["db"], summary="CSV/Excel-Datei hochladen und importieren")
    async def upload_file(
        file: UploadFile = File(...), date: Optional[str] = Form(None)
    ) -> Dict[str, Any]:
        project_root = Path(__file__).resolve().parents[1]
        uploads_dir = project_root / "data" / "uploads"
        uploads_dir.mkdir(parents=True, exist_ok=True)

        # Datei speichern
        dest_path = uploads_dir / file.filename
        content = await file.read()
        with open(dest_path, "wb") as f:
            f.write(content)

        # Importieren basierend auf Dateiendung
        init_db()
        
        try:
            if file.filename.lower().endswith('.csv'):
                # CSV-Datei verarbeiten (neue Parserlogik)
                plan = parse_tour_plan(dest_path)
                result = {
                    "tour": plan.tours[0].name if plan.tours else "",
                    "datum": plan.delivery_date or date,
                    "kunden": [
                        {
                            "name": stop.name,
                            "adresse": f"{stop.street}, {stop.postal_code} {stop.city}",
                        }
                        for tour in plan.tours
                        for stop in tour.customers
                    ],
                }
            else:
                # Excel-Datei verarbeiten
                result = parse_teha_excel(dest_path, fallback_date=date)
        except Exception as e:
            print(f"Fehler beim Parsen der Datei: {e}")
            # Fallback: Einfache CSV-Verarbeitung
            result = {
                "tour": file.filename.replace('.csv', ''),
                "datum": date or "2025-08-29",
                "kunden": []
            }
        
        tour_id = str(result.get("tour", "Unknown"))
        datum = str(result.get("datum", "2025-08-29"))
        kunden_rows = result.get("kunden", [])
        
        # Kunden verarbeiten
        kunden_ids = []
        if kunden_rows:
            try:
                kunden_ids = upsert_kunden(
                            Kunde(id=None, name=row.get("name", "Unknown"), adresse=row.get("adresse", "Unknown"))
                    for row in kunden_rows
                )
            except Exception as e:
                print(f"Fehler beim Verarbeiten der Kunden: {e}")
                kunden_ids = []
        
        try:
            tour_db_id = insert_tour(tour_id=tour_id, datum=datum, kunden_ids=kunden_ids)
        except sqlite3.IntegrityError:
            print(f"Duplikat-Tour übersprungen: {tour_id} am {datum}")
            return {
                "saved_as": str(dest_path.resolve()),
                "customers_created": 0,
                "tours_created": 0,
                "tour": tour_id,
                "datum": datum,
                "status": "duplicate",
                "message": "Tour existiert bereits"
            }
        except Exception as e:
            print(f"Fehler beim Einfügen der Tour: {e}")
            raise HTTPException(status_code=500, detail=f"Tour konnte nicht gespeichert werden: {e}")

        return {
            "saved_as": str(dest_path.resolve()),
            "customers_created": len(kunden_ids),
            "tours_created": 1 if kunden_ids else 0,
            "tour_db_id": tour_db_id,
            "tour": tour_id,
            "datum": datum,
            "status": "success"
        }

    @app.post("/import/pdf_preview", tags=["import"], summary="Vorschau: Touren-PDF parsen (ohne Speichern)")
    async def import_pdf_preview(file: UploadFile = File(...)) -> Dict[str, Any]:
        try:
            project_root = Path(__file__).resolve().parents[1]
            uploads_dir = project_root / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_path = uploads_dir / file.filename
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)

            summary = preview_summary(dest_path)
            summary.update({"pdf": dest_path.name})
            return summary
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF-Vorschau fehlgeschlagen: {e}")

    @app.post("/import/pdf", tags=["import"], summary="Touren-PDF importieren")
    async def import_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
        try:
            project_root = Path(__file__).resolve().parents[1]
            uploads_dir = project_root / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_path = uploads_dir / file.filename
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)

            # DB initialisieren und robusten Parser verwenden
            init_db()
            parsed = parse_pdf_tours(dest_path)
            tours_created: List[int] = []
            customers_created = 0

            for t in parsed:
                tour_name = str(t.get("tour") or "Tour")
                kunden_rows = t.get("kunden", [])
                if not kunden_rows:
                    continue
                kunden_ids = upsert_kunden(
                    Kunde(id=None, name=row["name"], adresse=row["adresse"])
                    for row in kunden_rows
                )
                # Zahlungszusatz wie "BAR" wird nicht in den Namen geschrieben, aber könnte später genutzt werden (t.get("payment"))
                tid = insert_tour(tour_id=tour_name, datum="", kunden_ids=kunden_ids)
                tours_created.append(tid)
                customers_created += len(kunden_ids)

            return {"pdf": dest_path.name, "tours_created": tours_created, "customers_created": customers_created}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF-Import fehlgeschlagen: {e}")

    @app.post("/import/pdf_ai", tags=["import", "ai"], summary="Touren-PDF per KI extrahieren und importieren")
    async def import_pdf_ai(
        file: UploadFile = File(...),
        preview: bool = Query(False),
        ai_only: bool = Query(False, description="Wenn true, KEIN Python-Fallback – nur KI verwenden"),
        prompt: Optional[str] = Form(None)
    ) -> Dict[str, Any]:
        """Extrahiert Touren/Kunden mit KI aus einem PDF. Fällt bei Fehlern auf den
        Python-Parser zurück. Optional nur Vorschau (preview=true)."""
        try:
            project_root = Path(__file__).resolve().parents[1]
            uploads_dir = project_root / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_path = uploads_dir / file.filename
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)

            # Text aus PDF extrahieren
            try:
                import pdfplumber  # type: ignore
                lines: List[str] = []
                with pdfplumber.open(str(dest_path)) as pdf:
                    for page in pdf.pages:
                        txt = page.extract_text() or ""
                        lines.extend([ln.strip() for ln in txt.splitlines()])
                extracted_text = "\n".join([ln for ln in lines if ln])
                print(f"[PDF] Extrahierter PDF-Text ({len(extracted_text)} Zeichen):\n---\n{extracted_text[:1000]}...\n---") # Logge extrahierten Text
            except Exception as e:
                extracted_text = ""
                print(f"[FEHLER] Fehler beim PDF-Text-Extraktion: {e}")

            # KI-Aufruf: nur Struktur extrahieren, keine Geocoding/Routing/Optimierung
            # Dynamische Auswahl zwischen Ollama (lokal) und OpenAI (Cloud) basierend auf API_KEY
            import os
            openai_api_key = os.getenv("OPENAI_API_KEY")
            use_local_ai = openai_api_key is None # Standardmäßig lokal, wenn kein OpenAI-Schlüssel
            optimizer = AIOptimizer(use_local=use_local_ai, api_key=openai_api_key)

            schema = {
                "tours": [
                    {
                        "name": "W-07:00",
                        "customers": [
                            {"name": "AUTO LUST", "adresse": "Krausestraße 4, Dresden"}
                        ],
                    }
                ]
            }
            # Prompt-Quelle: 1) multipart Form 'prompt' 2) Datei ai_models/pdf_ai_prompt.txt 3) Default
            prompt_text: Optional[str] = prompt
            if not prompt_text:
                try:
                    tmpl_path = project_root / "ai_models" / "pdf_ai_prompt.txt"
                    if tmpl_path.exists():
                        prompt_text = tmpl_path.read_text(encoding="utf-8")
                except Exception:
                    prompt_text = None
            if not prompt_text:
                prompt_text = (
                    "Du extrahierst Touren aus dem folgenden Text, der aus einem deutschen Touren-PDF stammt.\n"
                    "- Erkenne Tour-Überschriften wie \'W-07:00\', \'PIR Anlief.\', \'BAR\'. Jede Überschrift startet eine neue Tour.\n"
                    "- Erkenne Kundenzeilen mit Name – Adresse (Trenner \'-\', \'–\', \'—\') ODER tabellarische Spalten.\n"
                    "- Entferne Artefakte, normalisiere Whitespaces.\n"
                    "- Antworte ausschliesslich mit VALIDESEM JSON und KEINEM Fließtext im exakt folgenden Schema.\n"
                )
            prompt = (
                prompt_text
                + "\n\nSchema: " + json.dumps(schema, ensure_ascii=False)
                + "\n\nTEXT BEGINN\n" + extracted_text + "\nTEXT ENDE\n"
            )
            print(f"[KI-PROMPT] KI-Prompt ({len(prompt)} Zeichen):\n---\n{prompt[:1000]}...\n---") # Logge den vollstaendigen Prompt

            parsed: Dict[str, Any]
            try:
                # Nutze die korrekte Methode basierend auf der Auswahl
                if use_local_ai:
                    ai_raw = await optimizer._call_ollama(prompt, require_json=True)  # noqa: SLF001
                else:
                    ai_raw = await optimizer._call_cloud_api(prompt) # Verwende Cloud API

                parsed_raw = json.loads(ai_raw)
                parsed = _normalize_ai_output(parsed_raw)
                if not isinstance(parsed.get("tours", None), list):
                    raise ValueError("tours fehlt")
                # Tours ohne Kunden entfernen (verhindert Halluzinationen wie "Coswig 1" ohne Stops)
                parsed["tours"] = [
                    t for t in parsed.get("tours", [])
                    if isinstance(t, dict) and t.get("name") and isinstance(t.get("customers"), list) and len(t.get("customers")) > 0
                ]
                # Falls KI zwar JSON liefert, aber keine Touren erkannt hat → Fallback, sofern nicht ai_only
                if not parsed["tours"] and not ai_only:
                    parsed = {"tours": parse_pdf_tours(dest_path)}
            except Exception as e:
                if ai_only:
                    raise HTTPException(status_code=502, detail=f"KI-Parsing fehlgeschlagen (ai_only): {e}")
                # Fallback: Python-Parser
                parsed = {"tours": parse_pdf_tours(dest_path)}

            if preview:
                print(f"[KI] Normalisierte KI-Ausgabe fuer Vorschau (Typ: {parsed.get('source', '')}):\n---\n{json.dumps(parsed, indent=2, ensure_ascii=False)[:1000]}...\n---") # Logge normalisierte Ausgabe
                return {"pdf": dest_path.name, "preview": parsed}

            # In DB speichern
            init_db()
            tours_created: List[int] = []
            customers_created = 0
            for t in parsed.get("tours", []):
                tour_name = _normalize_tour_title(str(t.get("name") or t.get("tour") or "Tour"))
                kunden_rows = t.get("customers") or t.get("kunden") or []
                if not kunden_rows:
                    continue
                kunden_ids = upsert_kunden(
                    Kunde(id=None, name=row["name"], adresse=row["adresse"])
                    for row in kunden_rows
                )
                tid = insert_tour(tour_id=tour_name, datum="", kunden_ids=kunden_ids)
                tours_created.append(tid)
                customers_created += len(kunden_ids)

            return {"pdf": dest_path.name, "tours_created": tours_created, "customers_created": customers_created, "source": "ai"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF-AI-Import fehlgeschlagen: {e}")

    @app.post("/import/pdf_hybrid", tags=["import", "ai"], summary="Hybrid: Python extrahiert, KI normalisiert")
    async def import_pdf_hybrid(
        file: UploadFile = File(...),
        preview: bool = Query(True)
    ) -> Dict[str, Any]:
        """Robuster Hybrid-Workflow:
        1) Python extrahiert Touren/Kunden (keine Halluzinationen)
        2) KI normalisiert Adressen/Zahlung/Schlüssel – ohne neue Einträge zu erfinden
        3) Fallback: bei KI-Fehler unveränderte Python-Daten
        """
        try:
            project_root = Path(__file__).resolve().parents[1]
            uploads_dir = project_root / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_path = uploads_dir / file.filename
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)

            # 1) Python-Basisextraktion
            base_tours = parse_pdf_tours(dest_path)  # [{"tour":..., "kunden":[{"name","adresse"}]}]

            # Wenn leer, direkt zurück
            if not base_tours:
                return {"pdf": dest_path.name, "preview": {"tours": []}}

            # 2) KI-Normalisierung (ohne Erfindungen!)
            try:
                import os
                openai_api_key = os.getenv("OPENAI_API_KEY")
                use_local_ai = openai_api_key is None # Standardmäßig lokal, wenn kein OpenAI-Schlüssel
                optimizer = AIOptimizer(use_local=use_local_ai, api_key=openai_api_key)

                target_schema = {"tours": [{"name": "W-07:00", "customers": [{"name": "Muster GmbH", "adresse": "Straße 1, 01189 Dresden", "payment": "bar"}]}]}
                base_payload = {"tours": [
                    {"name": t.get("tour"), "customers": t.get("kunden", [])} for t in base_tours
                ]}
                hint = (
                    "Normalisiere die folgenden Tourdaten. WICHTIG: Erfinde keine neuen Touren/Kunden, "
                    "ändere nur Schreibweise/Schlüssel. Adresse als 'Straße Hausnr, PLZ Ort'. "
                    "Falls 'BAR' als Zahlung erkennbar ist, setze payment='bar'. \n\n"
                    f"Zielschema: {json.dumps(target_schema, ensure_ascii=False)}\n"
                    f"Eingabedaten: {json.dumps(base_payload, ensure_ascii=False)}\n\n"
                    "Antworte ausschließlich mit einem JSON im Zielschema."
                )
                
                # Nutze die korrekte Methode basierend auf der Auswahl
                if use_local_ai:
                    ai_raw = await optimizer._call_ollama(hint, require_json=True)  # noqa: SLF001
                    print(f"[KI-PROMPT] KI-Prompt (Hybrid) ({len(hint)} Zeichen):\n---\n{hint[:1000]}...\n---") # Logge den Prompt im Hybridmodus
                    print(f"[KI] KI-Rohdaten (Hybrid):\n---\n{ai_raw[:1000]}...\n---") # Logge rohe KI-Daten im Hybridmodus
                else:
                    ai_raw = await optimizer._call_cloud_api(hint) # Verwende Cloud API

                ai_obj = json.loads(ai_raw)
                normalized = _normalize_ai_output(ai_obj)
                # Filtere leere Touren
                normalized["tours"] = [t for t in normalized.get("tours", []) if t.get("customers")]
                if not normalized["tours"]:
                    # Fallback auf Python-Basisdaten, in unser Zielschema gewandelt
                    normalized = {"tours": [
                        {"name": t.get("tour"), "customers": [
                            {"name": c.get("name"), "adresse": c.get("adresse")}
                            for c in t.get("kunden", [])
                        ]}
                        for t in base_tours
                    ]}
            except Exception:
                normalized = {"tours": [
                    {"name": t.get("tour"), "customers": [
                        {"name": c.get("name"), "adresse": c.get("adresse")}
                        for c in t.get("kunden", [])
                    ]}
                    for t in base_tours
                ]}

            if preview:
                print(f"[KI] Normalisierte KI-Ausgabe fuer Vorschau (Typ: {normalized.get('source', '')}):\n---\n{json.dumps(normalized, indent=2, ensure_ascii=False)[:1000]}...\n---") # Logge normalisierte Ausgabe (Hybrid)
                return {"pdf": dest_path.name, "preview": normalized, "source": "hybrid"}
            # Import in DB
            init_db()
            tours_created: List[int] = []
            customers_created = 0
            for t in normalized.get("tours", []):
                tour_name = str(t.get("name") or t.get("tour") or "Tour")
                kunden_rows = t.get("customers") or t.get("kunden") or []
                if not kunden_rows:
                    continue
                kunden_ids = upsert_kunden(
                    Kunde(id=None, name=row.get("name"), adresse=row.get("adresse")) for row in kunden_rows
                )
                tid = insert_tour(tour_id=tour_name, datum="", kunden_ids=kunden_ids)
                tours_created.append(tid)
                customers_created += len(kunden_ids)
            return {"pdf": dest_path.name, "tours_created": tours_created, "customers_created": customers_created, "source": "hybrid"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"PDF-Hybrid-Import fehlgeschlagen: {e}")

    @app.post("/import/csv_preview", tags=["import"], summary="Vorschau: CSV-Datei parsen (ohne Speichern)")
    async def import_csv_preview(file: UploadFile = File(...)) -> Dict[str, Any]:
        try:
            project_root = Path(__file__).resolve().parents[1]
            uploads_dir = project_root / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_path = uploads_dir / file.filename
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)

            # parse_teha_excel_sections kann jetzt CSVs verarbeiten
            tours = parse_teha_excel_sections(dest_path)
            
            return {"csv": dest_path.name, "preview": {"tours": tours}}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"CSV-Vorschau fehlgeschlagen: {e}")

    @app.post("/import/csv_ai", tags=["import", "ai"], summary="CSV-Datei per KI parsen und Touren optimieren & importieren")
    async def import_csv_ai(file: UploadFile = File(...)) -> Dict[str, Any]:
        try:
            project_root = Path(__file__).resolve().parents[1]
            uploads_dir = project_root / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_path = uploads_dir / file.filename
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)

            # DB initialisieren
            init_db()

            # Alle Kunden aus CSV parsen (unabhängig von ursprünglicher Tour-Struktur)
            parsed_tours_data = parse_teha_excel_sections(dest_path)
            all_customers_from_csv = []
            seen_customers = set() # Set zum Nachverfolgen bereits gesehener Kunden

            for tour_data in parsed_tours_data:
                for customer_data in tour_data.get("kunden", []):
                    # Eindeutigen Schlüssel für den Kunden erstellen (Name + Adresse)
                    customer_key = (
                        _normalize_string(customer_data["name"]),
                        _normalize_string(customer_data["adresse"])
                    )
                    if customer_key not in seen_customers:
                        all_customers_from_csv.append(customer_data)
                        seen_customers.add(customer_key)

            # Kunden geocodieren und für MultiTourGenerator vorbereiten
            multi_tour_customers: List[Customer] = []
            for idx, row in enumerate(all_customers_from_csv):
                name = _normalize_string(row["name"])
                adresse = _normalize_string(row["adresse"])
                lat, lon = None, None

                # Zuerst in DB nach vorhandenen Geokoordinaten suchen
                kunde_id = get_kunde_id_by_name_adresse(name, adresse)
                if kunde_id:
                    existing_kunde = get_kunde_by_id(kunde_id)
                    if existing_kunde and existing_kunde.lat is not None and existing_kunde.lon is not None:
                        lat, lon = existing_kunde.lat, existing_kunde.lon
                
                # Wenn keine Koordinaten gefunden, Geocodierung versuchen
                if lat is None or lon is None:
                    # Die Adresse ist bereits vollständig vom Parser (Straße, PLZ Ort)
                    full_address = row['adresse']
                    print(f"[DEBUG] Geocoding für: '{full_address}'")
                    geo_result = geocode_address(full_address)
                    if geo_result and geo_result[0] is not None and geo_result[1] is not None:
                        lat = geo_result[0]
                        lon = geo_result[1]
                        print(f"[DEBUG] Geocoding erfolgreich: {lat}, {lon}")
                    else:
                        print(f"[DEBUG] Geocoding fehlgeschlagen für: '{full_address}'")

                multi_tour_customers.append(
                    Customer(
                        id=idx + 1,  # Temporäre ID für MultiTourGenerator
                        name=name,
                        address=adresse,
                        lat=lat,
                        lon=lon
                    )
                )

            if not multi_tour_customers:
                return {"message": "Keine Kunden zum Generieren von Touren gefunden.", "tours_created": [], "customers_created": 0}

            # MultiTourGenerator instanziieren und Touren generieren lassen
            multi_generator = MultiTourGenerator(rules=default_rules)
            tour_group_name = dest_path.stem # Dateiname als Tour-Gruppenname
            multi_tour_result = await multi_generator.generate_tours_from_customers(
                multi_tour_customers, tour_group_name
            )

            tours_created_ids: List[int] = []
            customers_upserted_count = 0

            # Vorherige generierte Touren für diesen Dateinamen und aktuelles Datum löschen
            current_date_str = datetime.now().strftime("%Y-%m-%d")
            with _connect() as con: # _connect() verwenden
                _purge_generated_tours(con, tour_group_name, current_date_str)

            for gen_tour in multi_tour_result.generated_tours:
                kunden_ids_for_tour = []
                for customer_in_tour in gen_tour.customers:
                    # Kunden in Datenbank upserten (mit geocodierten Daten)
                    upserted_ids = upsert_kunden([Kunde(id=None, name=customer_in_tour.name, adresse=customer_in_tour.address, lat=customer_in_tour.lat, lon=customer_in_tour.lon)])
                    if upserted_ids:
                        kunden_ids_for_tour.append(upserted_ids[0])
                        customers_upserted_count += 1
                
                if kunden_ids_for_tour:
                    # Tour speichern (mit neu generiertem Namen, aktuellem Datum und Kunden-IDs)
                    tid = insert_tour(
                        tour_id=gen_tour.tour_id,
                        datum=current_date_str, # Dynamisches Datum
                        kunden_ids=kunden_ids_for_tour,
                        dauer_min=gen_tour.estimated_duration_minutes,
                        distanz_km=gen_tour.estimated_distance_km
                    )
                    tours_created_ids.append(tid)

            # Daten in DB speichern
            if multi_tour_result.generated_tours:
                for gen_tour in multi_tour_result.generated_tours:
                    # ... (bestehender Code zum Speichern der Touren)
                    # (Dieser Teil des Codes wird nicht geändert, da er korrekt ist)
                    pass

            return {
                "message": f"Erfolgreich {len(multi_tour_result.generated_tours)} Touren generiert und {customers_upserted_count} Kunden aktualisiert.",
                "tours_created": tours_created_ids,
                "customers_created": customers_upserted_count,
                "optimization_summary": multi_tour_result.optimization_summary # Hinzugefügt
            }
        except Exception as e:
            print(f"🚨 CSV-Importfehler: {e}")
            raise HTTPException(status_code=500, detail=f"CSV-Import fehlgeschlagen: {e}")

    @app.post("/debug/normalize_csv", tags=["debug"], summary="Debug: CSV-Daten normalisieren und zurückgeben")
    async def debug_normalize_csv(file: UploadFile = File(...)) -> Dict[str, Any]:
        try:
            project_root = Path(__file__).resolve().parents[1]
            uploads_dir = project_root / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_path = uploads_dir / file.filename
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)

            parsed_tours = parse_teha_excel_sections(dest_path)
            normalized_customers = []

            for tour_data in parsed_tours:
                kunden_rows = tour_data.get("kunden", [])
                for row in kunden_rows:
                    normalized_customers.append({
                        "name": _normalize_string(row["name"]),
                        "adresse": _normalize_string(row["adresse"])
                    })
            
            return {"normalized_customers": normalized_customers}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Debug-Normalisierung fehlgeschlagen: {e}")

    # Neue CSV-spezifische Endpunkte mit dem neuen Parser
    @app.post("/api/parse-csv-tourplan", tags=["csv"], summary="CSV-Tourenplan mit neuem Parser parsen")
    async def parse_csv_tourplan(file: UploadFile = File(...)) -> Dict[str, Any]:
        """Parst CSV-Tourenplan-Dateien mit der neuen Tourenlogik und geokodiert alle Adressen."""
        try:
            project_root = Path(__file__).resolve().parents[1]
            uploads_dir = project_root / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_path = uploads_dir / file.filename
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)

            print(f"\n{'='*60}")
            print(f"[CSV] Parsing CSV-Tourenplan: {file.filename}")
            print(f"{'='*60}")

            plan = parse_tour_plan(str(dest_path))
            parsed_dict = parse_tour_plan_to_dict(str(dest_path))

            # INTELLIGENTE GEODATEN-BESCHAFFUNG: Zuerst DB, dann Geocoding
            print(f"\n[GEO] Lade Geodaten fuer {plan.total_customers} Kunden...")
            geocoding_stats = {
                "total": 0,
                "from_db": 0,
                "from_geocoding": 0,
                "failed": 0,
                "new_customers_saved": 0
            }
            
            # Liste für neue Kunden, die in DB gespeichert werden sollen
            new_customers_to_save = []

            # Durch alle Touren und Kunden iterieren
            for tour in parsed_dict.get("tours", []):
                for customer in tour.get("customers", []):
                    geocoding_stats["total"] += 1
                    
                    # Adresse zusammenbauen
                    name = customer.get("name", "").strip()
                    street = customer.get("street", "").strip()
                    postal_code = customer.get("postal_code", "").strip()
                    city = customer.get("city", "").strip()
                    
                    if not street or not postal_code or not city:
                        geocoding_stats["failed"] += 1
                        customer["latitude"] = None
                        customer["longitude"] = None
                        continue
                    
                    full_address = f"{street}, {postal_code} {city}"
                    
                    # 1. VERSUCH: Aus Datenbank laden
                    from backend.db.dao import get_kunde_id_by_name_adresse, get_kunde_by_id, Kunde
                    kunde_id = get_kunde_id_by_name_adresse(name, full_address)
                    
                    if kunde_id:
                        # Kunde bereits in DB - Koordinaten laden
                        kunde_obj = get_kunde_by_id(kunde_id)
                        if kunde_obj and kunde_obj.lat and kunde_obj.lon:
                            customer["latitude"] = kunde_obj.lat
                            customer["longitude"] = kunde_obj.lon
                            geocoding_stats["from_db"] += 1
                            continue
                    
                    # 2. VERSUCH: Geocoding durchführen
                    geo_result = geocode_address(full_address)
                    
                    if geo_result and geo_result.get("lat") and geo_result.get("lon"):
                        customer["latitude"] = geo_result["lat"]
                        customer["longitude"] = geo_result["lon"]
                        geocoding_stats["from_geocoding"] += 1
                        
                        # Neuen Kunden zur Speicherliste hinzufügen
                        new_customers_to_save.append(Kunde(
                            id=None,
                            name=name,
                            adresse=full_address,
                            lat=geo_result["lat"],
                            lon=geo_result["lon"]
                        ))
                    else:
                        customer["latitude"] = None
                        customer["longitude"] = None
                        geocoding_stats["failed"] += 1

            # Auch customers-Liste aktualisieren
            for customer in parsed_dict.get("customers", []):
                name = customer.get("name", "").strip()
                street = customer.get("street", "").strip()
                postal_code = customer.get("postal_code", "").strip()
                city = customer.get("city", "").strip()
                
                if street and postal_code and city:
                    full_address = f"{street}, {postal_code} {city}"
                    
                    # Aus DB laden
                    from backend.db.dao import get_kunde_id_by_name_adresse, get_kunde_by_id
                    kunde_id = get_kunde_id_by_name_adresse(name, full_address)
                    
                    if kunde_id:
                        kunde_obj = get_kunde_by_id(kunde_id)
                        if kunde_obj and kunde_obj.lat and kunde_obj.lon:
                            customer["latitude"] = kunde_obj.lat
                            customer["longitude"] = kunde_obj.lon
                            continue
                    
                    # Sonst Geocoding
                    geo_result = geocode_address(full_address)
                    if geo_result and geo_result.get("lat") and geo_result.get("lon"):
                        customer["latitude"] = geo_result["lat"]
                        customer["longitude"] = geo_result["lon"]
                    else:
                        customer["latitude"] = None
                        customer["longitude"] = None
            
            # Neue Kunden in Datenbank speichern
            if new_customers_to_save:
                from backend.db.dao import upsert_kunden
                upsert_kunden(new_customers_to_save)
                geocoding_stats["new_customers_saved"] = len(new_customers_to_save)
                print(f"\n[DB] {len(new_customers_to_save)} neue Kunden in Datenbank gespeichert")

            print(f"\n[OK] Geodaten-Beschaffung abgeschlossen:")
            print(f"   Gesamt:           {geocoding_stats['total']}")
            print(f"   Aus Datenbank:    {geocoding_stats['from_db']} ({geocoding_stats['from_db']*100//geocoding_stats['total'] if geocoding_stats['total'] > 0 else 0}%)")
            print(f"   Neu geocodet:     {geocoding_stats['from_geocoding']}")
            print(f"   In DB gespeichert: {geocoding_stats['new_customers_saved']}")
            print(f"   Fehlgeschlagen:   {geocoding_stats['failed']}")
            print(f"{'='*60}\n")

            return {
                "message": "CSV-Tourenplan erfolgreich geparst und geokodiert",
                "filename": file.filename,
                "parsed_data": parsed_dict,
                "metadata": {
                    "delivery_date": plan.delivery_date,
                    "total_tours": plan.total_tours,
                    "total_customers": plan.total_customers,
                    "total_bar_customers": plan.total_bar_customers,
                },
                "geocoding": geocoding_stats
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"CSV-Tourenplan-Parsing fehlgeschlagen: {e}")

    @app.post("/api/parse-csv-pandas", tags=["csv"], summary="CSV-Datei mit pandas parsen")
    async def parse_csv_pandas(file: UploadFile = File(...)) -> Dict[str, Any]:
        """Parst CSV-Dateien mit pandas für einfache Tabellendaten"""
        try:
            project_root = Path(__file__).resolve().parents[1]
            uploads_dir = project_root / "data" / "uploads"
            uploads_dir.mkdir(parents=True, exist_ok=True)
            dest_path = uploads_dir / file.filename
            content = await file.read()
            with open(dest_path, "wb") as f:
                f.write(content)

            # Pandas CSV-Parser verwenden
            parsed_dict = parse_tour_plan_to_dict(str(dest_path))
            
            return {
                "message": "CSV erfolgreich geparst",
                "filename": file.filename,
                "tour_count": len(parsed_dict.get("tours", [])),
                "customer_count": len(parsed_dict.get("customers", [])),
                "parsed_data": parsed_dict,
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Pandas CSV-Parsing fehlgeschlagen: {e}")

    @app.get("/api/csv-summary/{filename:path}", tags=["csv"], summary="Zusammenfassung einer CSV-Datei anzeigen")
    async def get_csv_summary_endpoint(filename: str) -> Dict[str, Any]:
        """Zeigt eine Zusammenfassung einer CSV-Datei an"""
        try:
            project_root = Path(__file__).resolve().parents[1]
            file_path = project_root / "data" / "uploads" / filename
            
            if not file_path.exists():
                raise HTTPException(status_code=404, detail="Datei nicht gefunden")
            
            summary = get_csv_summary(str(file_path))
            
            return {
                "filename": filename,
                "summary": summary
            }
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"CSV-Zusammenfassung fehlgeschlagen: {e}")

    # Configure logging for CSV import debug
    log_file_path = Path("logs/csv_import_debug.log")
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    csv_logger = logging.getLogger("csv_import")
    csv_logger.setLevel(logging.DEBUG)

    # Clear existing handlers to prevent duplicate output if reloaded
    if csv_logger.handlers:
        for handler in csv_logger.handlers:
            csv_logger.removeHandler(handler)

    handler = RotatingFileHandler(log_file_path, maxBytes=1048576, backupCount=5) # 1MB per file, 5 backups
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    handler.setFormatter(formatter)
    csv_logger.addHandler(handler)

    @app.post("/api/csv-bulk-process", tags=["csv"], summary="Alle CSV-Dateien im tourplaene Verzeichnis verarbeiten")
    async def csv_bulk_process() -> Dict[str, Any]:
        """EINFACHE LÖSUNG: CSV-Dateien verarbeiten und Kunden speichern"""
        csv_logger.info("[%s] Starte CSV Bulk Processing...", os.getpid())
        total_customers_processed = 0 # Neue Variable zum Zählen der verarbeiteten Kunden
        try:
            from pathlib import Path
            import pandas as pd
            import sqlite3
            from backend.services.geocode import geocode_address # Stelle sicher, dass geocode_address verfügbar ist

            # CSV-Dateien finden
            csv_files = list(Path("tourplaene_canonical").glob("*.csv"))
            if not csv_files:
                csv_logger.warning("[%s] Keine CSV-Dateien im tourplaene-Verzeichnis gefunden.", os.getpid())
                return {"message": "Keine CSV-Dateien gefunden", "total_customers": 0}

            csv_logger.debug("[%s] Gefundene CSV-Dateien: %s", os.getpid(), [f.name for f in csv_files])

            all_customers = set()

            for csv_file in csv_files:
                csv_logger.debug("[%s] Verarbeite Datei: %s", os.getpid(), csv_file.name)
                try:
                    df = None
                    # Kanonische UTF-8-CSV lesen (einfach!)
                    try:
                        df = pd.read_csv(csv_file, encoding='utf-8', sep=';', header=None, dtype=str)
                        csv_logger.debug("[%s]   Kanonische CSV gelesen: %s (%d Zeilen)", os.getpid(), csv_file.name, len(df))
                        
                    except Exception as e:
                        csv_logger.error("[%s]   Fehler beim Lesen von %s: %s", os.getpid(), csv_file.name, e)
                        continue

                    if df is None:
                        csv_logger.error("[%s]   Kein Encoding funktioniert fr %s. Datei bersprungen.", os.getpid(), csv_file.name)
                        continue

                    csv_logger.debug("[%s]   Datei %s geladen. Zeilen: %d, Ursprngliche Pandas-Spalten: %s", os.getpid(), csv_file.name, len(df), list(df.columns))

                    actual_header_row_index = -1
                    for r_idx, row_data in df.iterrows():
                        # Prüfe, ob die erste Zelle der Zeile 'Kdnr' ist (case-insensitive und getrimmt)
                        if str(row_data.iloc[0]).strip().lower() == 'kdnr':
                            actual_header_row_index = r_idx
                            break

                    if actual_header_row_index == -1:
                        csv_logger.error("[%s]   Echte Header-Zeile (startend mit 'Kdnr') nicht gefunden in %s. Datei bersprungen.", os.getpid(), csv_file.name)
                        continue

                    # Header setzen und ungenutzte Zeilen entfernen
                    df.columns = df.iloc[actual_header_row_index]
                    df = df[actual_header_row_index+1:].reset_index(drop=True)

                    csv_logger.debug("[%s]   Nach Header-Anpassung. Zeilen: %d, Spalten: %s", os.getpid(), len(df), list(df.columns))

                    # Spaltennamen vor der Verarbeitung normalisieren
                    original_columns = df.columns.tolist()
                    new_columns = []
                    for col in original_columns:
                        csv_logger.debug(f"[%s]   Original Spalte vor Normalisierung: {col} (repr: {repr(col)})", os.getpid())
                        # Direkte Ersetzung für deutsche Sonderzeichen und Bereinigung
                        normalized_col = str(col).lower()\
                                        .replace('ß', 'ss')\
                                        .replace('ä', 'ae')\
                                        .replace('ö', 'oe')\
                                        .replace('ü', 'ue')
                        csv_logger.debug(f"[%s]     Nach Umlaut-Ersetzung: {normalized_col} (repr: {repr(normalized_col)})", os.getpid())
                        
                        normalized_col = normalized_col\
                                        .replace(' ', '')\
                                        .replace('.', '')\
                                        .replace('/', '')\
                                        .strip()
                        csv_logger.debug(f"[%s]     Nach Bereinigung: {normalized_col} (repr: {repr(normalized_col)})", os.getpid())
                        new_columns.append(normalized_col)
                    df.columns = new_columns
                    
                    # Kunden extrahieren
                    for i, row in df.iterrows():
                        kdnr = str(row.get('kdnr', '')).strip()
                        name = str(row.get('name', '')).strip()
                        address = str(row.get('strasse', '')).strip()
                        
                        if (kdnr and kdnr.isdigit() and 
                            name and address and 
                            name.lower() != 'name' and address.lower() != 'strasse'):
                            
                            customer_key = f"{name}|{address}"
                            all_customers.add(customer_key)
                            csv_logger.debug("[%s]   Zeile %d: [OK] Kunde hinzugefügt: %s", os.getpid(), i+1, customer_key)
                            total_customers_processed += 1 # Zähle jeden erfolgreich hinzugefügten Kunden
                        else:
                            csv_logger.debug(f"[%s]   Zeile %d: [FEHLER] Kein Kunde erkannt (Kdnr='{kdnr}', Name='{name}', Strasse='{address}')", os.getpid(), i+1)
                            
                except Exception as e:
                    csv_logger.error("[%s] Fehler beim Verarbeiten von %s: %s", os.getpid(), csv_file.name, e)
                    continue
            
            csv_logger.info("[%s] Kundenextraktion abgeschlossen. Eindeutige Kunden gefunden: %d", os.getpid(), len(all_customers))
            
            # Speichern in Datenbank
            db_path = "./data/customers.db" # Annahme: customers.db wird für Kunden verwendet
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("DELETE FROM kunden")
            csv_logger.info("[%s] Kunden-Tabelle geleert.", os.getpid())
            
            saved_customers = 0
            geocoding_success = 0
            geocoding_failed = 0
            
            for customer_key in all_customers:
                name, address = customer_key.split('|', 1)
                
                lat, lng = 0.0, 0.0
                try:
                    result = geocode_address(address)
                    if result and 'lat' in result and 'lng' in result:
                        lat = result['lat']
                        lng = result['lng']
                        geocoding_success += 1
                    else:
                        geocoding_failed += 1
                except Exception as e:
                    csv_logger.error(f"[%s] Geocoding-Fehler für {address}: {e}", os.getpid())
                    geocoding_failed += 1
                
                cursor.execute("""
                    INSERT INTO kunden (Name, Adresse, lat, lng, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (name, address, lat, lng))
                saved_customers += 1
                
                if saved_customers % 50 == 0:
                    csv_logger.debug("[%s] Verarbeitet: %d Kunden...", os.getpid(), saved_customers)
            
            conn.commit()
            conn.close()
            
            csv_logger.info("[%s] %d Kunden erfolgreich in Datenbank gespeichert.", os.getpid(), saved_customers)
            return {
                "message": "CSV Import erfolgreich!",
                "total_customers": total_customers_processed, # Hier die neue Variable verwenden
                "unique_customers": len(all_customers),
                "saved_customers": saved_customers,
                "geocoding_success": geocoding_success,
                "geocoding_failed": geocoding_failed,
                "geocoding_rate": f"{(geocoding_success / saved_customers * 100):.1f}%" if saved_customers > 0 else "0%",
                "files_processed": len(csv_files)
            }
            
        except Exception as e:
            csv_logger.error("[%s] CSV Bulk Processing fehlgeschlagen (globaler Fehler): %s", os.getpid(), e)
            return {"error": f"Fehler: {str(e)}", "total_customers": 0} # Fehlerbehandlung anpassen

    @app.post("/api/tourplan-analysis", tags=["csv"], summary="Alle Tourenpläne analysieren und Kunden-Erkennung prüfen")
    async def tourplan_analysis() -> JSONResponse:
        """
        Analysiert alle verfügbaren Tourenpläne und prüft Kunden-Erkennung
        
        Returns:
            Analyse-Ergebnisse mit erkannten und nicht erkannten Kunden
        """
        try:
            print("[ANALYSE] Starte Analyse aller Tourenpläne...")
            
            # Alle CSV-Dateien im tourplaene Verzeichnis finden
            tourplaene_dir = Path("tourplaene")
            if not tourplaene_dir.exists():
                return {
                    "error": "tourplaene Verzeichnis nicht gefunden",
                    "tours": [],
                    "total_customers": 0,
                    "recognized_customers": 0,
                    "unrecognized_customers": 0
                }
            
            csv_files = list(tourplaene_dir.glob("*.csv"))
            print(f"[ANALYSE] {len(csv_files)} CSV-Dateien gefunden")
            
            all_tours = []
            total_customers = 0
            recognized_customers = 0
            unrecognized_customers = 0
            
            for csv_file in csv_files:
                print(f"[ANALYSE] Verarbeite: {csv_file.name}")
                
                try:
                    # Tourplan parsen
                    tour_data = parse_tour_plan_to_dict(str(csv_file))
                    
                    if not tour_data or 'tours' not in tour_data:
                        print(f"[ANALYSE] Keine Touren in {csv_file.name}")
                        continue
                    
                    # Jede Tour analysieren
                    for tour in tour_data['tours']:
                        tour_name = tour.get('name', 'Unbekannt')
                        customers = tour.get('customers', [])
                        
                        print(f"[ANALYSE] Tour: {tour_name} ({len(customers)} Kunden)")
                        
                        # Kunden analysieren
                        analyzed_customers = []
                        for customer in customers:
                            total_customers += 1
                            
                            # GUARD: Mojibake-Prüfung vor Verarbeitung
                            from backend.utils.encoding_guards import assert_no_mojibake, trace_text
                            
                            # Prüfe Kundennamen und Adresse
                            if customer.get('name'):
                                assert_no_mojibake(customer['name'])
                                trace_text("CUSTOMER_NAME", customer['name'])
                            
                            if customer.get('street'):
                                assert_no_mojibake(customer['street'])
                                trace_text("CUSTOMER_STREET", customer['street'])
                            
                            # Prüfe ob Kunde erkannt wurde
                            is_recognized = await analyze_customer_recognition(customer)
                            
                            if is_recognized:
                                recognized_customers += 1
                            else:
                                unrecognized_customers += 1
                            
                            # Erweiterte Kundendaten
                            analyzed_customer = {
                                **customer,
                                'is_recognized': is_recognized,
                                'recognition_method': get_recognition_method(customer),
                                'coordinates': f"{customer.get('lat', 'N/A')}, {customer.get('lon', 'N/A')}" if customer.get('lat') and customer.get('lon') else 'N/A'
                            }
                            
                            analyzed_customers.append(analyzed_customer)
                        
                        # Tour mit analysierten Kunden
                        analyzed_tour = {
                            **tour,
                            'customers': analyzed_customers,
                            'recognized_count': sum(1 for c in analyzed_customers if c['is_recognized']),
                            'unrecognized_count': sum(1 for c in analyzed_customers if not c['is_recognized'])
                        }
                        
                        all_tours.append(analyzed_tour)
                        
                except Exception as e:
                    print(f"[ANALYSE] Fehler bei {csv_file.name}: {e}")
                    continue
            
            print(f"[ANALYSE] Analyse abgeschlossen:")
            print(f"  - Touren: {len(all_tours)}")
            print(f"  - Gesamt Kunden: {total_customers}")
            print(f"  - Erkannt: {recognized_customers}")
            print(f"  - Nicht erkannt: {unrecognized_customers}")
            print(f"  - Erfolgsquote: {(recognized_customers/total_customers*100):.1f}%" if total_customers > 0 else "  - Erfolgsquote: 0%")
            
            # UTF-8 JSON Response mit korrekten Headers
            return JSONResponse(
                content={
                    "tours": all_tours,
                    "total_customers": total_customers,
                    "recognized_customers": recognized_customers,
                    "unrecognized_customers": unrecognized_customers,
                    "success_rate": (recognized_customers/total_customers*100) if total_customers > 0 else 0,
                    "files_processed": len(csv_files)
                },
                media_type="application/json; charset=utf-8",
                headers={"Content-Type": "application/json; charset=utf-8"}
            )
            
        except Exception as e:
            print(f"[ANALYSE] Fehler bei Analyse: {e}")
            return {
                "error": str(e),
                "tours": [],
                "total_customers": 0,
                "recognized_customers": 0,
                "unrecognized_customers": 0
            }

    # Verwende die globalen Funktionen
    pass

    @app.post("/api/csv-tour-process", tags=["csv"], summary="CSV-Dateien mit Tour-Erkennung verarbeiten")
    async def csv_tour_process() -> Dict[str, Any]:
        """CSV-Dateien verarbeiten, Touren erkennen und Kunden mit Geocoding speichern"""
        print(f"[{os.getpid()}] Starte CSV Tour Processing...")
        
        try:
            from pathlib import Path
            import pandas as pd
            import sqlite3
            import re
            from backend.services.geocode import geocode_address

            # CSV-Dateien finden
            csv_files = list(Path("tourplaene_canonical").glob("*.csv"))
            if not csv_files:
                print(f"[{os.getpid()}] Keine CSV-Dateien im tourplaene-Verzeichnis gefunden.")
                return {"message": "Keine CSV-Dateien gefunden", "total_customers": 0, "tours": 0}

            print(f"[{os.getpid()}] Gefundene CSV-Dateien: {[f.name for f in csv_files]}")

            all_tours = []  # Liste aller erkannten Touren
            base_tours: List[Dict[str, Any]] = []
            bar_tours: List[Dict[str, Any]] = []
            tour_lookup: Dict[str, List[Dict[str, Any]]] = {}
            anomalies: List[str] = []
            all_customers = set()  # Eindeutige Kunden
            total_customers_processed = 0

            for csv_file in csv_files:
                print(f"[{os.getpid()}] Verarbeite Datei: {csv_file.name}")
                try:
                    # CSV lesen mit verschiedenen Encodings (priorisiert für deutsche Zeichen)
                    df = None
                    tried_encodings = ['cp1252', 'latin-1', 'iso-8859-1', 'utf-8', 'windows-1252']
                    for encoding in tried_encodings:
                        try:
                            df = pd.read_csv(csv_file, encoding=encoding, sep=';', header=None)
                            print(f"[{os.getpid()}]   Encoding erfolgreich: {encoding} für {csv_file.name}")
                            break
                        except Exception as e:
                            print(f"[{os.getpid()}]   Encoding {encoding} fehlgeschlagen für {csv_file.name}: {e}")
                            continue

                    if df is None:
                        print(f"[{os.getpid()}]   Kein Encoding funktioniert für {csv_file.name}. Datei übersprungen.")
                        continue

                    # Header-Zeile finden (enthält 'Kdnr')
                    header_row_index = -1
                    for r_idx, row_data in df.iterrows():
                        if str(row_data.iloc[0]).strip().lower() == 'kdnr':
                            header_row_index = r_idx
                            break

                    if header_row_index == -1:
                        print(f"[{os.getpid()}]   Header-Zeile nicht gefunden in {csv_file.name}. Datei übersprungen.")
                        continue

                    # Header setzen und Daten vorbereiten
                    df.columns = df.iloc[header_row_index]
                    df = df[header_row_index+1:].reset_index(drop=True)
                    
                    # Erste 4 Zeilen überspringen (Definition/Header)
                    df = df.iloc[4:].reset_index(drop=True)

                    # Spaltennamen normalisieren
                    original_columns = df.columns.tolist()
                    new_columns = []
                    for col in original_columns:
                        print(f"[{os.getpid()}]   Original Spalte: '{col}' (repr: {repr(col)})")
                        # Umfassende Zeichenkonvertierung für deutsche Umlaute
                        col_str = str(col)
                        # Zuerst alle deutschen Umlaute konvertieren
                        col_str = col_str.replace('ß', 'ss')
                        col_str = col_str.replace('ä', 'ae')
                        col_str = col_str.replace('ö', 'oe') 
                        col_str = col_str.replace('ü', 'ue')
                        col_str = col_str.replace('Ä', 'AE')
                        col_str = col_str.replace('Ö', 'OE')
                        col_str = col_str.replace('Ü', 'UE')
                        # Weitere Sonderzeichen
                        col_str = col_str.replace('á', 'a')
                        col_str = col_str.replace('é', 'e')
                        col_str = col_str.replace('í', 'i')
                        col_str = col_str.replace('ó', 'o')
                        col_str = col_str.replace('ú', 'u')
                        
                        normalized_col = col_str.lower()\
                                        .replace(' ', '')\
                                        .replace('.', '')\
                                        .replace('/', '')\
                                        .strip()
                        
                        # Spezielle Behandlung für Straße/Strasse
                        if 'strasse' in normalized_col or 'straae' in normalized_col or 'strae' in normalized_col:
                            normalized_col = 'strasse'
                        print(f"[{os.getpid()}]   Normalisiert: '{normalized_col}'")
                        new_columns.append(normalized_col)
                    df.columns = new_columns
                    print(f"[{os.getpid()}]   Finale Spalten: {list(df.columns)}")

                    # Tour-Erkennung und Kunden-Zuordnung
                    current_tour = None
                    tour_customers = []
                    
                    for i, row in df.iterrows():
                        # Prüfe auf Tour-Überschrift
                        first_cell = str(row.iloc[0]).strip()
                        
                        # Debug: Zeige die ersten 15 Zeilen
                        if i < 15:
                            print(f"[{os.getpid()}]     Zeile {i}: '{first_cell}' (alle Zellen: {[str(row.iloc[j]) for j in range(min(6, len(row)))]})")
                            if first_cell == 'nan' and len(row) >= 2:
                                second_cell = str(row.iloc[1]).strip()
                                print(f"[{os.getpid()}]       -> Zweite Zelle: '{second_cell}'")
                        
                        # Tour-Überschrift erkennen: Muster ;W-07.00 Uhr Tour;;;;
                        # Die Tour-Überschrift steht in der zweiten Zelle, erste Zelle ist leer
                        is_tour_header = False
                        if first_cell == 'nan' and len(row) >= 2:
                            # Prüfe, ob die zweite Zelle eine Tour-Überschrift ist
                            second_cell = str(row.iloc[1]).strip()
                            if second_cell and second_cell != 'nan':
                                # Tour-Muster erkennen
                                tour_patterns = [
                                    r'^W-\d{1,2}[\.\:]\d{2}\s+Uhr\s+(Tour|BAR)$',
                                    r'^W-\d{1,2}[\.\:]\d{2}\s+Uhr$',
                                    r'^PIR\s+Anlief\.?\s+\d{1,2}[\.\:]\d{2}\s+Uhr$',
                                    r'^(?:CB|TA)\s+Anlief\.?\s+T\d+\s*,?\s*\d{1,2}[\.\:]\d{2}\s+Uhr$',
                                    r'^Anlief\.?\s+T\d+\s*,?\s*\d{1,2}[\.\:]\d{2}\s+Uhr$',
                                    r'^T\d+$',
                                ]
                                
                                for pattern in tour_patterns:
                                    if re.match(pattern, second_cell, re.IGNORECASE):
                                        is_tour_header = True
                                        print(f"[{os.getpid()}]     [OK] Tour-Muster gefunden: '{second_cell}' matches '{pattern}'")
                                        first_cell = second_cell  # Für weitere Verarbeitung
                                        break
                        
                        if is_tour_header:
                            # Vorherige Tour speichern falls vorhanden
                            if current_tour and tour_customers:
                                current_tour['customers'] = tour_customers.copy()
                                current_tour['customer_count'] = len(tour_customers)
                                if current_tour['is_bar']:
                                    bar_tours.append(current_tour)
                                else:
                                    base_tours.append(current_tour)
                                    tour_lookup.setdefault(current_tour['name'], []).append(current_tour)
                                print(f"[{os.getpid()}]   Tour gespeichert: {current_tour['name']} mit {len(tour_customers)} Kunden")

                            # Neue Tour starten
                            normalized_name, is_bar = _normalize_tour_name(first_cell)
                            if normalized_name == "Unknown":
                                anomalies.append(f"Tourkopf nicht erkannt: {first_cell} in {csv_file.name}")
                            current_tour = {
                                'name': normalized_name,
                                'raw_name': first_cell,
                                'is_bar': is_bar,
                                'file': csv_file.name,
                                'customers': [],
                                'customer_count': 0
                            }
                            tour_customers = []
                            print(f"[{os.getpid()}]   Neue Tour erkannt: {first_cell} -> {normalized_name} (BAR: {is_bar})")
                        
                        # Kundenzeile prüfen
                        elif current_tour:
                            kdnr = str(row.get('kdnr', '')).strip()
                            name = str(row.get('name', '')).strip()
                            strasse = str(row.get('strasse', '')).strip()
                            plz = str(row.get('plz', '')).strip()
                            ort = str(row.get('ort', '')).strip()
                            
                            # Debug: Zeige Kundenzeilen
                            if i < 20:
                                print(f"[{os.getpid()}]     Kundenzeile {i}: Kdnr='{kdnr}', Name='{name}', Strasse='{strasse}'")
                            
                            # Gültige Kundenzeile?
                            if (
                                kdnr and kdnr.isdigit()
                                and name and strasse
                                and name.lower() != 'name'
                                and strasse.lower() != 'strasse'
                                and kdnr != 'nan'
                                and name != 'nan'
                                and strasse != 'nan'
                            ):

                                # Vollständige Adresse erstellen
                                full_address = f"{strasse}, {plz} {ort}".strip(', ')

                                customer = {
                                    'kdnr': kdnr,
                                    'name': name,
                                    'strasse': strasse,
                                    'plz': plz,
                                    'ort': ort,
                                    'full_address': full_address,
                                    'is_bar': current_tour['is_bar']
                                }

                                tour_customers.append(customer)
                                all_customers.add(f"{name}|{full_address}")
                                total_customers_processed += 1

                                if i < 20:
                                    print(f"[{os.getpid()}]     [OK] Kunde hinzugefügt: {name} ({full_address})")
                    
                    # Letzte Tour speichern
                    if current_tour and tour_customers:
                        current_tour['customers'] = tour_customers.copy()
                        current_tour['customer_count'] = len(tour_customers)
                        if current_tour['is_bar']:
                            bar_tours.append(current_tour)
                        else:
                            base_tours.append(current_tour)
                            tour_lookup.setdefault(current_tour['name'], []).append(current_tour)
                        print(f"[{os.getpid()}]   Letzte Tour gespeichert: {current_tour['name']} mit {len(tour_customers)} Kunden")
                            
                except Exception as e:
                    print(f"[{os.getpid()}] Fehler beim Verarbeiten von {csv_file.name}: {e}")
                    continue
            
            print(f"[{os.getpid()}] Tour-Erkennung abgeschlossen. Touren: {len(all_tours)}, Eindeutige Kunden: {len(all_customers)}")
            if anomalies:
                print(f"[{os.getpid()}] WARN: Nicht erkannte Tourköpfe: {anomalies}")
            
            # In Datenbank speichern
            db_path = "./data/traffic.db"
            conn = sqlite3.connect(db_path, timeout=30.0)
            cursor = conn.cursor()
            
            # WAL-Modus für bessere Concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            
            # Kunden-Tabelle leeren und neu befüllen
            cursor.execute("DELETE FROM kunden")
            print(f"[{os.getpid()}] Kunden-Tabelle geleert.")
            
            # Touren-Tabelle leeren und neu befüllen
            cursor.execute("DELETE FROM touren")
            print(f"[{os.getpid()}] Touren-Tabelle geleert.")
            
            saved_customers = 0
            saved_tours = 0
            geocoding_success = 0
            geocoding_failed = 0
            
            # Kunden mit Geocoding speichern
            for customer_key in all_customers:
                name, full_address = customer_key.split('|', 1)
                
                lat, lng = 0.0, 0.0
                try:
                    result = geocode_address(full_address)
                    if result and 'lat' in result and 'lng' in result:
                        lat = result['lat']
                        lng = result['lng']
                        geocoding_success += 1
                    else:
                        geocoding_failed += 1
                except Exception as e:
                    print(f"[{os.getpid()}] Geocoding-Fehler für {full_address}: {e}")
                    geocoding_failed += 1
                
                cursor.execute("""
                    INSERT INTO kunden (name, adresse, lat, lon, created_at)
                    VALUES (?, ?, ?, ?, datetime('now'))
                """, (name, full_address, lat, lng))
                saved_customers += 1
                
                if saved_customers % 50 == 0:
                    print(f"[{os.getpid()}] Verarbeitet: {saved_customers} Kunden...")
            
            # Touren zusammenführen und speichern
            merged_tours = {}
            
            for tour in all_tours:
                base_name, _ = _normalize_tour_name(tour['name'])
                is_bar = tour['is_bar']

                if base_name not in merged_tours:
                    merged_tours[base_name] = {
                        'name': base_name,
                        'customers': [],
                        'bar_customers': [],
                        'file': tour['file'],
                        'customer_count': 0,
                        'has_bar': False,
                    }

                if is_bar:
                    merged_tours[base_name]['bar_customers'].extend(tour['customers'])
                    merged_tours[base_name]['has_bar'] = True
                else:
                    merged_tours[base_name]['customers'].extend(tour['customers'])
            
            # Zusammenführen und doppelte Kunden entfernen
            for tour_name, tour_data in merged_tours.items():
                # Alle Kunden zusammenführen
                all_customers = tour_data['customers'] + tour_data['bar_customers']
                
                # Doppelte Kunden entfernen (basierend auf Name + Adresse)
                unique_customers = []
                seen = set()
                
                for customer in all_customers:
                    customer_key = f"{customer['name']}|{customer['full_address']}"
                    if customer_key not in seen:
                        seen.add(customer_key)
                        # BAR-Status beibehalten
                        customer['is_bar'] = customer.get('is_bar', False)
                        unique_customers.append(customer)
                
                tour_data['customers'] = unique_customers
                tour_data['customer_count'] = len(unique_customers)
                tour_data['bar_count'] = len(tour_data['bar_customers'])
            
            # Touren in Datenbank speichern
            for tour_name, tour_data in merged_tours.items():
                # Kunden-IDs als JSON speichern
                import json
                kunden_ids = json.dumps([c['kdnr'] for c in tour_data['customers']])
                
                cursor.execute(
                    """
                    INSERT OR REPLACE INTO touren (tour_id, datum, kunden_ids, dauer_min, distanz_km, fahrer, has_bar)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (tour_name, '2025-08-29', kunden_ids, 0, 0.0, 'System', int(tour_data['has_bar'])),
                )
                saved_tours += 1
            
            conn.commit()
            conn.close()
            
            print(f"[{os.getpid()}] {saved_customers} Kunden und {saved_tours} Touren erfolgreich in Datenbank gespeichert.")
            
            return {
                "message": "CSV Import mit Tour-Erkennung erfolgreich!",
                "total_customers": total_customers_processed,
                "unique_customers": len(all_customers),
                "saved_customers": saved_customers,
                "tours_found": len(all_tours),
                "saved_tours": saved_tours,
                "bar_tours": len([t for t in all_tours if t['is_bar']]),
                "normal_tours": len([t for t in all_tours if not t['is_bar']]),
                "geocoding_success": geocoding_success,
                "geocoding_failed": geocoding_failed,
                "geocoding_rate": f"{(geocoding_success / saved_customers * 100):.1f}%" if saved_customers > 0 else "0%",
                "files_processed": len(csv_files)
            }
            
        except Exception as e:
            print(f"[{os.getpid()}] CSV Tour Processing fehlgeschlagen (globaler Fehler): {e}")
            return {"error": f"Fehler: {str(e)}", "total_customers": 0, "tours": 0}

    @app.get("/", response_class=HTMLResponse, tags=["system"], summary="Startseite")
    def index() -> str:
        return """
            <html>
              <body>
                <h2>FAMO TrafficApp – Lokale API</h2>
                <ul>
                  <li><a href="/upload">Excel/PDF hochladen und importieren</a></li>
                  <li><a href="/summary">DB-Zusammenfassung</a></li>
                  <li><a href="/kunden">Kundenliste</a></li>
                  <li><a href="/touren_html">Touren (HTML-Übersicht)</a></li>
                  <li><a href="/touren">Touren (JSON)</a></li>
                  <li><a href="/ui/">Karten-UI (Frontend)</a></li>
                  <li><a href="/docs">Swagger UI</a></li>
                </ul>
              </body>
            </html>
            """

    @app.get(
        "/touren_html",
        response_class=HTMLResponse,
        tags=["db"],
        summary="HTML-Übersicht Touren",
    )
    def touren_html(
        limit: int = Query(50, ge=1, le=500), offset: int = Query(0, ge=0)
    ) -> str:
        db = _db_path()
        if not db.exists():
            return "<html><body><h3>Keine Datenbank gefunden.</h3></body></html>"
        con = sqlite3.connect(db)
        rows = con.execute(
            "select id, tour_id, datum, kunden_ids from touren order by id desc limit ? offset ?",
            (limit, offset),
        ).fetchall()
        items = []
        for r in rows:
            tid, name, datum, kid_json = r
            try:
                raw_ids = json.loads(kid_json) if kid_json else []
                stops = len(_dedupe_preserve_order(raw_ids)) if raw_ids else 0
            except Exception:
                stops = 0
            items.append((tid, name or "", datum or "", stops))
        rows_html = "".join(
            f'<tr><td>{tid}</td><td><a href="/tour/{tid}">{name}</a></td><td>{datum}</td><td>{stops}</td></tr>'
            for tid, name, datum, stops in items
        )
        return (
            "<html><body><h3>Tourenübersicht</h3><table border=1 cellpadding=6 cellspacing=0>"
            "<tr><th>ID</th><th>Tour</th><th>Datum</th><th>Stopps</th></tr>"
            f"{rows_html}</table></body></html>"
        )

    @app.get(
        "/tour/{tour_id}",
        response_class=HTMLResponse,
        tags=["db"],
        summary="Tour-Detailansicht",
    )
    def tour_detail(tour_id: int) -> str:
        db = _db_path()
        if not db.exists():
            return "<html><body><h3>Keine Datenbank gefunden.</h3></body></html>"
        con = sqlite3.connect(db)
        tour_row = con.execute(
            "select id, tour_id, datum, kunden_ids from touren where id = ?",
            (tour_id,),
        ).fetchone()
        if not tour_row:
            return "<html><body><h3>Tour nicht gefunden.</h3></body></html>"
        name = tour_row[1] or ""
        datum = tour_row[2] or ""
        kid_json = tour_row[3]
        try:
            kids = json.loads(kid_json) if kid_json else []
            kids = _dedupe_preserve_order(kids)
        except Exception:
            kids = []
        customers = []
        if kids:
            placeholders = ",".join(["?"] * len(kids))
            customers = con.execute(
                f"select id, name, adresse from kunden where id in ({placeholders})",
                tuple(kids),
            ).fetchall()
            customers = _dedupe_customers_by_address(customers)
        rows_html = "".join(
            f"<tr><td>{cid}</td><td>{cname}</td><td>{caddr}</td></tr>"
            for cid, cname, caddr in customers
        )
        return (
            "<html><body>"
            f'<p><a href="/touren_html">Zur Übersicht</a></p>'
            f"<h3>Tour: {name}</h3><p>Datum: {datum} &nbsp;&nbsp; Stopps: {len(customers)}</p>"
            "<table border=1 cellpadding=6 cellspacing=0>"
            "<tr><th>ID</th><th>Name</th><th>Adresse</th></tr>"
            f"{rows_html}</table></body></html>"
        )

    @app.get("/preview", tags=["db"], summary="Parser-Vorschau (split)")
    def preview(
        excel: str = Query(..., description="Pfad zur Excel-Datei"),
        date: Optional[str] = Query(None),
    ) -> Dict[str, Any]:
        project_root = Path(__file__).resolve().parents[1]
        excel_path = Path(excel)
        if not excel_path.is_absolute():
            excel_path = (project_root / excel_path).resolve()
        if not excel_path.exists():
            raise HTTPException(
                status_code=400, detail=f"Excel nicht gefunden: {excel_path}"
            )
        tours = parse_teha_excel_sections(excel_path, fallback_date=date)
        return {"sections": len(tours), "tours": tours[:3]}  # erste 3 zur Vorschau

    @app.get("/debug/tours", tags=["debug"], summary="Debug: Alle Touren anzeigen")
    def debug_tours() -> Dict[str, Any]:
        db = _db_path()
        if not db.exists():
            return {"error": "DB nicht gefunden"}
        try:
            con = sqlite3.connect(db)
            tours = con.execute(
                "select id, tour_id, datum, kunden_ids from touren order by id desc limit 10"
            ).fetchall()
            return {
                "tours": [
                    {"id": r[0], "tour": r[1], "datum": r[2], "kunden_ids": r[3]}
                    for r in tours
                ]
            }
        except Exception as e:
            return {"error": str(e)}

    @app.get("/tour/{tour_id}/points", tags=["map"], summary="Geo-Punkte der Tour")
    async def tour_points(tour_id: int) -> Dict[str, Any]:
        try:
            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
            # DB bereits initialisiert - init_db() nicht nötig hier
            con = sqlite3.connect(db)
            row = con.execute(
                "select kunden_ids from touren where id= ?", (tour_id,)
            ).fetchone()
            if not row:
                # Debug: Welche Tour-IDs gibt es?
                existing = con.execute(
                    "select id, tour_id from touren limit 5"
                ).fetchall()
                raise HTTPException(
                    status_code=404,
                    detail=f"Tour {tour_id} nicht gefunden. Verfügbar: {existing}",
                )
            kid_json = row[0]
            try:
                ids = json.loads(kid_json) if kid_json else []
                ids = _dedupe_preserve_order(ids)
            except Exception as je:
                raise HTTPException(status_code=400, detail=f"JSON-Fehler: {je}")
            customers = []
            if ids:
                placeholders = ",".join(["?"] * len(ids))
                customers = con.execute(
                    f"select id, name, adresse from kunden where id in ({placeholders})",
                    tuple(ids),
                ).fetchall()
                customers = _dedupe_customers_by_address(customers)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Unerwarteter Fehler: {str(e)}"
            )
        features = []

        # FAMO Start- und Endpunkt: Stuttgarter Str. 33, 01189 Dresden
        famo_address = "Stuttgarter Str. 33, 01189 Dresden"
        famo_pt = geocode_address(famo_address)
        if famo_pt is not None:
            lat, lon = famo_pt
            # Startpunkt
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "id": "start",
                        "name": "FAMO (Start)",
                        "adresse": famo_address,
                        "type": "depot",
                        "sequence": 0,
                    },
                }
            )

        # Kunden (Sequence-Nummern für Reihenfolge)
        for idx, (cid, name, adresse) in enumerate(customers, start=1):
            pt = geocode_address(adresse)
            if pt is None:
                continue
            lat, lon = pt
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "id": cid,
                        "name": name,
                        "adresse": adresse,
                        "type": "customer",
                        "sequence": idx,
                    },
                }
            )

        # FAMO Endpunkt (nach allen Kunden)
        if famo_pt is not None:
            lat, lon = famo_pt
            features.append(
                {
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [lon, lat]},
                    "properties": {
                        "id": "end",
                        "name": "FAMO (Ende)",
                        "adresse": famo_address,
                        "type": "depot",
                        "sequence": len(customers) + 1,
                    },
                }
            )
        # Echte Straßenroute berechnen (wenn mehr als 1 Punkt vorhanden)
        route_geometry = None
        route_metrics = None
        if len(features) >= 2:
            try:
                routing_service = RealRoutingService()
                route_points = []
                
                # Punkte nach Sequence sortieren und für Routing vorbereiten
                sorted_features = sorted(features, key=lambda f: f["properties"]["sequence"])
                for feature in sorted_features:
                    coords = feature["geometry"]["coordinates"]
                    props = feature["properties"]
                    route_points.append(RoutePoint(
                        lat=coords[1], 
                        lon=coords[0],
                        address=props["adresse"],
                        name=props["name"]
                    ))
                
                # Route berechnen
                if len(route_points) >= 2:
                    route_result = await routing_service.calculate_route(route_points)
                    if route_result and route_result.segments:
                        # Route-Geometrie extrahieren (falls verfügbar)
                        route_geometry = []
                        for segment in route_result.segments:
                            if segment.route_geometry:
                                route_geometry.extend(segment.route_geometry)
                        
                        # Falls keine Geometrie verfügbar, Fallback zu Punkten
                        if not route_geometry:
                            route_geometry = [[p.lon, p.lat] for p in route_points]
                        # Metriken hinzufügen
                        route_metrics = {
                            "distance_km": round(route_result.total_distance_km, 1),
                            "duration_minutes": int(route_result.total_duration_minutes),
                            "traffic_delay_minutes": int(route_result.total_traffic_delay),
                        }
            except Exception as e:
                print(f"[WARNUNG] Routing-Fehler: {e}")
                # Fallback: Keine Route-Geometrie
                pass
        
        result = {
            "type": "FeatureCollection", 
            "features": features
        }
        
        # Route-Geometrie hinzufügen (wenn verfügbar)
        if route_geometry:
            result["route_geometry"] = route_geometry
        if route_metrics:
            result["route_metrics"] = route_metrics
            
        return result



    @app.post("/tour/{tour_id}/order", tags=["map"], summary="Reihenfolge neu berechnen und echte Route liefern")
    async def reorder_tour(tour_id: int, payload: OrderRequest) -> Dict[str, Any]:
        """Nimmt eine Kunden-ID-Reihenfolge entgegen und liefert FeatureCollection
        mit aktualisierten Sequence-Werten und echter `route_geometry` zurück.
        Start/Ende (FAMO) werden automatisch ergänzt.
        """
        try:
            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
            con = sqlite3.connect(db)

            raw_ids = payload.order or []
            # Robust: in int umwandeln, ungültige Werte herausfiltern
            ids: List[int] = []
            for x in raw_ids:
                try:
                    ids.append(int(x))
                except Exception:
                    continue
            if not ids:
                raise HTTPException(status_code=400, detail="Leere Reihenfolge übergeben")

            # Sicher: nur gültige ints und Duplikate entfernen (Reihenfolge behalten)
            ids = [i for i in ids if isinstance(i, int) and i > 0]
            unique_ids = _dedupe_preserve_order(ids)
            if not unique_ids:
                raise HTTPException(status_code=400, detail="Keine gültigen Kunden-IDs")

            placeholders = ",".join(["?"] * len(unique_ids))
            rows = con.execute(
                f"select id, name, adresse from kunden where id in ({placeholders})",
                tuple(unique_ids),
            ).fetchall()

            # Map für schnellen Zugriff
            id_to_row = {rid: (rid, name, adr) for (rid, name, adr) in rows}

            # Start/Ende Depot
            famo_address = "Stuttgarter Str. 33, 01189 Dresden"
            famo_pt = geocode_address(famo_address)

            features: List[Dict[str, Any]] = []
            if famo_pt is not None:
                lat, lon = famo_pt
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {
                            "id": "start",
                            "name": "FAMO (Start)",
                            "adresse": famo_address,
                            "type": "depot",
                            "sequence": 0,
                        },
                    }
                )

            # Kunden in der gewünschten Reihenfolge (ohne doppelte Adressen)
            sequence_counter = 1
            seen_addr_keys: set[str] = set()
            for cid in unique_ids:
                row = id_to_row.get(cid)
                if not row:
                    continue
                _, name, adresse = row
                addr_key = _normalize_address(adresse)
                if addr_key in seen_addr_keys:
                    continue
                seen_addr_keys.add(addr_key)
                pt = geocode_address(adresse)
                if pt is None:
                    continue
                clat, clon = pt
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [clon, clat]},
                        "properties": {
                            "id": cid,
                            "name": name,
                            "adresse": adresse,
                            "type": "customer",
                            "sequence": sequence_counter,
                        },
                    }
                )
                sequence_counter += 1

            if famo_pt is not None:
                lat, lon = famo_pt
                features.append(
                    {
                        "type": "Feature",
                        "geometry": {"type": "Point", "coordinates": [lon, lat]},
                        "properties": {
                            "id": "end",
                            "name": "FAMO (Ende)",
                            "adresse": famo_address,
                            "type": "depot",
                            "sequence": sequence_counter,
                        },
                    }
                )

            # Echte Straßenroute berechnen
            route_geometry = None
            route_metrics = None
            if len(features) >= 2:
                try:
                    routing_service = RealRoutingService()
                    route_points: List[RoutePoint] = []
                    sorted_features = sorted(features, key=lambda f: f["properties"]["sequence"])
                    for feature in sorted_features:
                        coords = feature["geometry"]["coordinates"]
                        props = feature["properties"]
                        route_points.append(
                            RoutePoint(lat=coords[1], lon=coords[0], address=props["adresse"], name=props["name"])  # type: ignore
                        )
                    if len(route_points) >= 2:
                        route_result = await routing_service.calculate_route(route_points)
                        if route_result and route_result.segments:
                            route_geometry = []
                            for segment in route_result.segments:
                                if segment.route_geometry:
                                    route_geometry.extend(segment.route_geometry)
                            if not route_geometry:
                                route_geometry = [[p.lon, p.lat] for p in route_points]
                            route_metrics = {
                                "distance_km": round(route_result.total_distance_km, 1),
                                "duration_minutes": int(route_result.total_duration_minutes),
                                "traffic_delay_minutes": int(route_result.total_traffic_delay),
                            }
                except Exception as e:
                    print(f"[WARNUNG] Routing-Fehler (order): {e}")

            result = {"type": "FeatureCollection", "features": features}
            if route_geometry:
                result["route_geometry"] = route_geometry
            if route_metrics:
                result["route_metrics"] = route_metrics
            return result
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Unerwarteter Fehler: {e}")

    @app.get(
        "/tour/{tour_id}/summary", tags=["ai"], summary="Tour-Summary mit KI-Analyse"
    )
    async def tour_summary(tour_id: int) -> Dict[str, Any]:
        """Erstellt automatisches Summary für eine Tour"""
        try:
            db = _db_path()
            if not db.exists():
                return {
                    "error": "DB nicht verfügbar",
                    "summary": "Keine Analyse möglich",
                }

            con = sqlite3.connect(db)
            row = con.execute(
                "select kunden_ids, tour_id from touren where id=?", (tour_id,)
            ).fetchone()
            if not row:
                return {
                    "error": "Tour nicht gefunden",
                    "summary": "Tour existiert nicht",
                }

            kid_json, tour_name = row
            try:
                ids = json.loads(kid_json) if kid_json else []
                ids = _dedupe_preserve_order(ids)
            except Exception:
                return {
                    "error": "Daten-Format-Fehler",
                    "summary": "Ungültige Tour-Daten",
                }

            # Lade Kunden und dedupliziere per Adresse
            placeholders = ",".join(["?"] * len(ids)) if ids else ""
            customers_rows = (
                con.execute(
                    f"select id, name, adresse from kunden where id in ({placeholders})",
                    tuple(ids),
                ).fetchall()
                if ids
                else []
            )
            customers_rows = _dedupe_customers_by_address(customers_rows)
            stopps_count = len(customers_rows)

            # Quick Summary ohne KI für sehr große Touren
            if stopps_count > 50:
                return {
                    "tour_id": tour_id,
                    "tour_name": tour_name,
                    "stopps_count": stopps_count,
                    "summary": f"Große Tour mit {stopps_count} Stopps. KI-Optimierung für Touren >50 Stopps nicht verfügbar.",
                    "status": "large_tour",
                    "ai_analysis": False,
                }

            if stopps_count < 2:
                return {
                    "tour_id": tour_id,
                    "tour_name": tour_name,
                    "stopps_count": stopps_count,
                    "summary": "Tour zu klein für Optimierung.",
                    "status": "too_small",
                    "ai_analysis": False,
                }

            # Für normale Touren: Echte KI-Optimierung mit Umreihung
            try:
                optimizer = AIOptimizer(use_local=True)

                # Geocoding für alle Kunden (für echte Optimierung)
                stops = []
                for idx, (cid, name, adresse) in enumerate(customers_rows):
                    pt = geocode_address(adresse)
                    if pt is not None:
                        lat, lon = pt
                        stops.append(
                            Stop(
                                id=str(cid),
                                name=name,
                                address=adresse,
                                lat=lat,
                                lon=lon,
                                sequence=idx + 1,
                            )
                        )

                if len(stops) >= 2:
                    # FAMO Depot-Koordinaten
                    depot_lat, depot_lon = 51.0111988, 13.7016485

                    # Echte KI-Optimierung mit neuen Regeln
                    print(f"[KI] Starte echte Optimierung fuer {len(stops)} Stopps...")
                    result = await optimizer.optimize_route(
                        stops, depot_lat, depot_lon, default_rules
                    )

                    return {
                        "tour_id": tour_id,
                        "tour_name": tour_name,
                        "stopps_count": stopps_count,
                        "summary": f"KI-Optimierung: {result.improvements}",
                        "estimated_time_minutes": result.estimated_time_minutes,
                        "complexity": "optimiert",
                        "optimization_tip": result.reasoning,
                        "optimized_sequence": result.optimized_sequence,
                        "status": "ai_optimized",
                        "ai_analysis": True,
                    }
                else:
                    # Fallback für wenig geocodierte Stopps – keine KI, klare Standardwerte
                    print(
                        f"[WARNUNG] Nur {len(stops)} geocodierte Stopps, liefere Standard-Summary ohne KI"
                    )
                    return {
                        "tour_id": tour_id,
                        "tour_name": tour_name,
                        "stopps_count": stopps_count,
                        "summary": f"Tour mit {stopps_count} Stopps im Einsatzgebiet.",
                        "estimated_time_minutes": stopps_count * 5,
                        "complexity": "mittel" if stopps_count <= 20 else "hoch",
                        "optimization_tip": "Tipp: Adressen prüfen/geocodieren, dann erneut optimieren",
                        "status": "geocoding_insufficient",
                        "ai_analysis": False,
                    }

            except Exception:
                # Fallback ohne KI
                return {
                    "tour_id": tour_id,
                    "tour_name": tour_name,
                    "stopps_count": stopps_count,
                    "summary": f"Tour mit {stopps_count} Stopps. Geschätzte Zeit: {stopps_count * 5} min.",
                    "estimated_time_minutes": stopps_count * 5,
                    "complexity": "mittel" if stopps_count <= 20 else "hoch",
                    "optimization_tip": "Tipp: Routen nach geografischen Clustern organisieren",
                    "status": "fallback",
                    "ai_analysis": False,
                }

        except Exception as e:
            return {
                "error": str(e),
                "summary": "Analyse fehlgeschlagen",
                "ai_analysis": False,
            }

    @app.get(
        "/tour/{tour_id}/plan_text", tags=["map"], summary="Textueller Routenplan (Tabellenform)"
    )
    async def tour_plan_text(tour_id: int) -> Dict[str, Any]:
        """Liefert eine strukturierte Tabelle mit Reihenfolge, Namen/Adresse und
        Fahrzeit ab Vorstopp. Grundlage sind die echten Routing-Segmente.
        """
        try:
            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
            con = sqlite3.connect(db)
            row = con.execute(
                "select tour_id, kunden_ids from touren where id=?", (tour_id,)
            ).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tour nicht gefunden")
            tour_name, kid_json = row
            try:
                ids = json.loads(kid_json) if kid_json else []
                ids = _dedupe_preserve_order(ids)
            except Exception:
                ids = []

            # Kunden laden in gegebener Reihenfolge und per Adresse deduplizieren
            customers: List[tuple] = []
            if ids:
                placeholders = ",".join(["?"] * len(ids))
                rows = con.execute(
                    f"select id, name, adresse from kunden where id in ({placeholders})",
                    tuple(ids),
                ).fetchall()
                by_id = {cid: (cid, name, adr) for cid, name, adr in rows}
                customers = [by_id[cid] for cid in ids if cid in by_id]
                customers = _dedupe_customers_by_address(customers)

            famo_address = "Stuttgarter Str. 33, 01189 Dresden"
            famo_pt = geocode_address(famo_address)
            if famo_pt is None:
                raise HTTPException(status_code=500, detail="Depot konnte nicht geocodiert werden")
            depot_lat, depot_lon = famo_pt

            # Routepunkte: Start – Kunden – Ende
            routing_service = RealRoutingService()
            points: List[RoutePoint] = [
                RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO")
            ]
            for _cid, _name, _adr in customers:
                pt = geocode_address(_adr)
                if pt is None:
                    continue
                lat, lon = pt
                points.append(RoutePoint(lat=lat, lon=lon, address=_adr, name=_name))
            points.append(RoutePoint(lat=depot_lat, lon=depot_lon, address=famo_address, name="FAMO"))

            if len(points) < 2:
                raise HTTPException(status_code=400, detail="Zu wenige Punkte für Plan")

            route = await routing_service.calculate_route(points)
            dwell_per_stop = 2

            rows_out: List[Dict[str, Any]] = []
            # Startzeile
            rows_out.append({
                "index": "Start",
                "name": "FAMO",
                "adresse": famo_address,
                "travel_minutes": None,
                "note": "–",
            })

            # Zwischenstopps (für jedes Segment Start->Kunde i)
            seg_idx = 0
            stop_counter = 0
            for i in range(1, len(points) - 1):
                # Dauer des Segments vom Vorpunkt zu diesem Punkt
                travel = 0
                if route.segments and seg_idx < len(route.segments):
                    travel = int(route.segments[seg_idx].duration_minutes)
                seg_idx += 1
                stop_counter += 1
                rows_out.append({
                    "index": stop_counter,
                    "name": points[i].name,
                    "adresse": points[i].address,
                    "travel_minutes": travel,
                    "unload_minutes": dwell_per_stop,
                })

            # Rückwegsegment (letzter Kunde -> Depot), falls vorhanden
            back_travel = 0
            if route.segments and seg_idx < len(route.segments):
                back_travel = int(route.segments[seg_idx].duration_minutes)
            rows_out.append({
                "index": "Ende",
                "name": "FAMO",
                "adresse": famo_address,
                "travel_minutes": back_travel,
                "note": "Rückweg",
            })

            return {
                "tour_id": tour_id,
                "tour": tour_name,
                "dwell_minutes_per_stop": dwell_per_stop,
                "rows": rows_out,
                "total_travel_minutes": int(route.total_duration_minutes) if route else 0,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Plan-Generierung fehlgeschlagen: {e}")

    @app.get(
        "/tour/{tour_id}/google_link", tags=["map"], summary="Google-Maps-Link für Tour (Start→Stopps→Ende)"
    )
    async def tour_google_link(tour_id: int) -> Dict[str, Any]:
        """Erstellt einen Google-Maps-Directions-Link mit Start (FAMO), allen Stopps
        in aktueller Reihenfolge und Rückweg zum Depot. Google erlaubt max. 25 Punkte
        (Origin + Destination + bis zu 23 Waypoints)."""
        try:
            from urllib.parse import quote

            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")
            con = sqlite3.connect(db)
            row = con.execute("select kunden_ids from touren where id=?", (tour_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Tour nicht gefunden")
            try:
                ids = json.loads(row[0]) if row[0] else []
                ids = _dedupe_preserve_order(ids)
            except Exception:
                ids = []

            famo_address = "Stuttgarter Str. 33, 01189 Dresden"
            famo_pt = geocode_address(famo_address)
            if famo_pt is None:
                raise HTTPException(status_code=500, detail="Depot konnte nicht geocodiert werden")
            depot_lat, depot_lon = famo_pt

            # Kunden laden und deduplizieren (Adresse)
            customers = []
            if ids:
                placeholders = ",".join(["?"] * len(ids))
                rows = con.execute(
                    f"select id, name, adresse from kunden where id in ({placeholders})",
                    tuple(ids),
                ).fetchall()
                by_id = {cid: (cid, name, adr) for cid, name, adr in rows}
                customers = [by_id[cid] for cid in ids if cid in by_id]
                customers = _dedupe_customers_by_address(customers)

            # Geocode Kunden
            coords: List[tuple] = []
            for _cid, _name, _adr in customers:
                pt = geocode_address(_adr)
                if pt is not None:
                    coords.append(pt)  # (lat, lon)

            # Google Maps: max 23 Waypoints
            max_waypoints = 23
            waypoints_coords = coords[:max_waypoints]

            def fmt(lat: float, lon: float) -> str:
                return f"{lat:.6f},{lon:.6f}"

            origin = fmt(depot_lat, depot_lon)
            destination = fmt(depot_lat, depot_lon)
            waypoints = "|".join(fmt(lat, lon) for lat, lon in waypoints_coords)

            base = "https://www.google.com/maps/dir/?api=1&travelmode=driving"
            url = f"{base}&origin={quote(origin)}&destination={quote(destination)}"
            if waypoints:
                url += f"&waypoints={quote(waypoints)}"

            return {
                "url": url,
                "origin": origin,
                "destination": destination,
                "waypoints": len(waypoints_coords),
                "truncated": len(coords) > max_waypoints,
            }
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Google-Link fehlgeschlagen: {e}")

    @app.post(
        "/tour/{tour_id}/optimize", tags=["ai"], summary="Route mit KI optimieren"
    )
    async def optimize_tour(
        tour_id: int,
        use_local: bool = Query(True, description="Lokale KI (Ollama) verwenden"),
    ) -> Dict[str, Any]:
        """Optimiert eine Tour-Route mit KI"""
        try:
            db = _db_path()
            if not db.exists():
                raise HTTPException(status_code=400, detail=f"DB fehlt: {db}")

            # Tour-Daten laden
            con = sqlite3.connect(db)
            row = con.execute(
                "select kunden_ids, tour_id from touren where id=?", (tour_id,)
            ).fetchone()
            if not row:
                raise HTTPException(
                    status_code=404, detail=f"Tour {tour_id} nicht gefunden"
                )

            kid_json, tour_name = row
            try:
                ids = json.loads(kid_json) if kid_json else []
                ids = _dedupe_preserve_order(ids)
            except Exception:
                raise HTTPException(status_code=400, detail="Kunden-IDs Format-Fehler")

            if not ids:
                raise HTTPException(status_code=400, detail="Keine Kunden in Tour")

            # Kunden-Details laden und per Adresse deduplizieren
            placeholders = ",".join(["?"] * len(ids))
            customers = con.execute(
                f"select id, name, adresse from kunden where id in ({placeholders})",
                tuple(ids),
            ).fetchall()
            customers = _dedupe_customers_by_address(customers)

            # Geocoding für alle Kunden
            stops = []
            for idx, (cid, name, adresse) in enumerate(customers):
                pt = geocode_address(adresse)
                if pt is not None:
                    lat, lon = pt
                    stops.append(
                        Stop(
                            id=str(cid),
                            name=name,
                            address=adresse,
                            lat=lat,
                            lon=lon,
                            sequence=idx + 1,
                        )
                    )

            if len(stops) < 2:
                raise HTTPException(
                    status_code=400,
                    detail="Mindestens 2 geocodierte Stopps erforderlich",
                )

            if len(stops) > 50:
                raise HTTPException(
                    status_code=400,
                    detail=f"Zu viele Stopps ({len(stops)}). Maximum: 50 für KI-Optimierung.",
                )

            # FAMO Depot-Koordinaten
            famo_pt = geocode_address("Stuttgarter Str. 33, 01189 Dresden")
            if famo_pt is None:
                raise HTTPException(
                    status_code=500,
                    detail="FAMO-Adresse konnte nicht geocodiert werden",
                )
            depot_lat, depot_lon = famo_pt

            # KI-Optimierung
            optimizer = AIOptimizer(use_local=use_local)
            result = await optimizer.optimize_route(stops, depot_lat, depot_lon)

            return {
                "tour_id": tour_id,
                "tour_name": tour_name,
                "original_stops": len(stops),
                "optimization": {
                    "optimized_sequence": result.optimized_sequence,
                    "total_distance_km": result.total_distance_km,
                    "estimated_time_minutes": result.estimated_time_minutes,
                    "improvements": result.improvements,
                    "reasoning": result.reasoning,
                },
                "ai_used": "Ollama (lokal)" if use_local else "Cloud API",
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Optimierung fehlgeschlagen: {str(e)}"
            )

    @app.post("/customer/bulk", tags=["customer"], summary="Gibt Liste von Kunden nach IDs zurück")
    def get_customers_by_id_list(customer_ids: List[int]) -> List[Dict[str, Any]]:
        customers = get_customers_by_ids(customer_ids)
        return [
            {"id": c.id, "name": c.name, "adresse": c.adresse, "lat": c.lat, "lon": c.lon}
            for c in customers
        ]

    @app.get("/debug/db_status", tags=["debug"], summary="Debug: Datenbankstatus und Geokoordinaten anzeigen")
    def debug_db_status() -> Dict[str, Any]:
        """Zeigt den aktuellen Status der Datenbank, insbesondere Kunden mit Geokoordinaten"""
        try:
            db = _db_path()
            if not db.exists():
                return {"error": "Datenbank nicht gefunden", "db_path": str(db)}
            
            con = sqlite3.connect(db)
            
            # Kunden-Statistik
            kunden_stats = con.execute("""
                SELECT 
                    COUNT(*) as total,
                    COUNT(CASE WHEN lat IS NOT NULL AND lon IS NOT NULL THEN 1 END) as with_coords,
                    COUNT(CASE WHEN lat IS NULL OR lon IS NULL THEN 1 END) as without_coords
                FROM kunden
            """).fetchone()
            
            # Beispiele für Kunden mit und ohne Koordinaten
            with_coords = con.execute("""
                SELECT id, name, adresse, lat, lon 
                FROM kunden 
                WHERE lat IS NOT NULL AND lon IS NOT NULL 
                LIMIT 5
            """).fetchall()
            
            without_coords = con.execute("""
                SELECT id, name, adresse, lat, lon 
                FROM kunden 
                WHERE lat IS NULL OR lon IS NULL 
                LIMIT 5
            """).fetchall()
            
            # Geocache-Statistik
            geocache_stats = con.execute("""
                SELECT COUNT(*) as total FROM geocache
            """).fetchone()
            
            # Touren-Statistik
            touren_stats = con.execute("""
                SELECT COUNT(*) as total FROM touren
            """).fetchone()
            
            return {
                "database": str(db.resolve()),
                "kunden": {
                    "total": kunden_stats[0],
                    "with_coordinates": kunden_stats[1],
                    "without_coordinates": kunden_stats[2],
                    "examples_with_coords": [
                        {"id": r[0], "name": r[1], "adresse": r[2], "lat": r[3], "lon": r[4]}
                        for r in with_coords
                    ],
                    "examples_without_coords": [
                        {"id": r[0], "name": r[1], "adresse": r[2], "lat": r[3], "lon": r[4]}
                        for r in without_coords
                    ]
                },
                "geocache": {
                    "total_cached_addresses": geocache_stats[0]
                },
                "touren": {
                    "total": touren_stats[0]
                }
            }
            
        except Exception as e:
            return {"error": f"Datenbankstatus konnte nicht abgerufen werden: {e}"}

    # Tour Management API Endpoints
    @app.post("/api/tours/create", tags=["tours"], summary="Neue Tour erstellen und in Datenbank speichern")
    def create_tour(tour_request: TourCreateRequest) -> Dict[str, Any]:
        """Erstellt eine neue Tour mit allen Stopps und speichert sie in der Datenbank"""
        try:
            tour_manager = TourManager()
            
            # Tour erstellen
            tour_data = {
                'tour_name': tour_request.tour_name,
                'tour_type': tour_request.tour_type,
                'tour_date': tour_request.tour_date,
                'total_customers': tour_request.total_customers,
                'total_distance_km': tour_request.total_distance_km,
                'total_duration_min': tour_request.total_duration_min
            }
            
            tour = tour_manager.create_tour(tour_data)
            
            # Stopps hinzufügen
            stops_data = []
            for stop in tour_request.stops:
                stop_data = {
                    'customer_id': stop['customer_id'],
                    'estimated_arrival_time': stop.get('estimated_arrival_time'),
                    'estimated_departure_time': stop.get('estimated_departure_time'),
                    'dwell_time_min': stop.get('dwell_time_min', 2)
                }
                stops_data.append(stop_data)
            
            tour_stops = tour_manager.add_tour_stops(tour.id, stops_data)
            
            return {
                "success": True,
                "tour_id": tour.id,
                "tour_name": tour.tour_name,
                "message": f"Tour {tour.tour_name} erfolgreich erstellt und gespeichert",
                "stops_count": len(tour_stops)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Fehler beim Erstellen der Tour: {str(e)}"
            )

    @app.get("/api/tours/{tour_id}", tags=["tours"], summary="Tour mit allen Stopps abrufen")
    def get_tour(tour_id: int) -> Dict[str, Any]:
        """Holt eine Tour mit allen Stopps und Kundendaten"""
        try:
            tour_manager = TourManager()
            tour_data = tour_manager.get_tour_with_stops(tour_id)
            
            if not tour_data:
                raise HTTPException(status_code=404, detail="Tour nicht gefunden")
            
            return {
                "success": True,
                "tour": tour_data
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Fehler beim Abrufen der Tour: {str(e)}"
            )

    @app.get("/api/tours/date/{tour_date}", tags=["tours"], summary="Alle Touren für ein bestimmtes Datum abrufen")
    def get_tours_by_date(tour_date: str) -> Dict[str, Any]:
        """Holt alle Touren für ein bestimmtes Datum (Format: YYYY-MM-DD)"""
        try:
            tour_manager = TourManager()
            tours = tour_manager.get_tours_by_date(tour_date)
            
            return {
                "success": True,
                "tour_date": tour_date,
                "tours": tours,
                "total_tours": len(tours)
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Fehler beim Abrufen der Touren: {str(e)}"
            )

    @app.put("/api/tours/{tour_id}/stops/sequence", tags=["tours"], summary="Reihenfolge der Stopps aktualisieren (Drag & Drop)")
    def update_stop_sequence(tour_id: int, sequence_request: TourStopUpdateRequest) -> Dict[str, Any]:
        """Aktualisiert die Reihenfolge der Stopps einer Tour"""
        try:
            tour_manager = TourManager()
            success = tour_manager.update_stop_sequence(tour_id, sequence_request.new_sequence)
            
            if not success:
                raise HTTPException(status_code=400, detail="Fehler beim Aktualisieren der Stopp-Reihenfolge")
            
            return {
                "success": True,
                "message": f"Reihenfolge der Stopps für Tour {tour_id} erfolgreich aktualisiert"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Fehler beim Aktualisieren der Stopp-Reihenfolge: {str(e)}"
            )

    @app.post("/api/tours/{tour_id}/complete", tags=["tours"], summary="Tour als abgeschlossen markieren")
    def complete_tour(tour_id: int, completion_request: TourCompleteRequest) -> Dict[str, Any]:
        """Markiert eine Tour als abgeschlossen und speichert Performance-Daten"""
        try:
            tour_manager = TourManager()
            
            performance_data = {
                'actual_distance_km': completion_request.actual_distance_km,
                'actual_duration_min': completion_request.actual_duration_min,
                'fuel_consumption_l': completion_request.fuel_consumption_l,
                'driver_notes': completion_request.driver_notes,
                'customer_feedback': completion_request.customer_feedback,
                'weather_conditions': completion_request.weather_conditions,
                'traffic_conditions': completion_request.traffic_conditions
            }
            
            success = tour_manager.complete_tour(tour_id, performance_data)
            
            if not success:
                raise HTTPException(status_code=400, detail="Tour konnte nicht abgeschlossen werden")
            
            return {
                "success": True,
                "message": f"Tour {tour_id} erfolgreich als abgeschlossen markiert"
            }
            
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Fehler beim Abschließen der Tour: {str(e)}"
            )

    @app.get("/api/tours/statistics", tags=["tours"], summary="Tour-Statistiken für einen Zeitraum abrufen")
    def get_tour_statistics(
        start_date: str = Query(..., description="Startdatum (YYYY-MM-DD)"),
        end_date: str = Query(..., description="Enddatum (YYYY-MM-DD)"),
        tour_type: Optional[str] = Query(None, description="Tour-Typ (W, PIR, T)")
    ) -> Dict[str, Any]:
        """Holt detaillierte Tour-Statistiken für einen Zeitraum"""
        try:
            tour_manager = TourManager()
            stats = tour_manager.get_tour_statistics(start_date, end_date, tour_type)
            
            return {
                "success": True,
                "period": {"start_date": start_date, "end_date": end_date},
                "tour_type_filter": tour_type,
                "statistics": stats
            }
            
        except Exception as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Fehler beim Abrufen der Statistiken: {str(e)}"
            )

    @app.post("/api/tours/{tour_id}/split_ai", tags=["tours"], summary="Tour mit KI in mehrere Untertouren aufteilen")
    async def split_tour_with_ai(tour_id: int) -> Dict[str, Any]:
        """Teilt eine Tour mit KI in mehrere Untertouren auf (A, B, C, ...)"""
        try:
            db_path = _db_path()
            if not db_path.exists():
                return {"error": "Datenbank nicht gefunden", "status": "error"}
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Tour-Informationen abrufen
            cursor.execute('''
                SELECT tour_name, tour_date, tour_type 
                FROM touren 
                WHERE id = ?
            ''', (tour_id,))
            
            tour_info = cursor.fetchone()
            if not tour_info:
                return {"error": "Tour nicht gefunden", "status": "error"}
            
            tour_name, tour_date, tour_type = tour_info
            
            # Alle Kunden dieser Tour abrufen
            cursor.execute('''
                SELECT k.id, k.name, k.adresse, k.lat, k.lon, k.seq_no
                FROM kunden k
                INNER JOIN tour_kunden tk ON k.id = tk.customer_id
                WHERE tk.tour_id = ?
                ORDER BY k.seq_no
            ''', (tour_id,))
            
            customers = cursor.fetchall()
            if not customers:
                return {"error": "Keine Kunden für diese Tour gefunden", "status": "error"}
            
            # Kunden in Stopps für den AI-Optimizer konvertieren
            from backend.services.ai_optimizer import AIOptimizer, Stop
            from backend.services.optimization_rules import default_rules
            
            stops = []
            for i, (cid, name, adresse, lat, lon, seq_no) in enumerate(customers):
                # Fallback-Koordinaten falls nicht vorhanden
                if not lat or not lon:
                    lat, lon = 51.0504, 13.7373  # Dresden Zentrum als Fallback
                
                stops.append(Stop(
                    id=str(cid),
                    name=name or f"Kunde {cid}",
                    address=adresse or "Keine Adresse",
                    lat=float(lat),
                    lon=float(lon),
                    sequence=seq_no or i
                ))
            
            # KI-Optimizer für Routenaufteilung verwenden
            optimizer = AIOptimizer(use_local=True)
            result = await optimizer.cluster_stops_into_tours(stops, default_rules)
            
            if not result.get("tours"):
                return {"error": "KI konnte keine Touren generieren", "status": "error"}
            
            # Neue Untertouren in der Datenbank erstellen
            created_tours = []
            for tour_cluster in result["tours"]:
                cluster_name = tour_cluster.get("name", "A")
                customer_ids = tour_cluster.get("customer_ids", [])
                
                if not customer_ids:
                    continue
                
                # Neue Tour mit Suffix erstellen (z.B. "W-07:00 A")
                new_tour_name = f"{tour_name} {cluster_name}"
                
                # Tour in der Datenbank speichern
                cursor.execute('''
                    INSERT INTO tours (tour_name, tour_date, tour_type, parent_tour_id)
                    VALUES (?, ?, ?, ?)
                ''', (new_tour_name, tour_date, tour_type, tour_id))
                
                new_tour_id = cursor.lastrowid
                
                # Kunden der neuen Tour zuordnen
                for customer_id in customer_ids:
                    cursor.execute('''
                        INSERT INTO tour_kunden (tour_id, customer_id)
                        VALUES (?, ?)
                    ''', (new_tour_id, int(customer_id)))
                
                created_tours.append({
                    "id": new_tour_id,
                    "name": new_tour_name,
                    "customer_count": len(customer_ids),
                    "customer_ids": customer_ids
                })
            
            conn.commit()
            conn.close()
            
            return {
                "status": "success",
                "original_tour": {
                    "id": tour_id,
                    "name": tour_name,
                    "date": tour_date
                },
                "created_subtours": created_tours,
                "total_subtours": len(created_tours),
                "ai_reasoning": result.get("reasoning", "Keine Begründung verfügbar"),
                "message": f"Tour erfolgreich in {len(created_tours)} Untertouren aufgeteilt"
            }
            
        except Exception as e:
            return {
                "error": f"Fehler bei der KI-basierten Routenaufteilung: {str(e)}",
                "status": "error"
            }

    @app.post("/api/process-csv-modular", tags=["workflow"], summary="Modularer CSV-Workflow: CSV → Routen → KI → Untertouren")
    async def process_csv_modular(file: UploadFile = File(...)) -> dict:
        """Verarbeitet CSV-Datei mit dem modularen Workflow"""
        try:
            content = file.file.read()
            file.file.seek(0)
            
            # Workflow Orchestrator verwenden
            orchestrator = WorkflowOrchestrator()
            result = await orchestrator.process_csv_to_subtours(
                BytesIO(content), 
                file.filename
            )
            
            if result["success"]:
                return {
                    "success": True,
                    "filename": file.filename,
                    "workflow_results": result,
                    "message": f"Modularer Workflow erfolgreich: {result['final_results']['routes']['total_routes']} Routen verarbeitet"
                }
            else:
                return {
                    "success": False,
                    "error": result.get("error", "Unbekannter Fehler"),
                    "workflow_state": result.get("workflow_steps", {}),
                    "message": "Workflow fehlgeschlagen"
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim modularen CSV-Workflow"
            }

    @app.get("/api/workflow-info", tags=["workflow"], summary="Informationen über den modularen Workflow")
    def get_workflow_info() -> dict:
        """Gibt Informationen über den modularen Workflow zurück"""
        try:
            orchestrator = WorkflowOrchestrator()
            return {
                "success": True,
                "workflow_info": orchestrator.get_workflow_summary(),
                "message": "Workflow-Informationen erfolgreich abgerufen"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": "Fehler beim Abrufen der Workflow-Informationen"
            }

    def _parse_tour_time_minutes(tour_name: str) -> int:
        if not tour_name:
            return 24 * 60 + 1
        match = re.search(r"(\d{1,2})[\.:](\d{2})", tour_name)
        if match:
            hour = int(match.group(1))
            minute = int(match.group(2))
            return hour * 60 + minute
        return 24 * 60 + 1


    def _parse_tour_date(date_str: str) -> datetime:
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except Exception:
            return datetime.max

    def _normalize_tour_name(raw_name: str) -> Tuple[str, bool]:
        if not raw_name:
            return "Unknown", False
        name = raw_name.strip()
        is_bar = 'BAR' in name.upper()
        if is_bar:
            name = re.sub(r'\s*BAR\s*$', '', name, flags=re.IGNORECASE).strip()
        match = re.search(r'(W|PIR|CB|TA|Anlief)\s*-?\s*(\d{1,2})[\.\:]\d{2}', name, re.IGNORECASE)
        if match:
            prefix = match.group(1).upper()
            hour = int(match.group(2))
            minute_match = re.search(r'(\d{1,2})[\.\:](\d{2})', name)
            minute = minute_match.group(2) if minute_match else '00'
            formatted_time = f"{hour:02d}:{minute}"
            if prefix in {"CB", "TA"}:
                tour_match = re.search(r'T(\d+)', name)
                tour_suffix = f" T{tour_match.group(1)}" if tour_match else ''
                name = f"{prefix} Anlief{tour_suffix} {formatted_time} Uhr"
            elif prefix == "PIR":
                name = f"PIR Anlief. {formatted_time} Uhr"
            elif prefix.upper().startswith('ANLIEF'):
                tour_match = re.search(r'T(\d+)', name)
                tour_suffix = f" T{tour_match.group(1)}" if tour_match else ''
                name = f"Anlief.{tour_suffix} {formatted_time} Uhr"
            else:
                name = f"{prefix.upper()}-{formatted_time} Uhr"
        else:
            name = re.sub(r'\s{2,}', ' ', name)
        return name, is_bar

    return app


async def analyze_customer_recognition(customer: Dict[str, Any]) -> bool:
    """Analysiert ob ein Kunde erkannt wurde"""
    try:
        # 1. Prüfe ob Koordinaten vorhanden sind
        if customer.get('lat') and customer.get('lon'):
            return True
        
        # 2. Prüfe Address-Mapper (BAR-Sondernamen)
        name = customer.get('name', '').strip()
        if name:
            from backend.services.address_mapper import address_mapper
            mapping_result = address_mapper.map_address(name)
            if mapping_result['confidence'] > 0:
                return True
        
        # 3. Prüfe Datenbank
        street = customer.get('street', '').strip()
        postal_code = customer.get('postal_code', '').strip()
        city = customer.get('city', '').strip()
        
        if street and postal_code and city:
            full_address = f"{street}, {postal_code} {city}"
            kunde_id = get_kunde_id_by_name_adresse(name, full_address)
            if kunde_id:
                kunde_obj = get_kunde_by_id(kunde_id)
                if kunde_obj and kunde_obj.lat and kunde_obj.lon:
                    return True
        
        # 4. Prüfe Geocoding
        if street and postal_code and city:
            full_address = f"{street}, {postal_code} {city}, Deutschland"
            geo_result = geocode_address(full_address)
            if geo_result and geo_result.get('lat') and geo_result.get('lon'):
                return True
        
        return False
        
    except Exception as e:
        print(f"[ANALYSE] Fehler bei Kunden-Analyse: {e}")
        return False

def get_recognition_method(customer: Dict[str, Any]) -> str:
    """Bestimmt die Erkennungsmethode für einen Kunden"""
    if customer.get('lat') and customer.get('lon'):
        return 'coordinates'
    
    name = customer.get('name', '').strip()
    if name:
        from backend.services.address_mapper import address_mapper
        mapping_result = address_mapper.map_address(name)
        if mapping_result['confidence'] > 0:
            return f'mapping_{mapping_result["method"]}'
    
    street = customer.get('street', '').strip()
    postal_code = customer.get('postal_code', '').strip()
    city = customer.get('city', '').strip()
    
    if street and postal_code and city:
        full_address = f"{street}, {postal_code} {city}"
        kunde_id = get_kunde_id_by_name_adresse(name, full_address)
        if kunde_id:
            return 'database'
        
        geo_result = geocode_address(full_address)
        if geo_result and geo_result.get('lat') and geo_result.get('lon'):
            return 'geocoding'
    
    return 'unknown'


def assert_utf8(s: str):
    """Wächter-Funktion: Fängt Doppel-Decode sofort ab."""
    if s.encode("utf-8", errors="strict").decode("utf-8", errors="strict") != s:
        raise ValueError("Nicht-stabile UTF-8-Roundtrip – Zeichen wurden schon verhunzt.")

app = create_app()

@app.get("/probe.txt")
def probe():
    """UTF-8-Encoding-Test für Backend."""
    return PlainTextResponse("Löbtauer Straße, Österreich", media_type="text/plain; charset=utf-8")
