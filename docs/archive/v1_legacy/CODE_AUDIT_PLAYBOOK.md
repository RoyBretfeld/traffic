# Code‑Audit Playbook · FAMO TrafficApp

> Einheitlicher Ablauf für Cursor‑Audits, Fix‑Vorschläge und Artefakte‑Packaging.

**Version:** 1.0  
**Gültig für:** Alle FAMO-Projekte  
**Letzte Aktualisierung:** 2025-11-13

---

## 1) Zielbild

* **Stabiler Start** (FastAPI + Uvicorn) und **klare Fehleroberfläche**.
* **OSRM erreichbar**: lokal (Docker) oder Proxmox‑LXC (Container 101) — konfigurierbar.
* **Predictable APIs** (Statuscodes, Schemas), **idempotente DB‑Schema‑Härtung**.
* **Reproduzierbare Audits**: immer gleiches Verfahren, gleiche Artefakte.

---

## 2) Umgebungen & Konfiguration

### Zwei Modi

* **Work/Proxmox (LXC‑Container 101)**: `OSRM_BASE_URL=http://172.16.1.191:5011`
* **Home/Docker**: `OSRM_BASE_URL=http://localhost:5011`

### .env Einträge (Backend)

```env
OSRM_BASE_URL=http://172.16.1.191:5011   # oder http://localhost:5011
OSRM_PROFILE=driving
OSRM_TIMEOUT=4
# Fallback auf Public nur für DEV
OSRM_FALLBACK_PUBLIC=true
OSRM_PUBLIC_URL=https://router.project-osrm.org
```

### Frontend (globale Config, z. B. `frontend/js/config.js`):

```javascript
window.APP_CONFIG = {
  apiBase: "http://127.0.0.1:8111",
  osrmBase: "http://172.16.1.191:5011" // oder http://localhost:5011
};
```

---

## 3) Quick‑Health Checks

### Backend

```bash
curl -sS http://127.0.0.1:8111/healthz
curl -sS http://127.0.0.1:8111/health/db
curl -sS http://127.0.0.1:8111/_debug/routes | head -n 30
```

### OSRM (Proxmox)

```bash
pct exec 101 -- bash -lc 'ss -ltnp | grep ":5011" || echo "OSRM NICHT LISTENING"'
pct exec 101 -- bash -lc 'curl -sS http://127.0.0.1:5011/health || true'
```

### OSRM (Home/Docker)

```bash
curl -sS http://127.0.0.1:5011/health || true
```

---

## 4) Standard‑Audit · Reihenfolge

1. **Route‑Inventar** loggen (Startup list): verifizieren, dass `POST /api/tour/route-details` registriert ist.

2. **DB‑Schema‑Härtung** ausführen (ohne destructive Migration):
   * `geo_fail.next_attempt` + Index vorhanden.
   * Keine `CREATE INDEX ... ON ... (missing_column)` Fehler; ggf. Vorab `ALTER TABLE`.

3. **Middleware‑Pfad** überprüfen:
   * `trace_id` & `error_handlers` dürfen **StreamingResponse** nicht mutieren.

4. **Statuscodes & Fehlertexte** harmonisieren:
   * Kein **402** für interne Fehler → **500**, Client‑Fehler → **400/422**.

5. **Frontend Fetch‑Nutzung** prüfen:
   * *Nur einmal* Body lesen; JSON vs. Text je nach `Content‑Type`.

6. **OSRM‑Client**: Base‑URL aus `.env`, Timeout, Fallback, Retry‑Backoff, Metriken.

7. **Cross‑Check** mit zweitem LLM (Verifier) → nur Read‑Only, keine Schreiboperationen.

8. **Artefakte packen** (siehe Abschnitt 10) → ZIP in `/ZIP` ablegen.

---

## 5) Fix‑Vorschläge (konkret)

### 5.1 Error‑Middleware: kein Zugriff auf `response.scope`

**Problem**: `_StreamingResponse` hat kein `scope`; Setting über `scope["extensions"]` crasht.

**Patch (Python, `backend/core/error_handlers.py`)**

```python
from starlette.responses import JSONResponse

async def dispatch(request, call_next):
    try:
        response = await call_next(request)
    except Exception as exc:  # Fallback, niemals Exceptions durchlassen
        # TODO: sauber loggen inkl. trace_id
        return JSONResponse({"detail": "Internal Server Error"}, status_code=500)

    # Korrelation nur über Header, niemals über response.scope
    trace_id = getattr(request.state, "trace_id", None)
    if trace_id:
        try:
            response.headers["X-Trace-Id"] = trace_id
        except Exception:
            # Worst case: ersatzweise neue Response
            payload = getattr(response, "body", b"") or b""
            safe = JSONResponse({"detail": "OK"})
            safe.headers["X-Trace-Id"] = trace_id
            return safe

    return response
```

### 5.2 Frontend: Body nur einmal lesen

**Problem**: `TypeError: Failed to execute 'text' on 'Response': body stream already read`.

**Patch (JS)**

```javascript
async function httpJson(url, opts) {
  const res = await fetch(url, opts);
  const isJson = (res.headers.get('content-type')||'').includes('application/json');
  const body = isJson ? await res.json() : await res.text();
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${isJson ? JSON.stringify(body) : body}`);
  }
  return body;
}
```

### 5.3 Statuscodes bereinigen

**Regel**

* **422**: Validierungsfehler (z. B. CSV fehlt / Parameter invalid)
* **404**: Endpoint oder Ressource nicht gefunden
* **500**: interner Fehler / OSRM down / DB‑Fehler
* **402**: **nicht verwenden** (Payment Required)

### 5.4 OSRM‑Client robust machen (`services/osrm_client.py`)

* Base‑URL aus `.env`, Timeout, **Retry mit Backoff** (max 2),
* Fallback auf Public nur DEV (Flag),
* Counter‑Metriken: `osrm_requests_total`, `osrm_errors_total`, `osrm_latency_ms`.

### 5.5 DB‑Schema‑Härtung (`db/schema.py`)

* Vor `CREATE INDEX IF NOT EXISTS idx_geo_fail_next_attempt ON geo_fail(next_attempt)` sicherstellen:
  * Spalte existiert; falls nicht: `ALTER TABLE geo_fail ADD COLUMN next_attempt TEXT DEFAULT NULL` (try/except, SQLite kompatibel).
* **Integrity‑Check** nach Härtung loggen.

---

## 6) Tests (API‑First, minimal aber hart)

### Smoke

```bash
pytest -q tests/smoke/test_health.py::test_health_all_ok
```

### Contract

* `tests/contract/test_route_details.py`: Request‑Schema, Response‑Schema (`geometries='polyline6'`), Statuscodes.

### OSRM Stub

* `tests/stubs/osrm_stub.py` → deterministische Polyline + Metriken.

---

## 7) Cursor‑Ablauf (deterministisch)

1. **Checkout** Feature‑Branch: `feat/audit‑<YYYYMMDD>`

2. **Run** Health‑Checks; speichere Output unter `artifacts/health/*.log`.

3. **Apply** Fix 5.1 → Commit: `fix(core): middleware safe header injection`

4. **Apply** Fix 5.2 → Commit: `fix(fe): single‑read fetch helper`

5. **Apply** Fix 5.3 → Commit: `chore(api): statuscode policy`

6. **Apply** Fix 5.4/5.5 → Commit: `feat(osrm|db): client hardening + schema guard`

7. **Run** Tests; bei Fail **kein** weiterer Refactor, zuerst Ursache reduzieren.

8. **Verifier‑LLM** (anderes Model): Diff + PR‑Review nur lesen, **keine Schreibrechte**.

9. **PR** mit Template (siehe unten), Labels: `audit`, `backend`, `frontend`.

### Commit‑Regeln

```
<type>(scope): kurze Aussage

WHY: Problem in 1 Satz
HOW: Fix in 1–2 Sätzen
RISK: low|medium|high
```

---

## 8) PR‑Template

```markdown
### Ziel

Kurzbeschreibung.

### Änderungen

- [ ] core/error_handlers
- [ ] fe/httpJson
- [ ] osrm_client
- [ ] schema guard

### Tests

- [ ] smoke
- [ ] contract
- [ ] stubbed osrm

### Risiken & Rollback

- Risiken: …
- Rollback: `git revert <sha>` und Service‑Restart
```

---

## 9) Artefakte‑Packaging (ZIP)

Am Ende jedes Audits **alles Relevante** unter `/ZIP` packen:

```
/ZIP/AUDIT_<YYYYMMDD_HHMM>.zip
  ├─ README_AUDIT.md (Kurzfazit, Repro, Fixliste)
  ├─ routes.txt (Auszug _debug/routes)
  ├─ health_app.log, health_db.log, health_osrm.log
  ├─ server_start.log (kompletter Start‑Log)
  ├─ frontend_console.txt (Export aus DevTools)
  ├─ env.sample (sensible Werte redacted)
  ├─ config/osrm_endpoints.json
  ├─ tests/ (nur neue/angepasste Specs)
  └─ screenshots/ (Fehler‑UI, Netz‑Tab)
```

**Verwendung**: Siehe `tools/make_audit_zip.py` und [Audit-ZIP-Pipeline](../STANDARDS.md#audit--compliance)

---

## 10) Proxmox · OSRM (LXC 101) Kurzrezepte

### Docker ok?

```bash
pct exec 101 -- bash -lc 'systemctl is-active docker || systemctl start docker || service docker start || true'
pct exec 101 -- bash -lc 'docker run --rm busybox:latest echo OK'
```

### OSRM via Docker (Port 5011 extern)

```bash
pct exec 101 -- bash -lc '
  mkdir -p /var/lib/osrm && cd /var/lib/osrm && \
  [ -f region.osm.pbf ] || curl -L https://download.geofabrik.de/europe/germany/sachsen-latest.osm.pbf -o region.osm.pbf && \
  docker run --rm -t -v $PWD:/data osrm/osrm-backend osrm-extract -p /opt/car.lua /data/region.osm.pbf && \
  docker run --rm -t -v $PWD:/data osrm/osrm-backend osrm-partition /data/region.osrm && \
  docker run --rm -t -v $PWD:/data osrm/osrm-backend osrm-customize /data/region.osrm && \
  (docker rm -f osrm || true) && \
  docker run -d --name osrm -p 5011:5000 -v $PWD:/data osrm/osrm-backend osrm-routed --algorithm mld /data/region.osrm'
```

### Checks

```bash
pct exec 101 -- bash -lc 'ss -ltnp | grep ":5011" || echo "OSRM NICHT LISTENING"'
pct exec 101 -- bash -lc 'curl -sS http://127.0.0.1:5011/route/v1/driving/13.7373,51.0504;13.7283,51.0615?overview=false'
```

---

## 11) Meine Einschätzung (kurz)

* **Hauptursachen** der 500er: Middleware‑Bug (Header‑Set über `scope`), doppelte Body‑Reads im FE, Statuscode‑Chaos.
* **OSRM**: Port‑Kollision (5000/Frigate), unstete Basis‑URL, Container‑Policy in LXC (nun gefixt).
* **Risiko**: mittel — fixes sind klar umrissen und lokal begrenzt.

### Priorität

1. Middleware‑Fix (5.1) → Crashes weg.
2. Frontend‑Fetch (5.2) → keine 500er‑Kaskade durch Fehlhandling.
3. Statuscode‑Policy (5.3) → bessere Telemetrie/Debuggability.
4. OSRM‑Client‑Härtung (5.4) + DB‑Guard (5.5).

---

## 12) Definition of Done

* Alle Health‑Checks grün; `/health/osrm` liefert OK.
* `route-details` liefert Geometrie (polyline6) ≥ 1 Segment.
* Frontend zeigt keine roten Errors im Network‑Tab bei Happy Path.
* ZIP‑Artefakt liegt unter `/ZIP/…` mit vollständiger Doku.
* PR gemergt, Tag `audit-<YYYYMMDD>` gesetzt.

---

## 13) Bonus: Mini‑Validator (Manuell)

```bash
# Backend OK?
curl -sS http://127.0.0.1:8111/_debug/routes | grep "/api/tour/route-details"

# OSRM Ping
curl -sS http://172.16.1.191:5011/health || curl -sS http://localhost:5011/health

# Probe-Route (kurz)
curl -sS "http://172.16.1.191:5011/route/v1/driving/13.7373,51.0504;13.7283,51.0615?overview=full&geometries=polyline6" | head -c 300
```

---

## Weiterführende Dokumentation

- **[STANDARDS.md](../STANDARDS.md)** - Zentrale Standards & Richtlinien
- **[RUNBOOK_ROUTING.md](../RUNBOOK_ROUTING.md)** - Routing-Runbook
- **[tools/make_audit_zip.py](../../tools/make_audit_zip.py)** - Audit-ZIP-Pipeline

---

**Dieses Playbook ist Teil der FAMO-Standards und sollte bei jedem Code-Audit befolgt werden.**

