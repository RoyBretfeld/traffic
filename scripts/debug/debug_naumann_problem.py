from repositories.geo_repo import bulk_get, normalize_addr
from repositories.geo_fail_repo import get_fail_status
from sqlalchemy import text
from db.core import ENGINE

# Prüfe alle Varianten der problematischen Adressen
addresses_to_check = [
    'Naumannstr. 12 / Halle 26F, 01809 Heidenau',  # PM Car Parts
    'Naumannstraße 12 | Halle 14, 01809 Heidenau',  # Dreihundert Dresden
    'PM Car Parts, Naumannstr. 12 / Halle 26F, 01809 Heidenau',
    'Dreihundert Dresden, Naumannstraße 12 | Halle 14, 01809 Heidenau'
]

print('🔍 Prüfe alle Varianten:')
for addr in addresses_to_check:
    geo_result = bulk_get([addr])
    if addr in geo_result:
        result = geo_result[addr]
        print(f'✅ Gefunden: {addr}')
        print(f'   Koordinaten: {result["lat"]}, {result["lon"]}')
    else:
        print(f'❌ Nicht gefunden: {addr}')
        
        # Prüfe auch Fail-Cache
        norm_addr = normalize_addr(addr)
        fail_status = get_fail_status(norm_addr)
        if fail_status:
            print(f'   ⚠️  In Fail-Cache: {fail_status["reason"]} bis {fail_status["expires_at"]}')

print()
print('🔍 Prüfe alle Einträge mit "Naumann":')
with ENGINE.begin() as conn:
    result = conn.execute(text('SELECT address_norm, lat, lon, source, by_user FROM geo_cache WHERE address_norm LIKE "%Naumann%"'))
    rows = result.fetchall()
    for row in rows:
        print(f'📋 {row[0]} -> {row[1]}, {row[2]} (Source: {row[3]}, User: {row[4]})')

print()
print('🔍 Prüfe alle Einträge mit "PM Car" oder "Dreihundert":')
with ENGINE.begin() as conn:
    result = conn.execute(text('SELECT address_norm, lat, lon, source, by_user FROM geo_cache WHERE address_norm LIKE "%PM Car%" OR address_norm LIKE "%Dreihundert%"'))
    rows = result.fetchall()
    for row in rows:
        print(f'📋 {row[0]} -> {row[1]}, {row[2]} (Source: {row[3]}, User: {row[4]})')

print()
print('🔍 Prüfe Fail-Cache für beide Adressen:')
for addr in ['Naumannstraße 12 | Halle 14, 01809 Heidenau', 'Naumannstr. 12 / Halle 26F, 01809 Heidenau']:
    norm_addr = normalize_addr(addr)
    fail_status = get_fail_status(norm_addr)
    if fail_status:
        print(f'❌ {addr} -> Fail-Cache: {fail_status["reason"]} bis {fail_status["expires_at"]}')
    else:
        print(f'✅ {addr} -> Nicht im Fail-Cache')
