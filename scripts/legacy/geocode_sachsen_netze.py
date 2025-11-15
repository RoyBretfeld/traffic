#!/usr/bin/env python3
"""
Geocoding für SachsenNetze GmbH (Kunde 4169)
"""
import sys
import asyncio
import httpx
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

from services.geocode_fill import _geocode_one
from repositories.geo_repo import upsert

async def geocode_sachsen_netze():
    """Geocode SachsenNetze GmbH Adresse"""
    print(f"🧪 Geocode SachsenNetze GmbH (Kunde 4169)...")
    
    address = "Friedrich-List-Platz 2, 01069 Dresden"
    
    try:
        async with httpx.AsyncClient() as client:
            result = await _geocode_one(address, client, "SachsenNetze GmbH")
            
            if result and result.get('lat') and result.get('lon'):
                print(f"✅ Geocoding erfolgreich!")
                print(f"   Adresse: {address}")
                print(f"   Koordinaten: {result['lat']}, {result['lon']}")
                
                # Im Geo-Cache speichern
                upsert(address, float(result['lat']), float(result['lon']))
                print("   Adresse im Geo-Cache gespeichert.")
                return True
            else:
                print(f"❌ Geocoding fehlgeschlagen für: {address}")
                return False
                
    except httpx.RequestError as e:
        print(f"❌ Fehler beim HTTP-Request: {e}")
        return False
    except Exception as e:
        print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(geocode_sachsen_netze())
