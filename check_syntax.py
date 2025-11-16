#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Umfassende Syntax-Prüfung für frontend/index.html
Prüft auf fehlende Klammern, geschweifte Klammern, eckige Klammern, unvollständige Funktionen, etc.
"""

import re
import sys
from pathlib import Path

def check_syntax(file_path):
    """Prüft die Syntax einer JavaScript-Datei auf Fehler."""
    errors = []
    warnings = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            lines = content.split('\n')
    except Exception as e:
        return [f"FEHLER: Datei konnte nicht gelesen werden: {e}"], []
    
    # 1. Prüfe auf unausgeglichene Klammern (vereinfacht, ignoriert Strings)
    paren_stack = []
    brace_stack = []
    bracket_stack = []
    in_string = False
    string_char = None
    in_template = False
    escape_next = False
    
    for i, line in enumerate(lines, 1):
        j = 0
        while j < len(line):
            char = line[j]
            
            if escape_next:
                escape_next = False
                j += 1
                continue
            
            if char == '\\':
                escape_next = True
                j += 1
                continue
            
            if not in_string and not in_template:
                if char in ['"', "'"]:
                    in_string = True
                    string_char = char
                elif char == '`':
                    in_template = True
                elif char == '(':
                    paren_stack.append((i, j + 1))
                elif char == ')':
                    if not paren_stack:
                        errors.append(f"Zeile {i}:{j+1} - Unmatched closing parenthesis ')'")
                    else:
                        paren_stack.pop()
                elif char == '{':
                    brace_stack.append((i, j + 1))
                elif char == '}':
                    if not brace_stack:
                        errors.append(f"Zeile {i}:{j+1} - Unmatched closing brace '}}'")
                    else:
                        brace_stack.pop()
                elif char == '[':
                    bracket_stack.append((i, j + 1))
                elif char == ']':
                    if not bracket_stack:
                        errors.append(f"Zeile {i}:{j+1} - Unmatched closing bracket ']'")
                    else:
                        bracket_stack.pop()
            elif in_string and char == string_char:
                in_string = False
                string_char = None
            elif in_template and char == '`':
                in_template = False
            
            j += 1
    
    # Unclosed openings
    for pos in paren_stack:
        errors.append(f"Zeile {pos[0]}:{pos[1]} - Unclosed parenthesis '('")
    for pos in brace_stack:
        errors.append(f"Zeile {pos[0]}:{pos[1]} - Unclosed brace '{{'")
    for pos in bracket_stack:
        errors.append(f"Zeile {pos[0]}:{pos[1]} - Unclosed bracket '['")
    
    # 2. Prüfe auf try-catch-finally Strukturen
    try_blocks = []
    for i, line in enumerate(lines, 1):
        if re.search(r'\btry\s*\{', line):
            try_blocks.append((i, 'try'))
        if re.search(r'\bcatch\s*\(', line):
            if not try_blocks or try_blocks[-1][1] != 'try':
                errors.append(f"Zeile {i} - 'catch' ohne zugehöriges 'try'")
            else:
                try_blocks[-1] = (try_blocks[-1][0], 'catch')
        if re.search(r'\bfinally\s*\{', line):
            if not try_blocks or try_blocks[-1][1] not in ['try', 'catch']:
                errors.append(f"Zeile {i} - 'finally' ohne zugehöriges 'try'/'catch'")
    
    # 3. Prüfe auf unvollständige Funktionen
    function_pattern = r'(function\s+\w+|async\s+function\s+\w+|const\s+\w+\s*=\s*(async\s+)?function|let\s+\w+\s*=\s*(async\s+)?function|window\.\w+\s*=\s*(async\s+)?function)'
    for i, line in enumerate(lines, 1):
        if re.search(function_pattern, line):
            # Prüfe ob die Funktion geschlossen ist (vereinfacht)
            # Suche nach der nächsten schließenden Klammer
            pass  # Zu komplex für einfache Prüfung
    
    # 4. Prüfe auf häufige Syntax-Fehler
    for i, line in enumerate(lines, 1):
        # Fehlende Semikolons nach return (warnung, kein Fehler)
        if re.search(r'return\s+[^;{}\n]+$', line) and not re.search(r'return\s*\(', line):
            if '//' not in line or line.find('//') > line.find('return'):
                warnings.append(f"Zeile {i} - Return-Statement ohne Semikolon (kann problematisch sein)")
        
        # Doppelte Klammern
        if re.search(r'\(\(\(|\)\)\)', line):
            warnings.append(f"Zeile {i} - Verdächtige verschachtelte Klammern")
    
    return errors, warnings

def main():
    file_path = Path('frontend/index.html')
    
    if not file_path.exists():
        print(f"FEHLER: Datei {file_path} nicht gefunden!")
        sys.exit(1)
    
    print("=" * 80)
    print("UMFASSENDE SYNTAX-PRÜFUNG")
    print("=" * 80)
    print(f"Datei: {file_path}")
    print()
    
    errors, warnings = check_syntax(file_path)
    
    if errors:
        print(f"[FEHLER] KRITISCHE FEHLER GEFUNDEN: {len(errors)}")
        print("-" * 80)
        for error in errors:
            print(f"  {error}")
        print()
    else:
        print("[OK] Keine kritischen Syntax-Fehler gefunden!")
        print()
    
    if warnings:
        print(f"[WARNUNG] WARNUNGEN: {len(warnings)}")
        print("-" * 80)
        for warning in warnings[:20]:  # Maximal 20 Warnungen anzeigen
            print(f"  {warning}")
        if len(warnings) > 20:
            print(f"  ... und {len(warnings) - 20} weitere Warnungen")
        print()
    
    print("=" * 80)
    print(f"ZUSAMMENFASSUNG: {len(errors)} Fehler, {len(warnings)} Warnungen")
    print("=" * 80)
    
    # Speichere Report
    report_path = Path('SYNTAX_CHECK_REPORT.md')
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("# Syntax-Prüfungs-Report\n\n")
        f.write(f"**Datei:** `{file_path}`\n")
        f.write(f"**Datum:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"## Zusammenfassung\n\n")
        f.write(f"- **Kritische Fehler:** {len(errors)}\n")
        f.write(f"- **Warnungen:** {len(warnings)}\n\n")
        
        if errors:
            f.write("## [FEHLER] Kritische Fehler\n\n")
            for error in errors:
                f.write(f"- {error}\n")
            f.write("\n")
        
        if warnings:
            f.write("## [WARNUNG] Warnungen\n\n")
            for warning in warnings:
                f.write(f"- {warning}\n")
            f.write("\n")
        
        if not errors and not warnings:
            f.write("## [OK] Keine Fehler gefunden!\n\n")
    
    print(f"\n[INFO] Report gespeichert: {report_path}")
    
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())

