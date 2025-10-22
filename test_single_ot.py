import asyncio
from services.geocode_fill import _geocode_one
import httpx

async def test_single_ot():
    addr = 'Ringstr. 43, 01468 Moritzburg OT Boxdorf'
    print(f'Teste: {addr}')
    
    async with httpx.AsyncClient(timeout=20) as client:
        result = await _geocode_one(addr, client)
        if result:
            print(f'Erfolg: {result["lat"]:.4f}, {result["lon"]:.4f}')
        else:
            print('Kein Ergebnis')

asyncio.run(test_single_ot())
