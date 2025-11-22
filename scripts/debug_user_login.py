#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Debug-Script für Login-Probleme.
Prüft Benutzer in DB und testet Passwort-Verifikation.
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

from backend.services.user_service import get_user_by_username, verify_password, hash_password
from sqlalchemy import text
from db.core import ENGINE

def main():
    print("=" * 60)
    print("Debug: Benutzer-Login")
    print("=" * 60)
    print()
    
    username = "Bretfeld"
    test_password = "Lisa01Bessy02"
    
    # 1. Prüfe ob Benutzer existiert
    print(f"1. Pruefe Benutzer '{username}'...")
    user = get_user_by_username(username)
    
    if not user:
        print(f"   [FEHLER] Benutzer '{username}' nicht gefunden!")
        return
    
    print(f"   [OK] Benutzer gefunden:")
    print(f"      ID: {user['id']}")
    print(f"      Benutzername: {user['username']}")
    print(f"      Rolle: {user['role']}")
    print(f"      Aktiv: {user['active']}")
    print(f"      Passwort-Hash: {user['password_hash'][:20]}...")
    print()
    
    # 2. Teste Passwort-Verifikation
    print(f"2. Teste Passwort-Verifikation...")
    print(f"   Test-Passwort: '{test_password}'")
    
    is_valid = verify_password(test_password, user['password_hash'])
    print(f"   Verifikation: {'[OK] Passwort korrekt' if is_valid else '[FEHLER] Passwort falsch'}")
    print()
    
    # 3. Zeige Hash-Details
    print("3. Hash-Details:")
    hash_str = user['password_hash']
    print(f"   Hash-Laenge: {len(hash_str)} Zeichen")
    print(f"   Hash-Start: {hash_str[:30]}...")
    print(f"   Hash-Typ: {'bcrypt' if hash_str.startswith('$2') else 'unbekannt'}")
    print()
    
    # 4. Teste neuen Hash
    print("4. Erstelle neuen Hash zum Vergleich...")
    new_hash = hash_password(test_password)
    print(f"   Neuer Hash: {new_hash[:30]}...")
    new_verify = verify_password(test_password, new_hash)
    print(f"   Neue Verifikation: {'[OK]' if new_verify else '[FEHLER]'}")
    print()
    
    # 5. Prüfe alle Benutzer in DB
    print("5. Alle Benutzer in DB:")
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(text("SELECT id, username, role, active FROM users"))
            users = result.fetchall()
            if users:
                for u in users:
                    print(f"   - ID {u[0]}: {u[1]} ({u[2]}, aktiv: {u[3]})")
            else:
                print("   [KEINE] Keine Benutzer gefunden")
    except Exception as e:
        print(f"   [FEHLER] {e}")
    
    print()
    print("=" * 60)

if __name__ == "__main__":
    main()

