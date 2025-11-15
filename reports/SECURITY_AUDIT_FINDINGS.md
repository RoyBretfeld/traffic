# 🛡️ SECURITY-AUDIT FINDINGS

**Datum:** 2025-11-13  
**Reviewer:** AI Code-Review (Automated)  
**Umfang:** Gesamte Backend-Codebase

---

## 📊 EXECUTIVE SUMMARY

### Risiko-Übersicht
- 🔴 **CRITICAL:** 1 Finding
- 🟡 **MEDIUM:** 5 Findings
- 🟢 **LOW:** 3 Findings
- ✅ **GOOD:** 12 Best Practices erkannt

### Gesamtbewertung
**RISIKO-SCORE: MEDIUM (6/10)**

Die Anwendung hat **grundlegende Security-Maßnahmen** implementiert, aber es gibt Verbesserungspotenzial in kritischen Bereichen (Passwort-Hashing, Session-Management).

---

## 🔴 CRITICAL FINDINGS

### 1. Schwaches Passwort-Hashing (SHA-256)

**Datei:** `backend/routes/auth_api.py`  
**Zeilen:** 46-53  
**Risiko:** 🔴 CRITICAL  
**CVSS Score:** 7.5 (HIGH)

**Problem:**
```python
def hash_password(password: str) -> str:
    """Erstellt SHA-256 Hash eines Passworts."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()
```

**Warum ist das ein Problem?**
- SHA-256 ist **KEIN geeigneter Password-Hashing-Algorithmus**
- **Keine Salt** → Rainbow-Table-Angriffe möglich
- **Zu schnell** → Brute-Force-Angriffe leicht durchführbar
- **Keine Key-Stretching** → GPU-Cracking effektiv

**Impact:**
- Kompromittierte Passwörter bei Datenbank-Leak
- Admin-Account angreifbar
- Compliance-Probleme (GDPR, OWASP)

**Empfohlene Lösung:**
```python
import bcrypt

def hash_password(password: str) -> str:
    """Erstellt bcrypt Hash eines Passworts."""
    salt = bcrypt.gensalt(rounds=12)  # 12 rounds = guter Balance
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, password_hash: str) -> bool:
    """Prüft ob Passwort mit Hash übereinstimmt."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
```

**Alternative:** `passlib` mit `argon2` (noch sicherer, OWASP-empfohlen):
```python
from passlib.hash import argon2

def hash_password(password: str) -> str:
    return argon2.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return argon2.verify(password, password_hash)
```

**Aufwand:** 2-3 Stunden (inkl. Migration existierender Hashes)  
**Priorität:** 🔴 HOCH (sofort beheben!)

---

## 🟡 MEDIUM FINDINGS

### 2. Session-Storage in Memory (nicht persistent)

**Datei:** `backend/routes/auth_api.py`  
**Zeile:** 21  
**Risiko:** 🟡 MEDIUM

**Problem:**
```python
_sessions: Dict[str, Dict] = {}  # In-Memory-Storage
```

**Warum ist das ein Problem?**
- Sessions gehen verloren bei Server-Neustart
- Nicht skalierbar (keine Multi-Instance-Support)
- Keine Session-Persistenz über Deployments hinweg

**Impact:**
- Alle User müssen nach Neustart neu einloggen
- Schlechte User-Experience
- Keine Horizontal-Scaling möglich

**Empfohlene Lösung:**
1. **Redis:** Persistente Session-Storage
2. **Database:** SQLite-Tabelle für Sessions
3. **JWT:** Stateless Tokens (keine Server-Side-Storage)

**Beispiel (Redis):**
```python
import redis
import json

redis_client = redis.Redis(host='localhost', port=6379, db=0)

def create_session() -> str:
    session_id = secrets.token_urlsafe(32)
    session_data = {
        "created_at": datetime.now().isoformat(),
        "expires_at": (datetime.now() + timedelta(hours=SESSION_DURATION_HOURS)).isoformat()
    }
    redis_client.setex(
        f"session:{session_id}",
        SESSION_DURATION_HOURS * 3600,
        json.dumps(session_data)
    )
    return session_id
```

**Aufwand:** 4-6 Stunden  
**Priorität:** 🟡 MITTEL

---

### 3. Secure-Cookie Flag auf False

**Datei:** `backend/routes/auth_api.py`  
**Zeile:** 173  
**Risiko:** 🟡 MEDIUM (in Produktion)

**Problem:**
```python
response.set_cookie(
    key="admin_session",
    value=session_id,
    max_age=SESSION_DURATION_HOURS * 3600,
    httponly=True,
    samesite="lax",
    secure=False  # ⚠️ PROBLEM in Produktion!
)
```

**Warum ist das ein Problem?**
- Cookie wird über **unverschlüsselte HTTP-Verbindungen** gesendet
- **Man-in-the-Middle-Angriffe** möglich
- Session-ID kann abgefangen werden

**Impact:**
- Session-Hijacking bei HTTP-Verbindungen
- Compliance-Probleme (HTTPS-Pflicht für Cookies mit sensiblen Daten)

**Empfohlene Lösung:**
```python
import os

# Automatische Erkennung: Produktion = True, Development = False
IS_PRODUCTION = os.getenv("ENVIRONMENT", "development") == "production"

response.set_cookie(
    key="admin_session",
    value=session_id,
    max_age=SESSION_DURATION_HOURS * 3600,
    httponly=True,
    samesite="lax",
    secure=IS_PRODUCTION  # ✅ Automatisch in Produktion auf True
)
```

**Aufwand:** 30 Minuten  
**Priorität:** 🟡 MITTEL (HOCH in Produktion)

---

### 4. Fehlende Rate-Limiting für Login-Endpoint

**Datei:** `backend/routes/auth_api.py`  
**Zeilen:** 138-176  
**Risiko:** 🟡 MEDIUM

**Problem:**
Kein Rate-Limiting für `/api/auth/login` → Brute-Force-Angriffe möglich

**Impact:**
- Unbegrenzte Login-Versuche
- Passwort-Guessing möglich
- DDoS-Anfälligkeit

**Empfohlene Lösung:**
```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

@router.post("/api/auth/login")
@limiter.limit("5/minute")  # Max 5 Login-Versuche pro Minute
async def login(login_req: LoginRequest, request: Request):
    # ... existing code ...
```

**Alternative:** IP-basiertes Blocking nach 5 Fehlversuchen für 15 Minuten

**Aufwand:** 2-3 Stunden  
**Priorität:** 🟡 MITTEL

---

### 5. Async/Await-Probleme (nest_asyncio-Hack)

**Dateien:** `backend/routes/workflow_api.py` (mehrere Stellen)  
**Zeilen:** 197-208, 1734-1752, 1837-1855  
**Risiko:** 🟡 MEDIUM (Code-Quality & Stability)

**Problem:**
```python
loop = asyncio.get_event_loop()
if loop.is_running():
    import nest_asyncio
    nest_asyncio.apply()  # ⚠️ HACKY!
    result = asyncio.run(geocode_async())
```

**Warum ist das ein Problem?**
- `nest_asyncio` ist ein **Workaround** für schlechtes Async-Design
- Kann zu **Race-Conditions** führen
- **Performance-Impact**
- Schwer zu debuggen

**Impact:**
- Potenzielle Deadlocks
- Unvorhersehbares Verhalten
- Schwierige Fehlersuche

**Empfohlene Lösung:**
```python
# VORHER (synchron mit async-Hack):
result = asyncio.run(geocode_async())

# NACHHER (korrekt async):
async def geocode(self, stop):
    result = await geocode_async()
    return result
```

**Oder:** Synchrone Funktion in Thread auslagern:
```python
import asyncio

async def geocode_in_thread(address):
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, sync_geocode_function, address)
    return result
```

**Aufwand:** 6-8 Stunden (Refactoring erforderlich)  
**Priorität:** 🟡 MITTEL

---

### 6. File-Upload ohne MIME-Type-Validierung

**Datei:** `backend/routes/upload_csv.py`  
**Zeilen:** 221-222  
**Risiko:** 🟡 LOW-MEDIUM

**Problem:**
```python
if not file.filename.lower().endswith('.csv'):
    raise HTTPException(400, detail="only .csv allowed")
```

**Warum ist das ein Problem?**
- **Nur Dateiendung wird geprüft** (leicht umgehbar)
- Keine MIME-Type-Validierung
- Keine Content-Validierung

**Impact:**
- Potenzielle Upload von schädlichen Dateien (getarnt als CSV)
- File-System-Missbrauch

**Empfohlene Lösung:**
```python
import magic  # python-magic

# 1. Dateiendung prüfen
if not file.filename.lower().endswith('.csv'):
    raise HTTPException(400, detail="only .csv allowed")

# 2. MIME-Type prüfen
content = await file.read()
mime_type = magic.from_buffer(content, mime=True)
if mime_type not in ['text/csv', 'text/plain', 'application/csv']:
    raise HTTPException(400, detail=f"Invalid file type: {mime_type}")

# 3. CSV-Struktur validieren
try:
    decoded = content.decode('utf-8')
    csv.reader(io.StringIO(decoded))  # Test ob valides CSV
except Exception:
    raise HTTPException(400, detail="Invalid CSV format")
```

**Aufwand:** 2-3 Stunden  
**Priorität:** 🟡 NIEDRIG-MITTEL

---

## 🟢 LOW FINDINGS

### 7. Hardcoded Admin-Credentials in Code

**Datei:** `backend/routes/auth_api.py`  
**Zeilen:** 24-29  
**Risiko:** 🟢 LOW (wenn Env-Vars genutzt werden)

**Problem:**
```python
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "Bretfeld")  # Hardcoded Fallback
ADMIN_PASSWORD_HASH = os.getenv(
    "ADMIN_PASSWORD_HASH",
    "9ffe125c5ece0e922d3cda3184ed75ebf3bb66342487d23b51f614fefdc27cb0"  # Hardcoded Hash
)
```

**Warum ist das ein (kleines) Problem?**
- Fallback-Credentials könnten in Git-History landen
- Default-Credentials sind bekannt (wenn im Repo)

**Impact:**
- Niedrig, wenn Env-Vars in Produktion gesetzt sind
- Mittel, wenn Defaults genutzt werden

**Empfohlene Lösung:**
```python
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH")

if not ADMIN_USERNAME or not ADMIN_PASSWORD_HASH:
    raise RuntimeError(
        "ADMIN_USERNAME and ADMIN_PASSWORD_HASH must be set in environment variables!"
    )
```

**Aufwand:** 30 Minuten  
**Priorität:** 🟢 NIEDRIG

---

### 8. Fehlende CSRF-Protection

**Risiko:** 🟢 LOW (dank SameSite=Lax)

**Problem:**
Keine explizite CSRF-Token-Validierung

**Impact:**
- **Niedrig**, weil `samesite="lax"` Cookie-Flag gesetzt ist
- Schützt gegen die meisten CSRF-Angriffe
- Aber nicht 100% sicher (z.B. bei GET-Requests mit State-Changes)

**Empfohlene Lösung (Optional):**
```python
from fastapi_csrf_protect import CsrfProtect

@router.post("/api/auth/login")
async def login(login_req: LoginRequest, request: Request, csrf_protect: CsrfProtect = Depends()):
    await csrf_protect.validate_csrf(request)
    # ... existing code ...
```

**Aufwand:** 3-4 Stunden  
**Priorität:** 🟢 NIEDRIG (Nice-to-have)

---

### 9. Logging von IP-Adressen (GDPR-Konformität)

**Datei:** `backend/routes/auth_api.py`  
**Zeilen:** 147, 152, 157  
**Risiko:** 🟢 LOW (GDPR-Compliance)

**Problem:**
```python
logger.warning(f"Fehlgeschlagener Login-Versuch von {request.client.host}")
```

**Warum ist das ein Problem?**
- IP-Adressen sind **personenbezogene Daten** (GDPR)
- Logging ohne Consent könnte problematisch sein
- Keine Anonymisierung/Pseudonymisierung

**Impact:**
- Potenzielle GDPR-Verstöße
- Abhängig von Jurisdiktion

**Empfohlene Lösung:**
```python
import hashlib

def anonymize_ip(ip: str) -> str:
    """Anonymisiert IP-Adresse (nur erste 3 Bytes für IPv4, erste 6 Bytes für IPv6)"""
    parts = ip.split('.')
    if len(parts) == 4:  # IPv4
        return f"{parts[0]}.{parts[1]}.{parts[2]}.xxx"
    else:  # IPv6
        return ip[:19] + "::xxxx"  # Vereinfachte IPv6-Anonymisierung

logger.warning(f"Fehlgeschlagener Login-Versuch von {anonymize_ip(request.client.host)}")
```

**Aufwand:** 1-2 Stunden  
**Priorität:** 🟢 NIEDRIG (abhängig von rechtlichen Anforderungen)

---

## ✅ GOOD PRACTICES ERKANNT

### Security-Maßnahmen die GUT implementiert sind:

1. **✅ Parameterisierte SQL-Queries**
   - Alle SQL-Queries nutzen `text()` mit Bind-Parameters
   - **Kein SQL Injection Risk!**

2. **✅ HttpOnly-Cookie für Sessions**
   - `httponly=True` verhindert JavaScript-Zugriff auf Session-Cookie
   - Schützt gegen XSS-Cookie-Theft

3. **✅ SameSite=Lax Cookie-Flag**
   - Schützt gegen die meisten CSRF-Angriffe
   - Guter Balance zwischen Security und Usability

4. **✅ Session-Expiry implementiert**
   - Sessions haben definierte Lebensdauer (24h Standard)
   - Cleanup-Mechanismus vorhanden

5. **✅ Path-Traversal-Prevention**
   - File-Uploads nutzen `path.resolve()` für Normalisierung
   - SAFE regex für Dateinamen-Sanitization

6. **✅ File-Size-Limits**
   - Max Upload-Size definiert (MAX_BYTES)
   - Verhindert DoS durch große Uploads

7. **✅ Error-Handling ohne Information-Leakage**
   - Generic Error-Messages für User
   - Details nur in Logs

8. **✅ Input-Validation mit Pydantic**
   - Alle API-Requests werden via Pydantic validiert
   - Type-Safety und Validation

9. **✅ Secrets mit cryptographic-strong Generator**
   - `secrets.token_urlsafe()` für Session-IDs
   - Kein `random()` (schwach)

10. **✅ Timeout-Configuration für externe Services**
    - OSRM, Geocoding, etc. haben Timeouts
    - Verhindert Hanging-Requests

11. **✅ Circuit-Breaker für OSRM**
    - Schützt gegen Service-Overload
    - Graceful Degradation

12. **✅ Logging mit Structured Data**
    - Trace-IDs für Request-Tracing
    - Gute Audit-Trail-Basis

---

## 📋 EMPFEHLUNGEN (PRIORISIERT)

### Sofort (Diese Woche)
1. 🔴 **Passwort-Hashing auf bcrypt/argon2 umstellen**
2. 🟡 **Rate-Limiting für Login-Endpoint**
3. 🟡 **Secure-Cookie Flag environment-basiert**

### Kurzfristig (Nächste 2 Wochen)
4. 🟡 **Session-Storage auf Redis/DB umstellen**
5. 🟡 **MIME-Type-Validierung für File-Uploads**
6. 🟢 **Hardcoded Fallbacks entfernen**

### Mittelfristig (Nächster Monat)
7. 🟡 **Async/Await-Refactoring** (nest_asyncio entfernen)
8. 🟢 **CSRF-Protection hinzufügen**
9. 🟢 **IP-Anonymisierung für Logs**

---

## 🔍 ZUSÄTZLICHE CHECKS EMPFOHLEN

1. **Dependency-Scanning:** `pip-audit` oder `safety` für bekannte CVEs
2. **SAST-Tools:** Bandit, Semgrep für automatische Security-Scans
3. **Penetration-Testing:** Manuelle Security-Tests
4. **Secrets-Scanning:** Prüfung ob Secrets in Git-History

---

## 📊 ZUSAMMENFASSUNG

### Risiko-Matrix

| Kategorie | Count | Priorität |
|-----------|-------|-----------|
| Critical | 1 | Sofort |
| Medium | 5 | 2-4 Wochen |
| Low | 3 | Optional |

### Geschätzter Aufwand für alle Fixes
- **Sofort-Maßnahmen:** 4-6 Stunden
- **Kurzfristig:** 10-15 Stunden
- **Mittelfristig:** 10-15 Stunden
- **Gesamt:** 24-36 Stunden

### ROI-Bewertung
**HOCH:** Die kritischen Fixes (Passwort-Hashing, Rate-Limiting) haben hohen Security-Impact bei vergleichsweise niedrigem Aufwand.

---

**Erstellt:** 2025-11-13  
**Review-Status:** Abgeschlossen  
**Nächster Review:** Nach Implementierung der Fixes

