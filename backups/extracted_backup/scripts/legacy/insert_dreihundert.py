from repositories.geo_repo import upsert

# Koordinaten für Dreihundert Dresden eintragen
address = 'Naumannstraße 12 | Halle 14, 01809 Heidenau'
lat = 50.97513350003193
lon = 13.876504538064527

print('📍 Eintrage Koordinaten für:', address)
print('   Koordinaten:', lat, lon)

result = upsert(address, lat, lon, source='manual_verified', by_user='user_verification')
print('✅ Erfolgreich eingetragen:', result)

# Verifikation
from repositories.geo_repo import bulk_get
geo_result = bulk_get([address])
if address in geo_result:
    stored = geo_result[address]
    print('🔍 Verifikation:')
    print('   Gespeichert:', stored['lat'], stored['lon'])
    print('   ✅ Adresse ist jetzt geocodiert!')
else:
    print('❌ Fehler: Adresse nicht gefunden nach Eintragung')
