from repositories.geo_repo import upsert

# Korrekte Adresse für PM Car Parts eintragen
address = 'Naumannstr. 12 / Halle 26F, 01809 Heidenau'
lat = 50.97511837936205
lon = 13.876685486210436

print('📍 Eintrage Koordinaten für PM Car Parts:')
print('   Adresse:', address)
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
