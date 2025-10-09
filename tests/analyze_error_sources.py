#!/usr/bin/env python3
"""
Analysiert die Quellen der Encoding-Fehler
"""

import pandas as pd
from pathlib import Path
import re

def analyze_error_sources():
    """Analysiert wo die Encoding-Fehler herkommen."""
    
    print("🔍 Fehlerquellen-Analyse")
    print("=" * 40)
    
    # Teste eine Datei mit UTF-8
    csv_file = Path("tourplaene/Tourenplan 01.09.2025.csv")
    
    try:
        df = pd.read_csv(csv_file, encoding='utf-8', sep=';', header=None)
        print(f"✅ Datei erfolgreich gelesen: {len(df)} Zeilen")
        
        # Analysiere die ersten 5 Zeilen
        print(f"\n📋 Erste 5 Zeilen (roh):")
        for i in range(min(5, len(df))):
            row_text = ' | '.join([str(cell) for cell in df.iloc[i]])
            print(f"  Zeile {i+1}: {row_text[:100]}...")
        
        # Suche nach spezifischen Fehlern
        print(f"\n🔍 Fehler-Muster suchen:")
        
        error_patterns = {
            '├í': 'ß → ├í',
            'í': 'ß → í',
            '´j´{': 'Umlaute → ´j´{',
            '┬': 'Umlaute → ┬',
            '├': 'Umlaute → ├',
            '': 'Replacement Character'
        }
        
        for pattern, description in error_patterns.items():
            count = 0
            for col in df.columns:
                if df[col].dtype == 'object':
                    col_text = df[col].astype(str).str.cat(sep=' ')
                    count += len(re.findall(pattern, col_text))
            
            if count > 0:
                print(f"  {description}: {count} Vorkommen")
        
        # Prüfe ob echte deutsche Zeichen vorhanden sind
        print(f"\n🇩🇪 Deutsche Zeichen suchen:")
        german_chars = ['ß', 'ä', 'ö', 'ü', 'Ä', 'Ö', 'Ü']
        
        for char in german_chars:
            count = 0
            for col in df.columns:
                if df[col].dtype == 'object':
                    col_text = df[col].astype(str).str.cat(sep=' ')
                    count += col_text.count(char)
            
            if count > 0:
                print(f"  {char}: {count} Vorkommen")
        
        # Teste verschiedene Encodings auf eine kleine Probe
        print(f"\n🧪 Encoding-Test auf erste 3 Zeilen:")
        
        # Lese nur die ersten 3 Zeilen
        df_small = df.head(3)
        small_content = df_small.to_string()
        
        encodings = ['utf-8', 'latin-1', 'cp1252']
        
        for encoding in encodings:
            try:
                # Simuliere das Encoding-Problem
                if encoding == 'utf-8':
                    # Original UTF-8
                    test_content = small_content
                else:
                    # Simuliere falsche Encoding-Interpretation
                    test_content = small_content.encode('utf-8').decode(encoding, errors='replace')
                
                # Zähle Fehler
                errors = 0
                for pattern in error_patterns.keys():
                    errors += len(re.findall(pattern, test_content))
                
                print(f"  {encoding:8}: {errors} Fehler")
                
            except Exception as e:
                print(f"  {encoding:8}: Fehler - {str(e)[:30]}...")
        
    except Exception as e:
        print(f"❌ Fehler beim Lesen der Datei: {e}")

if __name__ == "__main__":
    analyze_error_sources()
