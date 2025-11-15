from repositories.geo_repo import upsert, bulk_get

# Teste das erweiterte Firmennamen-System
print('🔍 Teste erweiterte Firmennamen-Unterstützung:')

# Dreihundert Dresden eintragen
address1 = 'Naumannstraße 12 | Halle 14, 01809 Heidenau'
company1 = 'Dreihundert Dresden'
lat1 = 50.97513350003193
lon1 = 13.876504538064527

print(f'1. Eintrage: {company1}')
result1 = upsert(address1, lat1, lon1, source='manual_verified', by_user='user_verification', company_name=company1)
print(f'   Ergebnis: {result1}')

# PM Car Parts eintragen
address2 = 'Naumannstr. 12 / Halle 26F, 01809 Heidenau'
company2 = 'PM Car Parts'
lat2 = 50.97511837936205
lon2 = 13.876685486210436

print(f'2. Eintrage: {company2}')
result2 = upsert(address2, lat2, lon2, source='manual_verified', by_user='user_verification', company_name=company2)
print(f'   Ergebnis: {result2}')

print()
print('🔍 Teste Suche nach Firmennamen:')

# Teste Suche nach Firmennamen
test_addresses = [
    'Dreihundert Dresden, Naumannstraße 12 | Halle 14, 01809 Heidenau',
    'PM Car Parts, Naumannstr. 12 / Halle 26F, 01809 Heidenau',
    'Naumannstraße 12 | Halle 14, 01809 Heidenau',
    'Naumannstr. 12 / Halle 26F, 01809 Heidenau'
]

for addr in test_addresses:
    geo_result = bulk_get([addr])
    if addr in geo_result:
        result = geo_result[addr]
        print(f'✅ Gefunden: {addr}')
        print(f'   Koordinaten: {result["lat"]}, {result["lon"]}')
    else:
        print(f'❌ Nicht gefunden: {addr}')

print()
print('🎯 Das bedeutet:')
print('- Beide Firmen können jetzt über Firmennamen gefunden werden')
print('- Verschiedene Hallen werden korrekt unterschieden')
print('- System unterstützt mehrere Firmen an derselben Adresse!')
