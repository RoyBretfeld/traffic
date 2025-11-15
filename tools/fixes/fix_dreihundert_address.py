#!/usr/bin/env python3
import sqlite3

def fix_dreihundert_address():
    """Korrigiere die Adresse für Dreihundert Dresden"""
    
    conn = sqlite3.connect('data/traffic.db')
    
    # Suche nach Dreihundert Dresden
    cur = conn.execute("SELECT id, name, adresse FROM kunden WHERE name LIKE '%dreihundert%'")
    rows = cur.fetchall()
    
    print("Gefundene Dreihundert-Einträge:")
    for row in rows:
        print(f"  ID: {row[0]}, Name: {row[1]}, Adresse: {row[2]}")
    
    if rows:
        # Aktualisiere die Adresse
        kunde_id = rows[0][0]
        old_address = rows[0][2]
        new_address = "Naumannstraße 12, 01809 Heidenau"
        
        cur = conn.execute(
            "UPDATE kunden SET adresse = ? WHERE id = ?",
            (new_address, kunde_id)
        )
        
        if cur.rowcount > 0:
            print(f"\nOK: Adresse für Dreihundert Dresden aktualisiert:")
            print(f"   Alt: {old_address}")
            print(f"   Neu: {new_address}")
            
            # Alte Adresse aus Geocache löschen
            cur = conn.execute("DELETE FROM geocache WHERE adresse = ?", (old_address,))
            print(f"   Alte Adresse aus Geocache gelöscht")
            
            # Neue Adresse mit den bereits vorhandenen Koordinaten in Geocache speichern
            lat = 50.9751327689272
            lon = 13.876502328748547
            cur = conn.execute(
                "INSERT OR REPLACE INTO geocache (adresse, lat, lon, provider) VALUES (?, ?, ?, ?)",
                (new_address, lat, lon, "manual_correction")
            )
            print(f"   Neue Adresse in Geocache gespeichert: {lat}, {lon}")
        else:
            print("ERROR: Keine Zeilen aktualisiert")
        
        conn.commit()
    else:
        print("ERROR: Kein Dreihundert-Eintrag gefunden")
    
    conn.close()

if __name__ == "__main__":
    fix_dreihundert_address()
