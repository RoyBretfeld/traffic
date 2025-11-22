#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test-Script: Prüft Security und Module-Funktionalität.
Sollte NICHTS kaputt machen - nur lesend prüfen.
"""
import sys
import io
from pathlib import Path

# Setze UTF-8 Encoding für Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import os
import importlib
from typing import List, Dict, Tuple

# Test-Ergebnisse
results: List[Tuple[str, bool, str]] = []

def test_result(name: str, success: bool, message: str = ""):
    """Speichert Test-Ergebnis."""
    results.append((name, success, message))
    status = "✅" if success else "❌"
    print(f"{status} {name}: {message if message else ('OK' if success else 'FEHLER')}")

def test_imports():
    """Test 1: Prüft ob alle wichtigen Module importierbar sind."""
    print("\n" + "="*60)
    print("TEST 1: Module-Imports")
    print("="*60)
    
    modules = [
        "backend.app",
        "backend.app_setup",
        "backend.routes.auth_api",
        "backend.services.user_service",
        "backend.middlewares.rate_limit",
        "db.schema",
        "db.schema_users",
    ]
    
    for module_name in modules:
        try:
            importlib.import_module(module_name)
            test_result(f"Import {module_name}", True)
        except Exception as e:
            test_result(f"Import {module_name}", False, str(e))

def test_auth_functions():
    """Test 2: Prüft ob Auth-Funktionen existieren."""
    print("\n" + "="*60)
    print("TEST 2: Auth-Funktionen")
    print("="*60)
    
    try:
        from backend.routes.auth_api import require_admin, require_auth
        test_result("require_admin existiert", True)
        test_result("require_auth existiert", True)
    except Exception as e:
        test_result("Auth-Funktionen", False, str(e))

def test_rate_limiting():
    """Test 3: Prüft Rate-Limiting-Middleware."""
    print("\n" + "="*60)
    print("TEST 3: Rate-Limiting")
    print("="*60)
    
    try:
        from backend.middlewares.rate_limit import RateLimitMiddleware, check_rate_limit
        test_result("RateLimitMiddleware importierbar", True)
        test_result("check_rate_limit Funktion existiert", True)
        
        # Test: Rate-Limit-Check (sollte funktionieren)
        allowed, remaining = check_rate_limit("127.0.0.1", 10, 15)
        test_result("check_rate_limit funktioniert", True, f"Allowed: {allowed}, Remaining: {remaining}")
    except Exception as e:
        test_result("Rate-Limiting", False, str(e))

def test_user_service():
    """Test 4: Prüft User-Service."""
    print("\n" + "="*60)
    print("TEST 4: User-Service")
    print("="*60)
    
    try:
        from backend.services.user_service import (
            hash_password, verify_password, get_user_by_username,
            authenticate_user, create_session, get_session
        )
        test_result("User-Service Funktionen importierbar", True)
        
        # Test: Passwort-Hashing (sollte funktionieren)
        test_password = "Test123"
        hashed = hash_password(test_password)
        verified = verify_password(test_password, hashed)
        test_result("Passwort-Hashing funktioniert", verified, "bcrypt")
    except Exception as e:
        test_result("User-Service", False, str(e))

def test_cors_config():
    """Test 5: Prüft CORS-Konfiguration."""
    print("\n" + "="*60)
    print("TEST 5: CORS-Konfiguration")
    print("="*60)
    
    try:
        from backend.app_setup import setup_middleware
        # Prüfe ob CORS-Logik in setup_middleware ist
        import inspect
        source = inspect.getsource(setup_middleware)
        if "CORS_ALLOWED_ORIGINS" in source or "allow_origins" in source:
            test_result("CORS-Konfiguration vorhanden", True)
        else:
            test_result("CORS-Konfiguration", False, "Nicht gefunden")
    except Exception as e:
        test_result("CORS-Konfiguration", False, str(e))

def test_database_schema():
    """Test 6: Prüft Datenbank-Schema."""
    print("\n" + "="*60)
    print("TEST 6: Datenbank-Schema")
    print("="*60)
    
    try:
        from db.schema import ensure_schema
        from db.schema_users import ensure_users_schema
        test_result("Schema-Funktionen importierbar", True)
        
        # Prüfe ob Schema-Funktionen existieren (ohne auszuführen!)
        test_result("ensure_schema existiert", callable(ensure_schema))
        test_result("ensure_users_schema existiert", callable(ensure_users_schema))
    except Exception as e:
        test_result("Datenbank-Schema", False, str(e))

def test_admin_routes():
    """Test 7: Prüft ob Admin-Router existieren (ohne sie zu ändern)."""
    print("\n" + "="*60)
    print("TEST 7: Admin-Router (nur Prüfung)")
    print("="*60)
    
    admin_route_files = [
        "backend/routes/db_management_api.py",
        "backend/routes/test_dashboard_api.py",
        "backend/routes/code_checker_api.py",
        "backend/routes/upload_csv.py",
        "backend/routes/backup_api.py",
        "backend/routes/system_rules_api.py",
    ]
    
    for route_file in admin_route_files:
        file_path = project_root / route_file
        if file_path.exists():
            test_result(f"Router-Datei existiert: {route_file}", True)
            # Prüfe ob require_admin verwendet wird (nur lesend)
            try:
                content = file_path.read_text(encoding='utf-8')
                if "require_admin" in content or "require_admin_auth" in content:
                    test_result(f"  → Auth-Check vorhanden", True)
                else:
                    test_result(f"  → Auth-Check fehlt", False, "ZU PRÜFEN")
            except Exception as e:
                test_result(f"  → Datei lesbar", False, str(e))
        else:
            test_result(f"Router-Datei: {route_file}", False, "Nicht gefunden")

def test_security_headers():
    """Test 8: Prüft ob Security-Header-Middleware existiert."""
    print("\n" + "="*60)
    print("TEST 8: Security-Header")
    print("="*60)
    
    security_header_file = project_root / "backend/middlewares/security_headers.py"
    if security_header_file.exists():
        test_result("Security-Header-Middleware existiert", True)
    else:
        test_result("Security-Header-Middleware", False, "Noch nicht implementiert (Phase B)")

def main():
    """Führt alle Tests aus."""
    print("="*60)
    print("SECURITY & MODULE-TESTS")
    print("="*60)
    print("WICHTIG: Diese Tests machen NICHTS kaputt - nur lesend!")
    print()
    
    # Führe Tests aus
    test_imports()
    test_auth_functions()
    test_rate_limiting()
    test_user_service()
    test_cors_config()
    test_database_schema()
    test_admin_routes()
    test_security_headers()
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    
    total = len(results)
    passed = sum(1 for _, success, _ in results if success)
    failed = total - passed
    
    print(f"Gesamt: {total} Tests")
    print(f"✅ Erfolgreich: {passed}")
    print(f"❌ Fehlgeschlagen: {failed}")
    
    if failed > 0:
        print("\nFehlgeschlagene Tests:")
        for name, success, message in results:
            if not success:
                print(f"  - {name}: {message}")
    
    print("\n" + "="*60)
    
    # Exit-Code: 0 wenn alle Tests erfolgreich
    return 0 if failed == 0 else 1

if __name__ == "__main__":
    exit(main())

