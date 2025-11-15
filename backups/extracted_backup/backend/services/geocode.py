from __future__ import annotations

from typing import Optional, Tuple, Dict, Any
import os
from urllib.parse import quote

import httpx
from geopy.geocoders import Nominatim

from backend.db.dao import geocache_get, geocache_set, postal_cache_get, postal_cache_set
from backend.services.address_mapper import address_mapper

MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")
GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "32abbda2bed24f58846db0c5685e8b49")


def geocode_address(address: str) -> Optional[Dict[str, Any]]:
    # 1. Address-Mapper prüfen (höchste Priorität)
    mapping_result = address_mapper.map_address(address)
    if mapping_result['confidence'] > 0:
        print(f"[ADDRESS_MAPPER] {mapping_result['method']}: '{address}' -> '{mapping_result['corrected_address']}'")
        
        # Wenn Mapping direkte Koordinaten hat, verwende diese
        if mapping_result['lat'] is not None and mapping_result['lon'] is not None:
            geocache_set(address, mapping_result['lat'], mapping_result['lon'], mapping_result['provider'])
            return {
                "lat": mapping_result['lat'], 
                "lon": mapping_result['lon'], 
                "provider": mapping_result['provider']
            }
        
        # Wenn Mapping nur Adresse korrigiert hat, verwende korrigierte Adresse für Geocoding
        if mapping_result['corrected_address'] != address:
            address = mapping_result['corrected_address']
            print(f"[ADDRESS_MAPPER] Verwende korrigierte Adresse für Geocoding: '{address}'")
    
    # 2. Cache prüfen
    cached = geocache_get(address)
    if cached is not None:
        lat, lon, provider = cached
        print(f"[CACHE HIT] {address} -> {(lat, lon)} via {provider or 'unknown'}")
        return {"lat": lat, "lon": lon, "provider": provider}

    # 3. API-Call nur wenn nicht im Cache
    print(f"[CACHE MISS] Geocoding für: '{address}'")
    
    # PRIORITÄT 1: Geoapify (Haupt-Provider)
    if GEOAPIFY_API_KEY:
        print(f"[GEOAPIFY] Versuche Geocoding mit Geoapify für: '{address}'")
        result = _geocode_with_geoapify(address)
        if result:
            print(f"[GEOAPIFY] OK Erfolgreich: ({result['lat']}, {result['lon']})")
            geocache_set(address, result["lat"], result["lon"], "geoapify")
            return result
        else:
            print(f"[GEOAPIFY] FEHLER: Kein Ergebnis gefunden für: '{address}'")
    
    # PRIORITÄT 2: Fallback nur wenn Geoapify nicht verfügbar oder fehlgeschlagen
    # (Mapbox nur als letzter Ausweg, wenn Geoapify nicht verfügbar)
    if not GEOAPIFY_API_KEY and MAPBOX_TOKEN:
        print(f"[MAPBOX] Fallback: Versuche Mapbox (Geoapify nicht verfügbar)")
        result = _geocode_with_mapbox(address)
        if result:
            geocache_set(address, result["lat"], result["lon"], "mapbox")
            return result

    # PRIORITÄT 3: Nominatim als letzter Fallback (nur wenn Geoapify nicht verfügbar)
    if not GEOAPIFY_API_KEY:
        print(f"[NOMINATIM] Fallback: Versuche Nominatim (Geoapify nicht verfügbar)")
        result = _geocode_with_nominatim(address)
        if result:
            geocache_set(address, result["lat"], result["lon"], "nominatim")
            return result
    else:
        print(f"[ERROR] Geoapify hat kein Ergebnis geliefert und kein Fallback verfügbar")

    return None


def _geocode_with_geoapify(address: str) -> Optional[Dict[str, Any]]:
    """
    Geocodiert eine Adresse über die Geoapify Location Platform API.
    Haupt-Provider für alle Geocoding-Anfragen.
    
    Args:
        address: Zu geokodierende Adresse
        
    Returns:
        Dict mit lat/lon/postal_code/city oder None bei Fehler
    """
    if not GEOAPIFY_API_KEY:
        print(f"[GEOAPIFY] FEHLER: Kein API-Key konfiguriert")
        return None
    
    try:
        url = "https://api.geoapify.com/v1/geocode/search"
        params = {
            "text": address,
            "apiKey": GEOAPIFY_API_KEY,
            "limit": 1,
            "format": "geojson",  # GeoJSON Format für features-Array
            "lang": "de",
            "filter": "countrycode:de"  # Nur Deutschland für bessere Ergebnisse
        }
        
        resp = httpx.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        # Geoapify gibt GeoJSON zurück: data.features oder data.results (je nach Format)
        features = data.get("features", [])
        if not features:
            # Fallback: Prüfe ob results vorhanden (falls format=json verwendet wurde)
            results = data.get("results", [])
            if results:
                result = results[0]
                lat = float(result.get("lat", 0))
                lon = float(result.get("lon", 0))
            else:
                print(f"[GEOAPIFY] Keine Ergebnisse für: '{address}'")
                return None
        else:
            # GeoJSON Format: features[0].geometry.coordinates = [lon, lat]
            feature = features[0]
            coords = feature.get("geometry", {}).get("coordinates", [])
            if not coords or len(coords) < 2:
                print(f"[GEOAPIFY] Ungültige Koordinaten für: '{address}'")
                return None
            
            # WICHTIG: Geoapify GeoJSON gibt [lon, lat] zurück!
            lon = float(coords[0])
            lat = float(coords[1])
            properties = feature.get("properties", {})
        
        # Validierung: Koordinaten müssen gültig sein
        if lat == 0.0 and lon == 0.0:
            print(f"[GEOAPIFY] Ungültige Koordinaten (0,0) für: '{address}'")
            return None
        
        # Extrahiere PLZ und Stadt
        if not features:
            # Wenn results verwendet wurde
            postal_code = result.get("postcode")
            city = result.get("city") or result.get("town") or result.get("village") or result.get("municipality")
        else:
            # Wenn features verwendet wurde
            postal_code = properties.get("postcode")
            city = properties.get("city") or properties.get("town") or properties.get("village") or properties.get("municipality")
        
        print(f"[GEOAPIFY] OK Gefunden: {address} -> ({lat}, {lon}) in {city or 'Unbekannt'}")
        
        return {
            "lat": lat,
            "lon": lon,
            "provider": "geoapify",
            "postal_code": postal_code,
            "city": city,
        }
    except httpx.HTTPStatusError as exc:
        print(f"[GEOAPIFY] HTTP-Fehler {exc.response.status_code} für '{address}': {exc}")
        if exc.response.status_code == 401:
            print(f"[GEOAPIFY] FEHLER: Unauthorized - API-Key ungültig!")
        elif exc.response.status_code == 402:
            print(f"[GEOAPIFY] FEHLER: Payment Required - Kontingent überschritten!")
    except httpx.TimeoutException:
        print(f"[GEOAPIFY] TIMEOUT: Timeout für '{address}'")
    except Exception as exc:
        print(f"[GEOAPIFY] FEHLER: Fehler für '{address}': {exc}")
        import traceback
        traceback.print_exc()
    
    return None


def _geocode_with_mapbox(address: str) -> Optional[Dict[str, Any]]:
    try:
        url = f"https://api.mapbox.com/geocoding/v5/mapbox.places/{quote(address)}.json"
        params = {"access_token": MAPBOX_TOKEN, "limit": 1, "language": "de"}
        resp = httpx.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        features = data.get("features") or []
        if features:
            feature = features[0]
            lon, lat = feature["center"]
            postal_code = feature.get("properties", {}).get("postcode") or feature.get("postal_code")
            city = None
            for item in feature.get("context", []):
                item_id = item.get("id", "")
                if not postal_code and item_id.startswith("postcode"):
                    postal_code = item.get("text")
                if item_id.startswith("place") and not city:
                    city = item.get("text")
            return {
                "lat": float(lat),
                "lon": float(lon),
                "provider": "mapbox",
                "postal_code": postal_code,
                "city": city,
            }
    except Exception as exc:
        print(f"[MAPBOX] Fehler für '{address}': {exc}")
    return None


def _geocode_with_nominatim(address: str) -> Optional[Dict[str, Any]]:
    geolocator = Nominatim(user_agent="famo_trafficapp")
    try:
        location = geolocator.geocode(address, timeout=10)
    except Exception as e:
        print(f"[Nominatim] Exception für '{address}': {e}")
        location = None

    if location:
        raw = location.raw or {}
        address_details = raw.get("address", {})
        postal_code = address_details.get("postcode")
        city = address_details.get("city") or address_details.get("town") or address_details.get("village")
        return {
            "lat": float(location.latitude),
            "lon": float(location.longitude),
            "provider": "nominatim",
            "postal_code": postal_code,
            "city": city,
        }

    print(f"[Nominatim] Kein Treffer für '{address}' – versuche AddressCorrector")
    try:
        from .address_corrector import address_corrector
        correction = address_corrector.correct_address(address)
        if correction.success:
            print(f"[AddressCorrector] [OK] {correction.corrected_address}")
            return {
                "lat": correction.lat,
                "lon": correction.lon,
                "provider": "address_corrector",
                "postal_code": correction.postal_code,
                "city": correction.city,
            }
        print("[AddressCorrector] [X] Keine Korrektur moeglich")
    except ImportError:
        print("[AddressCorrector] Modul nicht verfügbar")
    except Exception as e:
        print(f"[AddressCorrector] Fehler: {e}")

    return None


def get_city_from_postal_code(postal_code: str) -> Optional[str]:
    # Einfaches Caching für Postleitzahl zu Ort
    cached_city = postal_cache_get(postal_code)
    if cached_city is not None:
        return cached_city

    geolocator = Nominatim(user_agent="famo_trafficapp")
    try:
        # Wir suchen nach der PLZ und versuchen den Ort zu extrahieren
        location = geolocator.geocode(postal_code, addressdetails=True, timeout=10)
    except Exception:
        return None

    if location and location.raw and 'address' in location.raw:
        address_details = location.raw['address']
        # Überprüfen, ob das zurückgegebene Land Deutschland ist
        if address_details.get('country') != 'Germany':
            print(f"[WARN] Ort für PLZ {postal_code} nicht in Deutschland gefunden: {address_details.get('country')}")
            return None
        
        city = address_details.get('city') or address_details.get('town') or address_details.get('village')
        if city:
            postal_cache_set(postal_code, city)
            return city
    return None