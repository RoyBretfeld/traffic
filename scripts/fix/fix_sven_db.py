import sys
sys.path.insert(0, '.')
from backend.db.dao import _connect

print('🔍 DEBUG: Sven - PF in DB fixen')
print('=' * 50)

conn = _connect()
cursor = conn.cursor()

# Update "sven - pf" mit Synonym-Adresse und Koordinaten
cursor.execute("""
    UPDATE kunden 
    SET adresse = 'Pf-Depot Sven, Dresden',
        lat = 51.06,
        lon = 13.73
    WHERE name = 'sven - pf' AND (adresse IS NULL OR adresse = '')
""")

print(f"✅ {cursor.rowcount} Sven - PF Einträge aktualisiert!")

# Prüfe das Ergebnis
cursor.execute('SELECT name, adresse, lat, lon FROM kunden WHERE name = "sven - pf"')
result = cursor.fetchone()
if result:
    name, adresse, lat, lon = result
    print(f"✅ Ergebnis: {name} -> '{adresse}' -> lat={lat}, lon={lon}")

conn.commit()
conn.close()
