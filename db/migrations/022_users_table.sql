-- Migration 022: Benutzer-Tabelle für Authentifizierung
-- Erstellt users Tabelle mit Rollen-System (Normal, Admin)
-- Datum: 2025-11-22

-- Benutzer-Tabelle
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'normal' CHECK(role IN ('normal', 'admin')),
    email TEXT,
    full_name TEXT,
    active INTEGER DEFAULT 1 CHECK(active IN (0, 1)),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    created_by TEXT,
    notes TEXT
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_active ON users(active);
CREATE INDEX IF NOT EXISTS idx_users_last_login ON users(last_login);

-- Session-Tabelle (für persistente Sessions)
CREATE TABLE IF NOT EXISTS user_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL UNIQUE,
    user_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    ip_address TEXT,
    user_agent TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Indizes für Sessions
CREATE INDEX IF NOT EXISTS idx_sessions_session_id ON user_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON user_sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_expires_at ON user_sessions(expires_at);

-- Audit-Log für Benutzer-Änderungen
CREATE TABLE IF NOT EXISTS user_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    action TEXT NOT NULL, -- 'created', 'updated', 'deleted', 'login', 'logout', 'password_changed'
    changed_by INTEGER, -- User-ID des Ändernden
    old_values TEXT, -- JSON
    new_values TEXT, -- JSON
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
    FOREIGN KEY (changed_by) REFERENCES users(id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_user_audit_user_id ON user_audit_log(user_id);
CREATE INDEX IF NOT EXISTS idx_user_audit_created_at ON user_audit_log(created_at DESC);

-- Kommentar: 
-- - Passwörter werden mit bcrypt gehasht (60 Zeichen)
-- - Rollen: 'normal' (Standard-Benutzer), 'admin' (Administrator)
-- - Sessions werden in DB gespeichert (statt Memory)
-- - Audit-Log protokolliert alle Änderungen

