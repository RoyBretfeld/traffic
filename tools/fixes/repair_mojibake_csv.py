#!/usr/bin/env python3
"""
Mojibake-Reparatur für CSV-Dateien
Repariert doppelte Zeichensatz-Korruption direkt in den CSV-Dateien
"""

import pandas as pd
from pathlib import Path
import unicodedata
import shutil
from typing import Dict, List

# Mojibake-Mappings basierend auf häufigen Korruptionen
MOJIBAKE_MAPPINGS = {
    # Box-Drawing-Zeichen (CP850-Fehlinterpretation)
    '┬': 'ß',      # U+252C → U+00DF
    '├': 'ä',      # U+251C → U+00E4  
    '┤': 'ö',      # U+2524 → U+00F6
    '┴': 'ü',      # U+2534 → U+00FC
    '┼': 'Ä',      # U+253C → U+00C4
    '┐': 'Ö',      # U+2510 → U+00D6
    '└': 'Ü',      # U+2514 → U+00DC
    '┘': 'ß',      # U+2518 → U+00DF (zusätzlich)
    '┌': 'ä',      # U+250C → U+00E4 (zusätzlich)
    '─': '',       # U+2500 → Leerzeichen entfernen
    '│': '',       # U+2502 → Leerzeichen entfernen
    
    # UTF-8-als-Latin-1 Marker
    'Ã': '',       # U+00C3 (oft bei UTF-8-als-Latin-1)
    'Â': '',       # U+00C2 (oft bei UTF-8-als-Latin-1)
    
    # Ersatzzeichen
    '\uFFFD': '',  # Unicode Replacement Character
    
    # Häufige Mojibake-Kombinationen
    'Ã¤': 'ä',     # UTF-8-als-Latin-1 für ä
    'Ã¶': 'ö',     # UTF-8-als-Latin-1 für ö
    'Ã¼': 'ü',     # UTF-8-als-Latin-1 für ü
    'ÃŸ': 'ß',     # UTF-8-als-Latin-1 für ß
    'Ã„': 'Ä',     # UTF-8-als-Latin-1 für Ä
    'Ã–': 'Ö',     # UTF-8-als-Latin-1 für Ö
    'Ãœ': 'Ü',     # UTF-8-als-Latin-1 für Ü
    
    # Zusätzliche Mojibake-Zeichen
    'â': '',       # U+00E2 (oft bei UTF-8-als-Latin-1)
    'â€': '',      # U+00E2 U+20AC (oft bei UTF-8-als-Latin-1)
    'â€œ': '',     # U+00E2 U+20AC U+201C (oft bei UTF-8-als-Latin-1)
    'â€\x9d': '',  # U+00E2 U+20AC U+009D (oft bei UTF-8-als-Latin-1)
}

def detect_mojibake(text: str) -> List[str]:
    """Erkennt Mojibake-Zeichen in einem Text"""
    found_mojibake = []
    for mojibake_char in MOJIBAKE_MAPPINGS.keys():
        if mojibake_char in text:
            found_mojibake.append(mojibake_char)
    return found_mojibake

def repair_mojibake(text: str) -> str:
    """Repariert Mojibake in einem Text"""
    if not text or not isinstance(text, str):
        return text
    
    # 1. Unicode normalisieren
    text = unicodedata.normalize("NFC", text)
    
    # 2. Mojibake-Zeichen ersetzen
    for mojibake_char, replacement in MOJIBAKE_MAPPINGS.items():
        text = text.replace(mojibake_char, replacement)
    
    return text

def repair_csv_file(csv_file_path: Path, create_backup: bool = True) -> Dict:
    """Repariert Mojibake in einer CSV-Datei"""
    
    print(f"Repariere: {csv_file_path.name}")
    
    # 1. Backup erstellen
    if create_backup:
        backup_path = csv_file_path.with_suffix('.csv.backup')
        shutil.copy2(csv_file_path, backup_path)
        print(f"   Backup erstellt: {backup_path.name}")
    
    # 2. CSV mit CP850 lesen (Windows-Standard)
    try:
        df = pd.read_csv(csv_file_path, encoding='cp850', sep=';', header=None, dtype=str)
        print(f"   OK: Gelesen: {len(df)} Zeilen")
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(csv_file_path, encoding='utf-8', sep=';', header=None, dtype=str)
            print(f"   OK: Gelesen (UTF-8): {len(df)} Zeilen")
        except Exception as e:
            print(f"   ERROR: Fehler beim Lesen: {e}")
            return {"success": False, "error": str(e)}
    
    # 3. Mojibake in allen Zellen reparieren
    mojibake_found = 0
    repairs_made = 0
    
    for col_idx in range(len(df.columns)):
        for row_idx in range(len(df)):
            cell_value = str(df.iloc[row_idx, col_idx])
            
            # Mojibake erkennen
            found_mojibake = detect_mojibake(cell_value)
            if found_mojibake:
                mojibake_found += 1
                print(f"   Mojibake gefunden in Zeile {row_idx+1}, Spalte {col_idx+1}: {[ord(c) for c in found_mojibake]}")
                
                # Reparieren
                repaired_value = repair_mojibake(cell_value)
                df.iloc[row_idx, col_idx] = repaired_value
                repairs_made += 1
                
                print(f"   Repariert: Zeile {row_idx+1}, Spalte {col_idx+1}")
    
    # 4. Als UTF-8 speichern
    try:
        df.to_csv(csv_file_path, encoding='utf-8', sep=';', header=False, index=False)
        print(f"   Gespeichert als UTF-8")
    except Exception as e:
        print(f"   ERROR: Fehler beim Speichern: {e}")
        return {"success": False, "error": str(e)}
    
    return {
        "success": True,
        "mojibake_found": mojibake_found,
        "repairs_made": repairs_made,
        "total_rows": len(df)
    }

def repair_all_csv_files(tourplaene_dir: Path = Path("tourplaene")) -> Dict:
    """Repariert Mojibake in allen CSV-Dateien"""
    
    if not tourplaene_dir.exists():
        print(f"ERROR: Verzeichnis nicht gefunden: {tourplaene_dir}")
        return {"success": False, "error": "Verzeichnis nicht gefunden"}
    
    csv_files = list(tourplaene_dir.glob("*.csv"))
    if not csv_files:
        print(f"ERROR: Keine CSV-Dateien gefunden in {tourplaene_dir}")
        return {"success": False, "error": "Keine CSV-Dateien gefunden"}
    
    print(f"Gefundene CSV-Dateien: {len(csv_files)}")
    print("=" * 60)
    
    total_mojibake = 0
    total_repairs = 0
    successful_files = 0
    
    for csv_file in csv_files:
        result = repair_csv_file(csv_file)
        if result["success"]:
            successful_files += 1
            total_mojibake += result["mojibake_found"]
            total_repairs += result["repairs_made"]
        print()
    
    print("=" * 60)
    print(f"ZUSAMMENFASSUNG:")
    print(f"   Erfolgreich repariert: {successful_files}/{len(csv_files)} Dateien")
    print(f"   Mojibake gefunden: {total_mojibake}")
    print(f"   Reparaturen durchgeführt: {total_repairs}")
    
    return {
        "success": True,
        "files_processed": len(csv_files),
        "successful_files": successful_files,
        "total_mojibake": total_mojibake,
        "total_repairs": total_repairs
    }

if __name__ == "__main__":
    import sys
    
    try:
        result = repair_all_csv_files()
        if result["success"]:
            print("Mojibake-Reparatur erfolgreich abgeschlossen!")
            sys.exit(0)
        else:
            print(f"ERROR: Mojibake-Reparatur fehlgeschlagen: {result['error']}")
            sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
