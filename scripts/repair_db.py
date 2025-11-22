#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SQLite Datenbank-Reparatur-Skript für Windows
Repariert eine potenziell korrupte SQLite-Datenbank.
"""
import sqlite3
import shutil
from pathlib import Path
from datetime import datetime
import sys
import io

# Fix für Windows-Konsolen-Encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

DB_FILE = Path("data/traffic.db")
BACKUP_DIR = Path("backups/db_repairs")
DUMP_FILE = Path("data/dump_repair.sql")
NEW_DB_FILE = Path("data/traffic_repaired.db")

def repair_database():
    """Repariert die SQLite-Datenbank."""
    print("=" * 70)
    print("SQLite Datenbank-Reparatur")
    print("=" * 70)
    print()
    
    if not DB_FILE.exists():
        print(f"[FEHLER] Datenbank-Datei nicht gefunden: {DB_FILE}")
        print("   Die Datenbank wird beim nächsten Server-Start automatisch erstellt.")
        return False
    
    # 1. Backup-Verzeichnis erstellen
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    
    # 2. Backup erstellen
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = BACKUP_DIR / f"traffic_db_backup_{timestamp}.db"
    print(f"1. Erstelle Backup: {backup_file}")
    try:
        shutil.copy2(DB_FILE, backup_file)
        print(f"   [OK] Backup erstellt: {backup_file}")
    except Exception as e:
        print(f"   [FEHLER] Fehler beim Erstellen des Backups: {e}")
        return False
    
    # 3. Integrity Check
    print("\n2. Prüfe Datenbank-Integrität...")
    try:
        conn = sqlite3.connect(str(DB_FILE))
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        
        if result == "ok":
            print("   [OK] Datenbank ist in Ordnung - keine Reparatur noetig")
            return True
        else:
            print(f"   [WARNUNG] Integritaetspruefung fehlgeschlagen: {result}")
    except Exception as e:
        print(f"   [WARNUNG] Fehler bei Integritaetspruefung: {e}")
        print("   → Versuche Reparatur...")
    
    # 4. SQL-Dump erstellen
    print("\n3. Erstelle SQL-Dump...")
    try:
        conn = sqlite3.connect(str(DB_FILE))
        with open(DUMP_FILE, 'w', encoding='utf-8') as f:
            for line in conn.iterdump():
                f.write(f"{line}\n")
        conn.close()
        print(f"   [OK] SQL-Dump erstellt: {DUMP_FILE}")
    except Exception as e:
        print(f"   [FEHLER] Fehler beim Erstellen des SQL-Dumps: {e}")
        print("   -> Versuche alternative Reparatur-Methode...")
        # Versuche mehrmals, die Datei zu verschieben (falls blockiert)
        import time
        for attempt in range(5):
            try:
                return repair_alternative(backup_file, auto_confirm=True)
            except (OSError, PermissionError) as e:
                if attempt < 4:
                    print(f"   [WARNUNG] Datei blockiert, warte 2 Sekunden... (Versuch {attempt+1}/5)")
                    time.sleep(2)
                else:
                    print(f"   [FEHLER] Datei konnte nach 5 Versuchen nicht verschoben werden: {e}")
                    print("   [HINWEIS] Bitte beenden Sie alle Python-Prozesse und versuchen Sie es erneut.")
                    return False
    
    # 5. Neue Datenbank aus Dump erstellen
    print("\n4. Erstelle neue Datenbank aus Dump...")
    try:
        if NEW_DB_FILE.exists():
            NEW_DB_FILE.unlink()
        
        conn = sqlite3.connect(str(NEW_DB_FILE))
        with open(DUMP_FILE, 'r', encoding='utf-8') as f:
            sql_script = f.read()
            conn.executescript(sql_script)
        conn.close()
        print(f"   [OK] Neue Datenbank erstellt: {NEW_DB_FILE}")
    except Exception as e:
        print(f"   [FEHLER] Fehler beim Erstellen der neuen Datenbank: {e}")
        return False
    
    # 6. Integrität der neuen DB prüfen
    print("\n5. Prüfe neue Datenbank...")
    try:
        conn = sqlite3.connect(str(NEW_DB_FILE))
        result = conn.execute("PRAGMA integrity_check").fetchone()[0]
        conn.close()
        
        if result == "ok":
            print("   [OK] Neue Datenbank ist in Ordnung")
        else:
            print(f"   [WARNUNG] Neue Datenbank hat noch Probleme: {result}")
    except Exception as e:
        print(f"   [WARNUNG] Fehler bei Integritaetspruefung: {e}")
    
    # 7. Alte DB umbenennen und neue DB einsetzen
    print("\n6. Ersetze alte Datenbank...")
    try:
        corrupted_file = Path(f"{DB_FILE}.corrupted_{timestamp}")
        DB_FILE.rename(corrupted_file)
        NEW_DB_FILE.rename(DB_FILE)
        print(f"   [OK] Alte DB gesichert als: {corrupted_file}")
        print(f"   [OK] Neue DB aktiviert: {DB_FILE}")
    except Exception as e:
        print(f"   [FEHLER] Fehler beim Ersetzen: {e}")
        return False
    
    # 8. Aufräumen
    print("\n7. Räume auf...")
    try:
        if DUMP_FILE.exists():
            DUMP_FILE.unlink()
        print("   [OK] Temporaere Dateien geloescht")
    except Exception as e:
        print(f"   [WARNUNG] Fehler beim Aufraeumen: {e}")
    
    print("\n" + "=" * 70)
    print("[OK] Datenbank-Reparatur abgeschlossen!")
    print("=" * 70)
    print(f"\nBackup gespeichert: {backup_file}")
    print(f"Korrupte DB gespeichert: {corrupted_file}")
    print("\nSie können die korrupte DB später löschen, wenn alles funktioniert.")
    
    return True

def repair_alternative(backup_file, auto_confirm=False):
    """Alternative Reparatur-Methode: Einfach neu erstellen."""
    print("\n" + "=" * 70)
    print("Alternative Reparatur: Datenbank wird neu erstellt")
    print("=" * 70)
    print("\n[WARNUNG] Alle Daten gehen verloren!")
    print("   Die Datenbank wird beim naechsten Server-Start automatisch neu erstellt.")
    
    if not auto_confirm:
        response = input("\nMoechten Sie fortfahren? (ja/nein): ")
        if response.lower() not in ['ja', 'j', 'yes', 'y']:
            print("Abgebrochen.")
            return False
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        corrupted_file = Path(f"{DB_FILE}.corrupted_{timestamp}")
        DB_FILE.rename(corrupted_file)
        print(f"[OK] Alte DB gesichert als: {corrupted_file}")
        print("[OK] Datenbank wird beim naechsten Server-Start neu erstellt.")
        return True
    except Exception as e:
        print(f"[FEHLER] Fehler: {e}")
        return False

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Repariert eine SQLite-Datenbank')
    parser.add_argument('--auto', action='store_true', help='Automatische Bestätigung (für Skripte)')
    args = parser.parse_args()
    
    try:
        # Wenn auto=True, überspringe Bestätigung
        if args.auto:
            # Temporär die input-Funktion überschreiben
            original_input = input
            def auto_input(prompt):
                return 'ja'
            import builtins
            builtins.input = auto_input
        
        success = repair_database()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nAbgebrochen durch Benutzer.")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FEHLER] Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

