# Ziel
Sichere, verkaufbare Auslieferung der **FAMO TrafficApp** (Windows-first), mit Online‑Lizenzprüfung, Offline‑Fallback, Revocation, minimaler Telemetrie und klaren Admin‑Workflows. Distribution zunächst per **USB‑Stick** + Downloadlink. Keine React‑Migration nötig.

---
# Überblick Architektur
- **Client (TrafficApp)**
  - Startet lokalen FastAPI‑Server (Uvicorn)
  - **LicenseManager** prüft beim Start: lokale Lizenzdatei → Signatur → Gültigkeit → ggf. Online‑Refresh
  - **Middleware** blockiert geschützte Endpoints, wenn Lizenz fehlt/abgelaufen (HTTP 402/403)
  - **Admin → „Lizenz“**: Eingabe Lizenzschlüssel, Proxy, Offline‑Aktivierung, Status

- **Lizenzserver (separat, klein)**
  - FastAPI‑Microservice, Postgres
  - Ed25519‑**Public/Private** Keypair (Server hält Private Key, Client hat Public Key eingebettet)
  - REST: `/v1/activate`, `/v1/verify`, `/v1/deactivate`, `/v1/heartbeat`, `/v1/public-key`, `/v1/licenses/{key}`
  - Gibt **JWT (alg: EdDSA)** mit Entitlements + kurzer Laufzeit (z. B. 7 Tage) zurück → Client cached

- **Verteilung**
  - **Installer (MSI/EXE)** via PyInstaller + (optional) Nuitka/Obfuskation
  - **Signiertes** Setup (Authenticode)
  - USB dient nur als Medium (kein Dongle). Enthält: Installer, signiertes `manifest.json` (Hashes), Offline‑Aktivierung‑Tool

---
# Lizenzmodell
- **Key-Format (menschlich, prüfbar)**: `FAMO-ABCD-EFGH-JKLM-NPQR-CHK`
  - **Crockford Base32**, 4er‑Gruppen, `CHK` = Prüfsumme (Luhn‑Mod‑32)
- **Aktivierungsmodell**: „Node‑Locked“ mit **N Aktivierungen** (z. B. 2 Geräte) _oder_ „Floating“ via Server‑Pool
- **Entitlements**: Edition (Std/Pro), Features (OSRM‑Routing, Export, Admin‑Tools), User‑Limit (optional)
- **Grace**: 7–14 Tage offline lauffähig (token `exp` + „grace_until“), danach Read‑Only/Start‑Block
- **Revocation**: Serverseitiger Status greift spätestens beim nächsten Verify/Heartbeat

---
# Datenmodell (Server)
**Tabellen**
- `license_keys(id, key_hash, edition, seats, seats_used, status, created_at, expires_at)`
- `devices(id, fingerprint_hash, first_seen_at, last_seen_at, meta_json)`
- `activations(id, license_id, device_id, activated_at, deactivated_at, status)`
- `heartbeats(id, device_id, license_id, app_version, ts)`
- `revocations(id, license_id, reason, ts)`

**Indexes**: `license_keys.key_hash` (unique), `devices.fingerprint_hash` (unique), FK‑Indices

---
# REST‑API (Server)
- `POST /v1/activate` → Body: `{license_key, device_fp, app_version}` → 200: `{jwt, entitlements, grace_until}`
- `POST /v1/verify` → Body: `{jwt, device_fp}` → 200: `{ok, jwt (optional refresh), status}`
- `POST /v1/deactivate` → Body: `{jwt, device_fp}` → 200: `{ok}`
- `POST /v1/heartbeat` → Body: `{jwt, device_fp, app_version}` → 200: `{ok}`
- `GET  /v1/public-key` → PEM (Ed25519)
- `GET  /v1/licenses/{key_hash}` (admin‑auth) → Details/Seats

**JWT‑Claims** (EdDSA/Ed25519):
```json
{
  "sub": "license_id",
  "lic": "key_hash",
  "dev": "device_fp_hash",
  "ent": {"edition": "pro", "features": ["routing","export"]},
  "nbf": 1730851200,
  "iat": 1730851200,
  "exp": 1731456000
}
```

---
# Client‑Integration (TrafficApp)
## Dateipfade
- Lizenzcache: `%ProgramData%/FAMO/TrafficApp/license.json` (Windows) | `/var/lib/famo/trafficapp/license.json` (Linux)
- Datei ACL eng setzen (Windows: BUILTIN\Users nur Read)

## Device‑Fingerprint (stabil, datensparsam)
- Windows: `MachineGuid` (Registry) + BaseBoard Serial + SystemDrive Volume GUID → `SHA256(salt || values)`
- Hash **nur** übertragen, niemals Rohdaten (DSGVO)

## Startup‑Flow
1) Lade `license.json` → Verify Signatur (embedded Public Key, EdDSA)
2) Wenn gültig & nicht abgelaufen → weiter; wenn <72h vor exp → **silent refresh** (`/verify`)
3) Falls ungültig/abgelaufen: zeige **Lizenzdialog** (Key, Proxy, Offline)
4) Bei Erfolg: speichere neues Token + `grace_until`

## Middleware (FastAPI)
- Dependency `require_license(entitlement: str)` prüft Token + Feature
- Bei Fail → `HTTPException(402/403, detail="license_invalid_or_missing")`

### Beispiel (Client, gekürzt)
```python
# app/licensing.py
import json, time, hashlib, os
from pathlib import Path
import jwt  # PyJWT >= 2.8, supports EdDSA
from typing import Optional

PUBLIC_KEY_PEM = """-----BEGIN PUBLIC KEY-----\n...Ed25519...\n-----END PUBLIC KEY-----\n"""
CACHE = Path(os.getenv("PROGRAMDATA", "/var/lib")) / "FAMO" / "TrafficApp" / "license.json"

class LicenseManager:
    def __init__(self, http):
        self.http = http  # requests-like client
        self.token: Optional[str] = None
        self.ent: dict = {}

    def load(self):
        if CACHE.exists():
            data = json.loads(CACHE.read_text("utf-8"))
            self.token = data.get("jwt")

    def save(self):
        CACHE.parent.mkdir(parents=True, exist_ok=True)
        CACHE.write_text(json.dumps({"jwt": self.token}), "utf-8")

    def verify_local(self) -> bool:
        if not self.token:
            return False
        try:
            payload = jwt.decode(self.token, PUBLIC_KEY_PEM, algorithms=["EdDSA"])
            self.ent = payload.get("ent", {})
            return payload.get("exp", 0) > time.time()
        except Exception:
            return False

    def activate_online(self, key: str, fp: str):
        resp = self.http.post("/v1/activate", json={"license_key": key, "device_fp": fp})
        resp.raise_for_status()
        self.token = resp.json()["jwt"]
        self.save()

    def require(self, feature: str) -> bool:
        return feature in self.ent.get("features", [])
```

```python
# app/main.py (Ausschnitt)
from fastapi import FastAPI, Depends, HTTPException
from app.licensing import LicenseManager

lm = LicenseManager(http_client)
lm.load()
if not lm.verify_local():
    # optional: try refresh; sonst UI für Aktivierung öffnen
    pass

app = FastAPI()

def require_license(feature: str):
    def _inner():
        if not lm.verify_local() or not lm.require(feature):
            raise HTTPException(status_code=402, detail="license_invalid_or_missing")
    return _inner

@app.get("/api/pro/route-details", dependencies=[Depends(require_license("routing"))])
async def route_details(...):
    ...
```

## Offline‑Aktivierung (Challenge‑Response)
- Client erzeugt `challenge.json`: `{ key, device_fp, app_version, ts }`
- Nutzer lädt Datei beim Händler/Portal hoch → erhält `license.json` (signiertes JWT)
- Import im Admin‑Dialog

---
# Sicherheit & Hardening
- **Code‑Signierung** (Authenticode) für Installer/EXE
- **Verpackung**: PyInstaller (OneDir) + `--key` + (optional) **Nuitka** für C‑Kompilierung
- **Obfuskation**: pyarmor/nuitka (nicht unknackbar, aber Hürde)
- **CSP/Headers** im Web-UI (wir haben bereits CSP im Security‑Konzept)
- **Speicherorte** mit restriktiven ACLs, Lizenzdatei signiert (fälschungssicher)
- **Rate‑Limit** + WAF am Lizenzserver, TLS only (ACME/Let’s Encrypt)
- **Datensparsamkeit (DSGVO)**: keine PII; nur `key_hash`, `device_fp_hash`, `version`; Löschroutine/Export bereitstellen

---
# Distribution & USB‑Prozess
1) Build (CI): Tests → PyInstaller → Signieren → SHA256 Hashes
2) Erzeuge `manifest.json` (Dateiliste + Hash + Signatur mit Release‑Key)
3) Kopiere auf USB (read‑only Sticks bevorzugen) + drucke **Seriennummer**
4) Auf Kunde: Installer prüft Manifest‑Signatur + Hashes, dann Setup
5) Erststart → Lizenzdialog

---
# Admin‑UI – „Lizenz“
- Eingabe Lizenzschlüssel, Aktivieren/Deaktivieren
- Offline‑Challenge Export/Import
- Status (Edition, Features, exp, grace), Geräte‑Info (gekürzt), Logs
- Proxy‑Support (HTTP/SOCKS)

---
# Tests (automatisiert)
- **Unit**: Prüfsumme/Luhn‑32, Key‑Parser, JWT‑Verify EdDSA, Device‑FP
- **Integration (Client)**: Startup mit gültigem/abgelaufenem Token, Grace‑Pfad, Revocation
- **Integration (Server)**: Activate → Seats, Double‑Activate, Deactivate, Verify/Refresh, Revocation
- **E2E**: App startet ohne Internet (grace ok), nach Grace Block, Offline‑Challenge‑Import, Revocation greift

---
# Arbeitspakete (Cursor‑Tasks)
1. **Server**: FastAPI‑Service + Postgres Schema, Endpoints, Ed25519‑Key mgmt, Dockerfile
2. **Client**: `LicenseManager`, Middleware, Admin‑UI „Lizenz“ (Vanilla JS), Proxy‑Dialog
3. **Packaging**: PyInstaller Spec, Signatur‑Pipeline (signtool), Manifest‑Signer
4. **Offline‑Tool**: `famo-offline-activation.exe` (kleines CLI/GUI)
5. **Tests**: pytest‑Suiten + CI‑Jobs
6. **Docs**: `docs/licensing-plan.md`, `docs/licensing-operations.md` (Revocation, Rotation, DSGVO)

---
# Entscheidungen (defaults)
- **Ed25519 + EdDSA‑JWT** (offline verifizierbar, schnell)
- **Grace 10 Tage**, **Heartbeat täglich**
- **Seats** Standard = 2 / Lizenz
- **Feature‑Flag** für Routing (schützt OSRM‑Funktion)

---
# Nächste Schritte
- [ ] Repo: `services/license-server/` anlegen, Boilerplate pushen
- [ ] TrafficApp: `app/licensing.py` + Admin‑UI „Lizenz“ Skeleton
- [ ] Packaging‑Script + Signatur‑Stubs
- [ ] Testfälle anlegen (Unit + Integration)
- [ ] Docs generieren und unter `docs/` einchecken

