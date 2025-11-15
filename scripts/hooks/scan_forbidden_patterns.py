#!/usr/bin/env python3
"""
Pre-commit Hook: Sucht nach verdächtigen Schreib-Mustern auf Tourplaene
Verhindert versehentliche Schreib-Calls, die auf Tourplaene zielen.
"""
import subprocess
import sys
import re
import os

# Verdächtige Muster für Schreibzugriffe auf Tourplaene
PATTERNS = [
    # Pandas to_csv mit Tourplaene
    re.compile(r"to_csv\(.*Tourplaene", re.I),
    # Python open() mit Schreibmodus
    re.compile(r"open\(.*Tourplaene.*['\"]w", re.I),
    # Pathlib write_text/write_bytes
    re.compile(r"write_text\(.*Tourplaene", re.I),
    re.compile(r"write_bytes\(.*Tourplaene", re.I),
    # Weitere verdächtige Muster
    re.compile(r"\.write\(.*Tourplaene", re.I),
    re.compile(r"with open\(.*Tourplaene.*['\"]w", re.I),
]

def main():
    try:
        # Git diff --cached --name-only ausführen
        result = subprocess.check_output(['git', 'diff', '--cached', '--name-only'], 
                                       stderr=subprocess.STDOUT, text=True)
        
        changed_files = result.splitlines()
        issues_found = []
        
        for file_path in changed_files:
            if not file_path.strip():
                continue
                
            # Nur relevante Dateitypen prüfen
            if not file_path.endswith(('.py', '.js', '.ts', '.tsx', '.html', '.md', '.yaml', '.yml')):
                continue
            
            # Datei existiert und ist lesbar?
            if not os.path.exists(file_path):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Prüfe auf verdächtige Muster
                for pattern in PATTERNS:
                    matches = pattern.findall(content)
                    if matches:
                        issues_found.append({
                            'file': file_path,
                            'pattern': pattern.pattern,
                            'matches': matches[:3]  # Nur erste 3 Matches zeigen
                        })
                        
            except Exception as e:
                print(f'WARNUNG: Konnte Datei {file_path} nicht lesen: {e}')
                continue
        
        if issues_found:
            print('ERROR: Verdächtige Schreib-Muster auf Tourplaene gefunden:')
            for issue in issues_found:
                print(f'   Datei: {issue["file"]}')
                print(f'   Muster: {issue["pattern"]}')
                print(f'   Treffer: {issue["matches"]}')
                print()
            print('   Der ./Tourplaene Ordner ist schreibgeschützt.')
            print('   Verwende ./data/staging oder ./data/output für Ausgaben.')
            sys.exit(1)
        
        print('OK: Pre-commit: Keine verdächtigen Schreib-Muster erkannt')
        sys.exit(0)
        
    except subprocess.CalledProcessError as e:
        print(f'ERROR: Fehler beim Ausführen von git diff: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'ERROR: Unerwarteter Fehler: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
