# Security TODO – TrafficApp 3.0

**Stand:** 2025-11-22  
**Status:** In Bearbeitung

---

## ✅ Bereits umgesetzt (2025-11-22)

- [x] **SC-03:** Cookies gehärtet (SameSite=Strict, Secure in Prod)
- [x] **SC-04:** Rate-Limiting für Login (10 Versuche / 15 Minuten)
- [x] **SC-06:** CORS gehärtet (Production: Whitelist, Development: `*`)
- [x] **SC-02:** bcrypt für Passwort-Hashing (aus Benutzerverwaltung)
- [x] **Benutzerverwaltung:** Datenbank-basiert mit Rollen

---

## 🔴 Phase A – Sofort (Ship-Now)

### 1. Admin-Router absichern

**Status:** ⚠️ **ZU PRÜFEN**

**Aufgabe:**
- Alle Admin-Router prüfen
- `Depends(require_admin)` hinzufügen wo fehlt

**Zu prüfende Router:**
- [ ] `/api/import/*` - Upload/Import-Routen
- [ ] `/api/db/*` - Datenbank-Viewer
- [ ] `/api/tests/*` - Test-Dashboard
- [ ] `/api/code-checker/*` - Code-Checker
- [ ] `/api/cost-tracker/*` - Kosten-Tracker
- [ ] `/api/system/rules` - Systemregeln
- [ ] `/api/backup/*` - Backup-Routen
- [ ] `/api/engine/*` - Engine-API
- [ ] Weitere Admin-Routen...

**Dateien:**
- `backend/routes/*.py` - Alle Router prüfen
- `backend/app_setup.py` - Router-Registrierung prüfen

---

### 2. Debug/Test-Routen absichern

**Status:** ⚠️ **ZU PRÜFEN**

**Aufgabe:**
- Debug-Routen nur mit `ENABLE_DEBUG_ROUTES=1` aktivieren
- Zusätzlich Admin-Auth erforderlich

**Zu prüfende Router:**
- [ ] `/api/tests/*` - Test-Dashboard
- [ ] `/api/code-checker/*` - Code-Checker
- [ ] `/api/debug/*` - Debug-Routen
- [ ] `/api/ai-test/*` - AI-Test-Routen

**Beispiel:**
```python
if os.getenv("ENABLE_DEBUG_ROUTES") == "1":
    app.include_router(
        test_dashboard_router,
        dependencies=[Depends(require_admin)]
    )
```

---

### 3. Upload-Sicherheit implementieren

**Status:** ⚠️ **NOCH OFFEN**

**Aufgabe:**
- Filename-Whitelist (nur erlaubte Zeichen)
- Pfad-Check mit `resolve()` (Path Traversal verhindern)
- Größen-Limits
- MIME-Type-Prüfung

**Dateien:**
- `backend/routes/upload_csv.py` - CSV-Upload
- `backend/routes/tourplan_*.py` - Tourplan-Uploads
- Weitere Upload-Routen...

**Code-Beispiel:**
```python
import re
from pathlib import Path

SAFE_FILENAME = re.compile(r"^[A-Za-z0-9_.\-]+$")

def validate_upload(filename: str, upload_dir: Path):
    # Filename-Whitelist
    if not SAFE_FILENAME.match(filename):
        raise HTTPException(400, "Ungültiger Dateiname")
    
    # Pfad-Check
    file_path = (upload_dir / filename).resolve()
    if not str(file_path).startswith(str(upload_dir.resolve())):
        raise HTTPException(400, "Pfad außerhalb erlaubt")
    
    # Größen-Limit (z.B. 10MB)
    MAX_SIZE = 10 * 1024 * 1024
    if file_path.stat().st_size > MAX_SIZE:
        raise HTTPException(400, "Datei zu groß")
    
    return file_path
```

---

## 🟡 Phase B – Woche 1

### 4. Security-Header implementieren

**Status:** ⚠️ **NOCH OFFEN**

**Aufgabe:**
- Middleware für Security-Header erstellen
- CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy

**Datei:** `backend/middlewares/security_headers.py`

**Code-Beispiel:**
```python
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        # CSP für Admin-UI
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:;"
        )
        return response
```

---

### 5. Requirements pinnen + CI Audit

**Status:** ⚠️ **ZU PRÜFEN**

**Aufgabe:**
- `requirements.txt` prüfen
- Exakte Versionen pinnen (kein `>=`)
- CI mit `pip-audit` erweitern

**Dateien:**
- `requirements.txt`
- `.github/workflows/ci.yml`

**CI-Erweiterung:**
```yaml
- name: Security Audit
  run: |
    pip install pip-audit
    pip-audit --requirement requirements.txt
```

---

### 6. Logging & PII

**Status:** ⚠️ **ZU PRÜFEN**

**Aufgabe:**
- Log-Level in Production auf INFO
- PII-Anonymisierung (Adressen, Namen)
- Retention-Policy dokumentieren

**Dateien:**
- `logging_setup.py`
- `backend/utils/enhanced_logging.py`

---

### 7. SQLite-Rechte & Backups

**Status:** ⚠️ **ZU PRÜFEN**

**Aufgabe:**
- SQLite-Datei-Rechte prüfen
- Backup-Strategie dokumentieren
- Restore-Playbook testen

---

## 🟢 Phase C – Woche 2+

### 8. CSRF-Schutz

**Status:** ⚠️ **NOCH OFFEN**

**Aufgabe:**
- CSRF-Token bei Cookie-Auth
- Oder Wechsel auf Bearer-Token

---

### 9. Rate-Limits für Heavy-Endpoints

**Status:** ⚠️ **TEILWEISE** (Login vorhanden)

**Aufgabe:**
- Rate-Limits für Import/Geocoding/Batch-Operationen
- Parallele Jobs begrenzen

---

### 10. Secrets-Management

**Status:** ⚠️ **ZU PRÜFEN**

**Aufgabe:**
- `MASTER_PASSWORD` prüfen (kein Default in Prod)
- `.env`/`secure_keys.json` in `.gitignore`
- Secrets nur aus ENV/Secret-Store

---

## 📊 Fortschritt

**Phase A:** 2/5 umgesetzt (40%)  
**Phase B:** 0/4 umgesetzt (0%)  
**Phase C:** 0/3 umgesetzt (0%)

**Gesamt:** 5/12 Punkte (42%)

---

## Nächste Aktion

1. **Admin-Router prüfen** (Phase A, Punkt 1)
2. **Upload-Sicherheit implementieren** (Phase A, Punkt 3)
3. **Security-Header implementieren** (Phase B, Punkt 4)

---

**Siehe auch:**
- `docs/SECURITY_CODE_REVIEW_2025-11-22.md` - Vollständiges Review
- `docs/SECURITY_GUIDE_2025-11-22.md` - Security Guide
- `docs/SECURITY_CHECKLIST.md` - Checkliste

