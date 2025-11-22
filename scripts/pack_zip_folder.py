#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Packt alle Dateien im ZIP-Ordner zu einem ZIP-Archiv.
Erstellt ein konsolidiertes Archiv für Code-Review.
"""
import zipfile
import os
import sys
import io
from pathlib import Path
from datetime import datetime

# Setze UTF-8 Encoding für Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

PROJECT_ROOT = Path(__file__).parent.parent
ZIP_FOLDER = PROJECT_ROOT / "ZIP"

def pack_zip_folder():
    """Packt alle Dateien im ZIP-Ordner zu einem ZIP."""
    if not ZIP_FOLDER.exists():
        print(f"❌ ZIP-Ordner nicht gefunden: {ZIP_FOLDER}")
        return None
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_zip = PROJECT_ROOT / f"ZIP_CONSOLIDATED_{timestamp}.zip"
    
    print("=" * 60)
    print("ZIP-Ordner konsolidieren")
    print("=" * 60)
    print(f"Quelle: {ZIP_FOLDER}")
    print(f"Ziel: {output_zip.name}")
    print()
    
    file_count = 0
    total_size = 0
    
    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_DEFLATED) as zipf:
        # Durchsuche ZIP-Ordner rekursiv
        for root, dirs, files in os.walk(ZIP_FOLDER):
            root_path = Path(root)
            
            # Überspringe .git und andere versteckte Verzeichnisse
            dirs[:] = [d for d in dirs if not d.startswith('.')]
            
            for file in files:
                file_path = root_path / file
                
                # Überspringe bereits erstellte konsolidierte ZIPs
                if file.startswith('ZIP_CONSOLIDATED_'):
                    continue
                
                # Relativer Pfad innerhalb des ZIP-Ordners
                rel_path = file_path.relative_to(ZIP_FOLDER)
                
                try:
                    zipf.write(file_path, f"ZIP/{rel_path}")
                    file_count += 1
                    total_size += file_path.stat().st_size
                    if file_count % 10 == 0:
                        print(f"   [{file_count}] {rel_path}")
                except Exception as e:
                    print(f"   [WARN] Fehler bei {rel_path}: {e}")
    
    print()
    print("=" * 60)
    print("Fertig!")
    print(f"[OK] {file_count} Dateien gepackt")
    print(f"[OK] Groesse: {total_size / 1024 / 1024:.2f} MB")
    print(f"[OK] ZIP-Groesse: {output_zip.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"[OK] Datei: {output_zip}")
    print("=" * 60)
    
    return output_zip

if __name__ == "__main__":
    pack_zip_folder()

