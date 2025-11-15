#!/usr/bin/env python3
"""Test-Script für AI-Test Route"""

import sys
from pathlib import Path

# Projekt-Root zum Python-Pfad hinzufügen
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.app import app

def test_ai_test_routes():
    """Prüft ob AI-Test Routes registriert sind"""
    routes = [(r.path, list(r.methods) if hasattr(r, 'methods') else []) for r in app.routes]
    
    ai_routes = [r for r in routes if 'ai-test' in r[0]]
    
    print("AI-Test Routes:")
    for path, methods in ai_routes:
        print(f"  {path} - {methods}")
    
    if not ai_routes:
        print("FEHLER: Keine AI-Test Routes gefunden!")
        return False
    
    # Prüfe ob HTML-Datei existiert
    html_file = PROJECT_ROOT / "frontend" / "ai-test.html"
    if not html_file.exists():
        print(f"FEHLER: HTML-Datei nicht gefunden: {html_file}")
        return False
    
    print(f"OK: HTML-Datei gefunden: {html_file} ({html_file.stat().st_size} bytes)")
    
    # Versuche HTML zu laden
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"OK: HTML-Datei geladen: {len(content)} Zeichen")
    except Exception as e:
        print(f"FEHLER: HTML-Datei konnte nicht geladen werden: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_ai_test_routes()
    sys.exit(0 if success else 1)

