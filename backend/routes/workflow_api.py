from fastapi import APIRouter, HTTPException, UploadFile, File, Query, Request
from fastapi.responses import JSONResponse
from pathlib import Path
import os
import json
import re
import asyncio
import time
import uuid
import unicodedata
import sqlite3
from typing import Optional, List, Dict, Any
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import get as geo_get, upsert as geo_upsert
from backend.services.geocode import geocode_address
from services.llm_optimizer import LLMOptimizer
from services.llm_monitoring import LLMMonitoringService
from services.prompt_manager import PromptManager
from services.workflow_engine import ColumnMap, Geocoder, run_workflow
from services.osrm_client import OSRMClient
from backend.services.tour_consolidator import consolidate_t10_tours
from services.sector_planner import SectorPlanner, should_use_sector_planning
from services.uid_service import generate_tour_uid, generate_stop_uid
from services.pirna_clusterer import PirnaClusterer, PirnaClusterParams
# from backend.services.routing_optimizer import optimize_route as routing_optimize_route  # Nicht mehr verwendet - verwende optimize_tour_stops() stattdessen
from .schemas import OptimizeTourRequest
from backend.services.real_routing import build_route_details, RouteDetailsReq
from backend.utils.safe_print import safe_print
from backend.utils.file_logger import log_to_file

router = APIRouter()  # Kein Prefix, da Endpoints bereits /api/ enthalten

# Progress-Tracker für Live-Geocoding-Status
_geocoding_progress: Dict[str, Dict[str, Any]] = {}

# Telemetrie für Timebox-Validierung
_timebox_metrics = {
    "timebox_violation_total": 0,
    "osrm_unavailable": 0,
    "route_after_validation_minutes": [],  # Histogram-Daten
    "splits_performed": 0
}

# Globale Services initialisieren
llm_optimizer = LLMOptimizer()
llm_monitoring = LLMMonitoringService()
prompt_manager = PromptManager()

# OSRM-Client LAZY initialisieren (wird beim ersten Zugriff erstellt, damit config.env geladen ist)
_osrm_client_instance = None

def get_osrm_client():
    """Lazy-Initialisierung von OSRM-Client (damit config.env geladen ist)"""
    global _osrm_client_instance
    if _osrm_client_instance is None:
        import logging
        _osrm_client_instance = OSRMClient()
        log_to_file(f"[OSRM] Client initialisiert: base_url={_osrm_client_instance.base_url}, available={_osrm_client_instance.available}")
    return _osrm_client_instance

# Für Kompatibilität: osrm_client als Proxy mit Lazy-Initialisierung
class OSRMClientProxy:
    """Proxy für OSRM-Client mit Lazy-Initialisierung"""
    def __getattr__(self, name):
        client = get_osrm_client()
        attr = getattr(client, name)
        # Wenn es eine Funktion ist, gebe sie zurück (für .get_route(), etc.)
        if callable(attr):
            return attr
        # Sonst gebe den Wert zurück (für .available, etc.)
        return attr

osrm_client = OSRMClientProxy()


# Lade Tour-Ignore-Liste und Allow-Liste (Touren die nicht geplant werden sollen)
def load_tour_filter_lists() -> tuple[list, list]:
    """Lädt die Ignore-Liste und Allow-Liste aus config/tour_ignore_list.json"""
    # Berechne Pfad: Von backend/routes/workflow_api.py -> Projektroot/config/tour_ignore_list.json
    # __file__ = backend/routes/workflow_api.py
    # parent = backend/routes/
    # parent.parent = backend/
    # parent.parent.parent = Projektroot
    project_root = Path(__file__).parent.parent.parent
    ignore_file = project_root / "config" / "tour_ignore_list.json"
    
    try:
        if ignore_file.exists():
            with open(ignore_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                ignore_list = data.get("ignore_tours", [])
                allow_list = data.get("allow_tours", [])
                log_to_file(f"[WORKFLOW] Tour-Filter geladen - Ignore: {len(ignore_list)} Einträge, Allow: {len(allow_list) if allow_list else 0} Einträge")
                return ignore_list, allow_list
        else:
            log_to_file(f"[WARNUNG] Tour-Filter-Datei nicht gefunden: {ignore_file}, verwende Standard-Listen")
            # Fallback: Standard-Listen
            return ["DBD", "DPD", "DVD"], []
    except Exception as e:
        log_to_file(f"[WARNUNG] Konnte Tour-Filter-Liste nicht laden: {e}, verwende Standard-Listen")
        import traceback
        log_to_file(f"[WARNUNG] Traceback: {traceback.format_exc()}")
        return ["DBD", "DPD", "DVD"], []

def should_process_tour(tour_name: str, ignore_list: list, allow_list: list) -> bool:
    """
    Prüft ob eine Tour verarbeitet werden soll.
    
    Logik:
    1. Ignore-Liste hat IMMER Vorrang (wird zuerst geprüft)
    2. Wenn Allow-Liste vorhanden und nicht leer: Nur Touren die in Allow-Liste stehen werden verarbeitet
    3. Wenn Allow-Liste leer/fehlt: Alle Touren werden verarbeitet (außer Ignore-Liste)
    """
    if not tour_name:
        return False
    
    tour_name_upper = tour_name.upper()
    
    # 1. Ignore-Liste hat Vorrang - flexibleres Pattern-Matching
    for ignore_pattern in ignore_list:
        pattern_upper = ignore_pattern.upper()
        # Normalisiere Pattern (entferne Punkte, Leerzeichen, Backticks für flexibleres Matching)
        pattern_normalized = pattern_upper.replace('.', '').replace(' ', '').replace('`', '').replace("'", "")
        tour_normalized = tour_name_upper.replace('.', '').replace(' ', '').replace('`', '').replace("'", "")
        
        # WICHTIG: Für sehr kurze Patterns (1-2 Zeichen): Nur am Anfang oder als ganzes Wort matchen
        # Verhindert False Positives (z.B. "T" matcht nicht "Tour")
        if len(pattern_upper) <= 2:
            # Kurze Patterns: Nur am Anfang oder mit Trennzeichen (Leerzeichen, Bindestrich, Punkt)
            if (tour_name_upper.startswith(pattern_upper + ' ') or
                tour_name_upper.startswith(pattern_upper + '-') or
                tour_name_upper.startswith(pattern_upper + '.') or
                tour_name_upper.startswith(pattern_upper) and len(tour_name_upper) == len(pattern_upper) or
                f' {pattern_upper} ' in f' {tour_name_upper} ' or
                f'-{pattern_upper}' in tour_name_upper or
                f'.{pattern_upper}' in tour_name_upper):
                log_to_file(f"[FILTER] Tour '{tour_name}' ignoriert (Pattern: '{ignore_pattern}')")
                return False  # Tour wird ignoriert
        else:
            # Längere Patterns: Flexibleres Matching (wie bisher)
            if (tour_name_upper.startswith(pattern_upper) or 
                pattern_upper in tour_name_upper or
                pattern_normalized in tour_normalized or
                tour_normalized.startswith(pattern_normalized)):
                log_to_file(f"[FILTER] Tour '{tour_name}' ignoriert (Pattern: '{ignore_pattern}')")
                return False  # Tour wird ignoriert
    
    # 2. Wenn Allow-Liste vorhanden und nicht leer: Nur diese Touren erlauben
    if allow_list and len(allow_list) > 0:
        for allow_pattern in allow_list:
            if tour_name_upper.startswith(allow_pattern) or allow_pattern in tour_name_upper:
                return True  # Tour ist erlaubt
        return False  # Tour ist nicht in Allow-Liste → ignorieren
    
    # 3. Keine Allow-Liste oder leer → alle Touren erlauben (außer Ignore-Liste)
    return True


class CachedGeocoder(Geocoder):
    """
    DB-First Geocoder: Einmal geocodiert = immer aus DB (nicht anders).
    
    Workflow:
    1. Prüfe ob Koordinaten bereits im Stop vorhanden
    2. Prüfe geo_cache (Datenbank)
    3. Falls nicht gefunden: Geocode und speichere in DB
    4. Beim nächsten Mal: Direkt aus DB (Schritt 2)
    """

    def geocode(self, stop):  # type: ignore[override]
        # 1. Bereits vorhandene Koordinaten (höchste Priorität)
        if stop.lat is not None and stop.lon is not None:
            return stop.lat, stop.lon, None

        street = (stop.street or "").strip()
        postal_code = (stop.postal_code or "").strip()
        city = (stop.city or "").strip()

        address = ", ".join(
            part for part in [street, f"{postal_code} {city}".strip()] if part
        )

        if not address:
            return None, None, "Keine Adresse vorhanden"

        # 2. DB-First: Prüfe geo_cache
        cached = geo_get(address)
        if cached:
            try:
                lat = float(cached["lat"])
                lon = float(cached["lon"])
                # Gefunden in DB - direkt zurückgeben (Regel: nicht anders)
                return lat, lon, None
            except (KeyError, TypeError, ValueError):
                pass

        # 3. Nicht in DB gefunden → Geocode und speichere automatisch
        # _geocode_one speichert automatisch über write_result in geo_cache
        # Beim nächsten Mal kommt die Adresse direkt aus der DB (Schritt 2)
        try:
            import asyncio
            from services.geocode_fill import _geocode_one
            import httpx
            
            # Async Geocoding durchführen (speichert automatisch in DB)
            async def geocode_async():
                async with httpx.AsyncClient(timeout=20.0) as client:
                    return await _geocode_one(address, client, company_name=stop.customer)
            
            # Synchroner Aufruf (für synchrone API)
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Event-Loop läuft bereits → Task verwenden
                    import nest_asyncio
                    nest_asyncio.apply()
                    result = asyncio.run(geocode_async())
                else:
                    result = asyncio.run(geocode_async())
            except RuntimeError:
                # Keine Loop vorhanden → neue erstellen
                result = asyncio.run(geocode_async())
            
            if result and result.get("lat") and result.get("lon"):
                lat = float(result["lat"])
                lon = float(result["lon"])
                # Bereits in DB gespeichert durch write_result in _geocode_one
                # Nächste Tour: Direkt aus DB (Schritt 2) - Regel: nicht anders
                return lat, lon, None
            else:
                # Kein Ergebnis → bereits in Manual-Queue durch write_result
                return None, None, f"Adresse nicht gefunden: {address}"
                
        except Exception as e:
            import logging
            log_to_file(f"[CachedGeocoder] WARNUNG: Fehler bei {address}: {e}")
            return None, None, f"Geocoding-Fehler: {e}"

def _estimate_tour_time_without_return(stops: List[Dict], use_osrm: bool = True) -> float:
    """Schätzt Fahrzeit + Servicezeit für eine Tour (OHNE Rückfahrt) - verwendet OSRM wenn verfügbar"""
    if len(stops) == 0:
        return 0.0
    
    SERVICE_TIME_PER_STOP = 2.0  # Minuten
    
    # Versuche OSRM wenn verfügbar
    if use_osrm:
        client = get_osrm_client()
        if client.available:
            try:
                # Depot-Koordinaten (FAMO Dresden)
                DEPOT_LAT = 51.0111988
                DEPOT_LON = 13.7016485
                
                # Erstelle Koordinaten-Liste: Depot + alle Stopps (OHNE Rückfahrt!)
                coords = [(DEPOT_LAT, DEPOT_LON)]
                for stop in stops:
                    if stop.get('lat') and stop.get('lon'):
                        coords.append((stop.get('lat'), stop.get('lon')))
                
                if len(coords) >= 2:
                    # Hole Route vom Depot über alle Stopps (OHNE Rückfahrt!)
                    # WICHTIG: Timeout hinzufügen um Blockierung zu verhindern
                    route = client.get_route(coords, timeout=5.0)
                    if route and route.get("source") == "osrm":
                        # OSRM-Route erfolgreich
                        driving_time_minutes = route.get("duration_min", 0.0)
                        service_time_minutes = len(stops) * SERVICE_TIME_PER_STOP
                        return driving_time_minutes + service_time_minutes
            except Exception as e:
                import logging
                log_to_file(f"[TOUR-TIME] WARNUNG: OSRM-Berechnung fehlgeschlagen: {e}, verwende Fallback")
    
    # Fallback: Haversine
    DEPOT_LAT = 51.0111988
    DEPOT_LON = 13.7016485
    SPEED_KMH = 50.0  # Durchschnittsgeschwindigkeit
    SAFETY_FACTOR = 1.3  # Haversine × 1.3 für Stadtverkehr
    
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371.0  # Erdradius in km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.asin(math.sqrt(a))
        return R * c
    
    # Berechne Fahrzeit (OHNE Rückfahrt!)
    total_distance_km = 0.0
    
    # Depot → erster Kunde
    if stops[0].get('lat') and stops[0].get('lon'):
        distance = haversine_distance(
            DEPOT_LAT, DEPOT_LON,
            stops[0]['lat'], stops[0]['lon']
        )
        total_distance_km += distance
    
    # Zwischen Kunden
    for i in range(len(stops) - 1):
        if stops[i].get('lat') and stops[i].get('lon') and stops[i+1].get('lat') and stops[i+1].get('lon'):
            distance = haversine_distance(
                stops[i]['lat'], stops[i]['lon'],
                stops[i+1]['lat'], stops[i+1]['lon']
            )
            total_distance_km += distance
    
    # WICHTIG: Rückfahrt wird NICHT mitgezählt!
    
    # Konvertiere zu Zeit (mit Sicherheitsfaktor)
    driving_time_minutes = (total_distance_km * SAFETY_FACTOR / SPEED_KMH) * 60
    service_time_minutes = len(stops) * SERVICE_TIME_PER_STOP
    
    return driving_time_minutes + service_time_minutes


# Timebox-Konstanten (DoD: 65/90 Minuten)
TIME_BUDGET_WITHOUT_RETURN = int(os.getenv("TIME_BUDGET_WITHOUT_RETURN", "65"))
TIME_BUDGET_WITH_RETURN = int(os.getenv("TIME_BUDGET_WITH_RETURN", "90"))


def _estimate_back_to_depot_minutes(last_stop: Dict) -> float:
    """Schätzt Rückfahrtzeit vom letzten Stop zum Depot - verwendet OSRM wenn verfügbar"""
    if not last_stop or not last_stop.get('lat') or not last_stop.get('lon'):
        return 0.0
    
    DEPOT_LAT = 51.0111988
    DEPOT_LON = 13.7016485
    
    # Versuche OSRM wenn verfügbar
    client = get_osrm_client()
    if client.available:
        try:
            coords = [(last_stop['lat'], last_stop['lon']), (DEPOT_LAT, DEPOT_LON)]
            # WICHTIG: Timeout hinzufügen um Blockierung zu verhindern
            route = client.get_route(coords, timeout=5.0)
            if route and route.get("source") == "osrm":
                return route.get("duration_min", 0.0)
        except Exception as e:
            import logging
            log_to_file(f"[RETURN-TIME] DEBUG: OSRM-Berechnung fehlgeschlagen: {e}, verwende Fallback")
            _timebox_metrics["osrm_unavailable"] += 1
    else:
        _timebox_metrics["osrm_unavailable"] += 1
    
    # Fallback: Haversine × 1.3
    import math
    R = 6371.0  # Erdradius in km
    lat1, lon1, lat2, lon2 = map(math.radians, [
        last_stop['lat'], last_stop['lon'],
        DEPOT_LAT, DEPOT_LON
    ])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    distance_km = R * 2 * math.asin(math.sqrt(a)) * 1.3  # × 1.3 für Stadtverkehr
    SPEED_KMH = 50.0
    return (distance_km / SPEED_KMH) * 60


def materialize_tour(tour_name: str, stops: List[Dict], est_no_return: float, back_minutes: float) -> Dict:
    """Erstellt ein Tour-Dict mit allen Metadaten"""
    return {
        "tour_id": tour_name,
        "stops": stops,
        "stop_count": len(stops),
        "estimated_time_minutes": round(est_no_return, 1),
        "estimated_return_time_minutes": round(back_minutes, 1),
        "estimated_total_with_return_minutes": round(est_no_return + back_minutes, 1)
    }


def enforce_timebox(tour_name: str, stops: List[Dict], max_depth: int = 3) -> List[Dict]:
    """
    Validiert hart gegen 65/90 und splittet ggf. automatisch.
    Nutzt OSRM Table (Fallback Haversine×1.3) + Servicezeiten.
    Rückgabe: Liste materialisierter Sub‑Touren.
    
    Args:
        tour_name: Name der Tour
        stops: Liste der Stopps
        max_depth: Maximale Rekursionstiefe (Standard: 2, verhindert Endlosschleifen)
    """
    import logging
    if not stops:
        return []
    
    if max_depth <= 0:
        # Rekursionstiefe erreicht → Tour trotzdem materialisieren (besser als Endlosschleife)
        log_to_file(f"[TIMEOBOX] WARNUNG: Max. Rekursionstiefe erreicht für '{tour_name}', materialisiere trotzdem")
        est_no_return = _estimate_tour_time_without_return(stops, use_osrm=True)
        try:
            last_stop = stops[-1] if stops else None
            back_minutes = _estimate_back_to_depot_minutes(last_stop) if last_stop else 0.0
        except Exception:
            back_minutes = 0.0
        return [materialize_tour(tour_name, stops, est_no_return, back_minutes)]
    
    # Berechne Zeit OHNE Rückfahrt
    est_no_return = _estimate_tour_time_without_return(stops, use_osrm=True)
    
    # Berechne Rückfahrt
    try:
        last_stop = stops[-1] if stops else None
        back_minutes = _estimate_back_to_depot_minutes(last_stop) if last_stop else 0.0
    except Exception as e:
        log_to_file(f"[TIMEOBOX] WARNUNG: Fehler bei Rückfahrtberechnung: {e}")
        back_minutes = 0.0
    
    # Prüfe gegen Limits
    if est_no_return > TIME_BUDGET_WITHOUT_RETURN or (est_no_return + back_minutes) > TIME_BUDGET_WITH_RETURN:
        # Telemetrie: Verletzung zählen
        _timebox_metrics["timebox_violation_total"] += 1
        _timebox_metrics["splits_performed"] += 1
        
        log_to_file(
            f"[TIMEOBOX] Timebox verletzt {est_no_return:.1f}/{est_no_return+back_minutes:.1f} → splitte '{tour_name}'"
        )
        # Splitte automatisch
        # WICHTIG: _split_large_tour_in_workflow() validiert bereits intern rekursiv
        # Daher hier NICHT nochmal rekursiv validieren, um Rekursionstiefe zu vermeiden
        split_tours = _split_large_tour_in_workflow(tour_name, stops, TIME_BUDGET_WITHOUT_RETURN)
        
        # Nur Materialisierung der bereits validierten Split-Touren
        validated_subs = []
        for sub_tour in split_tours:
            sub_stops = sub_tour.get("stops", [])
            if sub_stops:
                # Berechne Zeiten für Materialisierung (aber keine weitere Validierung/Splitting)
                est_no_return = sub_tour.get("estimated_time_minutes", 
                    _estimate_tour_time_without_return(sub_stops, use_osrm=True))
                try:
                    last_stop = sub_stops[-1] if sub_stops else None
                    back_minutes = _estimate_back_to_depot_minutes(last_stop) if last_stop else 0.0
                except Exception:
                    back_minutes = 0.0
                # Materialisiere ohne weitere Rekursion
                validated_subs.append(materialize_tour(sub_tour["tour_id"], sub_stops, est_no_return, back_minutes))
            else:
                validated_subs.append(sub_tour)
        return validated_subs
    
    # Route ist OK → materialisiere
    tour_dict = materialize_tour(tour_name, stops, est_no_return, back_minutes)
    # Telemetrie: Route-Zeit speichern (für Histogram)
    _timebox_metrics["route_after_validation_minutes"].append(est_no_return)
    return [tour_dict]


def _split_large_tour_in_workflow(tour_name: str, stops: List[Dict], max_time_without_return: float, recursion_depth: int = 0) -> List[Dict]:
    """
    Splittet eine große Tour in mehrere separate Touren (A, B, C, D, E) basierend auf Zeit-Constraint.
    
    WICHTIG: Validiert jede Route nach dem Splitting und teilt sie weiter auf, falls sie zu lang ist.
    
    Args:
        recursion_depth: Aktuelle Rekursionstiefe (max. 10, verhindert Endlosschleifen)
    """
    MAX_RECURSION_DEPTH = 10
    
    if len(stops) == 0:
        return []
    
    # Schutz gegen Endlosschleifen
    if recursion_depth >= MAX_RECURSION_DEPTH:
        import logging
        log_to_file(f"[SPLIT] WARNUNG: Max. Rekursionstiefe erreicht für '{tour_name}', gebe Tour trotzdem zurück")
        # Berechne Zeit und gebe Tour zurück (auch wenn zu lang)
        client = get_osrm_client()
        use_osrm = client.available
        final_time = _estimate_tour_time_without_return(stops, use_osrm=use_osrm)
        return [{
            "tour_id": tour_name,
            "stops": stops,
            "stop_count": len(stops),
            "estimated_time_minutes": round(final_time, 1),
            "warning": f"Max. Rekursionstiefe erreicht, Route könnte zu lang sein ({final_time:.1f} Min)"
        }]
    
    # Wenn nur ein Stop übrig ist und dieser zu lang ist, gebe ihn trotzdem zurück
    if len(stops) == 1:
        client = get_osrm_client()
        use_osrm = client.available
        single_stop_time = _estimate_tour_time_without_return(stops, use_osrm=use_osrm)
        if single_stop_time > max_time_without_return:
            import logging
            log_to_file(f"[SPLIT] WARNUNG: Einzelner Stop '{tour_name}' überschreitet Limit ({single_stop_time:.1f} Min > {max_time_without_return:.1f} Min), gebe trotzdem zurück")
            return [{
                "tour_id": tour_name,
                "stops": stops,
                "stop_count": 1,
                "estimated_time_minutes": round(single_stop_time, 1),
                "warning": f"Einzelner Stop überschreitet Limit ({single_stop_time:.1f} Min)"
            }]
    
    # Extrahiere Basis-Name (z.B. "W-07.00 Uhr Tour" → "W-07.00 Uhr Tour")
    # Entferne "BAR" wenn vorhanden, behalte Rest
    base_name = re.sub(r'\s*BAR\s*$', '', tour_name, flags=re.IGNORECASE).strip()
    
    # Filtere nur Stopps mit Koordinaten
    stops_with_coords = [s for s in stops if s.get('lat') and s.get('lon')]
    
    if len(stops_with_coords) == 0:
        # Keine Koordinaten → kann nicht splitten
        return [{"tour_id": tour_name, "stops": stops, "stop_count": len(stops)}]
    
    # Verwende OSRM wenn verfügbar für bessere Genauigkeit
    client = get_osrm_client()
    use_osrm = client.available
    
    split_tours = []
    current_route = []
    # Keine Buchstaben mehr nötig - jede Route ist automatisch eine separate Tour
    
    for stop in stops_with_coords:
        # Berechne geschätzte Zeit für Route MIT neuem Stop
        test_route = current_route + [stop]
        estimated_time = _estimate_tour_time_without_return(test_route, use_osrm=use_osrm)
        
        # Prüfe ob Stop in aktuelle Route passt (OHNE Rückfahrt!)
        if estimated_time <= max_time_without_return:
            # Passt → hinzufügen
            current_route.append(stop)
        else:
            # Zu groß → neue Route starten
            if current_route:
                # Validiere aktuelle Route: Berechne exakte Zeit
                final_time = _estimate_tour_time_without_return(current_route, use_osrm=use_osrm)
                
                # Prüfe ob Route zu lang ist (OHNE Toleranz - muss exakt sein!)
                if final_time > max_time_without_return:
                    log_to_file(f"[WORKFLOW] Route {base_name} ist zu lang ({final_time:.1f} Min > {max_time_without_return:.1f} Min), teile weiter auf")
                    # Rekursiv weiter aufteilen (mit erhöhter Tiefe)
                    sub_tours = _split_large_tour_in_workflow(
                        base_name,
                        current_route,
                        max_time_without_return,
                        recursion_depth=recursion_depth + 1
                    )
                    # Verwende Sub-Touren mit korrekten Namen
                    for idx, sub_tour in enumerate(sub_tours):
                        # Keine Buchstaben mehr nötig - jede Sub-Tour ist automatisch eine separate Tour
                        sub_tour["tour_id"] = base_name
                        split_tours.append(sub_tour)
                    # Buchstaben nicht mehr nötig - jede Route ist automatisch eine separate Tour
                else:
                    # Route ist OK → speichern (OHNE Buchstaben, da Aufteilung automatisch ist)
                    new_tour_name = base_name
                    split_tours.append({
                        "tour_id": new_tour_name,
                        "stops": current_route.copy(),  # Kopie erstellen
                        "stop_count": len(current_route),
                        "estimated_time_minutes": round(final_time, 1)
                    })
                    log_to_file(f"[WORKFLOW] Route {new_tour_name} erstellt: {len(current_route)} Stopps, {final_time:.1f} Min")
                # Buchstaben nicht mehr nötig - jede Route ist automatisch eine separate Tour
            
            # Neue Route mit diesem Stop starten
            current_route = [stop]
    
    # Letzte Route hinzufügen und validieren
    # WICHTIG: Die letzte Route kann sehr lang werden, wenn viele Stopps übrig bleiben!
    # Daher: IMMER prüfen und bei Bedarf weiter aufteilen
    if current_route:
        final_time = _estimate_tour_time_without_return(current_route, use_osrm=use_osrm)
        
        log_to_file(f"[WORKFLOW] Letzte Route prüfen: {len(current_route)} Stopps, {final_time:.1f} Min (Limit: {max_time_without_return:.1f} Min)")
        
        # Falls letzte Route zu lang ist, teile sie IMMER weiter auf (keine Toleranz!)
        if final_time > max_time_without_return:
            log_to_file(f"[WORKFLOW] Letzte Route {base_name} ist zu lang ({final_time:.1f} Min > {max_time_without_return:.1f} Min), teile weiter auf")
            sub_tours = _split_large_tour_in_workflow(
                base_name,
                current_route,
                max_time_without_return,
                recursion_depth=recursion_depth + 1
            )
            # Verwende Sub-Touren mit korrekten Namen
            for idx, sub_tour in enumerate(sub_tours):
                # Keine Buchstaben mehr nötig - jede Sub-Tour ist automatisch eine separate Tour
                sub_tour["tour_id"] = base_name
                split_tours.append(sub_tour)
            log_to_file(f"[WORKFLOW] Letzte Route in {len(sub_tours)} Sub-Routen aufgeteilt")
        else:
            # Route ist OK → speichern (OHNE Buchstaben, da Aufteilung automatisch ist)
            new_tour_name = base_name
            split_tours.append({
                "tour_id": new_tour_name,
                "stops": current_route,
                "stop_count": len(current_route),
                "estimated_time_minutes": round(final_time, 1)
            })
            log_to_file(f"[WORKFLOW] Letzte Route {new_tour_name} OK: {final_time:.1f} Min")
    
    # WICHTIG: Stopps OHNE Koordinaten müssen auch verteilt werden
    # Füge sie der ersten Route hinzu (als Warnung)
    stops_without_coords = [s for s in stops if not (s.get('lat') and s.get('lon'))]
    if stops_without_coords and split_tours:
        split_tours[0]["stops"].extend(stops_without_coords)
        split_tours[0]["stop_count"] = len(split_tours[0]["stops"])
        log_to_file(f"[WORKFLOW] {len(stops_without_coords)} Stopps ohne Koordinaten zur ersten Route hinzugefügt")
    
    # Finale Validierung: Prüfe ALLE Routen nochmal und teile bei Bedarf weiter auf
    validated_tours = []
    for tour in split_tours:
        # Berechne exakte Zeit für diese Route
        final_time = _estimate_tour_time_without_return(tour["stops"], use_osrm=use_osrm)
        
        # Falls Route immer noch zu lang ist (sollte nicht passieren, aber Sicherheit)
        if final_time > max_time_without_return:
            log_to_file(f"[WORKFLOW] KRITISCH: Route {tour['tour_id']} überschreitet Limit: {final_time:.1f} Min > {max_time_without_return:.1f} Min, teile weiter auf")
            # Teile diese Route weiter auf (mit erhöhter Tiefe)
            sub_tours = _split_large_tour_in_workflow(
                tour["tour_id"],
                tour["stops"],
                max_time_without_return,
                recursion_depth=recursion_depth + 1
            )
            # Verwende Sub-Touren (OHNE Buchstaben, da Aufteilung automatisch ist)
            for idx, sub_tour in enumerate(sub_tours):
                # Keine Buchstaben mehr nötig - jede Sub-Tour ist automatisch eine separate Tour
                sub_tour["tour_id"] = tour["tour_id"]
                validated_tours.append(sub_tour)
        else:
            # Route ist OK → speichern mit exakter Zeit
            tour["estimated_time_minutes"] = round(final_time, 1)
            validated_tours.append(tour)
    
    # Logging: Zeige Zusammenfassung
    if len(validated_tours) > 0:
        log_to_file(f"[WORKFLOW] Tour {tour_name} in {len(validated_tours)} Routen aufgeteilt:")
        for tour in validated_tours:
            log_to_file(f"  - {tour['tour_id']}: {tour.get('stop_count', 0)} Stopps, {tour.get('estimated_time_minutes', 0):.1f} Min")
    
    return validated_tours if validated_tours else [{"tour_id": tour_name, "stops": stops, "stop_count": len(stops)}]


def _apply_sector_planning_to_w_tour(tour_name: str, stops_with_coords: List[Dict], all_stops: List[Dict]) -> List[Dict]:
    """
    Wendet automatische Sektor-Planung auf W-Tour an (Teil der normalen Routing-Optimierung).
    
    Prozess:
    1. Sektorisierung: Teilt Stopps nach N/O/S/W (feste Cluster) - NUR INTERN
    2. Pro Sektor: Erstellt Sub-Routen mit Zeitbox (07:00 → 09:00)
    3. Gibt separate Touren zurück mit ORIGINAL-NAMEN (z.B. "W-07.00 Uhr Tour", "W-07.00 Uhr Tour A", etc.)
    
    WICHTIG: Tour-Namen werden NICHT umbenannt! Die Sektoren (N/O/S/W) sind nur interne Organisation.
    Die Sektor-Information wird als Metadaten gespeichert, aber der Tour-Name bleibt gleich.
    
    Alle Stopps bleiben in ihrem Sektor - es werden keine Stopps zwischen Sektoren verschoben.
    """
    depot_lat = 51.0111988
    depot_lon = 13.7016485
    
    # Initialisiere SectorPlanner
    sector_planner = SectorPlanner(osrm_client)
    
    # Schritt 1: Konvertiere Stopps zu Format für SectorPlanner (mit stop_uid)
    stops_for_sectorizer = []
    stop_mapping = {}  # stop_uid → original_stop
    
    for idx, stop in enumerate(stops_with_coords):
        # Generiere stop_uid basierend auf customer_number, name, address
        source_id = stop.get('customer_number') or stop.get('order_id') or f"stop_{idx}"
        address = stop.get('address', '')
        postal_code = stop.get('postal_code', '')
        city = stop.get('city', '')
        
        # Normalisiere Adresse für UID (wie in uid_service)
        normalized_address = address.strip().upper() if address else ""
        normalized_plz = postal_code.strip() if postal_code else ""
        normalized_city = city.strip().upper() if city else ""
        
        # Generiere stop_uid (vereinfacht - sollte eigentlich generate_stop_uid verwenden)
        uid_input = f"{source_id}|{normalized_address}|{normalized_plz}|{normalized_city}"
        import hashlib
        stop_uid = f"sha256:{hashlib.sha256(uid_input.encode('utf-8')).hexdigest()[:16]}"
        
        stops_for_sectorizer.append({
            "stop_uid": stop_uid,
            "lat": float(stop['lat']),
            "lon": float(stop['lon'])
        })
        
        stop_mapping[stop_uid] = stop
    
    if len(stops_for_sectorizer) < 2:
        # Zu wenige Stopps für Sektor-Planung
        return []
    
    # Schritt 2: Sektorisierung (N/O/S/W) - FESTE CLUSTER
    try:
        stops_with_sectors = sector_planner.sectorize_stops(
            stops_for_sectorizer,
            depot_lat,
            depot_lon,
            sectors=4  # N, O, S, W
        )
    except Exception as e:
        log_to_file(f"[WORKFLOW] Fehler bei Sektorisierung: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    # Schritt 3: Gruppiere Stopps nach Sektor (FESTE CLUSTER - keine Verschiebung zwischen Sektoren)
    stops_by_sector = {"N": [], "O": [], "S": [], "W": []}
    for stop_ws in stops_with_sectors:
        sector = stop_ws.sector.value
        stops_by_sector[sector].append(stop_ws)
    
    log_to_file(f"[WORKFLOW] Sektorisierung abgeschlossen: N={len(stops_by_sector['N'])}, O={len(stops_by_sector['O'])}, S={len(stops_by_sector['S'])}, W={len(stops_by_sector['W'])}")
    
    # Schritt 4: Planung pro Sektor (mit Zeitbox 07:00 → 09:00)
    from services.sector_planner import SectorPlanParams
    
    params = SectorPlanParams(
        depot_uid="depot_uid",
        depot_lat=depot_lat,
        depot_lon=depot_lon,
        start_time="07:00",
        hard_deadline="09:00",
        # Harte Timebox ohne Rückfahrt (DoD): 65 Minuten
        time_budget_minutes=65.0,
        service_time_default=2.0,
        service_time_per_stop={},
        include_return_to_depot=True,
        sectors=4
    )
    
    sector_tours = []
    sector_names = {"N": "Nord", "O": "Ost", "S": "Süd", "W": "West"}
    
    for sector, stops_in_sector in stops_by_sector.items():
        if not stops_in_sector:
            continue
        
        try:
            # Planung für diesen Sektor (erstellt automatisch Sub-Routen wenn zu groß)
            routes = sector_planner.plan_by_sector(stops_in_sector, params)
            
            # Konvertiere Routes zu Tour-Format
            for route_idx, route in enumerate(routes):
                # WICHTIG: Tour-Name NICHT ändern! Jede Route ist automatisch eine separate Tour.
                # Keine Buchstaben mehr nötig, da Aufteilung automatisch erfolgt.
                tour_name_final = tour_name  # Original-Name beibehalten
                
                # Konvertiere route_uids zurück zu originalen Stopps (in richtiger Reihenfolge)
                tour_stops = []
                for route_uid in route.route_uids:
                    if route_uid == "depot_uid":
                        continue  # Depot wird nicht als Stop hinzugefügt (wird visuell auf Karte gezeigt)
                    # Finde originalen Stop
                    original_stop = stop_mapping.get(route_uid)
                    if original_stop:
                        tour_stops.append(original_stop)
                
                # Füge auch Stopps ohne Koordinaten hinzu (wenn vorhanden) - zur ersten Route
                if route_idx == 0:  # Nur zur ersten Route des Sektors
                    stops_without_coords = [s for s in all_stops if not (s.get('lat') and s.get('lon'))]
                    if stops_without_coords:
                        tour_stops.extend(stops_without_coords)
                
                # WICHTIG: Zeiten korrekt zuordnen
                # route.total_time_minutes = Fahrzeit OHNE Rückfahrt + Servicezeit
                # route.meta.get("total_time_with_return") = Gesamtzeit INKL. Rückfahrt
                return_time = route.meta.get("return_time_minutes", 0.0)
                total_with_return = route.meta.get("total_time_with_return", route.total_time_minutes + return_time)
                is_validated = route.meta.get("validated", True)  # Validierungs-Flag aus Route
                
                # ✅ KRITISCHE VALIDIERUNG: Route MUSS ≤ 65 Min OHNE Rückfahrt sein!
                if route.total_time_minutes > 65.0:
                    log_to_file(f"❌ FEHLER: {tour_name_final} überschreitet 65 Min OHNE Rückfahrt: {route.total_time_minutes:.1f} Min → TEILE AUF!")
                    # Route ist zu lang → TEILE AUF mit enforce_timebox()
                    split_tours = enforce_timebox(tour_name_final, tour_stops, max_depth=3)
                    # Füge aufgeteilte Touren hinzu (statt der zu langen Tour)
                    for split_tour in split_tours:
                        sector_tours.append({
                            "tour_id": split_tour.get("tour_id", tour_name_final),
                            "stops": split_tour.get("stops", tour_stops),
                            "stop_count": split_tour.get("stop_count", len(tour_stops)),
                            "sector": sector,
                            "sector_name": sector_names[sector],
                            "estimated_driving_time_minutes": split_tour.get("estimated_driving_time_minutes", 0),
                            "estimated_service_time_minutes": split_tour.get("estimated_service_time_minutes", 0),
                            "estimated_total_time_minutes": split_tour.get("estimated_time_minutes", 0),
                            "estimated_return_time_minutes": split_tour.get("estimated_return_time_minutes", 0),
                            "estimated_total_with_return_minutes": split_tour.get("estimated_total_with_return_minutes", 0),
                            "is_validated": True,
                            "is_sector_route": True,
                            "was_split": True  # Flag: Tour wurde aufgeteilt
                        })
                    continue  # Überspringe die ursprüngliche Tour (wurde bereits aufgeteilt)
                
                if total_with_return > 90.0:
                    log_to_file(f"⚠️ WARNUNG: {tour_name_final} überschreitet 90 Min INKL. Rückfahrt: {total_with_return:.1f} Min (aber OHNE Rückfahrt OK: {route.total_time_minutes:.1f} Min)")
                
                sector_tours.append({
                    "tour_id": tour_name_final,  # Original-Name (ohne "Nord", "Ost", etc.)
                    "stops": tour_stops,
                    "stop_count": len(tour_stops),
                    "sector": sector,  # Sektor als Metadaten (N/O/S/W) - für interne Organisation
                    "sector_name": sector_names[sector],  # "Nord", "Ost", "Süd", "West" (nur für Anzeige)
                    "estimated_driving_time_minutes": round(route.driving_time_minutes, 1),  # OHNE Rückfahrt
                    "estimated_service_time_minutes": round(route.service_time_minutes, 1),
                    "estimated_total_time_minutes": round(route.total_time_minutes, 1),  # OHNE Rückfahrt
                    "estimated_return_time_minutes": round(return_time, 1),  # Rückfahrt separat
                    "estimated_total_with_return_minutes": round(total_with_return, 1),  # INKL. Rückfahrt
                    "is_validated": is_validated,  # Validierungs-Flag
                    "is_sector_route": True  # Flag für Frontend
                })
                
                status_icon = "✅" if is_validated else "⚠️"
                log_to_file(f"{status_icon} [WORKFLOW] Sektor-Route erstellt: {tour_name_final} ({sector_names[sector]}, {len(tour_stops)} Stopps, {route.total_time_minutes:.1f} Min OHNE Rückfahrt, {total_with_return:.1f} Min INKL. Rückfahrt)")
        
        except Exception as e:
            log_to_file(f"[WORKFLOW] Fehler bei Planung für Sektor {sector}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    return sector_tours


def _apply_pirna_clustering_to_tour(tour_name: str, stops_with_coords: List[Dict], all_stops: List[Dict]) -> List[Dict]:
    """
    Wendet automatisches PIRNA-Clustering auf PIR-Tour an (Teil der normalen Routing-Optimierung).
    
    Problem: PIR-Touren werden oft in zu viele kleine Routen aufgeteilt (z.B. 3 Personen mit je 3 Stopps).
    Lösung: Gruppierung nach geografischer Nähe, damit weniger Routen mit mehr Stopps entstehen.
    
    Prozess:
    1. Clustering: Gruppiert Stopps nach geografischer Nähe (max. 8 Stopps pro Cluster, max. 90 Min)
    2. Erstellt separate Touren pro Cluster: "PIR-07.00 Tour Cluster 1", "PIR-07.00 Tour Cluster 2", etc.
    """
    depot_lat = 51.0111988
    depot_lon = 13.7016485
    
    # Initialisiere PirnaClusterer
    clusterer = PirnaClusterer(osrm_client)
    
    # Schritt 1: Konvertiere Stopps zu Format für Clusterer
    stops_for_clusterer = []
    stop_mapping = {}  # stop_uid → original_stop
    
    for idx, stop in enumerate(stops_with_coords):
        # Generiere stop_uid basierend auf customer_number, name, address
        source_id = stop.get('customer_number') or stop.get('order_id') or f"stop_{idx}"
        address = stop.get('address', '')
        postal_code = stop.get('postal_code', '')
        city = stop.get('city', '')
        
        # Normalisiere Adresse für UID
        normalized_address = address.strip().upper() if address else ""
        normalized_plz = postal_code.strip() if postal_code else ""
        normalized_city = city.strip().upper() if city else ""
        
        # Generiere stop_uid
        uid_input = f"{source_id}|{normalized_address}|{normalized_plz}|{normalized_city}"
        import hashlib
        stop_uid = f"sha256:{hashlib.sha256(uid_input.encode('utf-8')).hexdigest()[:16]}"
        
        stops_for_clusterer.append({
            "stop_uid": stop_uid,
            "lat": float(stop['lat']),
            "lon": float(stop['lon']),
            "name": stop.get('customer') or stop.get('name', 'Unbekannt'),
            "customer_number": stop.get('customer_number') or stop.get('order_id', ''),
            "address": stop.get('address', ''),
            "street": stop.get('street', ''),
            "postal_code": stop.get('postal_code', ''),
            "city": stop.get('city', ''),
            "bar_flag": stop.get('bar_flag', False)
        })
        
        stop_mapping[stop_uid] = stop
    
    if len(stops_for_clusterer) < 2:
        # Zu wenige Stopps für Clustering
        return []
    
    # Schritt 2: Clustering durchführen
    params = PirnaClusterParams(
        depot_uid="depot_uid",
        depot_lat=depot_lat,
        depot_lon=depot_lon,
        max_stops_per_cluster=15,  # Max. 15 Stopps pro Cluster (verhindert zu frühes Aufteilen)
        # Harte Timebox ohne Rückfahrt (DoD): 65 Minuten
        max_time_per_cluster_minutes=65,  # Max. 65 Minuten pro Cluster (ohne Rückfahrt)
        service_time_default=2.0,
        service_time_per_stop={},
        include_return_to_depot=True
    )
    
    try:
        clusters = clusterer.cluster_stops(stops_for_clusterer, params)
    except Exception as e:
        log_to_file(f"[WORKFLOW] Fehler bei Clustering: {e}")
        import traceback
        traceback.print_exc()
        return []
    
    if not clusters:
        return []
    
    log_to_file(f"[WORKFLOW] PIRNA-Clustering abgeschlossen: {len(stops_for_clusterer)} Stopps → {len(clusters)} Cluster")
    
    # Schritt 3: Konvertiere Cluster zu Tour-Format
    clustered_tours = []
    
    for cluster_idx, cluster in enumerate(clusters):
        # Erstelle Tour-Name: "PIR-07.00 Tour Cluster 1", "PIR-07.00 Tour Cluster 2", etc.
        cluster_tour_name = f"{tour_name} Cluster {cluster.cluster_id}"
        
        # Konvertiere Cluster-Stopps zurück zu originalen Stopps (in richtiger Reihenfolge)
        tour_stops = []
        for cluster_stop in cluster.stops:
            stop_uid = cluster_stop.get('stop_uid')
            original_stop = stop_mapping.get(stop_uid)
            if original_stop:
                tour_stops.append(original_stop)
        
        # Füge auch Stopps ohne Koordinaten hinzu (wenn vorhanden) - nur zum ersten Cluster
        if cluster_idx == 0:
            stops_without_coords = [s for s in all_stops if not (s.get('lat') and s.get('lon'))]
            if stops_without_coords:
                tour_stops.extend(stops_without_coords)
        
        clustered_tours.append({
            "tour_id": cluster_tour_name,
            "stops": tour_stops,
            "stop_count": len(tour_stops),
            "cluster_id": cluster.cluster_id,
            "estimated_time_minutes": round(cluster.estimated_time_minutes, 1),
            "is_clustered_route": True  # Flag für Frontend
        })
        
        log_to_file(f"[WORKFLOW] PIRNA-Cluster-Route erstellt: {cluster_tour_name} ({len(tour_stops)} Stopps, {cluster.estimated_time_minutes:.1f} Min)")
    
    return clustered_tours


def optimize_tour_stops(stops, use_llm: bool = True):
    """Optimiert die Reihenfolge der Stops in einer Tour"""
    if not stops or len(stops) <= 1:
        return stops
    
    # Filtere Stops mit Koordinaten
    valid_stops = [stop for stop in stops if stop.get('lat') and stop.get('lon')]
    if len(valid_stops) <= 1:
        return stops
    
    # LLM-Optimierung falls verfügbar
    if use_llm and llm_optimizer.enabled:
        try:
            result = llm_optimizer.optimize_route(valid_stops, region="Dresden")
            
            # Logge LLM-Interaktion
            llm_monitoring.log_interaction(
                model=result.model_used,
                task_type="route_optimization",
                prompt="Route optimization prompt",
                response=result.reasoning,
                tokens_used={"total_tokens": result.tokens_used},
                processing_time=result.processing_time,
                success=True,
                metadata={"confidence_score": result.confidence_score}
            )
            
            # Verwende optimierte Route falls Confidence hoch genug
            if result.confidence_score > 0.7:
                return [valid_stops[i] for i in result.optimized_route]
            
        except Exception as e:
            log_to_file(f"LLM optimization failed, using fallback: {e}")
    
    # Fallback: Nearest-Neighbor Optimierung
    import math
    
    def haversine_distance(lat1, lon1, lat2, lon2):
        R = 6371000.0  # Erdradius in Metern
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        return 2 * R * math.asin(math.sqrt(a))
    
    # Starte mit dem ersten Stop
    optimized = [valid_stops[0]]
    remaining = valid_stops[1:]
    
    while remaining:
        last_stop = optimized[-1]
        # Finde den nächsten Stop
        nearest_idx = min(range(len(remaining)), 
                        key=lambda i: haversine_distance(
                            last_stop['lat'], last_stop['lon'],
                            remaining[i]['lat'], remaining[i]['lon']
                        ))
        optimized.append(remaining.pop(nearest_idx))
    
    return optimized

@router.post("/api/workflow/complete")
async def complete_workflow(
    filename: str = Query(..., description="Name der CSV-Datei im Tourplaene-Verzeichnis")
):
    """
    Kompletter Workflow: Parse → Geocode → Optimize
    
    Verarbeitet eine CSV-Datei aus dem Tourplaene-Verzeichnis und führt
    den kompletten Workflow durch: Parsing, Geocoding und Routen-Optimierung.
    """
    try:
        # Dateipfad validieren
        tourplaene_dir = Path(os.getenv("ORIG_DIR", "./tourplaene"))
        csv_path = tourplaene_dir / filename
        
        if not csv_path.exists():
            raise HTTPException(404, detail=f"Datei nicht gefunden: {filename}")
        
        if not csv_path.suffix.lower() == '.csv':
            raise HTTPException(400, detail="Nur CSV-Dateien werden unterstützt")
        
        # Verwende bestehenden Parser
        tour_data = parse_tour_plan_to_dict(str(csv_path))
        
        # Zähle OK/Warn/Bad
        ok_count = 0
        warn_count = 0
        bad_count = 0
        warnings = []
        errors = []
        
        optimized_tours = []
        
        for tour in tour_data.get('tours', []):
            customers = tour.get('customers', [])
            
            # Geocode fehlende Adressen
            for customer in customers:
                if customer.get('lat') and customer.get('lon'):
                    ok_count += 1
                else:
                    # Versuche Geocoding
                    address = customer.get('address', '')
                    if address:
                        geo_result = geo_get(address)
                        if geo_result:
                            customer['lat'] = geo_result['lat']
                            customer['lon'] = geo_result['lon']
                            ok_count += 1
                        else:
                            warn_count += 1
                            warnings.append(f"Keine Koordinaten für {customer.get('name', 'Unbekannt')} - {address}")
                    else:
                        # Keine Adresse - aber Kunde wird trotzdem hinzugefügt (z.B. für PF-Kunden ohne Synonym)
                        # WICHTIG: Nicht als kritischer Fehler behandeln, sondern als Warnung
                        warn_count += 1  # Ändere von bad_count zu warn_count
                        warnings.append(f"Keine Adresse für {customer.get('name', 'Unbekannt')}")  # Ändere von errors zu warnings
                
                # Optimiere Tour-Reihenfolge mit LLM
                optimized_customers = optimize_tour_stops(customers, use_llm=True)
                
                # WICHTIG: Workflow soll NUR zusammenfassen, NICHT aufteilen!
                # Die Aufteilung erfolgt erst bei der Routen-Optimierung.
                tour_name = tour.get('name', 'Unbekannt')
                # Jede Route bekommt eine eindeutige Farbe basierend auf ihrem Index
                route_index = len(optimized_tours)  # Index für Farbzuweisung
                tour_dict = {
                    "tour_id": tour_name,
                    "stops": optimized_customers,
                    "stop_count": len(optimized_customers),
                    "estimated_time_minutes": None,  # Wird bei Optimierung berechnet
                    "estimated_return_time_minutes": None,
                    "estimated_total_with_return_minutes": None,
                    "_route_index": route_index  # Eindeutiger Index für Farbzuweisung
                }
                optimized_tours.append(tour_dict)
        
        # LLM-Performance-Report
        llm_performance = llm_optimizer.get_performance_report()
        llm_metrics = llm_monitoring.get_performance_metrics(days=1)
        
        return JSONResponse({
            "success": True,
            "filename": filename,
            "status": f"Workflow erfolgreich. {ok_count} OK, {warn_count} Warn, {bad_count} Bad",
            "counts": {
                "ok": ok_count,
                "warn": warn_count,
                "bad": bad_count
            },
            "warnings": warnings,
            "errors": errors,
            "tours": optimized_tours,
            "tour_count": len(optimized_tours),
            "total_stops": sum(tour["stop_count"] for tour in optimized_tours),
            "llm_performance": llm_performance,
            "llm_metrics": llm_metrics.__dict__ if hasattr(llm_metrics, '__dict__') else llm_metrics
        }, media_type="application/json; charset=utf-8")
        
    except Exception as e:
        log_to_file(f"[WORKFLOW ERROR] {e}")
        raise HTTPException(500, detail=f"Workflow-Fehler: {str(e)}")

@router.get("/api/workflow/geocoding-progress/{session_id}")
async def get_geocoding_progress(session_id: str):
    """
    Liefert den aktuellen Geocoding-Progress für eine Session.
    """
    progress = _geocoding_progress.get(session_id, {
        "total": 0,
        "processed": 0,
        "current": "",
        "status": "idle"
    })
    return JSONResponse(progress)

@router.post("/api/workflow/upload")
async def workflow_upload(file: UploadFile = File(...)):
    """
    Workflow mit Upload-Datei
    
    Verarbeitet eine hochgeladene CSV-Datei und führt den kompletten Workflow durch.
    Zeigt Live-Progress beim Geocoding.
    """
    # Session-ID für Progress-Tracking
    session_id = str(uuid.uuid4())
    _geocoding_progress[session_id] = {
        "total": 0,
        "processed": 0,
        "current": "",
        "status": "parsing",
        "db_hits": 0,
        "geoapify_calls": 0,
        "errors": 0
    }
    
    try:
        if not file.filename:
            raise HTTPException(400, detail="Kein Dateiname angegeben")
        
        if not file.filename.lower().endswith('.csv'):
            raise HTTPException(400, detail="Nur CSV-Dateien werden unterstützt")
        
        # Datei lesen
        content = await file.read()
        
        # Prüfe ob TEHA-Format (Tourenübersicht/Lieferdatum Header)
        content_str = content.decode('utf-8-sig', errors='replace')[:2000]
        is_teha_format = (
            "Tourenübersicht" in content_str or 
            "Tourenbersicht" in content_str or  # Ohne Umlaut
            "Lieferdatum:" in content_str or
            ("Kdnr" in content_str and "PLZ" in content_str and "Ort" in content_str)
        )
        
        if is_teha_format:
            # TEHA-Format: Verwende parse_tour_plan_to_dict
            from pathlib import Path
            import os
            import time
            import logging
            log_to_file(f"[WORKFLOW] TEHA-Format erkannt, Datei: {file.filename}")
            
            # Temporäre Datei für Parser (auf Windows: robuste Datei-Handhabung)
            tmp_path = None
            try:
                # Erstelle temporäre Datei im staging-Verzeichnis (absoluter Pfad)
                staging_dir_env = os.getenv("STAGING_DIR", "./data/staging")
                staging_dir = Path(staging_dir_env).resolve()
                staging_dir.mkdir(parents=True, exist_ok=True)
                
                # Eindeutiger Dateiname (ohne Sonderzeichen, die Probleme verursachen könnten)
                timestamp = int(time.time() * 1000)
                safe_filename = re.sub(r'[<>:"/\\|?*]', '_', file.filename)  # Ersetze gefährliche Zeichen
                # WICHTIG: Kürze Dateiname falls zu lang (Windows MAX_PATH = 260 Zeichen)
                # Berücksichtige: staging_dir + "workflow_temp_" + timestamp + "_" + filename
                max_filename_length = 100  # Max. 100 Zeichen für Dateinamen
                if len(safe_filename) > max_filename_length:
                    name_part = safe_filename[:max_filename_length-4]  # Platz für ".csv"
                    ext = safe_filename[-4:] if safe_filename.endswith('.csv') else '.csv'
                    safe_filename = name_part + ext
                    log_to_file(f"[WORKFLOW] WARNUNG: Dateiname gekürzt auf {max_filename_length} Zeichen: {safe_filename}")
                tmp_filename = f"workflow_temp_{timestamp}_{safe_filename}"
                tmp_path = staging_dir / tmp_filename
                
                # Prüfe Gesamt-Pfad-Länge (Windows MAX_PATH = 260 Zeichen)
                tmp_path_str = str(tmp_path.resolve())
                if len(tmp_path_str) > 260:
                    log_to_file(f"[WORKFLOW] WARNUNG: Pfad zu lang ({len(tmp_path_str)} Zeichen): {tmp_path_str[:100]}...")
                    # Kürze Dateinamen noch mehr falls nötig
                    max_safe_length = 50
                    if len(safe_filename) > max_safe_length:
                        name_part = safe_filename[:max_safe_length-4]
                        ext = safe_filename[-4:] if safe_filename.endswith('.csv') else '.csv'
                        safe_filename = name_part + ext
                        tmp_filename = f"workflow_temp_{timestamp}_{safe_filename}"
                        tmp_path = staging_dir / tmp_filename
                        log_to_file(f"[WORKFLOW] Dateiname weiter gekürzt auf {max_safe_length} Zeichen")
                
                # Schreibe Datei mit explizitem Flush und Schließen
                try:
                    file_handle = None
                    try:
                        file_handle = open(tmp_path, 'wb')
                        file_handle.write(content)
                        file_handle.flush()  # Zwinge Write zum Disk
                        # os.fsync() kann Errno 22 werfen bei ungültigen Pfaden/Dateinamen → optional
                        try:
                            os.fsync(file_handle.fileno())  # Synchronisiere mit Filesystem
                        except OSError as fsync_error:
                            # Errno 22: Invalid argument (z.B. zu langer Pfad, ungültige Zeichen)
                            log_to_file(f"[WORKFLOW] WARNUNG: os.fsync() fehlgeschlagen (nicht kritisch): {fsync_error}")
                            # Datei wurde trotzdem geschrieben (flush() reicht)
                    finally:
                        if file_handle:
                            file_handle.close()
                            file_handle = None  # Explizit auf None setzen
                    
                    # WICHTIG: Warte, damit Windows das File-Handle sicher freigibt
                    time.sleep(0.2)
                except Exception as write_error:
                    # Fallback: Verwende System-Temp-Verzeichnis
                    import tempfile as tf
                    temp_dir = Path(tf.gettempdir())
                    tmp_path = temp_dir / tmp_filename
                    log_to_file(f"[WORKFLOW] WARNUNG: Staging-Verzeichnis Fehler, verwende Temp: {write_error}")
                    
                    file_handle = None
                    try:
                        file_handle = open(tmp_path, 'wb')
                        file_handle.write(content)
                        file_handle.flush()
                        # os.fsync() kann Errno 22 werfen bei ungültigen Pfaden/Dateinamen → optional
                        try:
                            os.fsync(file_handle.fileno())
                        except OSError as fsync_error:
                            # Errno 22: Invalid argument (z.B. zu langer Pfad, ungültige Zeichen)
                            log_to_file(f"[WORKFLOW] WARNUNG: os.fsync() fehlgeschlagen (nicht kritisch): {fsync_error}")
                            # Datei wurde trotzdem geschrieben (flush() reicht)
                    finally:
                        if file_handle:
                            file_handle.close()
                            file_handle = None
                    time.sleep(0.2)
                
                # Prüfe ob Datei existiert und lesbar ist
                if not tmp_path.exists():
                    raise Exception(f"Temporäre Datei konnte nicht erstellt werden: {tmp_path}")
                
                # Versuche Datei mehrmals zu öffnen (Test ob sie nicht gesperrt ist)
                max_attempts = 5
                for attempt in range(max_attempts):
                    try:
                        test_handle = open(tmp_path, 'rb')
                        test_handle.read(1)  # Lese ein Byte
                        test_handle.close()
                        break  # Erfolgreich geöffnet
                    except (PermissionError, OSError) as e:
                        if attempt < max_attempts - 1:
                            time.sleep(0.3)  # Warte länger bei jedem Versuch
                        else:
                            # Beim letzten Versuch: Fehler werfen
                            raise Exception(f"Datei konnte nach {max_attempts} Versuchen nicht geöffnet werden: {tmp_path}. Fehler: {e}")
                
                # Pfad als String normalisieren (absolute Pfad für Windows, aber ohne Long-Path-Präfix)
                tmp_path_absolute = tmp_path.resolve()
                tmp_path_str = str(tmp_path_absolute)
                # Falls Long-Path-Präfix vorhanden, entferne es
                if tmp_path_str.startswith('\\\\?\\'):
                    tmp_path_str = tmp_path_str[4:]
                
                # Verwende bestehenden TEHA-Parser
                try:
                    tour_data = parse_tour_plan_to_dict(tmp_path_str)
                except Exception as parse_error:
                    import traceback
                    error_trace = traceback.format_exc()
                    log_to_file(f"[WORKFLOW] FEHLER: Parser-Fehler für {tmp_path_str}: {parse_error}")
                    raise Exception(f"Parser-Fehler: {str(parse_error)}. Datei: {tmp_path_str}")
                
                # Geocode fehlende Adressen
                ok_count = 0
                warn_count = 0
                bad_count = 0
                warnings = []
                errors = []
                
                optimized_tours = []
                
                # Berechne Gesamtanzahl für Progress-Tracking
                total_customers = sum(len(tour.get('customers', [])) for tour in tour_data.get('tours', []))
                _geocoding_progress[session_id]["total"] = total_customers
                _geocoding_progress[session_id]["status"] = "geocoding"
                
                processed_count = 0
                
                for tour in tour_data.get('tours', []):
                    customers = tour.get('customers', [])
                    
                    # Geocode fehlende Adressen - ABER: ALLE Kunden behalten (auch ohne Koordinaten)
                    all_customers_for_tour = []
                    for customer in customers:
                        processed_count += 1
                        customer_name = customer.get('name', 'Unbekannt')
                        _geocoding_progress[session_id]["processed"] = processed_count
                        _geocoding_progress[session_id]["current"] = f"Verarbeite: {customer_name} ({processed_count}/{total_customers})"
                        # Prüfe ob Koordinaten bereits vorhanden sind (z.B. aus Synonymen im Parser)
                        # Prüfe auf Koordinaten (aus Synonymen oder bereits vorhanden)
                        has_coords = bool(customer.get('lat') and customer.get('lon'))
                        warning_message = None
                        
                        if has_coords:
                            # Koordinaten bereits vorhanden (z.B. aus Synonymen im Parser)
                            log_to_file(f"[WORKFLOW] Kunde {customer.get('name', '?')} hat bereits Koordinaten: lat={customer.get('lat')}, lon={customer.get('lon')}")
                            # Koordinaten bereits vorhanden (z.B. aus Synonymen) → direkt verwenden
                            # Aber: Speichere auch in geo_cache für zukünftige Verwendung
                            address = customer.get('address', '')
                            if not address:
                                street = customer.get('street', '').strip()
                                postal_code = customer.get('postal_code', '').strip()
                                city = customer.get('city', '').strip()
                                if street or postal_code or city:
                                    address = ", ".join(filter(None, [street, f"{postal_code} {city}".strip()]))
                            
                            if address:
                                # Prüfe ob bereits in geo_cache, wenn nicht: speichere
                                existing = geo_get(address)
                                if not existing:
                                    lat = float(customer.get('lat'))
                                    lon = float(customer.get('lon'))
                                    geo_upsert(
                                        address=address,
                                        lat=lat,
                                        lon=lon,
                                        source="synonym",  # Markiere als Synonym-basiert
                                        company_name=customer.get('name')
                                    )
                                    log_to_file(f"[GEOCODE] Synonym-Koordinaten in geo_cache gespeichert: {address} -> ({lat}, {lon})")
                            
                            ok_count += 1
                            _geocoding_progress[session_id]["db_hits"] = _geocoding_progress[session_id].get("db_hits", 0) + 1
                        elif not has_coords:
                            # Versuche Geocoding
                            address = customer.get('address', '')
                            if not address:
                                # Baue Adresse aus Street/PLZ/City
                                street = customer.get('street', '').strip()
                                postal_code = customer.get('postal_code', '').strip()
                                city = customer.get('city', '').strip()
                                if street or postal_code or city:
                                    address = ", ".join(filter(None, [street, f"{postal_code} {city}".strip()]))
                            
                            if address:
                                # SCHRITT 1: Zuerst DB prüfen (schnell)
                                geo_result = geo_get(address)
                                
                                if geo_result:
                                    # In DB gefunden → direkt verwenden
                                    customer['lat'] = geo_result['lat']
                                    customer['lon'] = geo_result['lon']
                                    ok_count += 1
                                    has_coords = True
                                    _geocoding_progress[session_id]["db_hits"] = _geocoding_progress[session_id].get("db_hits", 0) + 1
                                    log_to_file(f"[GEOCODE] OK DB-Hit: {address} -> ({geo_result['lat']}, {geo_result['lon']})")
                                else:
                                    # Nicht in DB → Geoapify aufrufen (live während Upload)
                                    _geocoding_progress[session_id]["current"] = f"Geoapify: {customer_name} ({processed_count}/{total_customers})"
                                    log_to_file(f"[GEOCODE] DB-Miss: {address}, rufe Geoapify auf...")
                                    geo_result = geocode_address(address)
                                    _geocoding_progress[session_id]["geoapify_calls"] = _geocoding_progress[session_id].get("geoapify_calls", 0) + 1
                                    
                                    if geo_result and geo_result.get('lat') and geo_result.get('lon'):
                                        # Geoapify erfolgreich → direkt in DB speichern
                                        lat = float(geo_result['lat'])
                                        lon = float(geo_result['lon'])
                                        geo_upsert(
                                            address=address,
                                            lat=lat,
                                            lon=lon,
                                            source="geoapify",
                                            company_name=customer.get('name')
                                        )
                                        customer['lat'] = lat
                                        customer['lon'] = lon
                                        ok_count += 1
                                        has_coords = True
                                        _geocoding_progress[session_id]["current"] = f"Gespeichert: {customer_name} ({processed_count}/{total_customers})"
                                        log_to_file(f"[GEOCODE] OK Geoapify + DB-Save: {address} -> ({lat}, {lon})")
                                        # Kurze Pause für Rate Limiting
                                        await asyncio.sleep(0.2)
                                    else:
                                        # Auch Geoapify fehlgeschlagen
                                        warn_count += 1
                                        _geocoding_progress[session_id]["errors"] = _geocoding_progress[session_id].get("errors", 0) + 1
                                        warning_message = f"Keine Koordinaten für {customer.get('name', 'Unbekannt')} - {address}"
                                        warnings.append(warning_message)
                                        _geocoding_progress[session_id]["current"] = f"Fehler: {customer_name} ({processed_count}/{total_customers})"
                                        log_to_file(f"[GEOCODE] FEHLER: Fehlgeschlagen für Adresse: '{address}' (Kunde: {customer_name})")
                                        # WICHTIG: Kunde wird trotzdem hinzugefügt (ohne Koordinaten), damit Tour erstellt wird
                            else:
                                # Keine Adresse - aber Kunde wird trotzdem hinzugefügt (z.B. für PF-Kunden ohne Synonym)
                                # WICHTIG: Nicht als kritischer Fehler behandeln, sondern als Warnung
                                warn_count += 1  # Ändere von bad_count zu warn_count
                                warning_message = f"Keine Adresse für {customer.get('name', 'Unbekannt')}"
                                warnings.append(warning_message)  # Ändere von errors zu warnings
                                log_to_file(f"[WORKFLOW] WARNUNG: {warning_message} (Kunde wird trotzdem hinzugefügt)")
                        else:
                            ok_count += 1
                        
                        # WICHTIG: ALLE Kunden hinzufügen (auch ohne Koordinaten), damit Warnungen sichtbar sind
                        # Konvertiere Kunden zu Stops-Format für Frontend
                        stop_data = {
                            "order_id": customer.get('customer_number', customer.get('kdnr', '')),
                            "customer": customer.get('name', 'Unbekannt'),
                            "customer_number": customer.get('customer_number', customer.get('kdnr', '')),
                            "street": customer.get('street', ''),
                            "postal_code": customer.get('postal_code', ''),
                            "city": customer.get('city', ''),
                            "lat": customer.get('lat'),
                            "lon": customer.get('lon'),
                            "address": customer.get('address', f"{customer.get('street', '')}, {customer.get('postal_code', '')} {customer.get('city', '')}".strip(', ')),
                            "bar_flag": customer.get('bar_flag', False),  # BAR-Flag vom Parser übernehmen
                            "has_coordinates": has_coords,  # Flag für Frontend
                            "warning": warning_message  # Warnung direkt beim Kunden
                        }
                        all_customers_for_tour.append(stop_data)
                    
                    # WICHTIG: Automatische Sektor-Planung für W-Touren (Teil der normalen Routing-Optimierung)
                    if all_customers_for_tour:
                        tour_name = tour.get('name', 'Unbekannt')
                        
                        # ✅ FILTER: Tour-Ignore-Liste und Allow-Liste prüfen
                        ignore_list, allow_list = load_tour_filter_lists()
                        if not should_process_tour(tour_name, ignore_list, allow_list):
                            ignored_reasons = []
                            for p in ignore_list:
                                if p in tour_name.upper():
                                    ignored_reasons.append(f"Ignore: {p}")
                            if allow_list and len(allow_list) > 0:
                                if not any(p in tour_name.upper() for p in allow_list):
                                    ignored_reasons.append(f"Nicht in Allow-Liste: {allow_list}")
                            log_to_file(f"[WORKFLOW] Tour '{tour_name}' übersprungen ({', '.join(ignored_reasons) if ignored_reasons else 'Filter-Regel'})")
                            # WICHTIG: Füge Warnung hinzu, damit Benutzer sieht warum Tour fehlt
                            warnings.append(f"Tour '{tour_name}' wurde durch Filter entfernt ({', '.join(ignored_reasons) if ignored_reasons else 'Filter-Regel'})")
                            continue  # Überspringe diese Tour komplett
                        
                        # WICHTIG: Workflow soll NUR zusammenfassen, NICHT aufteilen!
                        # Sektor-Planung und Clustering werden NICHT im Workflow durchgeführt.
                        # Die Aufteilung erfolgt erst bei der Routen-Optimierung.
                        # Erstelle Tour mit allen Kunden (zusammenfassen, nicht aufteilen)
                        # Jede Route bekommt eine eindeutige Farbe basierend auf ihrem Index
                        route_index = len(optimized_tours)  # Index für Farbzuweisung
                        tour_dict = {
                            "tour_id": tour_name,
                            "stops": all_customers_for_tour,
                            "stop_count": len(all_customers_for_tour),
                            "estimated_time_minutes": None,  # Wird bei Optimierung berechnet
                            "estimated_return_time_minutes": None,
                            "estimated_total_with_return_minutes": None,
                            "_route_index": route_index  # Eindeutiger Index für Farbzuweisung
                        }
                        optimized_tours.append(tour_dict)
                        log_to_file(f"[WORKFLOW] Tour {tour_name} zusammengefasst: {len(all_customers_for_tour)} Kunden (Aufteilung erfolgt bei Optimierung), Route-Index: {route_index}")
                    else:
                        # ANLIEF-Touren können auch mit 0 Kunden existieren (z.B. wenn nur Kommentar)
                        tour_name = tour.get('name', 'Unbekannt')
                        if 'Anlief' in tour_name or 'Anlief.' in tour_name:
                            # Für ANLIEF-Touren: Warnung statt Fehler
                            warnings.append(f"Tour {tour_name} hat keine Kunden (möglicherweise leere Tour).")
                        else:
                            # Leere Tour als Warnung behandeln
                            warnings.append(f"Tour {tour_name} hat keine Kunden.")
                
                # WICHTIG: Konsolidiere kleine T-Touren (z.B. T10 mit ≤3 Stopps) NACH Optimierung
                tours_before_consolidation = len(optimized_tours)
                optimized_tours = consolidate_t10_tours(optimized_tours, max_stops=3)
                tours_after_consolidation = len(optimized_tours)
                
                if tours_before_consolidation != tours_after_consolidation:
                    log_to_file(f"[WORKFLOW] T-Tour-Konsolidierung: {tours_before_consolidation} → {tours_after_consolidation} Touren")
                    consolidated_info = f" ({tours_before_consolidation - tours_after_consolidation} T-Touren zusammengelegt)"
                else:
                    consolidated_info = ""
                
                # Progress abschließen
                _geocoding_progress[session_id]["status"] = "completed"
                _geocoding_progress[session_id]["current"] = f"Fertig! {ok_count} OK, {warn_count} Warn"
                
                # ✅ FILTER: Ignorierte Touren aus der Antwort entfernen (werden nicht angezeigt)
                ignore_list, allow_list = load_tour_filter_lists()
                filtered_tours = []
                filtered_out_count = 0
                for tour in optimized_tours:
                    tour_id = tour.get("tour_id") if isinstance(tour, dict) else getattr(tour, "tour_id", None)
                    if tour_id and not should_process_tour(tour_id, ignore_list, allow_list):
                        filtered_out_count += 1
                        log_to_file(f"[WORKFLOW] Tour '{tour_id}' durch Filter entfernt (Ignore/Allow-Liste)")
                        continue  # Tour überspringen - nicht in Antwort aufnehmen
                    filtered_tours.append(tour)
                
                # WICHTIG: Wenn ALLE Touren gefiltert wurden, füge Warnung hinzu
                if len(optimized_tours) > 0 and len(filtered_tours) == 0:
                    warnings.append(f"ALLE {len(optimized_tours)} Touren wurden durch Filter-Liste entfernt (Allow-Liste: {allow_list}, Ignore-Liste: {ignore_list[:3]}...)")
                    log_to_file(f"[WORKFLOW] ⚠️ KRITISCH: Alle Touren gefiltert! Allow-Liste: {allow_list}, Ignore-Liste: {ignore_list}")
                
                return JSONResponse({
                    "success": True,
                    "filename": file.filename,
                    "status": f"Workflow erfolgreich. {ok_count} OK, {warn_count} Warn, {bad_count} Bad{consolidated_info}",
                    "counts": {
                        "ok": ok_count,
                        "warn": warn_count,
                        "bad": bad_count
                    },
                    "warnings": warnings,
                    "errors": errors,
                    "tours": filtered_tours,
                    "tour_count": len(filtered_tours),
                    "total_stops": sum(len(tour.get("stops", []) if isinstance(tour, dict) else getattr(tour, "stops", [])) for tour in filtered_tours),
                    "tours_consolidated": tours_before_consolidation != tours_after_consolidation,
                    "tours_before_consolidation": tours_before_consolidation,
                    "geocoding_session_id": session_id,  # Session-ID für Progress-Tracking
                    "geocoding_stats": {
                        "db_hits": _geocoding_progress[session_id].get("db_hits", 0),
                        "geoapify_calls": _geocoding_progress[session_id].get("geoapify_calls", 0),
                        "errors": _geocoding_progress[session_id].get("errors", 0)
                    }
                }, media_type="application/json; charset=utf-8")
            finally:
                # Temporäre Datei löschen (auf Windows: warte kurz falls noch geöffnet)
                if tmp_path:
                    try:
                        # Mehrere Versuche auf Windows (Datei kann noch geöffnet sein)
                        for attempt in range(3):
                            try:
                                if Path(tmp_path).exists():
                                    Path(tmp_path).unlink(missing_ok=True)
                                    break
                            except (OSError, PermissionError):
                                if attempt < 2:
                                    time.sleep(0.2)  # Warte länger bei Fehler
                                else:
                                    # Beim letzten Versuch: Datei umbenennen statt löschen (für späteres Cleanup)
                                    try:
                                        Path(tmp_path).rename(Path(tmp_path).with_suffix('.csv.todelete'))
                                    except Exception as rename_err:
                                        # Datei kann bereits gelöscht sein oder keine Berechtigung
                                        log_to_file(f"[CLEANUP] Konnte temp-Datei nicht umbenennen: {rename_err}")
                    except Exception as e:
                        # Ignoriere Fehler beim Löschen (Datei kann bereits gelöscht sein)
                        pass
        
        # Standard CSV-Format: Verwende run_workflow
        # CSV Header analysieren für automatische Spaltenerkennung
        import csv
        import io
        from services.workflow_engine import CSVReader
        
        reader = CSVReader()
        sample_rows = reader.read(content[:4096])
        
        # Wenn keine Daten, versuche vollständigen Content
        if not sample_rows and len(content) > 4096:
            sample_rows = reader.read(content)
        
        # Automatische Spaltenerkennung
        if sample_rows:
            headers = list(sample_rows[0].keys())
            log_to_file(f"[WORKFLOW] CSV-Header gefunden: {headers}")
            
            # Fallback-Mapping für verschiedene CSV-Formate
            def find_column(possible_names):
                for name in possible_names:
                    for header in headers:
                        if name.lower() in header.lower():
                            return header
                return None
            
            column_map = ColumnMap(
                tour_id=find_column(["tour_id", "tour", "route", "route_id"]) or "tour_id",
                order_id=find_column(["order_id", "order", "nr", "nummer", "id"]) or "order_id",
                customer=find_column(["customer", "kunde", "firma", "name", "customer_name"]) or "customer",
                street=find_column(["street", "straße", "strasse", "str", "adresse", "address"]) or "street",
                postal_code=find_column(["postal_code", "plz", "postcode", "zip"]) or "postal_code",
                city=find_column(["city", "stadt", "ort"]) or "city",
                lat=find_column(["lat", "latitude", "breite"]) or "lat",
                lon=find_column(["lon", "lng", "longitude", "long", "länge"]) or "lon"
            )
            log_to_file(f"[WORKFLOW] Spalten-Mapping: tour_id={column_map.tour_id}, customer={column_map.customer}")
        else:
            # Standard Column-Mapping für FAMO-Tourpläne
            column_map = ColumnMap(
                tour_id="tour_id",
                customer="customer",
                street="street", 
                postal_code="postal_code",
                city="city",
                lat="lat",
                lon="lon"
            )
            log_to_file(f"[WORKFLOW] Warnung: Keine CSV-Header gefunden, verwende Standard-Mapping")
        
        # Geocoder mit Datenbank-Integration
        geocoder = CachedGeocoder()
        
        # Workflow ausführen
        result = run_workflow(content, column_map=column_map, geocoder=geocoder)
        
        # Ergebnis für UI aufbereiten
        # ✅ FILTER: Ignorierte Touren aus der Antwort entfernen (werden nicht angezeigt)
        ignore_list, allow_list = load_tour_filter_lists()
        
        tours_data = []
        for tour in result.tours:
            # Prüfe ob Tour ignoriert werden soll
            tour_id = getattr(tour, 'tour_id', None) or (tour.get('tour_id') if isinstance(tour, dict) else None)
            if tour_id and not should_process_tour(tour_id, ignore_list, allow_list):
                # Tour überspringen - nicht in Antwort aufnehmen
                continue
            stops_data = []
            for stop in tour.stops:
                stops_data.append({
                    "order_id": stop.order_id,
                    "customer": stop.customer,
                    "street": stop.street,
                    "postal_code": stop.postal_code,
                    "city": stop.city,
                    "lat": stop.lat,
                    "lon": stop.lon,
                    "address": f"{stop.street}, {stop.postal_code} {stop.city}"
                })
            
            tours_data.append({
                "tour_id": tour.tour_id,
                "stops": stops_data,
                "stop_count": len(stops_data)
            })
        
        return JSONResponse({
            "success": True,
            "filename": file.filename,
            "status": f"Workflow erfolgreich. {result.ok} OK, {result.warn} Warn, {result.bad} Bad",
            "counts": {
                "ok": result.ok,
                "warn": result.warn,
                "bad": result.bad
            },
            "warnings": result.warnings,
            "errors": result.errors,
            "tours": tours_data,
            "tour_count": len(tours_data),
            "total_stops": sum(len(tour["stops"]) for tour in tours_data)
        }, media_type="application/json; charset=utf-8")
        
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        import logging
        error_details = traceback.format_exc()
        
        # Detailliertes Logging
        log_to_file(f"[WORKFLOW UPLOAD ERROR] Exception: {type(e).__name__}: {e}")
        log_to_file(f"[WORKFLOW UPLOAD ERROR] Traceback: {error_details[:500]}")
        
        # Fehlermeldung als JSON zurückgeben (nicht als Plain Text)
        error_msg = str(e)
        
        # WICHTIG: JSONResponse statt HTTPException, damit Frontend JSON parsen kann
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": "Upload-Workflow-Fehler",
                "detail": error_msg,
                "type": type(e).__name__
            },
            media_type="application/json; charset=utf-8"
        )

@router.get("/api/workflow/status")
async def workflow_status():
    """
    Status des Workflow-Systems mit LLM-Integration.
    """
    llm_performance = llm_optimizer.get_performance_report()
    llm_metrics = llm_monitoring.get_performance_metrics(days=7)
    
    return JSONResponse({
        "workflow_engine": "Verfügbar mit LLM-Integration",
        "geocoder": "FAMO-spezifisch mit Datenbank-Integration",
        "optimizer": "Nearest-Neighbor + 2-Opt + LLM-Optimierung",
        "llm_status": llm_performance.get("status", "unknown"),
        "llm_model": llm_performance.get("model", "N/A"),
        "llm_performance": llm_performance,
        "llm_metrics": llm_metrics.__dict__ if hasattr(llm_metrics, '__dict__') else llm_metrics,
        "supported_formats": ["CSV"],
        "endpoints": {
            "complete": "/api/workflow/complete - Kompletter Workflow mit Tourplaene-Dateien",
            "upload": "/api/workflow/upload - Workflow mit Upload-Dateien",
            "status": "/api/workflow/status - System-Status",
            "llm_monitoring": "/api/llm/monitoring - LLM-Monitoring und Performance-Metriken",
            "llm_templates": "/api/llm/templates - Prompt-Templates und Konfiguration",
            "llm_optimize": "/api/llm/optimize - Direkte LLM-Routenoptimierung"
        }
    }, media_type="application/json; charset=utf-8")

@router.get("/api/llm/monitoring")
async def llm_monitoring_status():
    """
    LLM-Monitoring und Performance-Metriken.
    """
    try:
        performance_metrics = llm_monitoring.get_performance_metrics(days=7)
        cost_analysis = llm_monitoring.get_cost_analysis(days=30)
        anomalies = llm_monitoring.detect_anomalies(days=7)
        recent_interactions = llm_monitoring.get_recent_interactions(limit=10)
        
        return JSONResponse({
            "status": "LLM-Monitoring aktiv",
            "performance_metrics": performance_metrics.__dict__ if hasattr(performance_metrics, '__dict__') else performance_metrics,
            "cost_analysis": cost_analysis,
            "anomalies": anomalies,
            "recent_interactions": recent_interactions
        })
        
    except Exception as e:
        raise HTTPException(500, detail=f"Monitoring-Fehler: {str(e)}")

@router.get("/api/llm/templates")
async def llm_templates():
    """
    Prompt-Templates und Konfiguration.
    """
    try:
        templates = prompt_manager.list_templates()
        config = prompt_manager.get_config()
        
        return JSONResponse({
            "status": "Prompt-Manager aktiv",
            "templates": templates,
            "config": config.__dict__ if hasattr(config, '__dict__') else config,
            "total_templates": len(templates)
        })
    except Exception as e:
        raise HTTPException(500, detail=f"Template-Fehler: {str(e)}")

@router.post("/api/ai-tour-classify")
async def ai_tour_classify(request: Request):
    """
    KI-basierte Tour-Klassifizierung (BAR, Tour-Typ, Gruppierung)
    """
    try:
        body = await request.json()
        tour_id = body.get('tour_id', '')
        stop_count = body.get('stop_count', 0)
        sample_stops = body.get('sample_stops', [])
        
        if not llm_optimizer.enabled:
            # Fallback: Pattern-basierte Erkennung
            is_bar = 'BAR' in tour_id.upper()
            base_name = re.sub(r'\s*(Uhr\s*)?(BAR|Tour)$', '', tour_id, flags=re.IGNORECASE).strip()
            return JSONResponse({
                "is_bar": is_bar,
                "base_name": base_name,
                "confidence": 0.7,
                "reasoning": "Pattern-basierte Erkennung (KI nicht verfügbar)"
            })
        
        # KI-Prompt für Tour-Klassifizierung
        prompt = f"""Analysiere diese Tour und klassifiziere sie:

Tour-ID: {tour_id}
Anzahl Stops: {stop_count}
Beispiel-Stops: {json.dumps(sample_stops[:3], ensure_ascii=False)}

Aufgaben:
1. Ist dies eine BAR-Tour? (BAR = Be- und Abholung)
2. Welches ist der Basis-Name (ohne "BAR"/"Tour"/"Uhr")?
3. Welche Zeit hat die Tour?

Antworte NUR mit JSON in diesem Format:
{{
  "is_bar": true/false,
  "base_name": "W-07.00",
  "time": "07:00",
  "confidence": 0.0-1.0,
  "reasoning": "kurze Begründung"
}}
"""
        
        # LLM-Aufruf (async)
        try:
            # Synchroner Wrapper für async OpenAI Client
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
            
            response = await asyncio.to_thread(
                lambda: llm_optimizer.client.chat.completions.create(
                    model=llm_optimizer.model,
                    messages=[{
                        "role": "system",
                        "content": "Du bist ein Experte für Tourenplanung. Antworte NUR mit valides JSON, keine zusätzlichen Erklärungen."
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.3,
                    max_tokens=200
                )
            )
            
            result_text = response.choices[0].message.content.strip()
            # Entferne Code-Blöcke falls vorhanden
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(result_text)
            
            return JSONResponse(result)
            
        except Exception as e:
            # Fallback bei KI-Fehler
            import re
            is_bar = bool(re.search(r'\bBAR\b', tour_id, re.IGNORECASE))
            base_name = re.sub(r'\s*(Uhr\s*)?(BAR|Tour)$', '', tour_id, flags=re.IGNORECASE).strip()
            time_match = re.search(r'(\d{1,2})[.:](\d{2})', tour_id)
            time = f"{time_match.group(1)}:{time_match.group(2)}" if time_match else ""
            
            return JSONResponse({
                "is_bar": is_bar,
                "base_name": base_name,
                "time": time,
                "confidence": 0.7,
                "reasoning": f"Pattern-basierte Erkennung (KI-Fehler: {str(e)})"
            })
            
    except Exception as e:
        raise HTTPException(500, detail=f"Klassifizierungs-Fehler: {str(e)}")

@router.post("/api/ai-tour-group")
async def ai_tour_group(request: Request):
    """
    KI-basierte Touren-Gruppierung (zusammengehörige Touren zusammenführen)
    """
    try:
        body = await request.json()
        tours = body.get('tours', [])
        
        if not llm_optimizer.enabled or len(tours) < 2:
            # Fallback: Einfache Gruppierung
            groups = []
            for i, tour in enumerate(tours):
                tour_id = tour.get('name', tour.get('id', f'Tour {i}'))
                base_name = re.sub(r'\s*(Uhr\s*)?(BAR|Tour)$', '', tour_id, flags=re.IGNORECASE).strip()
                is_bar = bool(re.search(r'\bBAR\b', tour_id, re.IGNORECASE))
                
                groups.append({
                    "tour_id": tour_id,
                    "group_id": base_name,
                    "base_name": base_name,
                    "is_bar": is_bar
                })
            
            return JSONResponse({"groups": groups})
        
        # KI-Prompt für Gruppierung
        prompt = f"""Gruppiere diese Touren. Touren mit gleichem Basis-Namen und Zeit gehören zusammen.
BAR-Touren gehören zu ihren gleichnamigen "Tour"-Touren.

Touren:
{json.dumps(tours, ensure_ascii=False)}

Antworte NUR mit JSON in diesem Format:
{{
  "groups": [
    {{
      "tour_id": "W-07.00 Uhr BAR",
      "group_id": "W-07.00",
      "base_name": "W-07.00",
      "is_bar": true,
      "time": "07:00"
    }},
    {{
      "tour_id": "W-07.00 Uhr Tour",
      "group_id": "W-07.00",
      "base_name": "W-07.00",
      "is_bar": false,
      "time": "07:00"
    }}
  ],
  "reasoning": "Begründung"
}}
"""
        
        try:
            # Synchroner Wrapper für async OpenAI Client
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import nest_asyncio
                nest_asyncio.apply()
            
            response = await asyncio.to_thread(
                lambda: llm_optimizer.client.chat.completions.create(
                    model=llm_optimizer.model,
                    messages=[{
                        "role": "system",
                        "content": "Du gruppierst Touren intelligently. Antworte NUR mit valides JSON."
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0.3,
                    max_tokens=500
                )
            )
            
            result_text = response.choices[0].message.content.strip()
            result_text = result_text.replace('```json', '').replace('```', '').strip()
            result = json.loads(result_text)
            
            return JSONResponse(result)
            
        except Exception as e:
            # Fallback bei KI-Fehler
            groups = []
            import re
            for i, tour in enumerate(tours):
                tour_id = tour.get('name', tour.get('id', f'Tour {i}'))
                base_name = re.sub(r'\s*(Uhr\s*)?(BAR|Tour)$', '', tour_id, flags=re.IGNORECASE).strip()
                is_bar = bool(re.search(r'\bBAR\b', tour_id, re.IGNORECASE))
                time_match = re.search(r'(\d{1,2})[.:](\d{2})', tour_id)
                time = f"{time_match.group(1)}:{time_match.group(2)}" if time_match else ""
                
                groups.append({
                    "tour_id": tour_id,
                    "group_id": base_name,
                    "base_name": base_name,
                    "is_bar": is_bar,
                    "time": time
                })
            
            return JSONResponse({
                "groups": groups,
                "reasoning": f"Pattern-basierte Gruppierung (KI-Fehler: {str(e)})"
            })
            
    except Exception as e:
        raise HTTPException(500, detail=f"Gruppierungs-Fehler: {str(e)}")

@router.post("/api/tour/optimize")
async def optimize_tour_with_ai(request: Request):
    """
    Optimiert eine Tour mit deterministischem Routing-Optimizer.
    
    WICHTIG: Gibt NIE 500 zurück, immer 200 mit success:true/false.
    Bei Fehlern wird Fallback verwendet (Nearest Neighbor oder Identität).
    
    Request Body (validiert mit Pydantic):
    {
        "tour_id": "T10",
        "stops": [
            {
                "customer_number": "123",
                "name": "Kunde 1",
                "address": "Straße 1, 01189 Dresden",
                "lat": 51.05,
                "lon": 13.74
            },
            ...
        ],
        "is_bar_tour": false,
        "profile": "car",
        "strategy": "mld"
    }
    
    Response:
    {
        "success": True,
        "optimized_stops": [...],
        "estimated_driving_time_minutes": 45.5,
        "estimated_service_time_minutes": 10,
        "estimated_total_time_minutes": 55.5,
        "metrics": {...},
        "warnings": [...],
        "trace_id": "abc123"
    }
    """
    # Hole Trace-ID aus Request-State (wird von TraceIDMiddleware gesetzt)
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4())[:8])
    
    # WICHTIG: Äußerer try-except Block fängt ALLE Fehler ab (auch vorherige)
    try:
        # Request-Validierung mit Pydantic (gibt 422 bei Fehler)
        try:
            body = await request.json()
        except Exception as json_error:
            log_to_file(f"[TOUR-OPTIMIZE] FEHLER beim Parsen des Request-Bodies: {json_error}")
            import traceback
            log_to_file(f"[TOUR-OPTIMIZE] JSON-Parse Traceback:\n{traceback.format_exc()}")
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": "Ungültiger Request-Body",
                    "error_detail": str(json_error),
                    "trace_id": trace_id
                }
            )
        
        # Validiere Request mit Pydantic
        try:
            validated_request = OptimizeTourRequest(**body)
        except Exception as validation_error:
            log_to_file(f"[TOUR-OPTIMIZE] Validierungsfehler: {validation_error}")
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": "Request-Validierung fehlgeschlagen",
                    "error_detail": str(validation_error),
                    "trace_id": trace_id
                }
            )
        
        tour_id = validated_request.tour_id
        stops = validated_request.stops
        
        # ✅ FILTER: Tour-Ignore-Liste und Allow-Liste prüfen (BEVOR Optimierung startet)
        ignore_list, allow_list = load_tour_filter_lists()
        if not should_process_tour(tour_id, ignore_list, allow_list):
            ignored_reasons = []
            for p in ignore_list:
                if p.upper() in tour_id.upper():
                    ignored_reasons.append(f"Ignore: {p}")
            if allow_list and len(allow_list) > 0:
                if not any(p.upper() in tour_id.upper() for p in allow_list):
                    ignored_reasons.append(f"Nicht in Allow-Liste: {allow_list}")
            log_to_file(f"[TOUR-OPTIMIZE] Tour '{tour_id}' übersprungen ({', '.join(ignored_reasons) if ignored_reasons else 'Filter-Regel'})")
            return JSONResponse(
                status_code=200,  # 200 OK, aber mit skipped=True
                content={
                    "success": True,
                    "skipped": True,
                    "reason": "Tour wird durch Ignore-Liste oder Allow-Liste gefiltert",
                    "ignored_reasons": ignored_reasons,
                    "tour_id": tour_id,
                    "optimized_stops": [],
                    "estimated_driving_time_minutes": 0,
                    "estimated_service_time_minutes": 0,
                    "estimated_total_time_minutes": 0,
                    "trace_id": trace_id
                }
            )
        
        log_to_file(f"[TOUR-OPTIMIZE] Anfrage für Tour: {tour_id}, {len(stops)} Stopps (Trace-ID: {trace_id})")
        
        if not stops:
            log_to_file(f"[TOUR-OPTIMIZE] FEHLER: Keine Stopps angegeben")
            return JSONResponse(
                status_code=422,
                content={
                    "success": False,
                    "error": "Keine Stopps angegeben",
                    "trace_id": trace_id
                }
            )
        
        # Filtere Stopps mit Koordinaten
        # WICHTIG: Stelle sicher, dass BAR-Flags erhalten bleiben
        is_bar_tour = validated_request.is_bar_tour or ('BAR' in str(tour_id).upper())
        
        valid_stops = []
        seen_coords = {}  # Dict: (lat, lon) -> erster Stop mit diesen Koordinaten
        duplicate_warnings = []
        
        for idx, s in enumerate(stops):
            # Pydantic-Modell: Zugriff auf Attribute direkt, nicht .get()
            if s.lat is not None and s.lon is not None:
                # Erstelle Kopie des Stops als Dict (Pydantic V2: model_dump())
                stop_copy = s.model_dump() if hasattr(s, 'model_dump') else s.dict()
                
                # Encoding Guard: Normalisiere Text-Felder (NACH Konvertierung zu Dict)
                if stop_copy.get('name'):
                    stop_copy['name'] = unicodedata.normalize("NFC", stop_copy['name'])
                if stop_copy.get('address'):
                    stop_copy['address'] = unicodedata.normalize("NFC", stop_copy['address'])
                
                # WICHTIG: Wenn bar_flag nicht vorhanden, aber Tour eine BAR-Tour ist → setze Flag
                if 'bar_flag' not in stop_copy or stop_copy.get('bar_flag') is None:
                    stop_copy['bar_flag'] = is_bar_tour
                
                # Duplikats-Erkennung: Prüfe auf identische/ähnliche Koordinaten
                lat = float(stop_copy.get('lat', 0))
                lon = float(stop_copy.get('lon', 0))
                coord_key = (round(lat, 5), round(lon, 5))  # Runde auf ~1 Meter Genauigkeit
                
                if coord_key in seen_coords:
                    # Duplikat gefunden!
                    first_stop = seen_coords[coord_key]
                    duplicate_warnings.append({
                        "stop_index": idx,
                        "stop_name": stop_copy.get('name', 'Unbekannt'),
                        "stop_address": stop_copy.get('address', ''),
                        "duplicate_of_index": first_stop['index'],
                        "duplicate_of_name": first_stop['name'],
                        "duplicate_of_address": first_stop['address'],
                        "coordinates": (lat, lon)
                    })
                    log_to_file(f"[TOUR-OPTIMIZE] DUPLIKAT erkannt: Stop {idx} ({stop_copy.get('name')}) hat identische Koordinaten wie Stop {first_stop['index']} ({first_stop['name']})")
                    # Füge Warnung zum Stop hinzu
                    if 'warnings' not in stop_copy:
                        stop_copy['warnings'] = []
                    stop_copy['warnings'].append(f"Duplikat: Gleiche Koordinaten wie '{first_stop['name']}'")
                else:
                    # Erster Stop mit diesen Koordinaten
                    seen_coords[coord_key] = {
                        'index': idx,
                        'name': stop_copy.get('name', 'Unbekannt'),
                        'address': stop_copy.get('address', '')
                    }
                
                valid_stops.append(stop_copy)
        
        # Sichere Print-Ausgabe (verhindert UnicodeEncodeError)
        log_to_file(f"[TOUR-OPTIMIZE] Tour {tour_id}: {len(valid_stops)}/{len(stops)} Stopps mit Koordinaten (BAR-Tour: {is_bar_tour})")
        log_to_file(f"[TOUR-OPTIMIZE] LLM-Optimizer Status: enabled={llm_optimizer.enabled}")
        
        # Validierungs-Check: Prüfe ob Koordinaten gültig sind
        invalid_coords = [s for s in valid_stops if not (-90 <= s.get('lat', 0) <= 90) or not (-180 <= s.get('lon', 0) <= 180)]
        if invalid_coords:
            log_to_file(f"[TOUR-OPTIMIZE] WARNUNG: {len(invalid_coords)} Stopps mit ungültigen Koordinaten gefunden")
            valid_stops = [s for s in valid_stops if (-90 <= s.get('lat', 0) <= 90) and (-180 <= s.get('lon', 0) <= 180)]
            log_to_file(f"[TOUR-OPTIMIZE] Nach Validierung: {len(valid_stops)} gültige Stopps")
        
        if not valid_stops:
            log_to_file(f"[TOUR-OPTIMIZE] FEHLER: Keine Stopps mit Koordinaten für Tour {tour_id}")
            # Nie 500: Immer success:false mit error (HTTP 200)
            return JSONResponse({
                "success": False,
                "error": "Keine Stopps mit Koordinaten gefunden",
                "warnings": ["Keine Koordinaten verfügbar für Optimierung"]
            }, status_code=200)
        
        log_to_file(f"[TOUR-OPTIMIZE] 🔄 Starte Optimierung für Tour {tour_id}...")
        log_to_file(f"[TOUR-OPTIMIZE] 📊 Verwende {len(valid_stops)} valide Stopps")
        
        # WICHTIG: Verwende die einfache optimize_tour_stops() Funktion (wie im Backup)
        # Diese ist robuster als routing_optimize_route()
        log_to_file(f"[TOUR-OPTIMIZE] 🎯 Methode: optimize_tour_stops() (Backup-Version)")
        
        try:
            log_to_file(f"[TOUR-OPTIMIZE] ⚙️ Versuche Optimierung...")
            # Versuche LLM-Optimierung wenn verfügbar
            if llm_optimizer.enabled:
                log_to_file(f"[TOUR-OPTIMIZE] 🤖 LLM ist aktiviert, versuche LLM-Optimizer...")
                try:
                    log_to_file(f"[TOUR-OPTIMIZE] 🔄 Rufe llm_optimizer.optimize_route() auf...")
                    result = llm_optimizer.optimize_route(valid_stops, region="Dresden")
                    optimized_stops_list = [valid_stops[i] for i in result.optimized_route]
                    reasoning = result.reasoning
                    method = result.model_used if hasattr(result, 'model_used') else "ai"
                    log_to_file(f"[TOUR-OPTIMIZE] ✅ LLM-Optimierung ERFOLGREICH!")
                    log_to_file(f"  • Methode: {method}")
                    log_to_file(f"  • Optimierte Stopps: {len(optimized_stops_list)}")
                except Exception as llm_error:
                    # LLM-Fehler → Nearest-Neighbor Fallback
                    log_to_file(f"[TOUR-OPTIMIZE] ⚠️ LLM-FEHLER: {type(llm_error).__name__}: {llm_error}")
                    log_to_file(f"[TOUR-OPTIMIZE] 🔄 Fallback auf Nearest-Neighbor...")
                    optimized_stops_list = optimize_tour_stops(valid_stops, use_llm=False)
                    reasoning = f"Nearest-Neighbor Optimierung (LLM nicht verfügbar: {str(llm_error)[:100]})"
                    method = "nearest_neighbor"
                    log_to_file(f"[TOUR-OPTIMIZE] ✅ Nearest-Neighbor abgeschlossen: {len(optimized_stops_list)} Stopps")
            else:
                # LLM deaktiviert → Nearest-Neighbor
                log_to_file(f"[TOUR-OPTIMIZE] ℹ️ LLM ist DEAKTIVIERT")
                log_to_file(f"[TOUR-OPTIMIZE] 🔄 Verwende Nearest-Neighbor direkt...")
                optimized_stops_list = optimize_tour_stops(valid_stops, use_llm=False)
                reasoning = "Nearest-Neighbor Optimierung"
                method = "nearest_neighbor"
                log_to_file(f"[TOUR-OPTIMIZE] ✅ Nearest-Neighbor abgeschlossen: {len(optimized_stops_list)} Stopps")
            
            # Erstelle optimierte Stopps-Liste (Kopien erstellen)
            log_to_file(f"[TOUR-OPTIMIZE] 📋 Erstelle Stopps-Kopien...")
            optimized_stops = []
            for stop in optimized_stops_list:
                optimized_stops.append(dict(stop))
            
            log_to_file(f"[TOUR-OPTIMIZE] 📦 Optimierte Stopps: {len(optimized_stops)}")
            
            if not optimized_stops:
                log_to_file(f"[TOUR-OPTIMIZE] ❌ KRITISCH: Optimierung gab KEINE Stopps zurück!")
                # Nie 500: Immer success:false mit error (HTTP 200)
                return JSONResponse({
                    "success": False,
                    "error": "Optimierung fehlgeschlagen: Keine optimierten Stopps generiert",
                    "warnings": ["Optimierung gab keine Stopps zurück"],
                    "optimized_stops": [],
                    "is_split": False,
                    "sub_tours": [],
                    "estimated_driving_time_minutes": 0,
                    "estimated_service_time_minutes": 0,
                    "estimated_total_time_minutes": 0,
                    "estimated_return_time_minutes": 0,
                    "reasoning": "Keine Stopps generiert",
                    "optimization_method": "error"
                }, status_code=200)
            
            # Zeitberechnung mit Haversine (wie im Backup)
            log_to_file(f"[TOUR-OPTIMIZE] ⏱️ Berechne Zeitbudget...")
            try:
                estimated_driving_time = _calculate_tour_time(optimized_stops)
                log_to_file(f"  • Fahrzeit: {estimated_driving_time:.1f} Min")
            except Exception as time_err:
                log_to_file(f"[TOUR-OPTIMIZE] ⚠️ Fehler bei _calculate_tour_time: {time_err}")
                estimated_driving_time = len(optimized_stops) * 3.0  # Fallback
                log_to_file(f"  • Fahrzeit (Fallback): {estimated_driving_time:.1f} Min")
            
            estimated_service_time = len(valid_stops) * 2  # 2 Minuten pro Kunde
            estimated_total_time = estimated_driving_time + estimated_service_time
            log_to_file(f"  • Servicezeit: {estimated_service_time} Min")
            log_to_file(f"  • Gesamtzeit: {estimated_total_time:.1f} Min")
            
        except Exception as routing_error:
            # Nie 500: Immer success:false mit error (HTTP 200)
            import traceback
            error_trace = traceback.format_exc()
            log_to_file(f"[TOUR-OPTIMIZE] ❌❌❌ KRITISCHER FEHLER bei Optimierung ❌❌❌")
            log_to_file(f"  • Exception-Typ: {type(routing_error).__name__}")
            log_to_file(f"  • Fehlermeldung: {routing_error}")
            log_to_file(f"  • Tour ID: {tour_id}")
            log_to_file(f"  • Anzahl valid_stops: {len(valid_stops) if 'valid_stops' in locals() else 'unknown'}")
            log_to_file(f"[TOUR-OPTIMIZE] 📋 Vollständiger Traceback:")
            log_to_file(error_trace)
            
            # Letzter Fallback: Identität (sollte nie passieren, aber sicherheitshalber)
            log_to_file(f"[TOUR-OPTIMIZE] 🚨 KRITISCHER FALLBACK: Verwende Identität (Original-Reihenfolge)")
            try:
                optimized_stops = [dict(s) for s in valid_stops]  # Kopien erstellen
                log_to_file(f"  • Fallback Stopps: {len(optimized_stops)}")
            except Exception as fallback_err:
                log_to_file(f"[TOUR-OPTIMIZE] ❌ KATASTROPHALER FEHLER: Auch Identität schlägt fehl: {fallback_err}")
                optimized_stops = []
            estimated_driving_time = _calculate_tour_time(optimized_stops) if optimized_stops else 0.0
            estimated_service_time = len(valid_stops) * 2
            estimated_total_time = estimated_driving_time + estimated_service_time
            reasoning = f"Kritischer Fehler: Identität verwendet (Optimierung fehlgeschlagen: {str(routing_error)[:100]})"
            method = "identity_critical"
            warnings = [f"critical_fallback_identity: {str(routing_error)[:100]}"]
        
        # Stelle sicher, dass BAR-Flags erhalten bleiben
        is_bar_tour = body.get('is_bar_tour', False) or ('BAR' in str(tour_id).upper())
        for stop in optimized_stops:
            if 'bar_flag' not in stop or stop.get('bar_flag') is None:
                stop['bar_flag'] = is_bar_tour
        
        log_to_file(f"[TOUR-OPTIMIZE] 🔍 Validiere Variablen...")
        
        # Alle Variablen sollten jetzt definiert sein (aus try/except Blöcken)
        # Zusätzliche Sicherheitsprüfungen (sollten nicht nötig sein, aber sicherheitshalber)
        if 'estimated_driving_time' not in locals() or estimated_driving_time is None:
            log_to_file(f"[TOUR-OPTIMIZE] ⚠️ estimated_driving_time fehlt, berechne neu...")
            estimated_driving_time = _calculate_tour_time(optimized_stops) if optimized_stops else 0.0
            log_to_file(f"  • Neu berechnet: {estimated_driving_time:.1f} Min")
        
        if 'estimated_service_time' not in locals() or estimated_service_time is None:
            log_to_file(f"[TOUR-OPTIMIZE] ⚠️ estimated_service_time fehlt, setze auf {len(valid_stops) * 2} Min")
            estimated_service_time = len(valid_stops) * 2  # 2 Minuten pro Kunde
        
        if 'estimated_total_time' not in locals() or estimated_total_time is None:
            log_to_file(f"[TOUR-OPTIMIZE] ⚠️ estimated_total_time fehlt, berechne neu...")
            estimated_total_time = estimated_driving_time + estimated_service_time
        
        if 'reasoning' not in locals() or reasoning is None:
            log_to_file(f"[TOUR-OPTIMIZE] ⚠️ reasoning fehlt, setze Default")
            reasoning = "Optimierung abgeschlossen"
        
        if 'method' not in locals() or method is None:
            log_to_file(f"[TOUR-OPTIMIZE] ⚠️ method fehlt, setze 'unknown'")
            method = "unknown"
        
        if 'warnings' not in locals() or warnings is None:
            warnings = []
        
        log_to_file(f"[TOUR-OPTIMIZE] ✅ Alle Variablen validiert")
        
        # Berechne individuelle Distanzen zwischen Stopps (für Splitting)
        segment_distances = []  # Distanzen zwischen aufeinanderfolgenden Stopps
        depot_lat = 51.0111988
        depot_lon = 13.7016485
        speed_kmh = 50.0  # Durchschnittsgeschwindigkeit
        
        if len(optimized_stops) > 0:
            # Distanz vom Depot zum ersten Stopp
            first_dist = _haversine_distance_km(
                depot_lat, depot_lon,
                optimized_stops[0].get('lat'), optimized_stops[0].get('lon')
            )
            segment_distances.append({
                "from": "depot",
                "to": 0,
                "distance_km": first_dist,
                "driving_time_minutes": (first_dist / speed_kmh) * 60
            })
        
        # Distanzen zwischen Stopps
        for i in range(len(optimized_stops) - 1):
            dist = _haversine_distance_km(
                optimized_stops[i].get('lat'), optimized_stops[i].get('lon'),
                optimized_stops[i+1].get('lat'), optimized_stops[i+1].get('lon')
            )
            # Faktor 1.3 für Stadtverkehr (Betriebsordnung §4)
            adjusted_dist = dist * 1.3
            segment_distances.append({
                "from": i,
                "to": i + 1,
                "distance_km": dist,
                "adjusted_distance_km": adjusted_dist,
                "driving_time_minutes": (adjusted_dist / speed_kmh) * 60
            })
        
        # Depot-Rückfahrt (wird nach der Tour addiert, zählt nicht in die Hauptzeit)
        last_stop = optimized_stops[-1] if optimized_stops else None
        return_time = 0
        if last_stop:
            return_dist = _haversine_distance_km(
                last_stop.get('lat'), last_stop.get('lon'),
                depot_lat, depot_lon
            )
            return_time = (return_dist / speed_kmh) * 60
        
        total_with_return = estimated_total_time + return_time
        
        warnings = []
        
        # Initialisiere Sub-Touren-Variable (wird bei Bedarf gefüllt)
        sub_tours_for_response = None
        
        # ✅ KRITISCHE VALIDIERUNG: Tour MUSS ≤ 65 Min OHNE Rückfahrt sein!
        if estimated_total_time > TIME_BUDGET_WITHOUT_RETURN:
            error_msg = f"Tour überschreitet 65 Min OHNE Rückfahrt: {estimated_total_time:.1f} Min → MUSS aufgeteilt werden!"
            log_to_file(f"❌ [TOUR-OPTIMIZE] {error_msg}")
            warnings.append(error_msg)
            # WICHTIG: Tour wird NICHT zurückgegeben, sondern muss vom Frontend aufgeteilt werden
            # ODER: Wir teilen hier direkt auf (besser!)
            try:
                # Teile Tour auf mit enforce_timebox()
                split_tours = enforce_timebox(tour_id, optimized_stops, max_depth=3)
                if split_tours and len(split_tours) > 0:
                    if len(split_tours) > 1:
                        # Tour wurde aufgeteilt → gebe ALLE Sub-Touren zurück
                        log_to_file(f"[TOUR-OPTIMIZE] Tour {tour_id} wurde in {len(split_tours)} Sub-Touren aufgeteilt")
                        first_split = split_tours[0]
                        optimized_stops = first_split.get("stops", optimized_stops)
                        estimated_total_time = first_split.get("estimated_time_minutes", estimated_total_time)
                        # Berechne estimated_driving_time neu basierend auf den Stopps
                        estimated_driving_time = _calculate_tour_time(optimized_stops)
                        estimated_service_time = len(optimized_stops) * 2  # Aktualisiere Service-Zeit
                        estimated_total_time = estimated_driving_time + estimated_service_time
                        warnings.append(f"Tour wurde automatisch aufgeteilt in {len(split_tours)} Sub-Touren.")
                        # WICHTIG: Speichere alle Sub-Touren für die Response
                        sub_tours_for_response = split_tours
                    else:
                        # Nur eine Tour zurückgegeben (könnte trotzdem zu lang sein, aber Rekursionstiefe erreicht)
                        log_to_file(f"[TOUR-OPTIMIZE] WARNUNG: Tour {tour_id} konnte nicht weiter aufgeteilt werden (Rekursionstiefe erreicht?)")
                        first_split = split_tours[0]
                        optimized_stops = first_split.get("stops", optimized_stops)
                        estimated_total_time = first_split.get("estimated_time_minutes", estimated_total_time)
                        estimated_driving_time = _calculate_tour_time(optimized_stops)
                        estimated_service_time = len(optimized_stops) * 2
                        estimated_total_time = estimated_driving_time + estimated_service_time
                        warnings.append(f"WARNUNG: Tour konnte nicht vollständig aufgeteilt werden. Zeit: {estimated_total_time:.1f} Min")
            except Exception as split_error:
                log_to_file(f"[TOUR-OPTIMIZE] FEHLER beim Aufteilen: {split_error}")
                import traceback
                log_to_file(f"[TOUR-OPTIMIZE] Traceback:\n{traceback.format_exc()}")
                # WICHTIG: Bei Fehler beim Aufteilen, gebe die Tour trotzdem zurück (mit Warnung)
                # Das Frontend kann dann versuchen, selbst aufzuteilen
                # Stelle sicher, dass alle Variablen definiert sind (verwende try/except statt locals())
                try:
                    if 'estimated_driving_time' not in vars() or estimated_driving_time is None:
                        estimated_driving_time = _calculate_tour_time(optimized_stops)
                except (NameError, UnboundLocalError):
                    estimated_driving_time = _calculate_tour_time(optimized_stops)
                
                try:
                    if 'estimated_service_time' not in vars() or estimated_service_time is None:
                        estimated_service_time = len(optimized_stops) * 2
                except (NameError, UnboundLocalError):
                    estimated_service_time = len(optimized_stops) * 2
                
                try:
                    if 'estimated_total_time' not in vars() or estimated_total_time is None:
                        estimated_total_time = estimated_driving_time + estimated_service_time
                except (NameError, UnboundLocalError):
                    estimated_total_time = estimated_driving_time + estimated_service_time
                
                try:
                    if 'total_with_return' not in vars() or total_with_return is None:
                        total_with_return = estimated_total_time + return_time
                except (NameError, UnboundLocalError):
                    total_with_return = estimated_total_time + return_time
                
                warnings.append(f"FEHLER: Tour konnte nicht automatisch aufgeteilt werden: {str(split_error)[:100]}")
                warnings.append("Die Tour wird trotzdem zurückgegeben, aber überschreitet das Zeit-Limit!")
        
        # Stelle sicher, dass alle Variablen definiert sind (vor dem return)
        try:
            estimated_driving_time
        except NameError:
            estimated_driving_time = _calculate_tour_time(optimized_stops)
        
        try:
            estimated_service_time
        except NameError:
            estimated_service_time = len(optimized_stops) * 2
        
        try:
            estimated_total_time
        except NameError:
            estimated_total_time = estimated_driving_time + estimated_service_time
        
        try:
            total_with_return
        except NameError:
            total_with_return = estimated_total_time + return_time
        
        if estimated_total_time > 60 and estimated_total_time <= TIME_BUDGET_WITHOUT_RETURN:
            warnings.append(f"WARNUNG: Tour dauert {estimated_total_time:.1f} Minuten (ohne Rückfahrt) - nahe am Limit von 65 Minuten!")
        
        if total_with_return > 90:
            warnings.append(f"WARNUNG: Gesamtzeit inkl. Rückfahrt: {total_with_return:.1f} Minuten - sehr lange Tour!")
        
        # Logge Interaktion (nur wenn LLM verwendet wurde)
        if llm_optimizer.enabled and method == "ai" and 'result' in locals():
            try:
                llm_monitoring.log_interaction(
                    model=result.model_used if hasattr(result, 'model_used') else "ai",
                    task_type="tour_optimization",
                    prompt=f"Tour optimization for {tour_id} with {len(valid_stops)} stops",
                    response=reasoning,
                    tokens_used={"total_tokens": result.tokens_used if hasattr(result, 'tokens_used') else 0},
                    processing_time=result.processing_time if hasattr(result, 'processing_time') else 0.0,
                    success=True,
                    metadata={
                        "tour_id": tour_id,
                        "stop_count": len(valid_stops),
                        "estimated_total_time": estimated_total_time,
                        "optimization_method": method
                    }
                )
            except Exception as log_error:
                log_to_file(f"[TOUR-OPTIMIZE] Fehler beim Logging: {log_error}")
        
        # Response zusammenbauen
        response_data = {
            "success": True,
            "tour_id": tour_id,
            "optimized_stops": optimized_stops,
            "estimated_driving_time_minutes": round(estimated_driving_time, 1),
            "estimated_service_time_minutes": estimated_service_time,
            "estimated_total_time_minutes": round(estimated_total_time, 1),
            "estimated_return_time_minutes": round(return_time, 1),
            "estimated_total_with_return_minutes": round(total_with_return, 1),
            "estimated_time_exceeds_one_hour": estimated_total_time > 60,
            "reasoning": reasoning,
            "optimization_method": method,
            "warnings": warnings,
            # NEU: Qualitätskennzahlen vom Routing-Optimizer
            "metrics": metrics if 'metrics' in locals() else {
                "total_duration_minutes": estimated_driving_time,
                "gain_vs_nearest_neighbor_pct": 0.0,
                "backend_used": "unknown",
                "solver_used": method,
                "time_ms": 0,
                "quality": "unknown"
            },
            # Neue Felder für variables Splitting
            "segment_distances": segment_distances,  # Individuelle Distanzen zwischen Stopps
            "depot_coordinates": {"lat": depot_lat, "lon": depot_lon}
        }
        
        # WICHTIG: Füge alle Sub-Touren hinzu, wenn die Tour aufgeteilt wurde
        if sub_tours_for_response is not None:
            # Konvertiere Sub-Touren in das Format für das Frontend
            formatted_sub_tours = []
            for idx, sub_tour in enumerate(sub_tours_for_response):
                sub_stops = sub_tour.get("stops", [])
                sub_time = sub_tour.get("estimated_time_minutes", 0)
                sub_driving_time = _calculate_tour_time(sub_stops)
                sub_service_time = len(sub_stops) * 2
                # Berechne Rückfahrt-Zeit (vom letzten Stop zum Depot)
                sub_return_time = 0.0
                if sub_stops and len(sub_stops) > 0:
                    last_stop = sub_stops[-1]
                    if last_stop.get('lat') and last_stop.get('lon'):
                        from math import radians, sin, cos, sqrt, atan2
                        lat1, lon1 = radians(last_stop['lat']), radians(last_stop['lon'])
                        lat2, lon2 = radians(depot_lat), radians(depot_lon)
                        dlat, dlon = lat2 - lat1, lon2 - lon1
                        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
                        c = 2 * atan2(sqrt(a), sqrt(1-a))
                        distance_km = 6371 * c
                        sub_return_time = (distance_km / 50.0) * 60  # 50 km/h Durchschnitt
                sub_total_with_return = sub_time + sub_return_time
                
                formatted_sub_tours.append({
                    "tour_id": f"{tour_id}",
                    "sub_route_index": idx,
                    "sub_route_letter": chr(65 + idx) if idx < 26 else f"A{idx}",  # A, B, C, ...
                    "optimized_stops": sub_stops,
                    "estimated_driving_time_minutes": round(sub_driving_time, 1),
                    "estimated_service_time_minutes": sub_service_time,
                    "estimated_total_time_minutes": round(sub_time, 1),
                    "estimated_return_time_minutes": round(sub_return_time, 1),
                    "estimated_total_with_return_minutes": round(sub_total_with_return, 1),
                    "stop_count": len(sub_stops),
                    "reasoning": f"Sub-Route {chr(65 + idx) if idx < 26 else f'A{idx}'} von {len(sub_tours_for_response)} Routen"
                })
            
            response_data["sub_tours"] = formatted_sub_tours
            response_data["is_split"] = True
            response_data["split_count"] = len(sub_tours_for_response)
            log_to_file(f"[TOUR-OPTIMIZE] ✅ Response enthält {len(formatted_sub_tours)} Sub-Touren")
        else:
            response_data["is_split"] = False
            response_data["sub_tours"] = []
            log_to_file(f"[TOUR-OPTIMIZE] ℹ️ Keine Aufteilung nötig (is_split=false)")
        
        log_to_file("=" * 80)
        log_to_file(f"[TOUR-OPTIMIZE] ✅ ERFOLGREICH ABGESCHLOSSEN - Trace-ID: {trace_id}")
        log_to_file(f"  • Tour ID: {tour_id}")
        log_to_file(f"  • Optimierte Stopps: {len(optimized_stops)}")
        log_to_file(f"  • Methode: {method}")
        log_to_file(f"  • Gesamtzeit: {estimated_total_time:.1f} Min")
        log_to_file(f"  • Aufgeteilt: {response_data.get('is_split', False)}")
        log_to_file("=" * 80)
        
        return JSONResponse(response_data, status_code=200)
        
    except HTTPException as http_err:
        # HTTPException NICHT weiterwerfen, sondern als 200 mit success:false zurückgeben
        # Das verhindert 500-Fehler und ermöglicht Fallback
        log_to_file("=" * 80)
        log_to_file(f"[TOUR-OPTIMIZE] ⚠️ HTTPException abgefangen")
        log_to_file(f"  • Status Code: {http_err.status_code}")
        log_to_file(f"  • Detail: {http_err.detail}")
        log_to_file(f"  • Trace-ID: {trace_id}")
        log_to_file("=" * 80)
        return JSONResponse({
            "success": False,
            "error": f"HTTP {http_err.status_code}",
            "error_detail": str(http_err.detail)[:500],
            "warnings": [f"HTTPException: {str(http_err.detail)[:200]}"],
            "trace_id": trace_id,
            # WICHTIG: Frontend erwartet diese Felder IMMER (auch bei Fehler)
            "optimized_stops": [],
            "is_split": False,
            "sub_tours": [],
            "estimated_driving_time_minutes": 0,
            "estimated_service_time_minutes": 0,
            "estimated_total_time_minutes": 0,
            "estimated_return_time_minutes": 0,
            "reasoning": "Fehler bei Optimierung",
            "optimization_method": "error"
        }, status_code=200)
    except sqlite3.DatabaseError as db_err:
        # SQLite-Fehler: Sofort 503 zurückgeben
        import traceback
        error_trace = traceback.format_exc()
        log_to_file("=" * 80)
        log_to_file(f"[TOUR-OPTIMIZE] 🔴 DATENBANK-FEHLER")
        log_to_file(f"  • Fehlertyp: {type(db_err).__name__}")
        log_to_file(f"  • Fehlermeldung: {db_err}")
        log_to_file(f"  • Trace-ID: {trace_id}")
        log_to_file(f"[TOUR-OPTIMIZE] Vollständiger Traceback:")
        log_to_file(error_trace)
        log_to_file("=" * 80)
        
        return JSONResponse({
            "success": False,
            "error": "Datenbank-Fehler",
            "error_detail": "Die Datenbank ist möglicherweise beschädigt. Bitte Support kontaktieren.",
            "warnings": [f"DB-Error: {str(db_err)[:200]}"],
            "trace_id": trace_id,
            # WICHTIG: Frontend erwartet diese Felder IMMER (auch bei Fehler)
            "optimized_stops": [],
            "is_split": False,
            "sub_tours": [],
            "estimated_driving_time_minutes": 0,
            "estimated_service_time_minutes": 0,
            "estimated_total_time_minutes": 0,
            "estimated_return_time_minutes": 0,
            "reasoning": "Datenbankfehler",
            "optimization_method": "error"
        }, status_code=503)
    except Exception as e:
        # Nie 500: Immer success:false mit error (HTTP 200)
        import traceback
        error_trace = traceback.format_exc()
        log_to_file("=" * 80)
        log_to_file(f"[TOUR-OPTIMIZE] 🔴🔴🔴 UNERWARTETER FEHLER 🔴🔴🔴")
        log_to_file(f"  • Exception-Typ: {type(e).__name__}")
        log_to_file(f"  • Fehlermeldung: {e}")
        log_to_file(f"  • Trace-ID: {trace_id}")
        log_to_file(f"[TOUR-OPTIMIZE] Vollständiger Traceback:")
        log_to_file(error_trace)
        log_to_file("=" * 80)
        
        return JSONResponse({
            "success": False,
            "error": f"Tour-Optimierung fehlgeschlagen: {type(e).__name__}",
            "error_detail": str(e)[:500],
            "warnings": [f"Unerwarteter Fehler: {str(e)[:200]}"],
            "trace_id": trace_id,
            # WICHTIG: Frontend erwartet diese Felder IMMER (auch bei Fehler)
            "optimized_stops": [],
            "is_split": False,
            "sub_tours": [],
            "estimated_driving_time_minutes": 0,
            "estimated_service_time_minutes": 0,
            "estimated_total_time_minutes": 0,
            "estimated_return_time_minutes": 0,
            "reasoning": f"Fehler: {type(e).__name__}",
            "optimization_method": "error"
        }, status_code=200)


def _decode_polyline6(encoded: str) -> List[List[float]]:
    """
    Dekodiert Polyline6-String (OSRM Format) zu Koordinaten-Liste.
    
    Args:
        encoded: Polyline6-encoded String
    
    Returns:
        Liste von [lat, lon] Koordinaten
    """
    if not encoded or not isinstance(encoded, str):
        return []
    
    coords = []
    index = 0
    lat = 0
    lon = 0
    shift = 5
    
    def next_value():
        nonlocal index
        result = 0
        b = None
        i = 0
        while True:
            if index >= len(encoded):
                return None
            b = ord(encoded[index]) - 63
            index += 1
            result |= (b & 0x1f) << (i * shift)
            i += 1
            if b < 0x20:
                break
        return ~(result >> 1) if (result & 1) else (result >> 1)
    
    while index < len(encoded):
        dlat = next_value()
        dlon = next_value()
        if dlat is None or dlon is None:
            break
        lat += dlat
        lon += dlon
        coords.append([lat / 1e6, lon / 1e6])
    
    return coords


def _haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Berechnet Haversine-Distanz zwischen zwei Koordinaten (in km).
    Robuste Implementierung mit Fehlerbehandlung.
    """
    try:
        import math
        
        # Validiere Koordinaten
        if not all(isinstance(x, (int, float)) for x in [lat1, lon1, lat2, lon2]):
            return 0.0
        
        if not (-90 <= lat1 <= 90 and -90 <= lat2 <= 90):
            return 0.0
        
        if not (-180 <= lon1 <= 180 and -180 <= lon2 <= 180):
            return 0.0
        
        R = 6371.0  # Erdradius in km
        lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        distance = 2 * R * math.asin(math.sqrt(a))
        
        # Plausibilitäts-Check: Distanz sollte zwischen 0 und 20000 km liegen
        if distance < 0 or distance > 20000:
            return 0.0
        
        return distance
    
    except Exception as e:
        import logging
        log_to_file(f"[HAVERSINE] WARNUNG: Fehler bei Distanzberechnung: {e}")
        return 0.0


def _calculate_tour_time(stops: List[Dict]) -> float:
    """
    Berechnet geschätzte Fahrzeit für eine Tour (in Minuten) - verwendet OSRM wenn verfügbar.
    Robuster Fallback auf Haversine bei jedem Fehler.
    """
    if not stops or len(stops) == 0:
        return 0.0
    
    if len(stops) == 1:
        # Nur ein Stop: Hin- und Rückfahrt zum Depot
        try:
            depot_lat = 51.0111988
            depot_lon = 13.7016485
            dist = _haversine_distance_km(
                depot_lat, depot_lon,
                stops[0].get('lat', depot_lat), stops[0].get('lon', depot_lon)
            )
            return (dist * 1.3 / 50.0) * 60 * 2  # Hin + zurück
        except Exception:
            return 10.0  # Minimaler Schätzwert
    
    # Versuche OSRM wenn verfügbar (mit robuster Fehlerbehandlung)
    try:
        client = get_osrm_client()
        if client and hasattr(client, 'available') and client.available:
            depot_lat = 51.0111988
            depot_lon = 13.7016485
            
            # Erstelle Koordinaten-Liste: Depot + alle Stopps
            coords = [(depot_lat, depot_lon)]
            for stop in stops:
                lat = stop.get('lat')
                lon = stop.get('lon')
                if lat is not None and lon is not None:
                    try:
                        lat_float = float(lat)
                        lon_float = float(lon)
                        if -90 <= lat_float <= 90 and -180 <= lon_float <= 180:
                            coords.append((lat_float, lon_float))
                    except (ValueError, TypeError):
                        pass  # Überspringe ungültige Koordinaten
            
            if len(coords) >= 2:
                try:
                    # Hole Route vom Depot über alle Stopps
                    route = client.get_route(coords, timeout=5.0)
                    if route and isinstance(route, dict) and route.get("source") == "osrm":
                        duration = route.get("duration_min", 0.0)
                        if duration > 0:
                            return duration
                except Exception as route_err:
                    import logging
                    log_to_file(f"[TOUR-TIME] WARNUNG: OSRM Route-Abfrage fehlgeschlagen: {route_err}")
    except Exception as osrm_err:
        import logging
        log_to_file(f"[TOUR-TIME] WARNUNG: OSRM-Client-Fehler: {osrm_err}")
    
    # Fallback: Haversine (mit robuster Fehlerbehandlung)
    try:
        total_distance_km = 0.0
        depot_lat = 51.0111988
        depot_lon = 13.7016485
        
        # Distanz vom Depot zum ersten Stopp
        if stops and len(stops) > 0:
            try:
                first_lat = float(stops[0].get('lat', depot_lat))
                first_lon = float(stops[0].get('lon', depot_lon))
                first_dist = _haversine_distance_km(depot_lat, depot_lon, first_lat, first_lon)
                total_distance_km += first_dist
            except (ValueError, TypeError, KeyError):
                pass  # Überspringe bei Fehler
        
        # Distanzen zwischen Stopps
        for i in range(len(stops) - 1):
            try:
                lat1 = float(stops[i].get('lat', 0))
                lon1 = float(stops[i].get('lon', 0))
                lat2 = float(stops[i+1].get('lat', 0))
                lon2 = float(stops[i+1].get('lon', 0))
                
                if all(-90 <= lat <= 90 for lat in [lat1, lat2]) and all(-180 <= lon <= 180 for lon in [lon1, lon2]):
                    dist = _haversine_distance_km(lat1, lon1, lat2, lon2)
                    total_distance_km += dist * 1.3  # Faktor für Stadtverkehr
            except (ValueError, TypeError, KeyError, ZeroDivisionError):
                pass  # Überspringe bei Fehler
        
        # Durchschnittsgeschwindigkeit: 50 km/h in der Stadt
        if total_distance_km > 0:
            driving_time_minutes = (total_distance_km / 50.0) * 60
            return max(driving_time_minutes, 5.0)  # Mindestens 5 Minuten
        else:
            # Fallback: Schätze basierend auf Anzahl Stopps
            return len(stops) * 3.0  # 3 Minuten pro Stop als Notfall-Schätzung
    
    except Exception as fallback_err:
        import logging
        log_to_file(f"[TOUR-TIME] KRITISCH: Auch Haversine-Fallback fehlgeschlagen: {fallback_err}")
        # Letzter Fallback: Basiere auf Anzahl Stopps
        return max(len(stops) * 3.0, 10.0)  # Mindestens 10 Minuten


@router.post("/api/llm/optimize")
async def llm_optimize_route(
    stops: List[Dict],
    region: str = "Dresden",
    use_llm: bool = True
):
    """
    Direkte LLM-Routenoptimierung.
    """
    try:
        if use_llm and llm_optimizer.enabled:
            result = llm_optimizer.optimize_route(stops, region)
            
            # Logge Interaktion
            llm_monitoring.log_interaction(
                model=result.model_used,
                task_type="route_optimization",
                prompt=f"Direct route optimization for {len(stops)} stops in {region}",
                response=result.reasoning,
                tokens_used={"total_tokens": result.tokens_used},
                processing_time=result.processing_time,
                success=True,
                metadata={"confidence_score": result.confidence_score}
            )
            
            return JSONResponse({
                "success": True,
                "optimized_route": result.optimized_route,
                "confidence_score": result.confidence_score,
                "reasoning": result.reasoning,
                "model_used": result.model_used,
                "tokens_used": result.tokens_used,
                "processing_time": result.processing_time
            })
        else:
            # Fallback ohne LLM
            optimized_stops = optimize_tour_stops(stops, use_llm=False)
            return JSONResponse({
                "success": True,
                "optimized_route": list(range(len(optimized_stops))),
                "confidence_score": 0.7,
                "reasoning": "Fallback: Nearest-Neighbor Optimierung",
                "model_used": "fallback",
                "tokens_used": 0,
                "processing_time": 0.0
            })
            
    except Exception as e:
        raise HTTPException(500, detail=f"LLM-Optimierung fehlgeschlagen: {str(e)}")


@router.post("/api/tour/route-details")
async def route_details(req: RouteDetailsReq):
    try:
        return await build_route_details(req)
    except HTTPException:
        raise
    except Exception as e:
        # 500 sauber fangen -> strukturierte Fehlermeldung
        raise HTTPException(status_code=500, detail=f"route-details failed: {type(e).__name__}: {e}")

# Debug-Alias (GET) nur für Smoke
@router.get("/api/tour/route-details")
async def route_details_get():
    return {"alive": True}
