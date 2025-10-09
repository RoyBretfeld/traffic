#!/usr/bin/env python3
import sqlite3
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def debug_geocache_detailed():
    """Debugge die geocache_get Funktion im Detail"""
    
    def _connect():
        return sqlite3.connect('data/traffic.db')
    
    def _ensure_geocache_columns(conn: sqlite3.Connection) -> None:
        cur = conn.execute("PRAGMA table_info(geocache)")
        columns = {row[1] for row in cur.fetchall()}
        if "provider" not in columns:
            conn.execute("ALTER TABLE geocache ADD COLUMN provider TEXT")
        if "updated_at" not in columns:
            conn.execute("ALTER TABLE geocache ADD COLUMN updated_at TEXT DEFAULT (datetime('now'))")
        conn.commit()
    
    def geocache_get_debug(adresse: str):
        with _connect() as conn:
            _ensure_geocache_columns(conn)
            print(f"  Suche nach Adresse: '{adresse}'")
            
            cur = conn.execute(
                "SELECT lat, lon, provider FROM geocache WHERE adresse = ?", (adresse,)
            )
            row = cur.fetchone()
            print(f"  SQL-Ergebnis: {row}")
            
            if row and row[0] is not None and row[1] is not None:
                print(f"  row[0]: '{row[0]}' (type: {type(row[0])})")
                print(f"  row[1]: '{row[1]}' (type: {type(row[1])})")
                print(f"  row[2]: '{row[2]}' (type: {type(row[2])})")
                
                try:
                    lat = float(row[0])
                    lon = float(row[1])
                    provider = row[2]
                    print(f"  Konvertierung OK: {lat}, {lon}, {provider}")
                    return lat, lon, provider
                except ValueError as e:
                    print(f"  Konvertierungsfehler: {e}")
                    return None
            return None
    
    # Test-Adressen
    test_addresses = [
        "Schulstraße 25, 01468 Moritzburg (OT Boxdorf)",
        "Rundteil 7b, 01728 Bannewitz OT Possendorf", 
        "Möglitztalstraße 10, 01773 Altenberg OT Bärenstein",
        "Fischhausstr. 15b, 01099 Dresden"  # Diese sollte funktionieren
    ]
    
    for address in test_addresses:
        print(f"\n=== Teste: {address} ===")
        result = geocache_get_debug(address)
        print(f"Ergebnis: {result}")

if __name__ == "__main__":
    debug_geocache_detailed()
