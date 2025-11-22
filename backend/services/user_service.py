"""
Benutzer-Service für Authentifizierung und Benutzerverwaltung.
Verwaltet Benutzer, Passwörter (bcrypt), Rollen und Sessions.
"""
import os
import bcrypt
from sqlalchemy import text
from db.core import ENGINE
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import logging
import secrets

logger = logging.getLogger(__name__)

# Session-Dauer (Standard: 24 Stunden)
SESSION_DURATION_HOURS = int(os.getenv("ADMIN_SESSION_DURATION_HOURS", "24"))


def hash_password(password: str) -> str:
    """Erstellt bcrypt Hash eines Passworts (sicher)."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Prüft ob Passwort mit bcrypt Hash übereinstimmt."""
    try:
        if not password_hash or not password:
            logger.warning("Passwort oder Hash ist leer")
            return False
        
        # Prüfe ob Hash bcrypt-Format hat
        if not password_hash.startswith('$2'):
            logger.warning(f"Hash hat nicht das erwartete bcrypt-Format: {password_hash[:20]}...")
            return False
        
        result = bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
        if not result:
            logger.debug(f"Passwort-Verifikation fehlgeschlagen für Hash: {password_hash[:20]}...")
        return result
    except Exception as e:
        logger.error(f"Fehler bei Passwort-Verifikation: {e}", exc_info=True)
        return False


def get_user_by_username(username: str) -> Optional[Dict]:
    """Holt Benutzer aus Datenbank nach Benutzername."""
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, username, password_hash, role, email, full_name, 
                           active, created_at, last_login
                    FROM users
                    WHERE username = :username AND active = 1
                """),
                {"username": username}
            )
            row = result.fetchone()
            if row:
                return {
                    "id": row[0],
                    "username": row[1],
                    "password_hash": row[2],
                    "role": row[3],
                    "email": row[4],
                    "full_name": row[5],
                    "active": bool(row[6]),
                    "created_at": row[7],
                    "last_login": row[8]
                }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen von Benutzer {username}: {e}")
    return None


def authenticate_user(username: str, password: str) -> Optional[Dict]:
    """Authentifiziert Benutzer und gibt User-Dict zurück."""
    logger.debug(f"Authentifiziere Benutzer: {username}")
    user = get_user_by_username(username)
    if not user:
        logger.debug(f"Benutzer '{username}' nicht gefunden")
        return None
    
    logger.debug(f"Benutzer gefunden: ID={user['id']}, Hash vorhanden={bool(user.get('password_hash'))}")
    
    password_valid = verify_password(password, user["password_hash"])
    if not password_valid:
        logger.warning(f"Passwort-Verifikation fehlgeschlagen für Benutzer '{username}'")
        return None
    
    logger.debug(f"Passwort-Verifikation erfolgreich für Benutzer '{username}'")
    
    # Aktualisiere last_login
    try:
        with ENGINE.begin() as conn:
            conn.execute(
                text("UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = :user_id"),
                {"user_id": user["id"]}
            )
    except Exception as e:
        logger.warning(f"Fehler beim Aktualisieren von last_login: {e}")
    
    return user


def create_session(user_id: int, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> str:
    """Erstellt Session in Datenbank und gibt Session-ID zurück."""
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    
    try:
        with ENGINE.begin() as conn:
            conn.execute(
                text("""
                    INSERT INTO user_sessions (session_id, user_id, expires_at, ip_address, user_agent)
                    VALUES (:session_id, :user_id, :expires_at, :ip_address, :user_agent)
                """),
                {
                    "session_id": session_id,
                    "user_id": user_id,
                    "expires_at": expires_at,
                    "ip_address": ip_address,
                    "user_agent": user_agent
                }
            )
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Session: {e}")
        raise
    
    return session_id


def get_session(session_id: str) -> Optional[Dict]:
    """Holt Session aus Datenbank."""
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT s.session_id, s.user_id, s.expires_at, s.created_at,
                           u.username, u.role, u.active
                    FROM user_sessions s
                    JOIN users u ON s.user_id = u.id
                    WHERE s.session_id = :session_id AND s.expires_at > CURRENT_TIMESTAMP
                """),
                {"session_id": session_id}
            )
            row = result.fetchone()
            if row:
                return {
                    "session_id": row[0],
                    "user_id": row[1],
                    "expires_at": row[2],
                    "created_at": row[3],
                    "username": row[4],
                    "role": row[5],
                    "active": bool(row[6])
                }
    except Exception as e:
        logger.error(f"Fehler beim Abrufen der Session: {e}")
    return None


def delete_session(session_id: str) -> bool:
    """Löscht Session aus Datenbank."""
    try:
        with ENGINE.begin() as conn:
            result = conn.execute(
                text("DELETE FROM user_sessions WHERE session_id = :session_id"),
                {"session_id": session_id}
            )
            return result.rowcount > 0
    except Exception as e:
        logger.error(f"Fehler beim Löschen der Session: {e}")
    return False


def cleanup_expired_sessions():
    """Bereinigt abgelaufene Sessions."""
    try:
        with ENGINE.begin() as conn:
            result = conn.execute(
                text("DELETE FROM user_sessions WHERE expires_at < CURRENT_TIMESTAMP")
            )
            if result.rowcount > 0:
                logger.debug(f"{result.rowcount} abgelaufene Sessions bereinigt")
    except Exception as e:
        logger.error(f"Fehler beim Bereinigen von Sessions: {e}")


def get_all_users() -> List[Dict]:
    """Holt alle aktiven Benutzer."""
    try:
        with ENGINE.connect() as conn:
            result = conn.execute(
                text("""
                    SELECT id, username, role, email, full_name, active, 
                           created_at, last_login
                    FROM users
                    ORDER BY username
                """)
            )
            users = []
            for row in result.fetchall():
                users.append({
                    "id": row[0],
                    "username": row[1],
                    "role": row[2],
                    "email": row[3],
                    "full_name": row[4],
                    "active": bool(row[5]),
                    "created_at": row[6],
                    "last_login": row[7]
                })
            return users
    except Exception as e:
        logger.error(f"Fehler beim Abrufen aller Benutzer: {e}")
    return []


def create_user(username: str, password: str, role: str = "normal", 
                email: Optional[str] = None, full_name: Optional[str] = None,
                created_by: Optional[int] = None) -> Optional[int]:
    """Erstellt neuen Benutzer."""
    password_hash = hash_password(password)
    
    try:
        with ENGINE.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO users (username, password_hash, role, email, full_name, created_by)
                    VALUES (:username, :password_hash, :role, :email, :full_name, :created_by)
                """),
                {
                    "username": username,
                    "password_hash": password_hash,
                    "role": role,
                    "email": email,
                    "full_name": full_name,
                    "created_by": created_by
                }
            )
            return result.lastrowid
    except Exception as e:
        logger.error(f"Fehler beim Erstellen von Benutzer {username}: {e}")
    return None


def update_user(user_id: int, **kwargs) -> bool:
    """Aktualisiert Benutzer-Daten."""
    allowed_fields = ["email", "full_name", "role", "active", "notes"]
    updates = {k: v for k, v in kwargs.items() if k in allowed_fields}
    
    if not updates:
        return False
    
    updates["updated_at"] = datetime.now()
    
    try:
        with ENGINE.begin() as conn:
            set_clause = ", ".join([f"{k} = :{k}" for k in updates.keys()])
            updates["user_id"] = user_id
            conn.execute(
                text(f"UPDATE users SET {set_clause} WHERE id = :user_id"),
                updates
            )
            return True
    except Exception as e:
        logger.error(f"Fehler beim Aktualisieren von Benutzer {user_id}: {e}")
    return False


def change_password(user_id: int, new_password: str) -> bool:
    """Ändert Passwort eines Benutzers."""
    password_hash = hash_password(new_password)
    
    try:
        with ENGINE.begin() as conn:
            conn.execute(
                text("UPDATE users SET password_hash = :password_hash, updated_at = CURRENT_TIMESTAMP WHERE id = :user_id"),
                {"password_hash": password_hash, "user_id": user_id}
            )
            return True
    except Exception as e:
        logger.error(f"Fehler beim Ändern des Passworts für Benutzer {user_id}: {e}")
    return False


def delete_user(user_id: int) -> bool:
    """Deaktiviert Benutzer (soft delete)."""
    try:
        with ENGINE.begin() as conn:
            conn.execute(
                text("UPDATE users SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = :user_id"),
                {"user_id": user_id}
            )
            # Lösche alle Sessions des Benutzers
            conn.execute(
                text("DELETE FROM user_sessions WHERE user_id = :user_id"),
                {"user_id": user_id}
            )
            return True
    except Exception as e:
        logger.error(f"Fehler beim Löschen von Benutzer {user_id}: {e}")
    return False

