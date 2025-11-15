#!/usr/bin/env python3
"""Prüft AI-Test Setup"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 60)
print("AI-Test Setup Check")
print("=" * 60)

# 1. Route-Prüfung
print("\n1. Route-Prüfung:")
try:
    from backend.app import app
    routes = [(r.path, list(r.methods) if hasattr(r, 'methods') else []) for r in app.routes]
    ai_routes = [r for r in routes if 'ai-test' in r[0]]
    
    if ai_routes:
        print("   [OK] Routes gefunden:")
        for path, methods in ai_routes:
            print(f"     - {path} ({methods})")
    else:
        print("   [FEHLER] KEINE AI-Test Routes gefunden!")
except Exception as e:
    print(f"   [FEHLER] Fehler beim Laden der App: {e}")

# 2. HTML-Datei-Prüfung
print("\n2. HTML-Datei-Prüfung:")
html_file = PROJECT_ROOT / "frontend" / "ai-test.html"
if html_file.exists():
    print(f"   [OK] Datei gefunden: {html_file}")
    print(f"     Groesse: {html_file.stat().st_size} bytes")
    
    try:
        with open(html_file, "r", encoding="utf-8") as f:
            content = f.read()
        print(f"     Inhalt geladen: {len(content)} Zeichen")
        
        # Prüfe wichtige Elemente
        if "<!DOCTYPE html>" in content:
            print("     [OK] DOCTYPE gefunden")
        if 'id="uploadArea"' in content:
            print("     [OK] Upload-Bereich gefunden")
        if 'id="fileInput"' in content:
            print("     [OK] File-Input gefunden")
        if "/api/ai-test/analyze" in content:
            print("     [OK] API-Endpoint-Referenz gefunden")
    except Exception as e:
        print(f"     [FEHLER] Fehler beim Laden: {e}")
else:
    print(f"   [FEHLER] Datei NICHT gefunden: {html_file}")

# 3. API-Router-Prüfung
print("\n3. API-Router-Prüfung:")
try:
    from backend.routes.ai_test_api import router
    print("   [OK] Router importiert")
    print(f"     Prefix: {router.prefix}")
    print(f"     Tags: {router.tags}")
    
    # Prüfe Routes im Router
    router_routes = [(r.path, list(r.methods) if hasattr(r, 'methods') else []) for r in router.routes]
    print(f"     Routes im Router: {len(router_routes)}")
    for path, methods in router_routes:
        print(f"       - {path} ({methods})")
except Exception as e:
    print(f"   [FEHLER] Fehler beim Import: {e}")

# 4. Zusammenfassung
print("\n" + "=" * 60)
print("Zusammenfassung:")
print("- Route muss im Server registriert sein")
print("- Server muss neu gestartet werden, damit Änderungen wirksam werden")
print("- Browser-Cache leeren falls Seite nicht lädt")
print("=" * 60)

