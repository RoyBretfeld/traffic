#!/usr/bin/env python3
"""
Prüft ungültige Adressen in der Datenbank
"""
import sys
sys.path.append('.')

from backend.db.dao import _connect

def check_invalid_addresses():
    """Prüft ungültige Adressen mit 'nan' oder ähnlichen Problemen"""
    conn = _connect()
    cursor = conn.cursor()
    
    # Suche nach ungültigen Adressen
    cursor.execute("""
        SELECT name, adresse, lat, lon 
        FROM kunden 
        WHERE adresse LIKE '%nan%' 
           OR adresse LIKE '%NaN%'
           OR adresse LIKE '%None%'
           OR adresse = ''
           OR adresse IS NULL
           OR lat IS NULL 
           OR lon IS NULL
           OR lat = 0 
           OR lon = 0
    """)
    
    invalid = cursor.fetchall()
    
    print("🚨 UNGÜLTIGE ADRESSEN IN DER DATENBANK:")
    print("=" * 80)
    
    if invalid:
        for i, (name, adresse, lat, lon) in enumerate(invalid, 1):
            print(f"{i:2d}. {name}")
            print(f"    Adresse: '{adresse}'")
            print(f"    Koordinaten: lat={lat}, lon={lon}")
            print()
    else:
        print("✅ Keine ungültigen Adressen gefunden!")
    
    conn.close()
    return invalid

if __name__ == "__main__":
    check_invalid_addresses()
