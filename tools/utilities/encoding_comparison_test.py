#!/usr/bin/env python3
"""
Encoding-Vergleichstest

Testet 5 Tourpläne mit beiden Encoding-Strategien und zählt Fehler.
"""

import pandas as pd
from pathlib import Path
import re

def count_encoding_errors(text):
    """Zählt verschiedene Encoding-Fehler in einem Text."""
    if not text or not isinstance(text, str):
        return 0
    
    # Verschiedene Korruptions-Muster
    error_patterns = [
        r'├í',           # ß → ├í
        r'í',            # ß → í  
        r'´j´{',         # Umlaute → ´j´{
        r'┬',            # Umlaute → ┬
        r'├',            # Umlaute → ├
        r'',            # Replacement Character
    ]
    
    total_errors = 0
    for pattern in error_patterns:
        matches = len(re.findall(pattern, text))
        total_errors += matches
    
    return total_errors

def test_encoding_strategy(csv_file, encoding):
    """Testet eine Encoding-Strategie an einer CSV-Datei."""
    try:
        df = pd.read_csv(csv_file, encoding=encoding, sep=';', header=None)
        
        # Zähle Fehler in allen Text-Spalten
        total_errors = 0
        error_details = {}
        
        for col in df.columns:
            if df[col].dtype == 'object':  # Text-Spalten
                col_content = df[col].astype(str).str.cat(sep=' ')
                col_errors = count_encoding_errors(col_content)
                total_errors += col_errors
                
                if col_errors > 0:
                    error_details[f'Spalte_{col}'] = col_errors
        
        return {
            'success': True,
            'total_errors': total_errors,
            'error_details': error_details,
            'rows': len(df)
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'total_errors': 999999,  # Sehr hohe Fehlerzahl für fehlgeschlagene Encodings
            'error_details': {},
            'rows': 0
        }

def run_encoding_comparison():
    """Führt den Encoding-Vergleichstest durch."""
    
    # Wähle 5 Tourpläne aus
    tourplaene_dir = Path("tourplaene")
    csv_files = list(tourplaene_dir.glob("*.csv"))[:5]  # Erste 5 Dateien
    
    print("🧪 Encoding-Vergleichstest")
    print("=" * 50)
    print(f"📁 Teste {len(csv_files)} Tourpläne")
    print()
    
    # Encoding-Strategien
    strategies = {
        'utf-8': 'UTF-8 (Standard)',
        'latin-1': 'Latin-1 (Windows)',
        'cp1252': 'CP1252 (Windows)',
        'iso-8859-1': 'ISO-8859-1 (Latin)'
    }
    
    results = {}
    
    for strategy, description in strategies.items():
        print(f"🔍 Teste {description} ({strategy})")
        print("-" * 40)
        
        strategy_results = []
        total_errors = 0
        successful_files = 0
        
        for csv_file in csv_files:
            print(f"  📄 {csv_file.name}: ", end="")
            
            result = test_encoding_strategy(csv_file, strategy)
            strategy_results.append(result)
            
            if result['success']:
                print(f"✅ {result['total_errors']} Fehler ({result['rows']} Zeilen)")
                total_errors += result['total_errors']
                successful_files += 1
            else:
                print(f"❌ Fehler: {result['error'][:50]}...")
        
        results[strategy] = {
            'description': description,
            'total_errors': total_errors,
            'successful_files': successful_files,
            'total_files': len(csv_files),
            'avg_errors_per_file': total_errors / max(successful_files, 1),
            'details': strategy_results
        }
        
        print(f"  📊 Gesamt: {total_errors} Fehler in {successful_files}/{len(csv_files)} Dateien")
        print()
    
    # Ergebnisse vergleichen
    print("📈 VERGLEICHSERGEBNISSE")
    print("=" * 50)
    
    # Sortiere nach Fehleranzahl (weniger ist besser)
    sorted_results = sorted(results.items(), key=lambda x: x[1]['total_errors'])
    
    for i, (strategy, data) in enumerate(sorted_results, 1):
        status = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else "❌"
        print(f"{status} {data['description']}")
        print(f"   Fehler: {data['total_errors']}")
        print(f"   Erfolgreiche Dateien: {data['successful_files']}/{data['total_files']}")
        print(f"   Ø Fehler pro Datei: {data['avg_errors_per_file']:.1f}")
        print()
    
    # Empfehlung
    best_strategy = sorted_results[0][0]
    best_data = sorted_results[0][1]
    
    print("🎯 EMPFEHLUNG")
    print("=" * 20)
    print(f"✅ Beste Strategie: {best_data['description']} ({best_strategy})")
    print(f"   Mit nur {best_data['total_errors']} Fehlern in {best_data['successful_files']} Dateien")
    
    if best_data['total_errors'] == 0:
        print("   🎉 Perfekt! Keine Encoding-Fehler!")
    elif best_data['total_errors'] < 10:
        print("   👍 Sehr gut! Nur wenige Fehler.")
    else:
        print("   ⚠️  Viele Fehler - Normalisierung nötig.")
    
    return results

if __name__ == "__main__":
    results = run_encoding_comparison()
    
    print(f"\n💡 Nächste Schritte:")
    print(f"1. Wählen Sie die beste Encoding-Strategie")
    print(f"2. Implementieren Sie sie im Backend")
    print(f"3. Testen Sie mit allen Tourplänen")
