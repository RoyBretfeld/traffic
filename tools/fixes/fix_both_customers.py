#!/usr/bin/env python3
import sqlite3

def fix_both_customers():
    """Korrigiere die Koordinaten für beide fehlgeschlagenen Kunden"""
    
    conn = sqlite3.connect('data/traffic.db')
    
    # Kunde 1: Autoservice Mehlig
    mehlig_address = "Schulstraße 25, 01468 Moritzburg (OT Boxdorf)"
    mehlig_lat = 51.120528130052655
    mehlig_lon = 13.696519739561964
    
    # Kunde 2: Dreihundert Dresden  
    dreihundert_address = "Naumannstraße 12 | Halle 14, 01809 Heidenau"
    dreihundert_lat = 50.9751327689272
    dreihundert_lon = 13.876502328748547
    
    # Suche nach den Kunden
    print("Suche nach den Kunden...")
    
    # Suche nach Mehlig (verschiedene Varianten)
    mehlig_found = False
    searches_mehlig = [
        ("%Mehlig%", "Name mit Mehlig"),
        ("%Schulstraße%", "Adresse mit Schulstraße"),
        ("%Moritzburg%", "Adresse mit Moritzburg")
    ]
    
    for pattern, description in searches_mehlig:
        cur = conn.execute("SELECT id, name, adresse FROM kunden WHERE name LIKE ? OR adresse LIKE ?", (pattern, pattern))
        rows = cur.fetchall()
        if rows:
            print(f"Gefunden ({description}):")
            for row in rows:
                print(f"  ID: {row[0]}, Name: {row[1]}, Adresse: {row[2]}")
                if "mehlig" in row[1].lower() or "schulstraße" in row[2].lower():
                    # Aktualisiere Koordinaten
                    cur = conn.execute("UPDATE kunden SET lat = ?, lon = ? WHERE id = ?", (mehlig_lat, mehlig_lon, row[0]))
                    print(f"  -> Koordinaten aktualisiert: {mehlig_lat}, {mehlig_lon}")
                    mehlig_found = True
                    break
        if mehlig_found:
            break
    
    if not mehlig_found:
        print("Mehlig nicht in DB gefunden - füge zu Geocache hinzu")
        cur = conn.execute(
            "INSERT OR REPLACE INTO geocache (adresse, lat, lon, provider) VALUES (?, ?, ?, ?)",
            (mehlig_address, mehlig_lat, mehlig_lon, "manual_correction")
        )
        print(f"Geocache aktualisiert für: {mehlig_address}")
    
    # Suche nach Dreihundert Dresden
    dreihundert_found = False
    searches_dreihundert = [
        ("%Dreihundert%", "Name mit Dreihundert"),
        ("%Naumannstraße%", "Adresse mit Naumannstraße"),
        ("%Heidenau%", "Adresse mit Heidenau")
    ]
    
    for pattern, description in searches_dreihundert:
        cur = conn.execute("SELECT id, name, adresse FROM kunden WHERE name LIKE ? OR adresse LIKE ?", (pattern, pattern))
        rows = cur.fetchall()
        if rows:
            print(f"\nGefunden ({description}):")
            for row in rows:
                print(f"  ID: {row[0]}, Name: {row[1]}, Adresse: {row[2]}")
                if "dreihundert" in row[1].lower() or "naumannstraße" in row[2].lower():
                    # Aktualisiere Koordinaten
                    cur = conn.execute("UPDATE kunden SET lat = ?, lon = ? WHERE id = ?", (dreihundert_lat, dreihundert_lon, row[0]))
                    print(f"  -> Koordinaten aktualisiert: {dreihundert_lat}, {dreihundert_lon}")
                    dreihundert_found = True
                    break
        if dreihundert_found:
            break
    
    if not dreihundert_found:
        print("Dreihundert nicht in DB gefunden - füge zu Geocache hinzu")
        cur = conn.execute(
            "INSERT OR REPLACE INTO geocache (adresse, lat, lon, provider) VALUES (?, ?, ?, ?)",
            (dreihundert_address, dreihundert_lat, dreihundert_lon, "manual_correction")
        )
        print(f"Geocache aktualisiert für: {dreihundert_address}")
    
    conn.commit()
    conn.close()
    
    print("\nFertig! Beide Kunden korrigiert.")

if __name__ == "__main__":
    fix_both_customers()
