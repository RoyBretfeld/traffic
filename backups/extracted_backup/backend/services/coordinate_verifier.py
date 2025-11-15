"""
Koordinaten-Verifizierung: Prüft ob Koordinaten wirklich zum Unternehmen passen.

Verwendet 3 Services:
- Google Maps (Reverse Geocoding / Places API)
- Geoapify (Reverse Geocoding)
- Nominatim/OpenStreetMap (Reverse Geocoding)

Jeder Service gibt zurück:
- Gefundene Adresse
- Gefundener Firmenname (wenn vorhanden)
- Status: ✅ gefunden / ❌ nicht gefunden
"""

from typing import Optional, Dict, Any, List, Tuple
import os
import httpx
from geopy.geocoders import Nominatim
from difflib import SequenceMatcher

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "32abbda2bed24f58846db0c5685e8b49")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")  # Optional


def similarity(a: str, b: str) -> float:
    """Berechnet Ähnlichkeit zwischen zwei Strings (0.0 - 1.0)"""
    if not a or not b:
        return 0.0
    a_lower = a.lower().strip()
    b_lower = b.lower().strip()
    return SequenceMatcher(None, a_lower, b_lower).ratio()


def normalize_company_name(name: str) -> str:
    """Normalisiert Firmennamen für Vergleich"""
    if not name:
        return ""
    # Entferne häufige Zusätze
    removals = ["gmbh", "ug", "ag", "ltd", "inc", "co", "kg", "ohg", "e.v", "e.v.", "e. v."]
    normalized = name.lower().strip()
    for removal in removals:
        normalized = normalized.replace(f" {removal}", "").replace(f" {removal}.", "")
    return normalized.strip()


async def verify_with_google_maps(lat: float, lon: float, company_name: str, address: str) -> Dict[str, Any]:
    """
    Verifiziert Koordinaten mit Google Maps Reverse Geocoding + Places API.
    
    Returns:
        {
            "service": "google_maps",
            "found": bool,
            "address": str,
            "company_name_found": str,
            "confidence": float,
            "error": str (optional)
        }
    """
    if not GOOGLE_MAPS_API_KEY:
        return {
            "service": "google_maps",
            "found": False,
            "address": "",
            "company_name_found": "",
            "confidence": 0.0,
            "error": "Google Maps API Key nicht konfiguriert"
        }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 1. Reverse Geocoding: Koordinaten → Adresse
            reverse_geo_url = "https://maps.googleapis.com/maps/api/geocode/json"
            reverse_params = {
                "latlng": f"{lat},{lon}",
                "key": GOOGLE_MAPS_API_KEY,
                "language": "de"
            }
            
            reverse_resp = await client.get(reverse_geo_url, params=reverse_params)
            reverse_data = reverse_resp.json()
            
            if reverse_data.get("status") != "OK":
                return {
                    "service": "google_maps",
                    "found": False,
                    "address": "",
                    "company_name_found": "",
                    "confidence": 0.0,
                    "error": f"Reverse Geocoding fehlgeschlagen: {reverse_data.get('status')}"
                }
            
            found_address = reverse_data["results"][0]["formatted_address"] if reverse_data.get("results") else ""
            
            # 2. Places API: Suche nach Firmen in der Nähe
            places_url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
            places_params = {
                "location": f"{lat},{lon}",
                "radius": 50,  # 50 Meter Radius
                "type": "establishment",
                "key": GOOGLE_MAPS_API_KEY,
                "language": "de"
            }
            
            places_resp = await client.get(places_url, params=places_params)
            places_data = places_resp.json()
            
            best_match = None
            best_similarity = 0.0
            
            if places_data.get("status") == "OK" and places_data.get("results"):
                for place in places_data["results"]:
                    place_name = place.get("name", "")
                    if place_name:
                        sim = similarity(normalize_company_name(company_name), normalize_company_name(place_name))
                        if sim > best_similarity:
                            best_similarity = sim
                            best_match = place_name
            
            # 3. Text Search als Fallback (falls nearbysearch nichts findet)
            if not best_match:
                text_search_url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
                text_params = {
                    "query": f"{company_name} {address}",
                    "location": f"{lat},{lon}",
                    "radius": 100,
                    "key": GOOGLE_MAPS_API_KEY,
                    "language": "de"
                }
                
                text_resp = await client.get(text_search_url, params=text_params)
                text_data = text_resp.json()
                
                if text_data.get("status") == "OK" and text_data.get("results"):
                    for place in text_data["results"]:
                        place_name = place.get("name", "")
                        if place_name:
                            sim = similarity(normalize_company_name(company_name), normalize_company_name(place_name))
                            if sim > best_similarity:
                                best_similarity = sim
                                best_match = place_name
            
            # Status: Gefunden wenn Similarity > 0.6 oder wenn Adresse passt
            address_match = similarity(address.lower(), found_address.lower()) > 0.7
            
            found = best_similarity > 0.6 or address_match
            
            return {
                "service": "google_maps",
                "found": found,
                "address": found_address,
                "company_name_found": best_match or "",
                "confidence": max(best_similarity, 0.9 if address_match else 0.0),
                "address_match": address_match,
                "similarity": best_similarity
            }
            
    except Exception as e:
        return {
            "service": "google_maps",
            "found": False,
            "address": "",
            "company_name_found": "",
            "confidence": 0.0,
            "error": str(e)
        }


async def verify_with_geoapify(lat: float, lon: float, company_name: str, address: str) -> Dict[str, Any]:
    """
    Verifiziert Koordinaten mit Geoapify Reverse Geocoding.
    
    Returns:
        {
            "service": "geoapify",
            "found": bool,
            "address": str,
            "company_name_found": str,
            "confidence": float,
            "error": str (optional)
        }
    """
    if not GEOAPIFY_API_KEY:
        return {
            "service": "geoapify",
            "found": False,
            "address": "",
            "company_name_found": "",
            "confidence": 0.0,
            "error": "Geoapify API Key nicht konfiguriert"
        }
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # Reverse Geocoding
            url = "https://api.geoapify.com/v1/geocode/reverse"
            params = {
                "lat": lat,
                "lon": lon,
                "apiKey": GEOAPIFY_API_KEY,
                "lang": "de"
            }
            
            resp = await client.get(url, params=params)
            data = resp.json()
            
            if resp.status_code != 200 or not data.get("features"):
                return {
                    "service": "geoapify",
                    "found": False,
                    "address": "",
                    "company_name_found": "",
                    "confidence": 0.0,
                    "error": f"API-Fehler: {resp.status_code}"
                }
            
            feature = data["features"][0]
            properties = feature.get("properties", {})
            
            # Baue Adresse aus Properties
            found_address_parts = []
            if properties.get("street"):
                found_address_parts.append(properties["street"])
            if properties.get("housenumber"):
                found_address_parts.append(properties["housenumber"])
            if properties.get("postcode"):
                found_address_parts.append(properties["postcode"])
            if properties.get("city"):
                found_address_parts.append(properties["city"])
            
            found_address = ", ".join(found_address_parts)
            
            # Prüfe ob Firmenname in Properties steht (manchmal in "name" oder "amenity")
            company_name_found = properties.get("name", "") or properties.get("amenity", "")
            
            # Vergleich
            address_sim = similarity(address.lower(), found_address.lower())
            company_sim = similarity(normalize_company_name(company_name), normalize_company_name(company_name_found)) if company_name_found else 0.0
            
            found = address_sim > 0.7 or company_sim > 0.6
            
            return {
                "service": "geoapify",
                "found": found,
                "address": found_address,
                "company_name_found": company_name_found,
                "confidence": max(address_sim, company_sim),
                "address_match": address_sim > 0.7,
                "similarity": company_sim
            }
            
    except Exception as e:
        return {
            "service": "geoapify",
            "found": False,
            "address": "",
            "company_name_found": "",
            "confidence": 0.0,
            "error": str(e)
        }


async def verify_with_nominatim(lat: float, lon: float, company_name: str, address: str) -> Dict[str, Any]:
    """
    Verifiziert Koordinaten mit Nominatim (OpenStreetMap) Reverse Geocoding.
    
    Returns:
        {
            "service": "nominatim",
            "found": bool,
            "address": str,
            "company_name_found": str,
            "confidence": float,
            "error": str (optional)
        }
    """
    try:
        geolocator = Nominatim(user_agent="famo_trafficapp_verifier")
        
        # Reverse Geocoding
        location = geolocator.reverse((lat, lon), timeout=10, language="de")
        
        if not location:
            return {
                "service": "nominatim",
                "found": False,
                "address": "",
                "company_name_found": "",
                "confidence": 0.0,
                "error": "Keine Ergebnisse von Nominatim"
            }
        
        found_address = location.address or ""
        
        # Prüfe Raw-Daten für Firmennamen
        raw = location.raw or {}
        address_parts = raw.get("address", {})
        company_name_found = address_parts.get("name", "") or address_parts.get("amenity", "") or ""
        
        # Vergleich
        address_sim = similarity(address.lower(), found_address.lower())
        company_sim = similarity(normalize_company_name(company_name), normalize_company_name(company_name_found)) if company_name_found else 0.0
        
        found = address_sim > 0.7 or company_sim > 0.6
        
        return {
            "service": "nominatim",
            "found": found,
            "address": found_address,
            "company_name_found": company_name_found,
            "confidence": max(address_sim, company_sim),
            "address_match": address_sim > 0.7,
            "similarity": company_sim
        }
        
    except Exception as e:
        return {
            "service": "nominatim",
            "found": False,
            "address": "",
            "company_name_found": "",
            "confidence": 0.0,
            "error": str(e)
        }


async def verify_coordinate(
    lat: float,
    lon: float,
    company_name: str,
    address: str
) -> Dict[str, Any]:
    """
    Verifiziert Koordinaten mit allen 3 Services parallel.
    
    Returns:
        {
            "google_maps": {...},
            "geoapify": {...},
            "nominatim": {...},
            "overall_status": "all_good" | "needs_review" | "critical",
            "success_count": int (0-3)
        }
    """
    import asyncio
    
    # Parallel alle 3 Services abfragen
    results = await asyncio.gather(
        verify_with_google_maps(lat, lon, company_name, address),
        verify_with_geoapify(lat, lon, company_name, address),
        verify_with_nominatim(lat, lon, company_name, address),
        return_exceptions=True
    )
    
    google_result = results[0] if not isinstance(results[0], Exception) else {
        "service": "google_maps",
        "found": False,
        "error": str(results[0])
    }
    geoapify_result = results[1] if not isinstance(results[1], Exception) else {
        "service": "geoapify",
        "found": False,
        "error": str(results[1])
    }
    nominatim_result = results[2] if not isinstance(results[2], Exception) else {
        "service": "nominatim",
        "found": False,
        "error": str(results[2])
    }
    
    success_count = sum([
        google_result.get("found", False),
        geoapify_result.get("found", False),
        nominatim_result.get("found", False)
    ])
    
    # Overall Status
    if success_count == 3:
        overall_status = "all_good"
    elif success_count >= 1:
        overall_status = "needs_review"
    else:
        overall_status = "critical"
    
    return {
        "google_maps": google_result,
        "geoapify": geoapify_result,
        "nominatim": nominatim_result,
        "overall_status": overall_status,
        "success_count": success_count,
        "total_services": 3
    }

