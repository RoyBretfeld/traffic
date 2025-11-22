# TrafficApp 3.0 – Security Code Review (2025‑11‑22)

## Zusammenfassung

Solide Architektur und umfangreiche Doku, aber mehrere sicherheitsrelevante Defaults/Öffnungen müssen vor Produktion geschlossen werden. Dieses Review priorisiert Fixes, liefert Code‑Snippets und eine PR‑Checkliste.

---

## Stärken

* Klare Modultrennung (routes/services/repositories), sinnvolle Logs/Tracing.

* CSV‑Staging, Fehlerbehandlung, erste Tests vorhanden.

* Statistik/Kosten‑Fundament vorbereitet.

---

## Kritische Punkte & Maßnahmen

### 1) CORS zu offen

**Ist:** `allow_origins=["*"]` + `allow_credentials=True`.

**Risiko:** Cross‑Site Requests mit Cookies; Browser‑Inkompatibilitäten.

**Fix (Prod):**

```python
app.add_middleware(CORSMiddleware,
  allow_origins=["https://trafficapp.example.com"],
  allow_credentials=True,
  allow_methods=["GET","POST","PUT","DELETE"],
  allow_headers=["Authorization","Content-Type"],
)
```

**Status:** ✅ **TEILWEISE UMGESETZT** (2025-11-22)
- Development: `["*"]` (für lokale Entwicklung)
- Production: Whitelist über `CORS_ALLOWED_ORIGINS` ENV
- Siehe: `backend/app_setup.py`

---

### 2) Admin‑APIs ohne zwingende Auth

**Ist:** sensible Router eingebunden (Import/DB/Tests/Code‑Tools), teils ohne Guard.

**Fix:** Router/Endpoints mit Dependency absichern:

```python
from fastapi import APIRouter, Depends
from backend.routes.auth_api import require_admin_auth

router = APIRouter(prefix="/api/import", tags=["import"],
                   dependencies=[Depends(require_admin_auth)])
```

**Status:** ⚠️ **ZU PRÜFEN**
- `require_admin` existiert in `backend/routes/auth_api.py`
- Alle Admin-Router müssen geprüft werden

---

### 3) Login/Session‑Härtung

**Ist:** statische Admin‑Creds (Test), SHA‑256 Hash, Cookie `secure=False`.

**Fix:** argon2/bcrypt, keine Defaults, Secure Cookies (Prod), Rate‑Limit.

```python
from passlib.hash import argon2
hashed = argon2.hash(password)
argon2.verify(password, hashed)

secure_cookie = os.getenv("APP_ENV") == "production"
response.set_cookie("admin_session", session_id,
  httponly=True, secure=secure_cookie, samesite="strict", max_age=28800)
```

**Status:** ✅ **UMGESETZT** (2025-11-22)
- ✅ bcrypt bereits implementiert (aus Benutzerverwaltung)
- ✅ Secure Cookie in Production
- ✅ SameSite=Strict
- ✅ Rate-Limiting aktiv (10 Versuche / 15 Minuten)
- ⚠️ argon2 noch nicht implementiert (bcrypt ist ausreichend)

---

### 4) Debug/Tests in Prod

**Ist:** `/api/tests`, Code‑Checker, Pytest‑Runner eingebunden.

**Fix:** Nur via Flag + Admin, in Prod aus.

```python
if os.getenv("ENABLE_DEBUG_ROUTES") == "1":
    app.include_router(test_dashboard_router,
        dependencies=[Depends(require_admin_auth)])
```

**Status:** ⚠️ **ZU PRÜFEN**
- `ENABLE_DEBUG_ROUTES` Flag existiert
- Debug-Router müssen geprüft werden

---

### 5) Upload/Path‑Traversal

**Ist:** Dateiname aus Request, keine harte Whitelist/`resolve()`‑Prüfung.

**Fix:**

```python
SAFE = re.compile(r"^[A-Za-z0-9_.\-]+$")
if not SAFE.match(filename):
    raise HTTPException(400, "Ungültiger Dateiname")

csv_path = (TOURPLAENE_DIR / filename).resolve()
if not str(csv_path).startswith(str(TOURPLAENE_DIR.resolve())):
    raise HTTPException(400, "Pfad außerhalb erlaubt")
```

* Größen‑/MIME‑Limits.

**Status:** ⚠️ **NOCH OFFEN**
- Upload-Routen müssen geprüft werden
- Filename-Whitelist implementieren
- Pfad-Check implementieren

---

### 6) Secrets & Key‑Management

**Ist:** MASTER_PASSWORD mit Default; `secure_keys.json` im Config‑Pfad.

**Fix:** Kein produktiver Default → App‑Start abbrechen, Secrets nie ins Repo, `.env`/`secure_keys.json` in `.gitignore`.

**Status:** ⚠️ **ZU PRÜFEN**
- `MASTER_PASSWORD` prüfen
- `.gitignore` prüfen
- `secure_keys.json` prüfen

---

### 7) Security‑Header & SRI

**Ist:** nicht gesetzt.

**Fix (Reverse Proxy/App):** CSP (whitelist), HSTS, X‑Frame‑Options, X‑Content‑Type‑Options, Referrer‑Policy. CDN‑Assets mit `integrity` oder lokal hosten.

**Status:** ⚠️ **NOCH OFFEN**
- Security-Header-Middleware implementieren

---

### 8) Logging & PII

**Ist:** sehr detailliert (Adressen/Fehler); gut für Dev, zu viel für Prod.

**Fix:** Prod‑Log auf INFO, PII kürzen/anonymisieren, Retention definieren.

**Status:** ⚠️ **ZU PRÜFEN**
- Log-Level in Production prüfen
- PII-Anonymisierung prüfen

---

### 9) Dependencies pinnen & auditieren

**Ist:** „>=“ Versionen.

**Fix:** exakte Pins, CI mit `pip-audit`/`safety`.

**Status:** ⚠️ **NOCH OFFEN**
- `requirements.txt` prüfen
- CI mit `pip-audit` erweitern

---

### 10) DB‑Zugriffe

**Ist:** teils `text()` – ok wenn parametrisiert.

**Fix:** überall Parameterbindung, SQLite‑Dateirechte einschränken, Restore testen.

**Status:** ⚠️ **ZU PRÜFEN**
- SQL-Queries prüfen
- Parameterbindung prüfen

---

## Priorisierte Umsetzung

### Phase A – Sofort (Ship‑Now)

* ✅ CORS auf Prod‑Domains begrenzen. **UMGESETZT**
* ✅ Login härten (argon2/bcrypt, Secure+Strict Cookies, Rate‑Limit). **UMGESETZT**
* ⚠️ Alle Admin‑Router mit `Depends(require_admin_auth)`. **ZU PRÜFEN**
* ⚠️ Debug/Tests nur via Flag + Admin. **ZU PRÜFEN**
* ⚠️ Upload‑Whitelist + `resolve()`‑Guard + Größenlimit. **NOCH OFFEN**

### Phase B – Woche 1

* ⚠️ Security‑Header/CSP/HSTS; SRI oder Self‑Host Assets. **NOCH OFFEN**
* ⚠️ Log‑Policy (PII/Retention) und Requirements pinnen + CI Audit. **ZU PRÜFEN**
* ⚠️ Admin‑Navigation konsolidieren (eine Seite/Tabs, konsistent). **TEILWEISE** (admin.html mit Tabs)
* ⚠️ Minimal‑RBAC (Admin/Dispo/ReadOnly) für Tabs & APIs. **TEILWEISE** (Rollen existieren, RBAC noch nicht vollständig)

### Phase C – Woche 2+

* ⚠️ CSRF bei Cookie‑Auth oder Bearer‑Token. **NOCH OFFEN**
* ⚠️ DoS/Rate‑Limits auf Import/Geocoding/Heavy‑Endpoints. **TEILWEISE** (Login-Rate-Limit vorhanden)
* ⚠️ Secrets nur via ENV/Secret‑Store. **ZU PRÜFEN**

---

## PR‑Checkliste (kopierfertig)

* [x] CORS auf feste Origins; keine `*` + Credentials **TEILWEISE** (Development: `*`, Production: Whitelist)
* [ ] `require_admin_auth` auf allen Admin‑Routern/Endpoints **ZU PRÜFEN**
* [x] Passwörter: argon2/bcrypt; keine Default‑Creds **UMGESETZT** (bcrypt)
* [x] Cookies: HttpOnly, Secure (Prod), SameSite=Strict **UMGESETZT**
* [x] Login‑Rate‑Limit implementiert **UMGESETZT**
* [ ] Debug/Test/Code‑Tools nur via Flag + Admin **ZU PRÜFEN**
* [ ] Upload‑Whitelist, `resolve()`‑Check, Size/MIME‑Limits **NOCH OFFEN**
* [ ] Security‑Header (CSP/HSTS/XFO/XCTO/Referrer) **NOCH OFFEN**
* [ ] Logs ohne PII/Secrets; Retention dokumentiert **ZU PRÜFEN**
* [ ] Requirements gepinnt; CI `pip-audit`/`safety` **ZU PRÜFEN**
* [ ] SQLite‑Rechte/Backups/Restore geprüft **ZU PRÜFEN**
* [ ] RBAC‑Rollen vorbereitet; Tabs & APIs rollenbasiert **TEILWEISE** (Rollen existieren)
* [ ] (Optional) CSRF oder Bearer‑Token; Rate‑Limits für Heavy‑Endpoints **NOCH OFFEN**

---

## Hinweise zur aktuellen Benutzerverwaltung

* ✅ Statischer Admin ist für Tests ok, aber **nicht** für Prod. **UMGESETZT** (Datenbank-basierte Benutzerverwaltung implementiert)
* ✅ Migration zu echter Benutzerverwaltung: `users`, `roles`, `user_roles`; Session/JWT mit `role` → Tabs & APIs per Rolle begrenzen. **UMGESETZT** (users, sessions, audit_log Tabellen existieren)

---

## Appendix: Beispiel‑Snippets

**Rate‑Limit (einfach, pro IP, Login)**

```python
from collections import defaultdict
from time import time

WINDOW, LIMIT = 900, 8
_attempts = defaultdict(list)

def allow(ip: str) -> bool:
    now = time()
    q = _attempts[ip] = [t for t in _attempts[ip] if now - t < WINDOW]
    if len(q) >= LIMIT: return False
    q.append(now); return True
```

**Status:** ✅ **IMPLEMENTIERT** (siehe `backend/middlewares/rate_limit.py`)

---

**Security‑Headers (FastAPI Middleware minimal)**

```python
@app.middleware("http")
async def security_headers(request, call_next):
    resp = await call_next(request)
    resp.headers.setdefault("X-Frame-Options", "DENY")
    resp.headers.setdefault("X-Content-Type-Options", "nosniff")
    resp.headers.setdefault("Referrer-Policy", "no-referrer")
    return resp
```

**Status:** ⚠️ **NOCH OFFEN** (muss implementiert werden)

---

**CSRF‑Token (Session‑basiert, Konzept)**

* Beim Login CSRF‑Token generieren und als non‑HttpOnly Cookie setzen.

* Frontend sendet Token in `X-CSRF-Token` Header.

* Backend vergleicht Header mit Session‑Token.

**Status:** ⚠️ **NOCH OFFEN** (Phase C)

---

## Nächste Schritte

1. **Sofort:** Admin-Router prüfen und absichern
2. **Sofort:** Upload-Sicherheit implementieren
3. **Woche 1:** Security-Header implementieren
4. **Woche 1:** Requirements pinnen + CI Audit
5. **Woche 2+:** CSRF oder Bearer-Token

---

**Letzte Aktualisierung:** 2025-11-22  
**Review-Datum:** 2025-11-22

