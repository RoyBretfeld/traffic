import asyncio
from services.geocode_fill import _geocode_one
import httpx

async def test_ot_geocoding():
    # Test-Adressen
    test_addrs = [
        'Ringstr. 43, 01468 Moritzburg OT Boxdorf',
        'Rundteil 7b, 01728 Bannewitz OT Possendorf'
    ]
    
    async with httpx.AsyncClient(timeout=20) as client:
        for addr in test_addrs:
            print(f'Teste: {addr}')
            try:
                result = await _geocode_one(addr, client)
                if result:
                    print(f'  Erfolg: {result["lat"]:.4f}, {result["lon"]:.4f}')
                else:
                    print(f'  Kein Ergebnis')
            except Exception as e:
                print(f'  Fehler: {e}')
            print()

asyncio.run(test_ot_geocoding())
