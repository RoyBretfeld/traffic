# Lizenzierungssystem für FAMO TrafficApp

**Erstellt:** 2025-01-10  
**Status:** Geplant  
**Ziel:** Sichere, verkaufbare Auslieferung mit Online-Lizenzprüfung, Offline-Fallback, Revocation, minimaler Telemetrie

---

## Überblick Architektur

### Client (TrafficApp)
- Startet lokalen FastAPI-Server (Uvicorn)
- **LicenseManager** prüft beim Start: lokale Lizenzdatei → Signatur → Gültigkeit → ggf. Online-Refresh
- **Middleware** blockiert geschützte Endpoints, wenn Lizenz fehlt/abgelaufen (HTTP 402/403)
- **Admin → „Lizenz"**: Eingabe Lizenzschlüssel, Proxy, Offline-Aktivierung, Status

### Lizenzserver (separat, klein)
- FastAPI-Microservice, Postgres
- Ed25519-Public/Private Keypair (Server hält Private Key, Client hat Public Key eingebettet)
- REST: `/v1/activate`, `/v1/verify`, `/v1/deactivate`, `/v1/heartbeat`, `/v1/public-key`, `/v1/licenses/{key}`
- Gibt **JWT (alg: EdDSA)** mit Entitlements + kurzer Laufzeit (z.B. 7 Tage) zurück → Client cached

### Verteilung
- **Installer (MSI/EXE)** via PyInstaller + (optional) Nuitka/Obfuskation
- **Signiertes** Setup (Authenticode)
- USB dient nur als Medium (kein Dongle). Enthält: Installer, signiertes `manifest.json` (Hashes), Offline-Aktivierung-Tool

---

## Lizenzmodell

### Key-Format (menschlich, prüfbar)
- Format: `FAMO-ABCD-EFGH-JKLM-NPQR-CHK`
- **Crockford Base32**, 4er-Gruppen, `CHK` = Prüfsumme (Luhn-Mod-32)

### Aktivierungsmodell
- **Node-Locked** mit **N Aktivierungen** (z.B. 2 Geräte) *oder* **Floating** via Server-Pool

### Entitlements
- Edition (Std/Pro)
- Features (OSRM-Routing, Export, Admin-Tools)
- User-Limit (optional)

### Grace-Period
- 7–14 Tage offline lauffähig (token `exp` + "grace_until")
- Danach Read-Only/Start-Block

### Revocation
- Serverseitiger Status greift spätestens beim nächsten Verify/Heartbeat

---

## Datenmodell (Server)

### Tabellen

**`license_keys`**
- `id` (PK)
- `key_hash` (unique, SHA256 des Keys)
- `edition` (std/pro)
- `seats` (Anzahl erlaubter Aktivierungen)
- `seats_used` (aktuell genutzt)
- `status` (active/revoked/expired)
- `created_at`
- `expires_at`

**`devices`**
- `id` (PK)
- `fingerprint_hash` (unique, SHA256 des Device-FP)
- `first_seen_at`
- `last_seen_at`
- `meta_json` (app_version, os, etc.)

**`activations`**
- `id` (PK)
- `license_id` (FK → license_keys)
- `device_id` (FK → devices)
- `activated_at`
- `deactivated_at`
- `status` (active/inactive)

**`heartbeats`**
- `id` (PK)
- `device_id` (FK → devices)
- `license_id` (FK → license_keys)
- `app_version`
- `ts` (timestamp)

**`revocations`**
- `id` (PK)
- `license_id` (FK → license_keys)
- `reason` (text)
- `ts` (timestamp)

### Indexes
- `license_keys.key_hash` (unique)
- `devices.fingerprint_hash` (unique)
- FK-Indices auf alle Foreign Keys

---

## REST-API (Server)

### Endpoints

**`POST /v1/activate`**
- Body: `{license_key, device_fp, app_version}`
- Response 200: `{jwt, entitlements, grace_until}`
- Prüft Key, Seats, erstellt Activation, gibt JWT zurück

**`POST /v1/verify`**
- Body: `{jwt, device_fp}`
- Response 200: `{ok, jwt (optional refresh), status}`
- Verifiziert JWT, prüft Revocation, gibt ggf. neues Token zurück

**`POST /v1/deactivate`**
- Body: `{jwt, device_fp}`
- Response 200: `{ok}`
- Deaktiviert Activation, reduziert seats_used

**`POST /v1/heartbeat`**
- Body: `{jwt, device_fp, app_version}`
- Response 200: `{ok}`
- Loggt Heartbeat, aktualisiert last_seen_at

**`GET /v1/public-key`**
- Response: PEM (Ed25519 Public Key)
- Öffentlicher Key für Client-Verifizierung

**`GET /v1/licenses/{key_hash}`** (admin-auth)
- Response: Details/Seats
- Admin-Endpoint für Lizenz-Status

### JWT-Claims (EdDSA/Ed25519)

```json
{
  "sub": "license_id",
  "lic": "key_hash",
  "dev": "device_fp_hash",
  "ent": {
    "edition": "pro",
    "features": ["routing", "export"]
  },
  "nbf": 1730851200,
  "iat": 1730851200,
  "exp": 1731456000
}
```

---

## Client-Integration (TrafficApp)

### Dateipfade

- **Windows**: `%ProgramData%/FAMO/TrafficApp/license.json`
- **Linux**: `/var/lib/famo/trafficapp/license.json`
- Datei ACL eng setzen (Windows: BUILTIN\Users nur Read)

### Device-Fingerprint (stabil, datensparsam)

- **Windows**: `MachineGuid` (Registry) + BaseBoard Serial + SystemDrive Volume GUID → `SHA256(salt || values)`
- **Linux**: `/etc/machine-id` + DMI Serial + Filesystem UUID → `SHA256(salt || values)`
- Hash **nur** übertragen, niemals Rohdaten (DSGVO)

### Startup-Flow

1. Lade `license.json` → Verify Signatur (embedded Public Key, EdDSA)
2. Wenn gültig & nicht abgelaufen → weiter; wenn <72h vor exp → **silent refresh** (`/verify`)
3. Falls ungültig/abgelaufen: zeige **Lizenzdialog** (Key, Proxy, Offline)
4. Bei Erfolg: speichere neues Token + `grace_until`

### Middleware (FastAPI)

- Dependency `require_license(entitlement: str)` prüft Token + Feature
- Bei Fail → `HTTPException(402/403, detail="license_invalid_or_missing")`

### Offline-Aktivierung (Challenge-Response)

- Client erzeugt `challenge.json`: `{ key, device_fp, app_version, ts }`
- Nutzer lädt Datei beim Händler/Portal hoch → erhält `license.json` (signiertes JWT)
- Import im Admin-Dialog

---

## Sicherheit & Hardening

### Code-Signierung
- **Authenticode** für Installer/EXE
- Signatur mit Code-Signing-Zertifikat

### Verpackung
- **PyInstaller** (OneDir) + `--key` + (optional) **Nuitka** für C-Kompilierung
- **Obfuskation**: pyarmor/nuitka (nicht unknackbar, aber Hürde)

### CSP/Headers
- CSP/Headers im Web-UI (bereits im Security-Konzept vorhanden)

### Speicherorte
- Restriktive ACLs, Lizenzdatei signiert (fälschungssicher)

### Server-Sicherheit
- **Rate-Limit** + WAF am Lizenzserver
- **TLS only** (ACME/Let's Encrypt)

### Datensparsamkeit (DSGVO)
- Keine PII; nur `key_hash`, `device_fp_hash`, `version`
- Löschroutine/Export bereitstellen

---

## Distribution & USB-Prozess

1. **Build (CI)**: Tests → PyInstaller → Signieren → SHA256 Hashes
2. **Erzeuge `manifest.json`**: Dateiliste + Hash + Signatur mit Release-Key
3. **Kopiere auf USB**: Read-only Sticks bevorzugen + drucke **Seriennummer**
4. **Auf Kunde**: Installer prüft Manifest-Signatur + Hashes, dann Setup
5. **Erststart**: Lizenzdialog

---

## Admin-UI – "Lizenz"

### Features
- Eingabe Lizenzschlüssel
- Aktivieren/Deaktivieren
- Offline-Challenge Export/Import
- Status (Edition, Features, exp, grace)
- Geräte-Info (gekürzt)
- Logs
- Proxy-Support (HTTP/SOCKS)

---

## Tests (automatisiert)

### Unit-Tests
- Prüfsumme/Luhn-32
- Key-Parser
- JWT-Verify EdDSA
- Device-FP-Generierung

### Integration (Client)
- Startup mit gültigem/abgelaufenem Token
- Grace-Pfad
- Revocation

### Integration (Server)
- Activate → Seats
- Double-Activate
- Deactivate
- Verify/Refresh
- Revocation

### E2E-Tests
- App startet ohne Internet (grace ok)
- Nach Grace Block
- Offline-Challenge-Import
- Revocation greift

---

## Implementierungsreihenfolge

1. **Server**: FastAPI-Service + Postgres Schema, Endpoints, Ed25519-Key mgmt, Dockerfile
2. **Client**: `LicenseManager`, Middleware, Admin-UI "Lizenz" (Vanilla JS), Proxy-Dialog
3. **Packaging**: PyInstaller Spec, Signatur-Pipeline (signtool), Manifest-Signer
4. **Offline-Tool**: `famo-offline-activation.exe` (kleines CLI/GUI)
5. **Tests**: pytest-Suiten + CI-Jobs
6. **Docs**: `docs/licensing-plan.md`, `docs/licensing-operations.md` (Revocation, Rotation, DSGVO)

---

## Entscheidungen (Defaults)

- **Ed25519 + EdDSA-JWT** (offline verifizierbar, schnell)
- **Grace 10 Tage**, **Heartbeat täglich**
- **Seats** Standard = 2 / Lizenz
- **Feature-Flag** für Routing (schützt OSRM-Funktion)

---

## Dateien-Übersicht

### Server (`services/license-server/`)
- `app/main.py` - FastAPI-App
- `app/models.py` - SQLAlchemy-Modelle
- `app/routes.py` - API-Endpoints
- `app/crypto.py` - Ed25519-Key-Management
- `app/database.py` - DB-Connection
- `migrations/` - Alembic-Migrationen
- `Dockerfile` - Container-Build
- `requirements.txt` - Dependencies
- `tests/` - Test-Suite

### Client (`app/licensing.py`)
- `LicenseManager` - Hauptklasse
- `device_fingerprint.py` - Device-FP-Generierung
- `key_parser.py` - Key-Validierung (Crockford Base32, Luhn-32)
- `offline_activation.py` - Challenge-Response-Logik

### Client (Middleware)
- `backend/middleware/license_middleware.py` - FastAPI-Dependency
- Integration in `backend/app.py`

### Client (Admin-UI)
- `frontend/admin.html` - Erweitern um "Lizenz"-Tab
- `frontend/js/admin_license.js` - Lizenz-UI-Logik
- `frontend/css/admin_license.css` - Styling

### Packaging
- `build/pyinstaller.spec` - PyInstaller-Konfiguration
- `build/sign.py` - Signatur-Script
- `build/manifest.py` - Manifest-Generator
- `build/offline_activation_tool.py` - Offline-Aktivierungs-Tool

### Tests
- `tests/test_licensing_unit.py` - Unit-Tests
- `tests/test_licensing_integration.py` - Integration-Tests
- `tests/test_licensing_e2e.py` - E2E-Tests

### Dokumentation
- `docs/licensing-plan.md` - Dieser Plan
- `docs/licensing-operations.md` - Operations-Guide (Revocation, Rotation, DSGVO)

---

## Akzeptanzkriterien

- [ ] Server: Alle Endpoints funktionieren, Ed25519-Signatur korrekt
- [ ] Client: LicenseManager lädt/verifiziert Token, Grace-Period funktioniert
- [ ] Middleware: Geschützte Endpoints blockiert ohne Lizenz (402/403)
- [ ] Admin-UI: Lizenz aktivieren/deaktivieren, Offline-Import funktioniert
- [ ] Packaging: Installer signiert, Manifest-Validierung funktioniert
- [ ] Offline-Tool: Challenge-Export/Import funktioniert
- [ ] Tests: Alle Test-Suiten laufen grün
- [ ] Dokumentation: Vollständig und aktuell

