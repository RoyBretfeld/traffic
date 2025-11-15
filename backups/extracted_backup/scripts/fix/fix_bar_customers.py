#!/usr/bin/env python3
"""
Behebt BAR-Kunden mit ungültigen Adressen
"""
import sys
sys.path.append('.')

from backend.db.dao import _connect

def fix_bar_customers():
    """Entfernt Koordinaten von BAR-Kunden mit leeren Adressen"""
    conn = _connect()
    cursor = conn.cursor()
    
    # Finde BAR-Kunden mit leeren Adressen
    cursor.execute("""
        SELECT name, adresse, lat, lon 
        FROM kunden 
        WHERE (adresse = '' OR adresse IS NULL)
          AND (lat IS NOT NULL OR lon IS NOT NULL)
    """)
    
    invalid_bar = cursor.fetchall()
    
    print("🚨 BAR-KUNDEN MIT UNGÜLTIGEN ADRESSEN:")
    print("=" * 60)
    
    for name, adresse, lat, lon in invalid_bar:
        print(f"❌ {name}: '{adresse}' -> lat={lat}, lon={lon}")
    
    if invalid_bar:
        # Lösche Koordinaten von BAR-Kunden mit leeren Adressen
        cursor.execute("""
            UPDATE kunden 
            SET lat = NULL, lon = NULL 
            WHERE (adresse = '' OR adresse IS NULL)
              AND (lat IS NOT NULL OR lon IS NOT NULL)
        """)
        
        affected = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ {affected} BAR-Kunden Koordinaten gelöscht!")
        print("🎯 Diese Kunden werden jetzt als 'warn' oder 'bad' angezeigt!")
    else:
        print("✅ Keine BAR-Kunden mit ungültigen Adressen gefunden!")
    
    conn.close()
    return len(invalid_bar)

if __name__ == "__main__":
    fix_bar_customers()
