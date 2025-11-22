"""
API-Endpoints für Tank- und Strompreise
"""
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse
from backend.services.fuel_price_api import get_current_fuel_prices
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/api/fuel-prices/current")
async def get_current_fuel_prices_endpoint(
    force_refresh: bool = Query(False, description="Cache ignorieren und neu laden")
):
    """
    Gibt aktuelle Tankpreise zurück (Diesel, E10, E5, AdBlue).
    
    Preise werden von Tankerkönig API geladen (kostenlos, Creative Commons).
    Preise werden 5 Minuten gecacht.
    
    Returns:
        JSON mit aktuellen Preisen
    """
    try:
        prices = await get_current_fuel_prices(force_refresh=force_refresh)
        
        # Berechne Preisänderungen (gegenüber vorherigem Wert)
        # TODO: Preisverlauf in DB speichern für echte Änderungsberechnung
        
        result = {
            "success": True,
            "prices": {
                "diesel": {
                    "price": prices["diesel"]["price"],
                    "unit": prices["diesel"]["unit"],
                    "source": prices["diesel"]["source"],
                    "last_update": prices["diesel"]["last_update"],
                    "change": 0.0  # TODO: Berechnen aus Preisverlauf
                },
                "e10": {
                    "price": prices["e10"]["price"],
                    "unit": prices["e10"]["unit"],
                    "source": prices["e10"]["source"],
                    "last_update": prices["e10"]["last_update"],
                    "change": 0.0
                },
                "e5": {
                    "price": prices["e5"]["price"],
                    "unit": prices["e5"]["unit"],
                    "source": prices["e5"]["source"],
                    "last_update": prices["e5"]["last_update"],
                    "change": 0.0
                },
                "adblue": {
                    "price": prices["adblue"]["price"],
                    "unit": prices["adblue"]["unit"],
                    "source": prices["adblue"]["source"],
                    "last_update": prices["adblue"]["last_update"],
                    "change": 0.0
                }
            },
            "timestamp": datetime.now().isoformat()
        }
        
        return JSONResponse(result)
        
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Tankpreise: {e}", exc_info=True)
        return JSONResponse({
            "success": False,
            "error": str(e),
            "prices": {}
        }, status_code=500)


@router.get("/api/fuel-prices/history")
async def get_fuel_price_history(
    days: int = Query(7, description="Anzahl Tage für Preisverlauf")
):
    """
    Gibt Preisverlauf zurück (für Chart).
    
    TODO: Implementierung folgt (Preise in DB speichern)
    """
    # TODO: Lade Preisverlauf aus DB
    return JSONResponse({
        "success": True,
        "history": [],
        "message": "Preisverlauf wird noch nicht gespeichert"
    })


@router.get("/api/electricity-prices/current")
async def get_current_electricity_prices():
    """
    Gibt aktuelle Strompreise zurück (vorsorglich).
    
    TODO: Implementierung folgt später
    """
    return JSONResponse({
        "success": True,
        "prices": {
            "ac": {
                "price": None,
                "unit": "€/kWh",
                "source": "not_implemented",
                "last_update": None
            },
            "dc": {
                "price": None,
                "unit": "€/kWh",
                "source": "not_implemented",
                "last_update": None
            },
            "home": {
                "price": None,
                "unit": "€/kWh",
                "source": "not_implemented",
                "last_update": None
            }
        },
        "message": "Strompreise werden später implementiert"
    })

