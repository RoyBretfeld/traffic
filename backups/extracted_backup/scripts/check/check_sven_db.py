import sys
sys.path.insert(0, '.')
from backend.db.dao import _connect

print('🔍 DEBUG: Datenbank prüfen - ist Sven in der DB?')
print('=' * 50)

conn = _connect()
cursor = conn.cursor()

# Prüfe kunden Tabelle für "Sven - PF"
print("1. Sven - PF in kunden Tabelle:")
cursor.execute('SELECT name, adresse, lat, lon FROM kunden WHERE name LIKE "%sven%" AND name LIKE "%pf%"')
sven_customers = cursor.fetchall()
if sven_customers:
    for name, adresse, lat, lon in sven_customers:
        print(f'   ✅ {name}: "{adresse}" -> lat={lat}, lon={lon}')
else:
    print("   ❌ Keine Sven - PF Kunden gefunden!")

# Prüfe alle PF-Kunden
print("\n2. Alle PF-Kunden:")
cursor.execute('SELECT name, adresse, lat, lon FROM kunden WHERE name LIKE "%pf%"')
pf_customers = cursor.fetchall()
if pf_customers:
    for name, adresse, lat, lon in pf_customers:
        print(f'   {name}: "{adresse}" -> lat={lat}, lon={lon}')
else:
    print("   ❌ Keine PF-Kunden gefunden!")

# Prüfe geo_cache für Sven-Adressen
print("\n3. Sven-Adressen im geo_cache:")
cursor.execute('SELECT address_norm, lat, lon FROM geo_cache WHERE address_norm LIKE "%sven%"')
sven_cache = cursor.fetchall()
if sven_cache:
    for addr, lat, lon in sven_cache:
        print(f'   ✅ Cache: "{addr}" -> ({lat}, {lon})')
else:
    print("   ❌ Keine Sven Cache-Einträge gefunden!")

conn.close()
