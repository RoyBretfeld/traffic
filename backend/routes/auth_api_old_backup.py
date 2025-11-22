"""
Authentifizierung für Admin-Bereich.
Einfaches Session-basiertes Login-System.
"""
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
import secrets
import hashlib
import os
from datetime import datetime, timedelta
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# Session-Speicher (in Produktion: Redis oder DB)
_sessions: Dict[str, Dict] = {}

# Admin-Credentials (in Produktion: aus DB oder Config laden)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Bretfeld")
# Passwort-Hash für "Lisa01Bessy02" (SHA-256)
ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH",
    "9ffe125c5ece0e922d3cda3184ed75ebf3bb66342487d23b51f614fefdc27cb0"  # "Lisa01Bessy02"
)

# Session-Dauer (Standard: 24 Stunden)
SESSION_DURATION_HOURS = int(os.getenv("ADMIN_SESSION_DURATION_HOURS", "24"))


class LoginRequest(BaseModel):
    username: str
    password: str


class SessionInfo(BaseModel):
    session_id: str
    expires_at: str
    created_at: str


def hash_password(password: str) -> str:
    """Erstellt SHA-256 Hash eines Passworts."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Prüft ob Passwort mit Hash übereinstimmt."""
    return hash_password(password) == password_hash


def create_session() -> str:
    """Erstellt eine neue Session und gibt Session-ID zurück."""
    session_id = secrets.token_urlsafe(32)
    expires_at = datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)
    
    _sessions[session_id] = {
        "created_at": datetime.now().isoformat(),
        "expires_at": expires_at.isoformat(),
        "authenticated": True
    }
    
    # Bereinige abgelaufene Sessions (einfache Bereinigung)
    cleanup_expired_sessions()
    
    return session_id


def cleanup_expired_sessions():
    """Entfernt abgelaufene Sessions."""
    now = datetime.now()
    expired = [
        sid for sid, session in _sessions.items()
        if datetime.fromisoformat(session["expires_at"]) < now
    ]
    for sid in expired:
        del _sessions[sid]


def is_session_valid(session_id: Optional[str]) -> bool:
    """Prüft ob Session gültig ist."""
    if not session_id:
        return False
    
    cleanup_expired_sessions()
    
    if session_id not in _sessions:
        return False
    
    session = _sessions[session_id]
    expires_at = datetime.fromisoformat(session["expires_at"])
    
    if expires_at < datetime.now():
        del _sessions[session_id]
        return False
    
    return session.get("authenticated", False)


def get_session_from_request(request: Request) -> Optional[str]:
    """Holt Session-ID aus Request (Cookie oder Header)."""
    # 1. Versuche Cookie
    session_id = request.cookies.get("admin_session")
    if session_id and is_session_valid(session_id):
        return session_id
    
    # 2. Versuche Authorization Header
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        session_id = auth_header.replace("Bearer ", "")
        if is_session_valid(session_id):
            return session_id
    
    return None


async def require_admin_auth(request: Request) -> str:
    """
    Dependency: Prüft ob Request authentifiziert ist.
    Wirft HTTPException 401 wenn nicht authentifiziert.
    """
    session_id = get_session_from_request(request)
    
    if not session_id or not is_session_valid(session_id):
        raise HTTPException(
            status_code=401,
            detail="Nicht authentifiziert. Bitte einloggen.",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return session_id


@router.post("/api/auth/login")
async def login(login_req: LoginRequest, request: Request):
    """
    Login-Endpoint für Admin-Bereich.
    
    Prüft Benutzername und Passwort und erstellt Session.
    """
    # Prüfe Benutzername
    if login_req.username != ADMIN_USERNAME:
        logger.warning(f"Fehlgeschlagener Login-Versuch (falscher Benutzername) von {request.client.host}")
        raise HTTPException(status_code=401, detail="Ungültiger Benutzername oder Passwort")
    
    # Prüfe Passwort
    if not verify_password(login_req.password, ADMIN_PASSWORD_HASH):
        logger.warning(f"Fehlgeschlagener Login-Versuch (falsches Passwort) von {request.client.host}")
        raise HTTPException(status_code=401, detail="Ungültiger Benutzername oder Passwort")
    
    # Erstelle Session
    session_id = create_session()
    logger.info(f"Admin-Login erfolgreich von {request.client.host}")
    
    # Response mit Session-Cookie
    response = JSONResponse({
        "success": True,
        "session_id": session_id,
        "expires_at": _sessions[session_id]["expires_at"]
    })
    
    # Setze Cookie (HttpOnly, Secure in Produktion)
    response.set_cookie(
        key="admin_session",
        value=session_id,
        max_age=SESSION_DURATION_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=False  # In Produktion mit HTTPS auf True setzen
    )
    
    return response


@router.post("/api/auth/logout")
async def logout(request: Request):
    """Logout-Endpoint: Löscht Session."""
    session_id = get_session_from_request(request)
    
    if session_id and session_id in _sessions:
        del _sessions[session_id]
        logger.info(f"Admin-Logout von {request.client.host}")
    
    response = JSONResponse({"success": True, "message": "Erfolgreich ausgeloggt"})
    response.delete_cookie(key="admin_session")
    return response


@router.get("/api/auth/status")
async def auth_status(request: Request):
    """Prüft ob Session gültig ist."""
    session_id = get_session_from_request(request)
    
    if session_id and is_session_valid(session_id):
        session = _sessions[session_id]
        return JSONResponse({
            "authenticated": True,
            "expires_at": session["expires_at"],
            "created_at": session["created_at"]
        })
    
    return JSONResponse({"authenticated": False})


@router.get("/api/auth/check")
async def check_auth(request: Request, session_id: str = Depends(require_admin_auth)):
    """
    Protected Endpoint: Prüft ob Request authentifiziert ist.
    Kann als Dependency verwendet werden.
    """
    return JSONResponse({
        "authenticated": True,
        "session_id": session_id
    })

