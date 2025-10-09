#!/usr/bin/env python3
"""
Encoding-Debug-Tool

Analysiert verschiedene Encoding-Probleme in CSV-Dateien.
"""

import pandas as pd
from pathlib import Path
import chardet

def analyze_encoding_issues():
    """Analysiert Encoding-Probleme in CSV-Dateien."""
    
    print("🔍 Encoding-Analyse der CSV-Dateien")
    print("=" * 50)
    
    # Teste verschiedene Encodings
    encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1', 'windows-1252']
    
    for csv_file in Path("tourplaene").glob("*.csv"):
        print(f"\n📄 Datei: {csv_file.name}")
        print("-" * 30)
        
        # Automatische Encoding-Erkennung
        with open(csv_file, 'rb') as f:
            raw_data = f.read()
            detected = chardet.detect(raw_data)
            print(f"🔍 Automatisch erkannt: {detected['encoding']} (Confidence: {detected['confidence']:.2f})")
        
        # Teste verschiedene Encodings
        for encoding in encodings:
            try:
                df = pd.read_csv(csv_file, encoding=encoding, sep=';', header=None, nrows=5)
                content = df.to_string()
                
                # Prüfe auf verschiedene Korruptions-Muster
                patterns = {
                    '├í': '├í' in content,
                    'í': 'í' in content,
                    '´j´{': '´j´{' in content,
                    'ß': 'ß' in content,
                    'ä': 'ä' in content,
                    'ö': 'ö' in content,
                    'ü': 'ü' in content,
                }
                
                found_patterns = [pattern for pattern, found in patterns.items() if found]
                
                if found_patterns:
                    print(f"  {encoding:12} → Gefunden: {', '.join(found_patterns)}")
                else:
                    print(f"  {encoding:12} → Sauber")
                    
            except Exception as e:
                print(f"  {encoding:12} → Fehler: {str(e)[:50]}...")
    
    print(f"\n💡 Empfehlung:")
    print(f"   - Verwende chardet für automatische Encoding-Erkennung")
    print(f"   - Teste mehrere Encodings und wähle das beste")
    print(f"   - Normalisiere alle deutschen Zeichen beim Einlesen")

def test_encoding_transformations():
    """Testet verschiedene Encoding-Transformationen."""
    
    print(f"\n🧪 Encoding-Transformationen testen")
    print("=" * 40)
    
    test_strings = [
        "Straße",
        "Müller", 
        "Größe",
        "Bäcker",
        "Berggießhübel"
    ]
    
    for original in test_strings:
        print(f"\nOriginal: '{original}'")
        
        # Simuliere verschiedene Encoding-Probleme
        try:
            # latin-1 → UTF-8 (häufigster Fehler)
            latin1_bytes = original.encode('latin-1')
            utf8_interpreted = latin1_bytes.decode('utf-8', errors='replace')
            print(f"  latin-1→UTF-8: '{utf8_interpreted}'")
        except:
            print(f"  latin-1→UTF-8: Fehler")
        
        try:
            # cp1252 → UTF-8
            cp1252_bytes = original.encode('cp1252')
            utf8_interpreted = cp1252_bytes.decode('utf-8', errors='replace')
            print(f"  cp1252→UTF-8:  '{utf8_interpreted}'")
        except:
            print(f"  cp1252→UTF-8:  Fehler")
        
        try:
            # windows-1252 → UTF-8
            win1252_bytes = original.encode('windows-1252')
            utf8_interpreted = win1252_bytes.decode('utf-8', errors='replace')
            print(f"  win1252→UTF-8: '{utf8_interpreted}'")
        except:
            print(f"  win1252→UTF-8: Fehler")

if __name__ == "__main__":
    print("🚀 Encoding-Debug-Tool")
    print("=" * 30)
    
    # Analysiere CSV-Dateien
    analyze_encoding_issues()
    
    # Teste Transformationen
    test_encoding_transformations()
    
    print(f"\n🎯 Fazit:")
    print(f"   - Encoding-Probleme entstehen durch falsche Interpretation")
    print(f"   - Verschiedene Systeme verwenden verschiedene Encodings")
    print(f"   - Lösung: Automatische Erkennung + Normalisierung")
