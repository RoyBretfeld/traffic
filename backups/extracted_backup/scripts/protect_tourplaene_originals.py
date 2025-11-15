#!/usr/bin/env python3
"""
Schützt den Tourenpläne-Ordner vor Änderungen
Setzt Read-Only Attribute und verhindert Schreibzugriffe
"""

import os
import stat
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent

# Mögliche Namen für den Tourenpläne-Ordner
TOURPLAENE_DIRS = [
    PROJECT_ROOT / "tourplaene",
    PROJECT_ROOT / "Tourenpläne",
    PROJECT_ROOT / "Tourplaene",
]

def set_readonly(path: Path, readonly: bool = True):
    """Setzt Read-Only Attribut für Datei/Ordner"""
    if not path.exists():
        return False
    
    current = stat.filemode(path.stat().st_mode)
    
    if path.is_file():
        if readonly:
            path.chmod(path.stat().st_mode & ~stat.S_IWRITE)
            print(f"  [OK] Read-Only gesetzt: {path.name}")
        else:
            path.chmod(path.stat().st_mode | stat.S_IWRITE)
            print(f"  [OK] Write-Only entfernt: {path.name}")
        return True
    elif path.is_dir():
        # Für Ordner: Alle Dateien darin
        for file_path in path.rglob("*"):
            if file_path.is_file():
                set_readonly(file_path, readonly)
        return True
    
    return False

def protect_tourplaene_directory():
    """Schützt alle Tourenpläne-Verzeichnisse vor Schreibzugriff"""
    print("=" * 70)
    print("Tourenpläne Original-Schutz")
    print("=" * 70)
    
    found_dirs = []
    
    for dir_path in TOURPLAENE_DIRS:
        if dir_path.exists() and dir_path.is_dir():
            found_dirs.append(dir_path)
            print(f"\n[GEFUNDEN] {dir_path}")
            
            # Prüfe aktuelle Berechtigungen
            current_mode = stat.filemode(dir_path.stat().st_mode)
            print(f"  Aktueller Modus: {current_mode}")
            
            # Setze Read-Only für alle CSV-Dateien
            csv_files = list(dir_path.glob("*.csv"))
            print(f"  CSV-Dateien gefunden: {len(csv_files)}")
            
            protected = 0
            for csv_file in csv_files:
                try:
                    # Windows: Entferne Write-Bit
                    if sys.platform == "win32":
                        os.chmod(csv_file, stat.S_IREAD)
                    else:
                        csv_file.chmod(0o444)  # Read-only für alle
                    protected += 1
                except Exception as e:
                    print(f"  [WARNUNG] Konnte {csv_file.name} nicht schützen: {e}")
            
            print(f"  [OK] {protected} Dateien geschützt")
    
    if not found_dirs:
        print("\n[WARNUNG] Kein Tourenpläne-Verzeichnis gefunden!")
        print("  Gesucht in:")
        for dir_path in TOURPLAENE_DIRS:
            print(f"    - {dir_path}")
    
    print("\n" + "=" * 70)
    print("Schutz aktiviert!")
    print("=" * 70)
    print("\nWICHTIG:")
    print("- Original-CSVs sind jetzt Read-Only")
    print("- Alle Änderungen müssen in data/staging/ oder data/temp/ gemacht werden")
    print("- Excel/Editor können die Dateien öffnen, aber nicht speichern")
    
    return found_dirs

if __name__ == "__main__":
    try:
        dirs = protect_tourplaene_directory()
        if dirs:
            print(f"\n[ERFOLG] {len(dirs)} Verzeichnis(se) geschützt")
            sys.exit(0)
        else:
            print("\n[FEHLER] Kein Verzeichnis gefunden")
            sys.exit(1)
    except Exception as e:
        print(f"\n[FEHLER] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

