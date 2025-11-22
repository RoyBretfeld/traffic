"""
Tankstellen-Preis-API Service
Lädt aktuelle Preise von Tankerkönig API (kostenlos, Creative Commons)
"""
import logging
import httpx
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from backend.config import cfg
import json

logger = logging.getLogger(__name__)

# Cache für Preise (5 Minuten TTL)
_price_cache = {
    "diesel": None,
    "e10": None,
    "e5": None,
    "adblue": None,
    "last_update": None,
    "cache_ttl_minutes": 5
}

# Dresden Koordinaten (für Suche)
DRESDEN_LAT = 51.0504
DRESDEN_LON = 13.7373
SEARCH_RADIUS_KM = 10  # 10km Radius um Dresden


def get_tankerkoenig_api_key() -> Optional[str]:
    """Lädt Tankerkönig API-Key aus Config."""
    # Versuche aus .env oder config/app.yaml
    import os
    api_key = os.getenv("TANKERKOENIG_API_KEY")
    if api_key:
        return api_key
    
    # Fallback: Aus config/app.yaml
    api_key = cfg("tankerkoenig:api_key", None)
    return api_key


async def fetch_fuel_prices_from_api() -> Dict:
    """
    Lädt aktuelle Tankpreise von Tankerkönig API.
    
    Returns:
        Dict mit Preisen für Diesel, E10, E5, AdBlue
    """
    api_key = get_tankerkoenig_api_key()
    
    if not api_key:
        logger.warning("Tankerkönig API-Key nicht konfiguriert. Verwende Fallback-Preise.")
        return get_fallback_prices()
    
    try:
        # Tankerkönig API: Suche nach Tankstellen in Dresden
        # Endpoint: https://creativecommons.tankerkoenig.de/json/list.php
        url = "https://creativecommons.tankerkoenig.de/json/list.php"
        
        params = {
            "lat": DRESDEN_LAT,
            "lng": DRESDEN_LON,
            "rad": SEARCH_RADIUS_KM,
            "sort": "price",  # Sortiere nach Preis
            "type": "diesel",  # Suche nach Diesel (günstigste)
            "apikey": api_key
        }
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("ok") and data.get("stations"):
                stations = data["stations"]
                
                # Finde günstigste Preise
                diesel_prices = []
                e10_prices = []
                e5_prices = []
                
                for station in stations:
                    if station.get("diesel"):
                        diesel_prices.append({
                            "price": float(station["diesel"]),
                            "station": station.get("name", "Unbekannt"),
                            "address": station.get("street", "") + ", " + station.get("place", "")
                        })
                    if station.get("e10"):
                        e10_prices.append({
                            "price": float(station["e10"]),
                            "station": station.get("name", "Unbekannt"),
                            "address": station.get("street", "") + ", " + station.get("place", "")
                        })
                    if station.get("e5"):
                        e5_prices.append({
                            "price": float(station["e5"]),
                            "station": station.get("name", "Unbekannt"),
                            "address": station.get("street", "") + ", " + station.get("place", "")
                        })
                
                # Sortiere nach Preis und nimm Durchschnitt der 5 günstigsten
                diesel_avg = sum(s["price"] for s in sorted(diesel_prices, key=lambda x: x["price"])[:5]) / min(5, len(diesel_prices)) if diesel_prices else None
                e10_avg = sum(s["price"] for s in sorted(e10_prices, key=lambda x: x["price"])[:5]) / min(5, len(e10_prices)) if e10_prices else None
                e5_avg = sum(s["price"] for s in sorted(e5_prices, key=lambda x: x["price"])[:5]) / min(5, len(e5_prices)) if e5_prices else None
                
                # AdBlue: Keine API-Daten, verwende Standard-Preis
                adblue_price = 0.80  # Standard-Preis (kann später aus Config kommen)
                
                result = {
                    "diesel": {
                        "price": diesel_avg,
                        "unit": "€/L",
                        "source": "tankerkoenig",
                        "last_update": datetime.now().isoformat(),
                        "stations_count": len(diesel_prices)
                    },
                    "e10": {
                        "price": e10_avg,
                        "unit": "€/L",
                        "source": "tankerkoenig",
                        "last_update": datetime.now().isoformat(),
                        "stations_count": len(e10_prices)
                    },
                    "e5": {
                        "price": e5_avg,
                        "unit": "€/L",
                        "source": "tankerkoenig",
                        "last_update": datetime.now().isoformat(),
                        "stations_count": len(e5_prices)
                    },
                    "adblue": {
                        "price": adblue_price,
                        "unit": "€/L",
                        "source": "standard",
                        "last_update": datetime.now().isoformat()
                    }
                }
                
                # Cache aktualisieren
                global _price_cache
                _price_cache.update({
                    "diesel": result["diesel"],
                    "e10": result["e10"],
                    "e5": result["e5"],
                    "adblue": result["adblue"],
                    "last_update": datetime.now()
                })
                
                return result
            else:
                logger.warning(f"Tankerkönig API Fehler: {data.get('message', 'Unbekannter Fehler')}")
                return get_fallback_prices()
                
    except Exception as e:
        logger.error(f"Fehler beim Laden der Tankpreise: {e}", exc_info=True)
        return get_fallback_prices()


def get_fallback_prices() -> Dict:
    """Gibt Fallback-Preise zurück (wenn API nicht verfügbar)."""
    return {
        "diesel": {
            "price": 1.45,
            "unit": "€/L",
            "source": "fallback",
            "last_update": datetime.now().isoformat()
        },
        "e10": {
            "price": 1.55,
            "unit": "€/L",
            "source": "fallback",
            "last_update": datetime.now().isoformat()
        },
        "e5": {
            "price": 1.60,
            "unit": "€/L",
            "source": "fallback",
            "last_update": datetime.now().isoformat()
        },
        "adblue": {
            "price": 0.80,
            "unit": "€/L",
            "source": "standard",
            "last_update": datetime.now().isoformat()
        }
    }


def get_cached_prices() -> Optional[Dict]:
    """Gibt gecachte Preise zurück, falls noch gültig."""
    global _price_cache
    
    if _price_cache["last_update"] is None:
        return None
    
    # Prüfe ob Cache noch gültig
    cache_age = datetime.now() - _price_cache["last_update"]
    if cache_age.total_seconds() < (_price_cache["cache_ttl_minutes"] * 60):
        return {
            "diesel": _price_cache["diesel"],
            "e10": _price_cache["e10"],
            "e5": _price_cache["e5"],
            "adblue": _price_cache["adblue"]
        }
    
    return None


async def get_current_fuel_prices(force_refresh: bool = False) -> Dict:
    """
    Gibt aktuelle Tankpreise zurück (mit Caching).
    
    Args:
        force_refresh: Wenn True, Cache ignorieren und neu laden
    
    Returns:
        Dict mit Preisen
    """
    # Prüfe Cache (außer bei force_refresh)
    if not force_refresh:
        cached = get_cached_prices()
        if cached:
            return cached
    
    # Lade neue Preise
    return await fetch_fuel_prices_from_api()

