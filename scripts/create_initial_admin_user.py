#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Erstellt initialen Admin-Benutzer in der Datenbank.
Sollte nach der Migration 022_users_table.sql ausgeführt werden.
"""
import sys
import os
import io
from pathlib import Path

# Setze UTF-8 Encoding für Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Füge Projekt-Root zum Python-Pfad hinzu
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from db.core import ENGINE
from db.schema_users import ensure_users_schema
from backend.services.user_service import create_user, get_user_by_username, hash_password
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Erstellt initialen Admin-Benutzer."""
    print("=" * 60)
    print("Initialen Admin-Benutzer erstellen")
    print("=" * 60)
    print()
    
    # Stelle sicher, dass Schema existiert
    print("Pruefe Datenbank-Schema...")
    ensure_users_schema()
    print("[OK] Schema verifiziert")
    print()
    
    # Standard-Credentials (können über ENV überschrieben werden)
    default_username = os.getenv("INITIAL_ADMIN_USERNAME", "Bretfeld")
    default_password = os.getenv("INITIAL_ADMIN_PASSWORD", "Lisa01Bessy02")
    
    # Prüfe ob Benutzer bereits existiert
    existing = get_user_by_username(default_username)
    if existing:
        print(f"[WARN] Benutzer '{default_username}' existiert bereits!")
        print(f"   ID: {existing['id']}")
        print(f"   Rolle: {existing['role']}")
        print()
        response = input("Moechten Sie das Passwort zuruecksetzen? (j/n): ")
        if response.lower() == 'j':
            from backend.services.user_service import change_password
            change_password(existing['id'], default_password)
            print(f"[OK] Passwort fuer '{default_username}' zurueckgesetzt")
        else:
            print("Abgebrochen.")
        print("=" * 60)
        return
    
    # Erstelle Admin-Benutzer
    print(f"Erstelle Admin-Benutzer: {default_username}")
    user_id = create_user(
        username=default_username,
        password=default_password,
        role="admin",
        full_name="Administrator",
        created_by=None  # System
    )
    
    if user_id:
        print(f"[OK] Admin-Benutzer erstellt!")
        print(f"   ID: {user_id}")
        print(f"   Benutzername: {default_username}")
        print(f"   Rolle: admin")
        print()
        print("[WARN] WICHTIG: Aendern Sie das Standard-Passwort nach dem ersten Login!")
    else:
        print("[FEHLER] Fehler beim Erstellen des Admin-Benutzers")
    
    print("=" * 60)


if __name__ == "__main__":
    main()

