import asyncio
from services.geocode_fill import fill_missing

async def test_bulk_ot_geocoding():
    # Die problematischen OT-Adressen
    ot_addresses = [
        'Ringstr. 43, 01468 Moritzburg OT Boxdorf',
        'Rundteil 7b, 01728 Bannewitz OT Possendorf',
        'Oberer Ladenberg 13, 01816 Bad Gottleuba OT Berggießhübel',
        'Alte Str. 33, 01768 Glashütte OT Hirschbach',
        'Zur Quelle 5, 01731 Kreischa OT Saida'
    ]
    
    print(f'Teste OT-Geocoding für {len(ot_addresses)} Adressen...')
    results = await fill_missing(ot_addresses, limit=10, dry_run=True)
    
    for result in results:
        addr = result['address']
        status = result['status']
        if status == 'ok':
            coords = result['result']
            print(f'Erfolg: {addr[:50]}... -> {coords["lat"]:.4f}, {coords["lon"]:.4f}')
        else:
            print(f'Fehler: {addr[:50]}... -> {status}')

asyncio.run(test_bulk_ot_geocoding())
