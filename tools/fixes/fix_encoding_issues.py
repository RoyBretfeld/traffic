#!/usr/bin/env python3
"""
DEPRECATED: Encoding-Problem-Reparatur

⚠️  WARNUNG: Diese Datei ist DEPRECATED!
Diese Ad-hoc-Reparaturen verschleiern nur Encoding-Probleme.
Verwende stattdessen: backend/utils/encoding_guards.py

Repariert korrupte deutsche Umlaute in den CSV-Dateien.
"""

import os
import re
from pathlib import Path

def fix_encoding_issues():
    """Repariert Encoding-Probleme in CSV-Dateien."""
    
    # Mapping für korrupte Zeichen zu korrekten deutschen Umlauten
    encoding_fixes = {
        '´j´{ch´j´{': 'ß',  # Berggießhübel
        '´j´{': 'ü',        # ü
        '´j´{a': 'ä',       # ä
        '´j´{o': 'ö',       # ö
        '´j´{A': 'Ä',       # Ä
        '´j´{O': 'Ö',       # Ö
        '´j´{U': 'Ü',       # Ü
        '´j´{s': 'ß',       # ß
    }
    
    tourplaene_dir = Path("tourplaene")
    fixed_count = 0
    
    print("🔧 Repariere Encoding-Probleme in CSV-Dateien...")
    
    for csv_file in tourplaene_dir.glob("*.csv"):
        print(f"  📄 Prüfe: {csv_file.name}")
        
        try:
            # Lese Datei mit verschiedenen Encodings
            content = None
            encoding_used = None
            
            for encoding in ['utf-8', 'cp1252', 'latin-1']:
                try:
                    with open(csv_file, 'r', encoding=encoding) as f:
                        content = f.read()
                    encoding_used = encoding
                    break
                except UnicodeDecodeError:
                    continue
            
            if not content:
                print(f"    ❌ Konnte {csv_file.name} nicht lesen")
                continue
            
            # Prüfe ob korrupte Zeichen vorhanden sind
            has_corrupt_chars = any(corrupt in content for corrupt in encoding_fixes.keys())
            
            if not has_corrupt_chars:
                print(f"    ✅ Keine Encoding-Probleme gefunden")
                continue
            
            # Repariere korrupte Zeichen
            original_content = content
            for corrupt, correct in encoding_fixes.items():
                content = content.replace(corrupt, correct)
            
            # Prüfe ob Änderungen gemacht wurden
            if content != original_content:
                # Erstelle Backup
                backup_file = csv_file.with_suffix('.csv.backup')
                with open(backup_file, 'w', encoding='utf-8') as f:
                    f.write(original_content)
                
                # Speichere reparierte Version
                with open(csv_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                
                print(f"    ✅ Repariert und gespeichert (Backup: {backup_file.name})")
                fixed_count += 1
            else:
                print(f"    ⚠️ Keine Änderungen nötig")
                
        except Exception as e:
            print(f"    ❌ Fehler bei {csv_file.name}: {e}")
    
    print(f"\n🎉 Encoding-Reparatur abgeschlossen!")
    print(f"📊 {fixed_count} Dateien repariert")
    
    return fixed_count

def test_encoding_fixes():
    """Testet die Encoding-Reparatur."""
    
    print("\n🧪 Teste Encoding-Reparatur...")
    
    # Test-Strings
    test_cases = [
        ("Berggie ´j´{ch´j´{bel", "Berggießhübel"),
        ("Müller ´j´{", "Müller ü"),
        ("Größe ´j´{s", "Größe ß"),
        ("Bäcker ´j´{a", "Bäcker ä"),
    ]
    
    for corrupt, expected in test_cases:
        # Simuliere Reparatur
        fixed = corrupt
        encoding_fixes = {
            '´j´{ch´j´{': 'ß',
            '´j´{': 'ü',
            '´j´{a': 'ä',
            '´j´{o': 'ö',
            '´j´{s': 'ß',
        }
        
        for corrupt_char, correct_char in encoding_fixes.items():
            fixed = fixed.replace(corrupt_char, correct_char)
        
        status = "✅" if fixed == expected else "❌"
        print(f"  {status} '{corrupt}' → '{fixed}' (erwartet: '{expected}')")

if __name__ == "__main__":
    print("🚀 Encoding-Problem-Reparatur")
    print("=" * 40)
    
    # Teste zuerst
    test_encoding_fixes()
    
    # Führe Reparatur durch
    fixed_count = fix_encoding_issues()
    
    if fixed_count > 0:
        print(f"\n💡 Tipp: Führen Sie die BAR-Kunden-Analyse erneut aus:")
        print(f"   python analyze_bar_customers_fixed.py")
