#!/usr/bin/env python3
"""
Prüft Jochen - PF Synonyme und Adressen
"""
import sys
sys.path.append('.')

from backend.db.dao import _connect

def check_jochen_pf():
    """Prüft ob es Synonyme oder Adressen für Jochen - PF gibt"""
    conn = _connect()
    cursor = conn.cursor()
    
    print("🔍 PRÜFE JOCHEEN - PF SYNONYME UND ADRESSEN:")
    print("=" * 60)
    
    # 1. Prüfe geo_alias Tabelle
    cursor.execute("""
        SELECT * FROM geo_alias 
        WHERE address_norm LIKE '%Jochen%' 
           OR address_norm LIKE '%jochen%'
           OR canonical_norm LIKE '%Jochen%'
           OR canonical_norm LIKE '%jochen%'
    """)
    jochen_aliases = cursor.fetchall()
    
    print("1. Jochen Aliases:")
    if jochen_aliases:
        for alias in jochen_aliases:
            print(f"   {alias}")
    else:
        print("   ❌ Keine Jochen Aliases gefunden!")
    
    # 2. Prüfe geo_cache Tabelle
    cursor.execute("""
        SELECT * FROM geo_cache 
        WHERE address_norm LIKE '%Jochen%' 
           OR address_norm LIKE '%jochen%'
    """)
    jochen_cache = cursor.fetchall()
    
    print("\n2. Jochen Cache:")
    if jochen_cache:
        for cache in jochen_cache:
            print(f"   {cache}")
    else:
        print("   ❌ Keine Jochen Cache-Einträge gefunden!")
    
    # 3. Prüfe kunden Tabelle nach Jochen
    cursor.execute("""
        SELECT name, adresse, lat, lon 
        FROM kunden 
        WHERE name LIKE '%Jochen%' 
           OR name LIKE '%jochen%'
    """)
    jochen_customers = cursor.fetchall()
    
    print("\n3. Jochen Kunden:")
    if jochen_customers:
        for customer in jochen_customers:
            print(f"   {customer}")
    else:
        print("   ❌ Keine Jochen Kunden gefunden!")
    
    # 4. Prüfe nach PF-Kunden
    cursor.execute("""
        SELECT name, adresse, lat, lon 
        FROM kunden 
        WHERE name LIKE '%PF%' 
           OR name LIKE '%pf%'
    """)
    pf_customers = cursor.fetchall()
    
    print("\n4. PF Kunden:")
    if pf_customers:
        for customer in pf_customers:
            print(f"   {customer}")
    else:
        print("   ❌ Keine PF Kunden gefunden!")
    
    conn.close()
    
    return jochen_aliases, jochen_cache, jochen_customers, pf_customers

if __name__ == "__main__":
    check_jochen_pf()
