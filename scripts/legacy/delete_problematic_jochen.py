#!/usr/bin/env python3
"""
LÖSCHT DEN PROBLEMATISCHEN JOCHEEN - PF EINTRAG SOFORT!
"""
import sys
sys.path.append('.')

from backend.db.dao import _connect

def delete_problematic_jochen():
    """Löscht den problematischen Jochen - PF Eintrag sofort"""
    conn = _connect()
    cursor = conn.cursor()
    
    print("🚨 LÖSCHE PROBLEMATISCHEN JOCHEEN - PF EINTRAG:")
    print("=" * 60)
    
    # Finde den problematischen Eintrag
    cursor.execute("""
        SELECT name, adresse, lat, lon 
        FROM kunden 
        WHERE name LIKE '%Jochen%' 
          AND adresse LIKE '%nan%'
    """)
    
    problematic = cursor.fetchall()
    
    print("Problematische Einträge:")
    for entry in problematic:
        print(f"   {entry}")
    
    if problematic:
        # Lösche den problematischen Eintrag
        cursor.execute("""
            DELETE FROM kunden 
            WHERE name LIKE '%Jochen%' 
              AND adresse LIKE '%nan%'
        """)
        
        deleted = cursor.rowcount
        conn.commit()
        
        print(f"\n✅ {deleted} problematische Einträge gelöscht!")
        print("🎯 Jetzt sollte kein Vietnam-Marker mehr erscheinen!")
    else:
        print("❌ Keine problematischen Einträge gefunden!")
    
    conn.close()

if __name__ == "__main__":
    delete_problematic_jochen()
