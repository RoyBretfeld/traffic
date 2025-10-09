#!/usr/bin/env python3
import sqlite3

def fix_mehlig_coordinates():
    """Korrigiere die Koordinaten für Autoservice Mehlig"""
    
    conn = sqlite3.connect('data/traffic.db')
    
    # Suche nach Autoservice Mehlig
    cur = conn.execute("SELECT id, name, adresse FROM kunden WHERE name LIKE '%Mehlig%'")
    rows = cur.fetchall()
    
    print("Gefundene Mehlig-Einträge:")
    for row in rows:
        print(f"  ID: {row[0]}, Name: {row[1]}, Adresse: {row[2]}")
    
    if rows:
        # Aktualisiere die Koordinaten
        kunde_id = rows[0][0]
        lat = 51.120528130052655
        lon = 13.696519739561964
        
        cur = conn.execute(
            "UPDATE kunden SET lat = ?, lon = ? WHERE id = ?",
            (lat, lon, kunde_id)
        )
        
        if cur.rowcount > 0:
            print(f"\nOK: Koordinaten für Autoservice Mehlig aktualisiert:")
            print(f"   Lat: {lat}")
            print(f"   Lon: {lon}")
            
            # Auch in Geocache speichern
            adresse = rows[0][2]
            if adresse:
                cur = conn.execute(
                    "INSERT OR REPLACE INTO geocache (adresse, lat, lon, provider) VALUES (?, ?, ?, ?)",
                    (adresse, lat, lon, "manual_correction")
                )
                print(f"   Geocache aktualisiert für: {adresse}")
        else:
            print("ERROR: Keine Zeilen aktualisiert")
        
        conn.commit()
    else:
        print("ERROR: Kein Mehlig-Eintrag gefunden")
    
    conn.close()

if __name__ == "__main__":
    fix_mehlig_coordinates()
