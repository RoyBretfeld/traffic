# TrafficApp 3.0 – SECURITY GUIDE (Stand 2025‑11‑22)

> **Status-Hinweis:** Benutzerverwaltung ist „in Arbeit". Für Tests existiert aktuell ein statischer Admin. Dieses Dokument definiert Sofortmaßnahmen und Zielzustand, damit die Umstellung auf echte User/Rollen reibungslos gelingt.

---

## 1) Quick Wins – Sofort umsetzen

* **Admin-Auth härtet**: Defaults raus, Passwort-Hash → `argon2`/`bcrypt`, `secure` Cookie an Prod, Rate-Limits.

* **Admin-APIs schützen**: überall `Depends(require_admin_auth)` auf kritischen Routen.

* **CORS hart konfigurieren**: keine `*` mit Credentials; nur erlaubte Domains.

* **Uploads absichern**: Filename-Whitelist + `resolve()`-Pfad-Check; keine fremden Pfade.

* **Secrets richtig**: `MASTER_PASSWORD` ohne brauchbaren Default; `.env`/`secure_keys.json` nicht im Repo.

* **Debug nur in Dev**: Test-/Code-Checker-/Pytest-Routen nur hinter Flag + Admin.

---

## 2) Auth & Sessions (heute → Ziel)

### 2.1 Heute (Testbetrieb)

* Statischer Admin über ENV; Session-Cookie, kein CSRF, SHA-256-Hash.

### 2.2 Ziel (Prod)

* Nutzer in DB, Passwörter via **argon2**/**bcrypt** (z.B. `passlib`).

* Session-Cookies: `HttpOnly`, `Secure` (Prod), `SameSite=Strict` (Admin-only UI).

* **Brute-Force-Schutz**: z.B. 5–10 Logins/15min je IP.

* **CSRF**: entweder Header-Token pro Session *oder* Wechsel auf stateless Bearer-Token.

**Beispiel Hashing (Passlib/argon2):**

```python
from passlib.hash import argon2

hashed = argon2.hash(plain_password)
argon2.verify(plain_password, hashed)
```

**Secure Cookie (je nach ENV):**

```python
secure_cookie = os.getenv("APP_ENV") == "production"
response.set_cookie(
  key="admin_session", value=session_id, httponly=True,
  secure=secure_cookie, samesite="strict", max_age=3600*8
)
```

---

## 3) Autorisierung: Admin-APIs absichern

**Ziel:** Alle sensiblen Endpunkte (DB-View, Import, Geocode-Batch, Code-Checker, Tests, Kosten, Systemregeln …) nur für Admins.

**FastAPI-Pattern:**

```python
from fastapi import APIRouter, Depends
from backend.routes.auth_api import require_admin_auth

router = APIRouter(prefix="/api/import", tags=["import"],
                   dependencies=[Depends(require_admin_auth)])

@router.post("/upload")
async def upload_file(...):
    ...
```

> Für einzelne Routen geht auch: Parameter `session_id: str = Depends(require_admin_auth)`.

---

## 4) CORS & CSRF

**Problem:** `allow_origins=["*"]` + `allow_credentials=True` ist unsauber.

**Ziel (Prod):**

```python
app.add_middleware(CORSMiddleware,
  allow_origins=["https://trafficapp.example.com"],
  allow_credentials=True,
  allow_methods=["GET","POST","PUT","DELETE"],
  allow_headers=["Authorization","Content-Type"],
)
```

* Bei Cookie-Auth zusätzlich CSRF-Token im Header prüfen **oder** auf Bearer-Token wechseln.

---

## 5) Uploads & Pfade (Path Traversal)

**Filename-Whitelist + Pfad-Check:**

```python
SAFE = re.compile(r"^[A-Za-z0-9_.\-]+$")
if not SAFE.match(filename):
    raise HTTPException(400, "Ungültiger Dateiname")

csv_path = (TOURPLAENE_DIR / filename).resolve()
if not str(csv_path).startswith(str(TOURPLAENE_DIR.resolve())):
    raise HTTPException(400, "Pfad außerhalb erlaubt")
```

* **Max-Größe** für Uploads setzen (Webserver/ASGI + App-Limits).

* **MIME/Content-Type** prüfen; nur erlaubte Endungen.

---

## 6) Secrets & Key-Management

* `MASTER_PASSWORD`: **kein** produktiver Default. Bei fehlendem Wert → **App-Start abbrechen**.

* `secure_keys.json` / `.env.*` → in **.gitignore**.

* API-Keys nur aus ENV/Secret-Store; nicht auf Platte persistieren (außer im klar definierten Dev-Mode).

---

## 7) Debug-/Test-Routen absichern

* Routen wie `/api/tests/*`, Code-Checker, Pytest-Runner:

  * Nur wenn `ENABLE_DEBUG_ROUTES=1`

  * Zusätzlich Admin-Auth.

  * In Prod **standardmäßig aus**.

---

## 8) Logging & Datenschutz

* Log-Level in Prod auf **INFO**; kein PII-Dump (volle Adressen, Tokens, Payloads vermeiden).

* Fehlversuche, Admin-Events und Import-Fehler **auditierbar** loggen.

* Retention festlegen (z.B. 30/90 Tage) + DSGVO-Kontext beachten.

---

## 9) Security Headers (Reverse Proxy / App)

* `Content-Security-Policy` (Admin-UI minimal):

  * `default-src 'self'` | erlaubte Maps/CDNs whitelisten

* `X-Frame-Options: DENY`

* `X-Content-Type-Options: nosniff`

* `Referrer-Policy: no-referrer`

* `Strict-Transport-Security` (bei HTTPS)

---

## 10) Rate Limits & DoS

* Login-/Import-/Geocoding-Endpunkte drosseln (pro IP/Session).

* CSV-/Batch-Größen limitieren; parallele Jobs begrenzen.

---

## 11) CSV/Parser-Sicherheit

* Zeilen-/Spaltenlimits; Abbruch bei Oversize.

* Explizites Encoding (`utf-8`), robustes Fehlerhandling.

* Keine Ausführung eingebetteter Formeln/„=" (Excel-CSV Injection vermeiden).

---

## 12) Dependencies & Build

* `requirements.txt`/`pyproject.toml` **pinnen**; Security-Scans (pip-audit, safety) in CI.

* Docker-Base-Image mit regelmäßigen Updates.

---

## 13) Datenbank & Backups

* SQLite-Datei nur für App-User les-/schreibbar; Pfad außerhalb Webroot.

* Regelmäßige Backups + Restore-Playbook testen.

* Migrations strikt versionieren.

---

## 14) Rollenmodell (für kommende Benutzerverwaltung)

**Rollen & Rechte (Minimal-RBAC):**

* **Admin**: alle Admin-Tabs, Imports, Systemregeln, Code-Tools.

* **Dispo**: Tourpläne, Statistik, Import **ohne** Systemregeln/Debug.

* **Fahrer**: nur operative UI (keine Admin-Tabs, keine API-Admin-Routen).

* **ReadOnly**: DB-Viewer/Statistik read-only.

**Technik:**

* JWT/Session enthält `role`; `Depends(require_role("admin"))` etc.

---

## 15) Migrationsplan: Statisch → Benutzerverwaltung

1. **Phase A (heute)**

   * Admin-Auth härten (Hash, Cookie, Rate-Limit, CORS, Upload-Schutz).

   * Admin-APIs konsequent mit `require_admin_auth`.

2. **Phase B (User/RBAC)**

   * `users`, `roles`, `user_roles` Tabellen.

   * Login → Session/JWT mit Rolle; Tabs/API per Rolle filtern.

3. **Phase C (CSRF/Token & Secrets)**

   * CSRF einziehen oder komplett auf Bearer-Token.

   * Secrets nur aus ENV/Manager.

4. **Phase D (Hardening/Monitoring)**

   * Security Headers, Rate-Limits überall, Logs/Audits, CI-Security-Scans.

---

## 16) SECURITY_CHECKLIST.md (Kurzform zum Abhaken)

**Ziel:** Schnell abhakbare Punkte für Reviews/PRs. Jede Zeile ist ein Muss-Kriterium.

* [SC-01] Keine Default-Admin-Credentials im Code

* [SC-02] Passwörter mit argon2/bcrypt (kein SHA‑256), Salt & Verify

* [SC-03] Cookies: HttpOnly + Secure (Prod) + SameSite=Strict

* [SC-04] Login-Rate-Limit aktiv (z. B. 5–10 Versuche/15 min/IP)

* [SC-05] Alle Admin-APIs abgesichert: `Depends(require_admin_auth)`

* [SC-06] CORS: nur erlaubte Origins (kein `*` mit Credentials)

* [SC-07] Uploads: Dateiname-Whitelist, `resolve()`-Check, Größen- & MIME-Limits

* [SC-08] Secrets: `MASTER_PASSWORD` ohne produktiven Default; `.env`/`secure_keys.json` nicht im Repo

* [SC-09] Debug-/Test-Routen nur via Flag + Admin; in Prod standardmäßig aus

* [SC-10] Logging: keine PII/Secrets; Retention-Policy dokumentiert

* [SC-11] Security Headers gesetzt (CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy)

* [SC-12] Dependencies gepinnt; CI mit `pip-audit`/`safety`

* [SC-13] Backups & Restore getestet; SQLite-Pfade & -Rechte eingeschränkt

* [SC-14] RBAC: Rollen definiert (Admin/Dispo/Fahrer/ReadOnly); Tabs & APIs rollenbasiert

* [SC-15] CSRF-Schutz (bei Cookie-Auth) **oder** Wechsel auf Bearer-Token

* [SC-16] DoS/Rate-Limits auf Import/Geocoding/Test-Endpunkten & parallele Jobs

---

**Letzte Aktualisierung:** 2025-11-22  
**Status:** Phase A (Quick Wins) - In Bearbeitung

