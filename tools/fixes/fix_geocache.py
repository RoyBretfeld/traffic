#!/usr/bin/env python3
import sqlite3

def fix_geocache():
    """Bereinige die Geocache-Tabelle von problematischen Einträgen"""
    
    conn = sqlite3.connect('data/traffic.db')
    
    # Zähle problematische Einträge
    cur = conn.execute("SELECT COUNT(*) FROM geocache WHERE lat = 'lat' OR lon = 'lon'")
    count = cur.fetchone()[0]
    print(f"Gefunden: {count} problematische Einträge")
    
    if count > 0:
        # Zeige problematische Einträge
        cur = conn.execute("SELECT adresse, lat, lon, provider FROM geocache WHERE lat = 'lat' OR lon = 'lon'")
        rows = cur.fetchall()
        print("\nProblematische Einträge:")
        for row in rows:
            print(f"  {row[0]} -> lat: {row[1]}, lon: {row[2]}, provider: {row[3]}")
        
        # Lösche problematische Einträge
        cur = conn.execute("DELETE FROM geocache WHERE lat = 'lat' OR lon = 'lon'")
        deleted = cur.rowcount
        conn.commit()
        
        print(f"\nGelöscht: {deleted} problematische Einträge")
        
        # Prüfe ob noch problematische Einträge vorhanden sind
        cur = conn.execute("SELECT COUNT(*) FROM geocache WHERE lat = 'lat' OR lon = 'lon'")
        remaining = cur.fetchone()[0]
        print(f"Verbleibende problematische Einträge: {remaining}")
        
        if remaining == 0:
            print("✅ Geocache erfolgreich bereinigt!")
        else:
            print("❌ Es sind noch problematische Einträge vorhanden")
    else:
        print("✅ Keine problematischen Einträge gefunden")
    
    conn.close()

if __name__ == "__main__":
    fix_geocache()
