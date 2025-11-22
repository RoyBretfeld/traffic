#!/usr/bin/env python3
"""
Script zum Erstellen von Test-Blitzern in der Datenbank
Fügt Beispiel-Blitzer in der Region Dresden ein

⚠️  WICHTIG: Dieses Script ist nur für Tests gedacht!
    Die Test-Blitzer können mit scripts/remove_test_speed_cameras.py entfernt werden.
"""
import sys
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from db.core import ENGINE
from datetime import datetime

# Beispiel-Blitzer in der Region Dresden
TEST_CAMERAS = [
    {
        "camera_id": "dresden_001",
        "lat": 51.0504,
        "lon": 13.7373,
        "type": "fixed",
        "direction": "both",
        "speed_limit": 50,
        "description": "Fester Blitzer - Hauptstraße Dresden",
        "verified": True
    },
    {
        "camera_id": "dresden_002",
        "lat": 51.0632,
        "lon": 13.7542,
        "type": "fixed",
        "direction": "north",
        "speed_limit": 50,
        "description": "Fester Blitzer - B6 Richtung Norden",
        "verified": True
    },
    {
        "camera_id": "dresden_003",
        "lat": 51.0345,
        "lon": 13.7215,
        "type": "mobile",
        "direction": "both",
        "speed_limit": 50,
        "description": "Mobiler Blitzer - Wechselnder Standort",
        "verified": False
    },
    {
        "camera_id": "dresden_004",
        "lat": 51.0891,
        "lon": 13.8012,
        "type": "fixed",
        "direction": "south",
        "speed_limit": 70,
        "description": "Fester Blitzer - A4 Richtung Süden",
        "verified": True
    },
    {
        "camera_id": "dresden_005",
        "lat": 51.0113,
        "lon": 13.7016,
        "type": "fixed",
        "direction": "both",
        "speed_limit": 50,
        "description": "Fester Blitzer - Gittersee (nahe Depot)",
        "verified": True
    },
    {
        "camera_id": "dresden_006",
        "lat": 51.0723,
        "lon": 13.7845,
        "type": "section_control",
        "direction": "both",
        "speed_limit": 50,
        "description": "Streckenkontrolle - Innenstadt Dresden",
        "verified": True
    },
    {
        "camera_id": "dresden_007",
        "lat": 50.9856,
        "lon": 13.6543,
        "type": "mobile",
        "direction": "both",
        "speed_limit": 50,
        "description": "Mobiler Blitzer - Freital",
        "verified": False
    },
    {
        "camera_id": "dresden_008",
        "lat": 51.1023,
        "lon": 13.8234,
        "type": "fixed",
        "direction": "east",
        "speed_limit": 70,
        "description": "Fester Blitzer - A4 Richtung Osten",
        "verified": True
    },
    {
        "camera_id": "dresden_009",
        "lat": 51.0456,
        "lon": 13.7123,
        "type": "fixed",
        "direction": "west",
        "speed_limit": 50,
        "description": "Fester Blitzer - B170 Richtung Westen",
        "verified": True
    },
    {
        "camera_id": "dresden_010",
        "lat": 51.0234,
        "lon": 13.7456,
        "type": "mobile",
        "direction": "both",
        "speed_limit": 30,
        "description": "Mobiler Blitzer - 30er Zone",
        "verified": False
    }
]


def create_speed_cameras_table():
    """Erstellt die speed_cameras Tabelle falls sie nicht existiert"""
    with ENGINE.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS speed_cameras (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                camera_id TEXT UNIQUE NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                type TEXT NOT NULL,
                direction TEXT,
                speed_limit INTEGER,
                description TEXT,
                verified INTEGER DEFAULT 0,
                last_seen TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now'))
            )
        """))
        print("[OK] Tabelle 'speed_cameras' erstellt/geprueft")


def insert_test_cameras():
    """Fügt Test-Blitzer in die Datenbank ein"""
    created_count = 0
    updated_count = 0
    
    with ENGINE.begin() as conn:
        for camera in TEST_CAMERAS:
            try:
                result = conn.execute(text("""
                    INSERT OR REPLACE INTO speed_cameras 
                    (camera_id, type, lat, lon, direction, speed_limit, description, verified, updated_at)
                    VALUES (:camera_id, :type, :lat, :lon, :direction, :speed_limit, :description, :verified, datetime('now'))
                """), {
                    "camera_id": camera["camera_id"],
                    "type": camera["type"],
                    "lat": camera["lat"],
                    "lon": camera["lon"],
                    "direction": camera.get("direction"),
                    "speed_limit": camera.get("speed_limit"),
                    "description": camera.get("description", ""),
                    "verified": 1 if camera.get("verified", False) else 0
                })
                
                # Prüfe ob INSERT oder UPDATE
                if result.rowcount > 0:
                    # Prüfe ob es ein UPDATE war (durch SELECT)
                    check = conn.execute(text("""
                        SELECT id FROM speed_cameras WHERE camera_id = :camera_id
                    """), {"camera_id": camera["camera_id"]})
                    if check.fetchone():
                        updated_count += 1
                    else:
                        created_count += 1
                    
                print(f"[OK] Blitzer eingefuegt/aktualisiert: {camera['camera_id']} - {camera['description']}")
                
            except Exception as e:
                print(f"[FEHLER] Fehler beim Einfuegen von {camera['camera_id']}: {e}")
    
    return created_count, updated_count


def count_cameras():
    """Zählt die Anzahl der Blitzer in der Datenbank"""
    with ENGINE.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM speed_cameras"))
        count = result.fetchone()[0]
        return count


def main():
    import sys
    import io
    
    # Setze UTF-8 Encoding für Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    print("=" * 60)
    print("Test-Blitzer in Datenbank einfuegen")
    print("=" * 60)
    print()
    print("⚠️  WARNUNG: Dieses Script fügt nur Test-Daten ein!")
    print("   Für Produktion sollten echte Blitzer-Daten verwendet werden.")
    print("   Test-Blitzer können mit scripts/remove_test_speed_cameras.py entfernt werden.")
    print()
    
    # Prüfe aktuelle Anzahl
    current_count = count_cameras()
    print(f"Aktuelle Anzahl Blitzer in DB: {current_count}")
    print()
    
    # Erstelle Tabelle falls nötig
    create_speed_cameras_table()
    print()
    
    # Füge Test-Blitzer ein
    print(f"Fuege {len(TEST_CAMERAS)} Test-Blitzer ein...")
    print()
    created, updated = insert_test_cameras()
    print()
    
    # Zeige Ergebnis
    new_count = count_cameras()
    print("=" * 60)
    print("Fertig!")
    print(f"Neue Anzahl Blitzer in DB: {new_count}")
    print(f"Neu erstellt: {created}")
    print(f"Aktualisiert: {updated}")
    print()
    print("Tipp: Lade die Seite neu und pruefe die Karte - die Blitzer sollten jetzt sichtbar sein!")
    print("=" * 60)


if __name__ == "__main__":
    main()

