import sys
sys.path.insert(0, '.')
from backend.db.dao import _connect

print('🔍 FINAL FIX: Alle PF-Kunden in DB korrigieren')
print('=' * 50)

conn = _connect()
cursor = conn.cursor()

# Alle PF-Kunden mit leeren Adressen finden und korrigieren
cursor.execute("""
    SELECT name, adresse, lat, lon 
    FROM kunden 
    WHERE name LIKE '%pf%' 
      AND (adresse IS NULL OR adresse = '' OR adresse LIKE '%nan%')
""")

problematic_customers = cursor.fetchall()

if problematic_customers:
    print("❌ Problematische PF-Kunden gefunden:")
    for name, adresse, lat, lon in problematic_customers:
        print(f"   {name}: '{adresse}' -> lat={lat}, lon={lon}")
        
        # Korrekte Adresse und Koordinaten setzen
        if 'jochen' in name.lower():
            cursor.execute("""
                UPDATE kunden 
                SET adresse = 'Pf-Depot Jochen, Dresden',
                    lat = 51.05,
                    lon = 13.7373
                WHERE name = ?
            """, (name,))
        elif 'sven' in name.lower():
            cursor.execute("""
                UPDATE kunden 
                SET adresse = 'Pf-Depot Sven, Dresden',
                    lat = 51.06,
                    lon = 13.73
                WHERE name = ?
            """, (name,))
        else:
            # Fallback für andere PF-Kunden
            cursor.execute("""
                UPDATE kunden 
                SET adresse = 'Pf-Depot, Dresden',
                    lat = 51.05,
                    lon = 13.73
                WHERE name = ?
            """, (name,))
    
    conn.commit()
    print(f"\n✅ {len(problematic_customers)} PF-Kunden korrigiert!")
else:
    print("✅ Keine problematischen PF-Kunden gefunden!")

# Prüfe das Ergebnis
print("\n📋 Alle PF-Kunden nach Fix:")
cursor.execute('SELECT name, adresse, lat, lon FROM kunden WHERE name LIKE "%pf%"')
pf_customers = cursor.fetchall()
for name, adresse, lat, lon in pf_customers:
    print(f"   {name}: '{adresse}' -> lat={lat}, lon={lon}")

conn.close()
