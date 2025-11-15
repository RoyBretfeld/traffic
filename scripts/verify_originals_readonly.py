#!/usr/bin/env python3
"""
Prüft ob alle Original-CSVs Read-Only sind
"""

import stat
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent

TOURPLAENE_DIRS = [
    PROJECT_ROOT / "tourplaene",
    PROJECT_ROOT / "Tourenpläne",
    PROJECT_ROOT / "Tourplaene",
]

def is_readonly(path: Path) -> bool:
    """Prüft ob eine Datei Read-Only ist"""
    if not path.exists():
        return False
    
    mode = path.stat().st_mode
    # Windows: Prüfe Write-Bit
    return not (mode & stat.S_IWRITE)

def verify_readonly():
    """Prüft alle CSV-Dateien in Tourenpläne-Verzeichnissen"""
    print("=" * 70)
    print("Pruefe Read-Only Schutz der Original-Tourenplaene")
    print("=" * 70)
    
    total_files = 0
    readonly_files = 0
    writable_files = []
    
    for dir_path in TOURPLAENE_DIRS:
        if not dir_path.exists():
            continue
        
        print(f"\n[{dir_path.name}]")
        csv_files = list(dir_path.glob("*.csv"))
        
        for csv_file in csv_files:
            total_files += 1
            if is_readonly(csv_file):
                readonly_files += 1
                print(f"  [OK] {csv_file.name} - Read-Only")
            else:
                writable_files.append(csv_file)
                print(f"  [WARNUNG] {csv_file.name} - SCHREIBBAR!")
    
    print("\n" + "=" * 70)
    print(f"Zusammenfassung:")
    print(f"  Gesamt: {total_files} Dateien")
    print(f"  Read-Only: {readonly_files}")
    print(f"  Schreibbar: {len(writable_files)}")
    print("=" * 70)
    
    if writable_files:
        print("\n[WARNUNG] Folgende Dateien sind NICHT Read-Only:")
        for f in writable_files:
            print(f"  - {f}")
        print("\nFuehre aus: python scripts/protect_tourplaene_originals.py")
        return False
    else:
        print("\n[OK] Alle Original-CSVs sind Read-Only geschuetzt!")
        return True

if __name__ == "__main__":
    success = verify_readonly()
    sys.exit(0 if success else 1)

