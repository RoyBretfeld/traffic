from __future__ import annotations

from typing import Optional, Tuple, Dict, Any
import os
from urllib.parse import quote

import httpx
from geopy.geocoders import Nominatim

from backend.db.dao import geocache_get, geocache_set, postal_cache_get, postal_cache_set
from backend.services.address_mapper import address_mapper

MAPBOX_TOKEN = os.getenv("MAPBOX_ACCESS_TOKEN")


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
    # 3a) Mapbox, falls Token vorhanden
    if MAPBOX_TOKEN:
        result = _geocode_with_mapbox(address)
        if result:
            geocache_set(address, result["lat"], result["lon"], "mapbox")
            return result

    # 3b) Nominatim als Fallback
    result = _geocode_with_nominatim(address)
    if result:
        geocache_set(address, result["lat"], result["lon"], "nominatim")
        return result

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