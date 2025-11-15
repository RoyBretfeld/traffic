#!/usr/bin/env python3
"""
Pre-commit Hook: Blockiert Schreibzugriffe auf ./Tourplaene
Verhindert Commits mit Änderungen im Original-Ordner.
"""
import subprocess
import sys

def main():
    try:
        # Git diff --cached --name-status ausführen
        result = subprocess.check_output(['git', 'diff', '--cached', '--name-status'], 
                                       stderr=subprocess.STDOUT, text=True)
        
        for line in result.splitlines():
            if not line.strip():
                continue
                
            parts = line.split('\t')
            if len(parts) < 2:
                continue
                
            status, path = parts[0], parts[1]
            
            # Prüfe auf Änderungen im Tourplaene-Verzeichnis
            if path.startswith('Tourplaene/') or path.startswith('./Tourplaene/'):
                print(f'ERROR: Änderungen im Original-Ordner verboten: {path}')
                print(f'   Status: {status}')
                print('   Der ./Tourplaene Ordner ist schreibgeschützt.')
                print('   Verwende ./data/staging oder ./data/output für Ausgaben.')
                sys.exit(1)
        
        print('OK: Pre-commit: Keine Änderungen im Original-Ordner erkannt')
        sys.exit(0)
        
    except subprocess.CalledProcessError as e:
        print(f'ERROR: Fehler beim Ausführen von git diff: {e}')
        sys.exit(1)
    except Exception as e:
        print(f'ERROR: Unerwarteter Fehler: {e}')
        sys.exit(1)

if __name__ == '__main__':
    main()
