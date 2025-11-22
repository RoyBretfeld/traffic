#!/usr/bin/env python3
"""
Script zum Entfernen von Test-Blitzern aus der Datenbank
Löscht alle Blitzer mit camera_id die mit "dresden_" beginnen
"""
import sys
from pathlib import Path

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from db.core import ENGINE
import io

def count_test_cameras():
    """Zählt die Anzahl der Test-Blitzer in der Datenbank"""
    with ENGINE.connect() as conn:
        result = conn.execute(text("""
            SELECT COUNT(*) FROM speed_cameras 
            WHERE camera_id LIKE 'dresden_%'
        """))
        count = result.fetchone()[0]
        return count

def list_test_cameras():
    """Listet alle Test-Blitzer auf"""
    with ENGINE.connect() as conn:
        result = conn.execute(text("""
            SELECT camera_id, lat, lon, type, description 
            FROM speed_cameras 
            WHERE camera_id LIKE 'dresden_%'
            ORDER BY camera_id
        """))
        return result.fetchall()

def remove_test_cameras():
    """Entfernt alle Test-Blitzer aus der Datenbank"""
    with ENGINE.begin() as conn:
        result = conn.execute(text("""
            DELETE FROM speed_cameras 
            WHERE camera_id LIKE 'dresden_%'
        """))
        deleted_count = result.rowcount
        return deleted_count

def main():
    import sys
    
    # Setze UTF-8 Encoding für Windows
    if sys.platform == 'win32':
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    
    # Prüfe ob --force Flag gesetzt ist
    force = '--force' in sys.argv or '-f' in sys.argv
    
    print("=" * 60)
    print("Test-Blitzer aus Datenbank entfernen")
    print("=" * 60)
    print()
    
    # Prüfe ob Tabelle existiert
    with ENGINE.connect() as conn:
        result = conn.execute(text("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='speed_cameras'
        """))
        if not result.fetchone():
            print("⚠️  Tabelle 'speed_cameras' existiert nicht.")
            print("   Es gibt keine Blitzer zu löschen.")
            return
    
    # Zähle Test-Blitzer
    test_count = count_test_cameras()
    print(f"Gefundene Test-Blitzer: {test_count}")
    print()
    
    if test_count == 0:
        print("✅ Keine Test-Blitzer gefunden. Nichts zu löschen.")
        return
    
    # Zeige Test-Blitzer
    print("Folgende Test-Blitzer werden gelöscht:")
    print("-" * 60)
    cameras = list_test_cameras()
    for cam in cameras:
        print(f"  - {cam[0]}: {cam[4]} ({cam[3]})")
    print("-" * 60)
    print()
    
    # Bestätigung (nur wenn nicht --force)
    if not force:
        try:
            response = input("Möchten Sie diese Test-Blitzer wirklich löschen? (ja/nein): ")
            if response.lower() not in ['ja', 'j', 'yes', 'y']:
                print("❌ Abgebrochen. Keine Blitzer gelöscht.")
                return
        except EOFError:
            print("⚠️  Keine interaktive Eingabe möglich. Verwenden Sie --force Flag.")
            print("   Beispiel: python scripts/remove_test_speed_cameras.py --force")
            return
    
    # Lösche Test-Blitzer
    print()
    print("Lösche Test-Blitzer...")
    deleted_count = remove_test_cameras()
    
    print()
    print("=" * 60)
    print("Fertig!")
    print(f"✅ {deleted_count} Test-Blitzer gelöscht.")
    print()
    print("Tipp: Lade die Seite neu - die Test-Blitzer sollten jetzt nicht mehr sichtbar sein!")
    print("=" * 60)

if __name__ == "__main__":
    main()

