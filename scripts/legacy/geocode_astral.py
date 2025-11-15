#!/usr/bin/env python3
"""
Geocode Astral UG Adresse
"""
import sys
import asyncio
import httpx
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from services.geocode_fill import _geocode_one
from repositories.geo_repo import upsert

async def geocode_astral():
    address = 'Löbtauer Straße 89, 01159 Dresden'
    company_name = 'Astral UG'
    
    print(f'Geocode: {address}')
    
    try:
        async with httpx.AsyncClient() as client:
            result = await _geocode_one(address, client, company_name)
            
            if result and result.get('lat') and result.get('lon'):
                print(f'✅ Geocoding erfolgreich!')
                print(f'   Koordinaten: {result["lat"]}, {result["lon"]}')
                
                # Im Geo-Cache speichern
                upsert(address, float(result['lat']), float(result['lon']), company_name=company_name)
                print('   💾 Im Geo-Cache gespeichert')
                return True
            else:
                print(f'❌ Geocoding fehlgeschlagen')
                return False
                
    except Exception as e:
        print(f'❌ Fehler: {e}')
        return False

if __name__ == '__main__':
    asyncio.run(geocode_astral())
