#!/usr/bin/env python3
"""
Lint-Check: Prüft, dass keine @app.* Dekoratoren auf Top-Level in backend/app.py stehen.
Diese müssen innerhalb von create_app() sein.
"""
import re
import sys
from pathlib import Path

def check_no_top_level_app():
    """Prüft backend/app.py auf Top-Level @app.* Dekoratoren."""
    app_file = Path(__file__).parent.parent / "backend" / "app.py"
    
    if not app_file.exists():
        print(f"FEHLER: {app_file} nicht gefunden")
        return 1
    
    with app_file.open("r", encoding="utf-8") as f:
        content = f.read()
    
    # Finde alle @app.* Dekoratoren
    lines = content.split("\n")
    in_create_app = False
    errors = []
    
    for i, line in enumerate(lines, 1):
        # Prüfe ob wir in create_app() sind
        if "def create_app()" in line:
            in_create_app = True
            continue
        
        # Prüfe ob create_app() beendet wird
        if in_create_app and line.strip().startswith("def ") and "create_app" not in line:
            # Neue Funktion außerhalb - aber könnte noch in create_app sein wenn verschachtelt
            # Einfacher: Prüfe auf return app
            if "return app" in line:
                in_create_app = False
                continue
        
        # Prüfe auf Top-Level @app.*
        if not in_create_app and re.match(r'^\s*@app\.', line):
            errors.append((i, line.strip()))
    
    if errors:
        print("FEHLER: Top-Level @app.* Dekoratoren gefunden (müssen in create_app() sein):")
        for line_num, line_content in errors:
            print(f"  Zeile {line_num}: {line_content}")
        return 1
    
    print("OK: Keine Top-Level @app.* Dekoratoren gefunden")
    return 0

if __name__ == "__main__":
    sys.exit(check_no_top_level_app())

