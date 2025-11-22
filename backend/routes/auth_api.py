"""
Authentifizierung für Admin-Bereich (Datenbank-basiert).
Nutzt user_service für Benutzer- und Session-Verwaltung.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from typing import Optional
import logging
import os

from backend.services.user_service import (
    authenticate_user, create_session, get_session, delete_session,
    cleanup_expired_sessions, get_all_users, create_user, update_user,
    change_password, delete_user, get_user_by_username, verify_password
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Session-Dauer (Standard: 24 Stunden)
SESSION_DURATION_HOURS = int(os.getenv("ADMIN_SESSION_DURATION_HOURS", "24"))


# Pydantic Models
class LoginRequest(BaseModel):
    username: str
    password: str


class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "normal"  # "normal" oder "admin"
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[str] = None
    active: Optional[bool] = None


class PasswordChange(BaseModel):
    old_password: Optional[str] = None  # Optional für Admin-Passwort-Reset
    new_password: str


# Helper Functions
def get_session_from_request(request: Request) -> Optional[str]:
    """Holt Session-ID aus Request (Cookie oder Header)."""
    # 1. Versuche Cookie
    session_id = request.cookies.get("admin_session")
    if session_id:
        session = get_session(session_id)
        if session:
            return session_id
    
    # 2. Versuche Authorization Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        session_id = auth_header.replace("Bearer ", "")
        session = get_session(session_id)
        if session:
            return session_id
    
    return None


async def require_auth(request: Request) -> dict:
    """
    Dependency: Prüft ob Request authentifiziert ist.
    Gibt Session-Dict zurück.
    """
    session_id = get_session_from_request(request)
    
    if not session_id:
        raise HTTPException(
            status_code=401,
            detail="Nicht authentifiziert. Bitte einloggen.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    session = get_session(session_id)
    if not session:
        raise HTTPException(
            status_code=401,
            detail="Session ungültig oder abgelaufen.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return session


async def require_admin(request: Request) -> dict:
    """
    Dependency: Prüft ob Request authentifiziert ist UND Admin-Rolle hat.
    """
    session = await require_auth(request)
    
    if session.get("role") != "admin":
        raise HTTPException(
            status_code=403,
            detail="Zugriff verweigert. Admin-Rechte erforderlich."
        )
    
    return session


# Auth Endpoints
@router.post("/api/auth/login")
async def login(login_req: LoginRequest, request: Request):
    """
    Login-Endpoint für Admin-Bereich.
    Prüft Benutzername und Passwort und erstellt Session in Datenbank.
    """
    # Bereinige abgelaufene Sessions
    cleanup_expired_sessions()
    
    # Authentifiziere Benutzer
    user = authenticate_user(login_req.username, login_req.password)
    
    if not user:
        logger.warning(f"Fehlgeschlagener Login-Versuch für '{login_req.username}' von {request.client.host}")
        raise HTTPException(status_code=401, detail="Ungültiger Benutzername oder Passwort")
    
    # Erstelle Session
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    
    try:
        session_id = create_session(user["id"], ip_address, user_agent)
        logger.info(f"Login erfolgreich: {user['username']} ({user['role']}) von {ip_address}")
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Session: {e}")
        raise HTTPException(status_code=500, detail="Fehler beim Erstellen der Session")
    
    # Response mit Session-Cookie
    response = JSONResponse({
        "success": True,
        "session_id": session_id,
        "user": {
            "id": user["id"],
            "username": user["username"],
            "role": user["role"],
            "full_name": user.get("full_name")
        }
    })
    
    # Setze Cookie (HttpOnly, Secure in Produktion)
    is_production = os.getenv("APP_ENV", "development") == "production"
    response.set_cookie(
        key="admin_session",
        value=session_id,
        max_age=SESSION_DURATION_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=is_production  # HTTPS in Produktion
    )
    
    return response


@router.post("/api/auth/logout")
async def logout(request: Request):
    """Logout-Endpoint: Löscht Session aus Datenbank."""
    session_id = get_session_from_request(request)
    
    if session_id:
        delete_session(session_id)
        logger.info(f"Logout von {request.client.host}")
    
    response = JSONResponse({"success": True, "message": "Erfolgreich ausgeloggt"})
    response.delete_cookie(key="admin_session")
    return response


@router.get("/api/auth/status")
async def auth_status(request: Request):
    """Prüft ob Session gültig ist und gibt User-Info zurück."""
    session_id = get_session_from_request(request)
    
    if session_id:
        session = get_session(session_id)
        if session:
            return JSONResponse({
                "authenticated": True,
                "user": {
                    "id": session["user_id"],
                    "username": session["username"],
                    "role": session["role"]
                },
                "expires_at": session["expires_at"].isoformat() if hasattr(session["expires_at"], "isoformat") else str(session["expires_at"])
            })
    
    return JSONResponse({"authenticated": False})


@router.get("/api/auth/check")
async def check_auth(session: dict = Depends(require_auth)):
    """
    Protected Endpoint: Prüft ob Request authentifiziert ist.
    """
    return JSONResponse({
        "authenticated": True,
        "user": {
            "id": session["user_id"],
            "username": session["username"],
            "role": session["role"]
        }
    })


# User Management Endpoints (nur für Admins)
@router.get("/api/users")
async def list_users(session: dict = Depends(require_admin)):
    """Listet alle Benutzer (nur für Admins)."""
    users = get_all_users()
    return JSONResponse({"users": users})


@router.post("/api/users")
async def create_new_user(user_data: UserCreate, session: dict = Depends(require_admin)):
    """Erstellt neuen Benutzer (nur für Admins)."""
    # Prüfe ob Benutzername bereits existiert
    existing = get_user_by_username(user_data.username)
    if existing:
        raise HTTPException(status_code=400, detail="Benutzername bereits vergeben")
    
    # Prüfe Rolle
    if user_data.role not in ["normal", "admin"]:
        raise HTTPException(status_code=400, detail="Ungültige Rolle. Erlaubt: 'normal', 'admin'")
    
    user_id = create_user(
        username=user_data.username,
        password=user_data.password,
        role=user_data.role,
        email=user_data.email,
        full_name=user_data.full_name,
        created_by=session["user_id"]
    )
    
    if not user_id:
        raise HTTPException(status_code=500, detail="Fehler beim Erstellen des Benutzers")
    
    logger.info(f"Benutzer erstellt: {user_data.username} ({user_data.role}) von {session['username']}")
    return JSONResponse({"success": True, "user_id": user_id})


@router.put("/api/users/{user_id}")
async def update_user_data(user_id: int, user_data: UserUpdate, session: dict = Depends(require_admin)):
    """Aktualisiert Benutzer-Daten (nur für Admins)."""
    # Prüfe Rolle
    if user_data.role and user_data.role not in ["normal", "admin"]:
        raise HTTPException(status_code=400, detail="Ungültige Rolle. Erlaubt: 'normal', 'admin'")
    
    success = update_user(user_id, **user_data.dict(exclude_unset=True))
    
    if not success:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    
    logger.info(f"Benutzer aktualisiert: ID {user_id} von {session['username']}")
    return JSONResponse({"success": True})


@router.post("/api/users/{user_id}/password")
async def change_user_password(user_id: int, password_data: PasswordChange, session: dict = Depends(require_admin)):
    """Ändert Passwort eines Benutzers (nur für Admins)."""
    # Wenn old_password gesetzt ist, prüfe es (für eigene Passwort-Änderung)
    if password_data.old_password:
        user = get_user_by_username(session["username"])
        if not user or not verify_password(password_data.old_password, user["password_hash"]):
            raise HTTPException(status_code=401, detail="Altes Passwort falsch")
    
    success = change_password(user_id, password_data.new_password)
    
    if not success:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    
    logger.info(f"Passwort geändert für Benutzer ID {user_id} von {session['username']}")
    return JSONResponse({"success": True})


@router.delete("/api/users/{user_id}")
async def delete_user_account(user_id: int, session: dict = Depends(require_admin)):
    """Deaktiviert Benutzer (soft delete, nur für Admins)."""
    # Verhindere Selbst-Löschung
    if user_id == session["user_id"]:
        raise HTTPException(status_code=400, detail="Sie können sich nicht selbst löschen")
    
    success = delete_user(user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Benutzer nicht gefunden")
    
    logger.info(f"Benutzer gelöscht: ID {user_id} von {session['username']}")
    return JSONResponse({"success": True})

