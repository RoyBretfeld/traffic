#!/usr/bin/env python3
"""
Test Geocoding für Dreihundert Dresden
"""
import sys
import asyncio
import httpx
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from services.geocode_fill import _geocode_one
from repositories.geo_repo import upsert

async def test_dreihundert_geocoding():
    """Teste Geocoding für Dreihundert Dresden"""
    print("🧪 Teste Geocoding für Dreihundert Dresden...")
    
    address = "Naumannstraße 12, Halle 14, 01809 Heidenau"
    
    try:
        async with httpx.AsyncClient() as client:
            result = await _geocode_one(address, client)
            
            if result and result.get('lat') and result.get('lon'):
                print(f"✅ Geocoding erfolgreich!")
                print(f"   Adresse: {address}")
                print(f"   Koordinaten: {result['lat']}, {result['lon']}")
                
                # In Geo-Cache speichern
                upsert(address, result['lat'], result['lon'])
                print(f"   ✅ In Geo-Cache gespeichert!")
                
                return True
            else:
                print(f"❌ Geocoding fehlgeschlagen!")
                print(f"   Ergebnis: {result}")
                return False
                
    except Exception as e:
        print(f"❌ Fehler beim Geocoding: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_dreihundert_geocoding())
    print(f"\n🎯 Geocoding-Test {'erfolgreich' if success else 'fehlgeschlagen'}!")
