#!/usr/bin/env python3
"""
DEPRECATED: Deutsche Encoding-Reparatur

⚠️  WARNUNG: Diese Datei ist DEPRECATED!
Diese Ad-hoc-Reparaturen verschleiern nur Encoding-Probleme.
Verwende stattdessen: backend/utils/encoding_guards.py

Repariert alle deutschen Umlaute und konvertiert ß zu ss beim Parsen.
"""

import re
import unicodedata

def normalize_german_text(text):
    """Normalisiert deutschen Text für bessere Erkennung."""
    if not text or not isinstance(text, str):
        return text
    
    # 1. Repariere korrupte Encoding-Zeichen
    text = fix_corrupt_encoding(text)
    
    # 2. Normalisiere Unicode
    text = unicodedata.normalize('NFD', text)
    
    # 3. Konvertiere ß zu ss (wie gewünscht)
    text = text.replace('ß', 'ss')
    
    # 4. Konvertiere Umlaute zu ae, oe, ue (für bessere Erkennung)
    text = text.replace('ä', 'ae')
    text = text.replace('ö', 'oe') 
    text = text.replace('ü', 'ue')
    text = text.replace('Ä', 'Ae')
    text = text.replace('Ö', 'Oe')
    text = text.replace('Ü', 'Ue')
    
    return text

def fix_corrupt_encoding(text):
    """Repariert korrupte Encoding-Zeichen."""
    if not text:
        return text
    
    # Mapping für korrupte Zeichen
    corrupt_fixes = {
        '´j´{ch´j´{': 'ss',  # ß wird zu ss
        '´j´{': 'ue',        # ü wird zu ue
        '´j´{a': 'ae',       # ä wird zu ae
        '´j´{o': 'oe',       # ö wird zu oe
        '´j´{A': 'Ae',       # Ä wird zu Ae
        '´j´{O': 'Oe',       # Ö wird zu Oe
        '´j´{U': 'Ue',       # Ü wird zu Ue
        '´j´{s': 'ss',       # ß wird zu ss
    }
    
    for corrupt, replacement in corrupt_fixes.items():
        text = text.replace(corrupt, replacement)
    
    return text

def test_german_encoding():
    """Testet die deutsche Encoding-Reparatur."""
    
    test_cases = [
        # Korrupte Zeichen
        ("Berggie ´j´{ch´j´{bel", "Berggiesshuebel"),
        ("Stra´j´{", "Strass"),
        ("Müller ´j´{", "Mueller ue"),
        ("Größe ´j´{s", "Groesse ss"),
        ("Bäcker ´j´{a", "Baecker ae"),
        
        # Normale deutsche Zeichen
        ("Berggießhübel", "Berggiesshuebel"),
        ("Straße", "Strasse"),
        ("Müller", "Mueller"),
        ("Größe", "Groesse"),
        ("Bäcker", "Baecker"),
        
        # Gemischte Fälle
        ("Autohaus in Berggie´j´{ch´j´{bel GmbH", "Autohaus in Berggiesshuebel GmbH"),
        ("Burgst´j´{dteler Str.", "Burgstaedteler Str."),
        ("P´j´{´j´{ler Autoteile", "Poeoeler Autoteile"),
    ]
    
    print("🧪 Teste deutsche Encoding-Reparatur:")
    print("=" * 50)
    
    for original, expected in test_cases:
        result = normalize_german_text(original)
        status = "✅" if result == expected else "❌"
        print(f"{status} '{original}' → '{result}' (erwartet: '{expected}')")
    
    print()

def apply_to_csv_files():
    """Wendet die Reparatur auf alle CSV-Dateien an."""
    
    from pathlib import Path
    import pandas as pd
    
    tourplaene_dir = Path("tourplaene")
    fixed_count = 0
    
    print("🔧 Repariere deutsche Zeichen in CSV-Dateien...")
    
    for csv_file in tourplaene_dir.glob("*.csv"):
        print(f"  📄 Verarbeite: {csv_file.name}")
        
        try:
            # Lese mit bestem Encoding
            df = None
            for encoding in ['utf-8', 'cp1252', 'latin-1']:
                try:
                    df = pd.read_csv(csv_file, encoding=encoding, sep=';', header=None)
                    break
                except:
                    continue
            
            if df is None:
                print(f"    ❌ Konnte {csv_file.name} nicht lesen")
                continue
            
            # Repariere alle Text-Spalten
            original_df = df.copy()
            for col in df.columns:
                if df[col].dtype == 'object':  # Text-Spalten
                    df[col] = df[col].astype(str).apply(normalize_german_text)
            
            # Prüfe ob Änderungen gemacht wurden
            if not df.equals(original_df):
                # Erstelle Backup
                backup_file = csv_file.with_suffix('.csv.backup')
                original_df.to_csv(backup_file, sep=';', index=False, encoding='utf-8')
                
                # Speichere reparierte Version
                df.to_csv(csv_file, sep=';', index=False, encoding='utf-8')
                
                print(f"    ✅ Repariert und gespeichert (Backup: {backup_file.name})")
                fixed_count += 1
            else:
                print(f"    ✅ Keine Änderungen nötig")
                
        except Exception as e:
            print(f"    ❌ Fehler bei {csv_file.name}: {e}")
    
    print(f"\n🎉 Deutsche Encoding-Reparatur abgeschlossen!")
    print(f"📊 {fixed_count} Dateien repariert")
    
    return fixed_count

if __name__ == "__main__":
    print("🚀 Deutsche Encoding-Reparatur")
    print("=" * 40)
    
    # Teste zuerst
    test_german_encoding()
    
    # Wende auf CSV-Dateien an
    fixed_count = apply_to_csv_files()
    
    if fixed_count > 0:
        print(f"\n💡 Tipp: Starten Sie den Server neu und testen Sie die Tourplan-Analyse erneut!")
