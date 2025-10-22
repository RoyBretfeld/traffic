#!/usr/bin/env python3
"""
Geocoding für die verbleibenden problematischen Adressen
"""
import sys
import asyncio
import httpx
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent))

from services.geocode_fill import _geocode_one
from repositories.geo_repo import upsert

async def geocode_remaining_addresses():
    """Geocode die verbleibenden problematischen Adressen"""
    print(f"🧪 Geocode verbleibende problematische Adressen...")
    
    addresses = [
        ("An der Triebe 25, 01468 Moritzburg", "Sven Teichmann (Kunde 1162)"),
        ("Bergstraße 93, 01744 Dippoldiswalde OT Seifersdorf", "Dippser-Auto-Ecke (Kunde 5646)"),
        ("Hauptstr. 110, 01809 Heidenau", "SachsenNetze GmbH (Kunde 4169)"),
    ]
    
    success_count = 0
    
    try:
        async with httpx.AsyncClient() as client:
            for address, customer_info in addresses:
                print(f"\n📍 Geocode: {address}")
                print(f"   Kunde: {customer_info}")
                
                result = await _geocode_one(address, client, customer_info)
                
                if result and result.get('lat') and result.get('lon'):
                    print(f"   ✅ Geocoding erfolgreich!")
                    print(f"   Koordinaten: {result['lat']}, {result['lon']}")
                    
                    # Im Geo-Cache speichern
                    upsert(address, float(result['lat']), float(result['lon']))
                    print(f"   Adresse im Geo-Cache gespeichert.")
                    success_count += 1
                else:
                    print(f"   ❌ Geocoding fehlgeschlagen")
                    
    except Exception as e:
        print(f"❌ Ein unerwarteter Fehler ist aufgetreten: {e}")
    
    print(f"\n📊 Ergebnis: {success_count}/{len(addresses)} Adressen erfolgreich geocodiert")
    return success_count == len(addresses)

if __name__ == "__main__":
    asyncio.run(geocode_remaining_addresses())
