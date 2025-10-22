from repositories.geo_repo import bulk_get
from sqlalchemy import text
from db.core import ENGINE

# Prüfe alle möglichen Varianten der Adresse
addresses_to_check = [
    'Rundteil 7b, 01728 Bannewitz OT Possendorf',
    'Rundteil 7b, 01728 Bannewitz',
    'Rundteil 7b, Bannewitz OT Possendorf',
    'Rundteil 7b, Bannewitz'
]

print('🔍 Prüfe alle Adress-Varianten in der Datenbank:')
for addr in addresses_to_check:
    geo_result = bulk_get([addr])
    if addr in geo_result:
        result = geo_result[addr]
        print(f'✅ Gefunden: {addr}')
        print(f'   Koordinaten: {result["lat"]}, {result["lon"]}')
    else:
        print(f'❌ Nicht gefunden: {addr}')

print()
print('🔍 Prüfe alle Einträge mit "Klassische" oder "Rundteil":')
with ENGINE.begin() as conn:
    result = conn.execute(text('SELECT address_norm, lat, lon FROM geo_cache WHERE address_norm LIKE "%Klassische%" OR address_norm LIKE "%Rundteil%"'))
    rows = result.fetchall()
    for row in rows:
        print(f'📋 {row[0]} -> {row[1]}, {row[2]}')

print()
print('🔍 Prüfe Fail-Cache für diese Adresse:')
with ENGINE.begin() as conn:
    result = conn.execute(text('SELECT address_norm, reason FROM geo_fail WHERE address_norm LIKE "%Rundteil%"'))
    rows = result.fetchall()
    if rows:
        for row in rows:
            print(f'❌ Im Fail-Cache: {row[0]} - {row[1]}')
    else:
        print('✅ Nicht im Fail-Cache')
