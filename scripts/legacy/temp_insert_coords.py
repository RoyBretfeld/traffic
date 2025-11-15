from repositories.geo_repo import upsert

# Koordinaten für Klassische Automobile Schwarz eintragen
address = 'Rundteil 7b, 01728 Bannewitz OT Possendorf'
lat = 50.95465562741884
lon = 13.70053199609067

print(f'📍 Eintrage Koordinaten für: {address}')
print(f'   Koordinaten: {lat}, {lon}')

result = upsert(address, lat, lon, source='manual_verified', by_user='user_verification')
print(f'✅ Erfolgreich eingetragen: {result}')

# Verifikation
from repositories.geo_repo import bulk_get
geo_result = bulk_get([address])
if address in geo_result:
    stored = geo_result[address]
    stored_lat = stored['lat']
    stored_lon = stored['lon']
    print(f'\n🔍 Verifikation:')
    print(f'   Gespeichert: {stored_lat}, {stored_lon}')
    print(f'   ✅ Adresse ist jetzt geocodiert!')
else:
    print('❌ Fehler: Adresse nicht gefunden nach Eintragung')
