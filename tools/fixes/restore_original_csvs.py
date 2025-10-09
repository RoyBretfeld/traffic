#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Wiederherstellung der Original-CSV-Dateien aus Backups
"""

import os
import shutil
from pathlib import Path

def restore_original_csvs():
    """Stellt alle Original-CSV-Dateien aus den .backup-Dateien wieder her"""
    
    tourplaene_dir = Path("tourplaene")
    if not tourplaene_dir.exists():
        print("ERROR: tourplaene Verzeichnis nicht gefunden")
        return False
    
    backup_files = list(tourplaene_dir.glob("*.backup"))
    if not backup_files:
        print("ERROR: Keine .backup-Dateien gefunden")
        return False
    
    print(f"Stelle {len(backup_files)} Original-CSV-Dateien wieder her...")
    
    restored_count = 0
    for backup_file in backup_files:
        # Original-Dateiname ohne .backup
        original_name = backup_file.name.replace('.backup', '')
        original_path = tourplaene_dir / original_name
        
        try:
            # Kopiere Backup über Original
            shutil.copy2(backup_file, original_path)
            print(f"  [OK] Wiederhergestellt: {original_name}")
            restored_count += 1
            
        except Exception as e:
            print(f"  [ERROR] Fehler bei {original_name}: {e}")
    
    print(f"\n[SUCCESS] {restored_count} von {len(backup_files)} Dateien erfolgreich wiederhergestellt!")
    return restored_count == len(backup_files)

if __name__ == "__main__":
    success = restore_original_csvs()
    if success:
        print("[SUCCESS] Alle Original-CSV-Dateien wurden wiederhergestellt!")
    else:
        print("[ERROR] Einige Dateien konnten nicht wiederhergestellt werden.")
