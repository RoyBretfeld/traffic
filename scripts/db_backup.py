#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Automatisches Datenbank-Backup für FAMO TrafficApp

Erstellt täglich um 16:00 Uhr ein Backup der traffic.db Datenbank.
Backups werden in data/backups/ gespeichert mit Datum im Dateinamen.

Verwendung:
    python scripts/db_backup.py

Windows Task Scheduler:
    - Programm: python
    - Argumente: E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0\scripts\db_backup.py
    - Zeitplan: Täglich um 16:00 Uhr
"""

import sys
import os
from pathlib import Path
from datetime import datetime
import shutil
import sqlite3

# Projekt-Root finden (Script ist in scripts/)
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Backup-Konfiguration
BACKUP_TIME = "16:00"  # 16:00 Uhr (4 PM)
BACKUP_DIR = PROJECT_ROOT / "data" / "backups"
BACKUP_RETENTION_DAYS = 30  # Backups älter als 30 Tage werden gelöscht

def get_database_path() -> Path:
    """Gibt den Pfad zur Haupt-Datenbank zurück."""
    db_path = PROJECT_ROOT / "data" / "traffic.db"
    if not db_path.exists():
        # Fallback: Versuche andere mögliche Pfade
        possible_paths = [
            PROJECT_ROOT / "data" / "traffic.db",
            Path("./data/traffic.db"),
            Path("data/traffic.db")
        ]
        for path in possible_paths:
            if path.exists():
                return path
        raise FileNotFoundError(f"Datenbank nicht gefunden: {db_path}")
    return db_path

def create_backup() -> tuple[bool, str]:
    """
    Erstellt ein Backup der Datenbank.
    
    Returns:
        (success: bool, message: str)
    """
    try:
        # Backup-Verzeichnis erstellen
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        # Datenbank-Pfad
        db_path = get_database_path()
        
        if not db_path.exists():
            return False, f"Datenbank nicht gefunden: {db_path}"
        
        # Backup-Dateiname mit Datum/Zeit
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"traffic_backup_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename
        
        # SQLite Backup mit sqlite3 (sicherer als shutil.copy bei aktiver DB)
        source_conn = sqlite3.connect(str(db_path), timeout=30.0)
        backup_conn = sqlite3.connect(str(backup_path), timeout=30.0)
        
        try:
            # SQLite native backup (erstellt konsistentes Backup, auch bei WAL-Mode)
            source_conn.backup(backup_conn)
            backup_conn.commit()
            backup_conn.close()
            
            # Dateigröße
            backup_size = backup_path.stat().st_size / (1024 * 1024)  # MB
            
            # Bereinige alte Backups
            cleanup_old_backups()
            
            return True, f"Backup erfolgreich erstellt: {backup_filename} ({backup_size:.2f} MB)"
            
        finally:
            source_conn.close()
            if backup_conn:
                backup_conn.close()
    
    except Exception as e:
        return False, f"Backup-Fehler: {str(e)}"

def cleanup_old_backups():
    """Löscht Backups die älter als BACKUP_RETENTION_DAYS sind."""
    if not BACKUP_DIR.exists():
        return
    
    cutoff_date = datetime.now().timestamp() - (BACKUP_RETENTION_DAYS * 24 * 3600)
    deleted_count = 0
    
    for backup_file in BACKUP_DIR.glob("traffic_backup_*.db"):
        try:
            file_age = backup_file.stat().st_mtime
            if file_age < cutoff_date:
                backup_file.unlink()
                deleted_count += 1
        except Exception as e:
            print(f"[BACKUP CLEANUP] Fehler beim Löschen von {backup_file.name}: {e}")
    
    if deleted_count > 0:
        print(f"[BACKUP CLEANUP] {deleted_count} alte Backups gelöscht (> {BACKUP_RETENTION_DAYS} Tage)")

def list_backups():
    """Listet alle verfügbaren Backups auf."""
    if not BACKUP_DIR.exists():
        return []
    
    backups = []
    for backup_file in sorted(BACKUP_DIR.glob("traffic_backup_*.db"), reverse=True):
        stat = backup_file.stat()
        size_mb = stat.st_size / (1024 * 1024)
        backups.append({
            "filename": backup_file.name,
            "path": str(backup_file),
            "size_mb": round(size_mb, 2),
            "created": datetime.fromtimestamp(stat.st_mtime).isoformat()
        })
    
    return backups

def restore_backup(backup_filename: str) -> tuple[bool, str]:
    """
    Stellt ein Backup wieder her.
    
    Args:
        backup_filename: Name der Backup-Datei
        
    Returns:
        (success: bool, message: str)
    """
    try:
        backup_path = BACKUP_DIR / backup_filename
        if not backup_path.exists():
            return False, f"Backup nicht gefunden: {backup_filename}"
        
        db_path = get_database_path()
        
        # Backup der aktuellen DB erstellen (für Sicherheit)
        safety_backup = db_path.parent / f"{db_path.name}.safety_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        if db_path.exists():
            shutil.copy2(db_path, safety_backup)
        
        # Backup wiederherstellen
        shutil.copy2(backup_path, db_path)
        
        return True, f"Backup wiederhergestellt: {backup_filename}. Alte DB gesichert als: {safety_backup.name}"
    
    except Exception as e:
        return False, f"Wiederherstellungs-Fehler: {str(e)}"

def main():
    """Hauptfunktion für Kommandozeile."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Datenbank-Backup für FAMO TrafficApp")
    parser.add_argument("--list", action="store_true", help="Liste alle Backups")
    parser.add_argument("--restore", type=str, help="Stelle ein Backup wieder her (Dateiname)")
    
    args = parser.parse_args()
    
    if args.list:
        backups = list_backups()
        if backups:
            print(f"\nVerfügbare Backups ({len(backups)}):\n")
            for backup in backups:
                print(f"  {backup['filename']}")
                print(f"    Größe: {backup['size_mb']} MB")
                print(f"    Erstellt: {backup['created']}")
                print()
        else:
            print("Keine Backups gefunden.")
        return
    
    if args.restore:
        success, message = restore_backup(args.restore)
        print(f"[RESTORE] {message}")
        return
    
    # Standard: Backup erstellen
    print(f"[BACKUP] Starte Backup um {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}...")
    success, message = create_backup()
    
    if success:
        print(f"[BACKUP] {message}")
        sys.exit(0)
    else:
        print(f"[BACKUP ERROR] {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()

