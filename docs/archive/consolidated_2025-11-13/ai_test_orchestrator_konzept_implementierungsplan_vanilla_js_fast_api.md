# AI-Test Orchestrator – Konzept & Implementierungsplan (Vanilla JS + FastAPI)

> Ziel: Die eingebaute KI (LLM) führt automatisierte Tests aus, interpretiert die Ergebnisse, erzeugt konkrete Handlungsempfehlungen (Performance, Robustheit, UX) und präsentiert alles in der neuen Admin-Rubrik **AI‑Test**. Umsetzung bleibt **Vanilla JS + FastAPI** – kein React nötig.

---

## 1) Ziele
- **Autom. Testausführung** (quick/full) per Klick oder Zeitplan.
- **LLM-Auswertung** der Testergebnisse (Root-Cause-Hinweise, Priorisierung P0–P2, Fix‑Skizzen).
- **Sichtbare Live‑Logs** + Ergebnis-Dash (auch in eigenem Fenster abdockbar).
- **Persistenz** der Läufe & Metriken (monatlich rollierend, Pfad konfigurierbar – inkl. Netzwerkpfad).
- **Früherkennung** typischer Fehler (404 auf registrierten Routen, Encoding/Mojibake, OSRM/Polyline, SQLite‑Konsistenz, Latenzspitzen).

---

## 2) Benutzerfluss (Admin)
1. Admin öffnet **Admin → AI‑Test**.
2. Wählt Modus **Quick** (≈ 1–2 Min) oder **Full** (tiefer, inkl. Last/Trend).
3. Start → **Live‑Log** (WebSocket)
4. Abschluss: **Summary** (LLM), **Findings**, **Performance**, **Fehler**.
5. Export: JSON/HTML. Pfad kann im Panel geändert/getestet werden.

---

## 3) Test-Suites & Checks (erste Iteration)
### A. Backend/API
- **A1 Routing-Endpoint vorhanden**: `/api/tour/route-details` → Erwartet **200** + Schema `{distance, duration, geometry(polyline)}`. Meldet **P0** bei 404.
- **A2 Weitere Endpoints**: Health, Upload, Construction, Matching. Schemakonsistenz & Status.
- **A3 SQLite-Integrität**: `PRAGMA integrity_check` + `VACUUM`‑Dry‑Run; **Auto‑Backup/Restore** bei *malformed*; Platzbedarf-Check.

### B. Daten/Encoding
- **B1 Mojibake‑Guard**: cp850/utf‑8 Roundtrip gegen Stichproben (z. B. `Löbtauer`, `Fröbelstraße`). **Fehlerklassifizierung** & Auto‑Normalisierung (NFC) verifiziert.
- **B2 CSV‑Ingest**: TEHA‑Erkennung, Feldanzahl, leere Spalten, BAR‑Integration (Depot‑Adresse gesetzt), Duplikate.

### C. Routing/Geometrie
- **C1 OSRM‑Roundtrip**: OSRM‑Request (Service online?), Polyline **decodierbar**, Punkte ≥ 2.
- **C2 Distanzplausibilität**: OSRM‑Distanz vs. Haversine; Abweichung < **+15 %** (Schwelle konfigurierbar).
- **C3 Geocoder‑Resilienz**: Heikle Beispiele (z. B. `Hamburger Straße 65 a`) → Trefferquote, Normalisierung, Fallbacks.

### D. Performance
- **D1 Latenz**: P50/P90/P99 für Kern-Endpoints; Regression gegen letzten erfolgreichen Lauf.
- **D2 Speicher/Platz**: freier Speicher im Zielpfad, Größe der letzten 30 Läufe; Warnung bei < 10 % frei.

### E. Frontend (Vanilla)
- **E1 UI‑Verfügbarkeit**: `/ui/` antwortet 200, wesentliche Assets 200.
- **E2 Polyline‑Dekodierung**: Testet JS‑Decoder (Golden‑Polyline) + Kartenrender (Headless Screenshot optional in Iteration 2).

---

## 4) KI‑Auswertung (LLM‑Pipeline)
- Aggregator sammelt **raw results** → generiert **compact JSON** mit:
  - `summary`, `findings[] {severity, area, detail, evidence}`, `actions[] {prio, title, steps}`
  - `perf {endpoint: {p50,p90,p99}}`, `regressions`, `risks`.
- Prompt enthält: letzte 3 Läufe (Kurzmetriken), Code‑Snippets (nur relevante Ausschnitte), Logs.
- Output wird im Panel angezeigt + als Markdown & JSON gespeichert.

---

## 5) API-Design (neu)
- **POST** `/api/ai-test/run` → `{suites?: string[], mode?: "quick"|"full"}` → `{run_id}`
- **GET** `/api/ai-test/status?run_id=` → `{state: queued|running|done|error, progress}`
- **GET** `/api/ai-test/result?run_id=` → komplettes Ergebnis JSON
- **WS** `/ws/ai-test/stream?run_id=` → Live‑Logs

**Auth**: Admin‑Key (ENV: `ADMIN_API_KEY`) Header `X-Admin-Key`.

---

## 6) Persistenz & Speicherpfad
- Default: `data/ai_test_runs/YYYY-MM/run_<ts>/`
- Konfigurierbar im UI (inkl. UNC `\\SERVER\share\path`) + Schreibtest.
- Aufbewahrung: 90 Tage (konfigurierbar). Auto‑Cleanup per Job.
- Artefakte: `result.json`, `summary.md`, `logs.ndjson`, `perf.csv`.

---

## 7) Admin‑UI (Vanilla JS)
**Pfad:** `frontend/admin/ai-test.html`
- Controls: Mode (Quick/Full), Suite‑Checkboxen, Speicherpfad + Test, **Run**‑Button.
- Live‑Konsole (WebSocket), Fortschritt‑Badge.
- Tabs: **Summary**, **Findings**, **Performance**, **Fehler**, **Artefakte**.
- **Abdocken**: Button „In Fenster öffnen“ → `window.open('ai-test.html?run_id=...')` → eigenständiges Log/Result‑UI.

**Navigationsänderungen**
- Hauptnavigation: **Start | Statistik | ABI‑Talks | Admin**
- **Admin** (Untermenü): **AI‑Test**, **Testboard (manuell)**, **Tasks**

---

## 8) Sicherheit
- Admin‑Pfad und AI‑Test‑API erfordern `X-Admin-Key`.
- Rate‑Limit Run (z. B. 1 gleichzeitiger Run). Queue via `asyncio.Queue`.

---

## 9) Geplante Tasks (für Cursor)
**Backend**
1. `backend/ai_test/__init__.py` – Suite‑Registry
2. `backend/ai_test/suites/` – A1..E2 Implementierungen
3. `backend/ai_test/runner.py` – Run‑Koordinator, WebSocket‑Broadcast
4. `backend/ai_test/aggregator.py` – Ergebnis‑Konsolidierung
5. `backend/ai_test/llm_interpreter.py` – LLM‑Prompting (bestehenden LLM‑Service wiederverwenden)
6. API‑Routes `routes.ai_test` – POST/GET/WS
7. SQLite‑Backup‑Utility: `services/sqlite_safety.py`

**Frontend (Vanilla)**
1. `frontend/admin/ai-test.html` & `frontend/js/ai-test.js`
2. WebSocket‑Client, Render der Tabs, Abdock‑Button
3. Pfad‑Picker + Schreibtest

**Persistenz/Config**
1. ENV: `ADMIN_API_KEY`, `AI_TEST_BASEDIR`, `AI_TEST_RETENTION_DAYS`
2. Settings laden & validieren

**Dokumentation**
1. `docs/ai-test-plan.md` (dieses Dokument als Basis)
2. `docs/api/ai-test.md` (Endpoints, Schemas, Beispiele)

---

## 10) Ergebnis‑Schema (vereinfacht)
```json
{
  "run_id": "20251106-120101-xyz",
  "mode": "full",
  "started_at": "2025-11-06T12:01:01Z",
  "suites": ["A1","C1","C2","D1"],
  "metrics": {
    "latency": {"/api/tour/route-details": {"p50":120, "p90":240, "p99":480}}
  },
  "findings": [
    {"severity":"P0","area":"Routing","detail":"/api/tour/route-details antwortet 404","evidence":"GET ... -> 404"}
  ],
  "actions": [
    {"prio":"P0","title":"FastAPI reload/Router-Fix","steps":["ensure include_router(...) executed once","disable duplicate reloader","add startup smoke"]}
  ],
  "summary": "Route-Endpoint 404, OSRM ok. Ursache: Reload/Import-Reihenfolge.",
  "artifacts": {"result":"result.json","logs":"logs.ndjson","summary":"summary.md"}
}
```

---

## 11) Quick Code‑Skeletons
**FastAPI-Routes** (`routes/ai_test.py`)
```python
router = APIRouter(prefix="/api/ai-test", tags=["ai-test"])

@router.post("/run", response_model=RunId)
async def run_ai_test(req: RunRequest, admin_key: str = Header(..., alias="X-Admin-Key")):
    auth_guard(admin_key)
    run_id = await runner.enqueue(req)
    return {"run_id": run_id}

@router.get("/status")
async def status(run_id: str, admin_key: str = Header(..., alias="X-Admin-Key")):
    auth_guard(admin_key)
    return runner.status(run_id)
```

**Vanilla JS – Start Run** (`frontend/js/ai-test.js`)
```js
async function startRun() {
  const key = localStorage.getItem('adminKey');
  const body = { mode: document.querySelector('#mode').value };
  const res = await fetch('/api/ai-test/run', {
    method: 'POST', headers: { 'Content-Type':'application/json', 'X-Admin-Key': key },
    body: JSON.stringify(body)
  });
  const { run_id } = await res.json();
  openLogStream(run_id);
}
```

---

## 12) Akzeptanzkriterien (Iteration 1)
- 404 auf `/api/tour/route-details` wird als **P0** erkannt & im Summary angezeigt.
- OSRM‑Roundtrip liefert **decodierbare** Polyline + Plausibilitätscheck **OK**.
- Live‑Logs sichtbar; Ergebnisse als JSON gespeichert; Pfad kann gesetzt & getestet werden.
- Abdocken des AI‑Test‑Panels in eigenem Fenster möglich.

---

## 13) Nächste Ausbauten (Iteration 2+)
- Headless Map‑Screenshot (E2 visuell)
- Trendcharts (P50/P90/P99) auf **Statistik‑Seite** (Verknüpfung AI‑Test ↔ Statistik)
- Gezielte Auto‑Fix‑PR‑Vorschläge (Patch‑Diffs) aus LLM‑Hinweisen
- CRON‑ähnlicher Scheduler (täglich 04:00) + Mail/Teams‑Webhook bei P0/P1

---

## 14) Risiken & Mitigation
- **LLM‑Kosten/Latenz** → Quick‑Mode ohne LLM möglich.
- **WS‑Skalierung** → 1 Run gleichzeitig; Logs drosseln.
- **Netzwerkpfade** → Vor Schreibtest mit Timeout & Fallback.

---

## 15) To‑Do Liste (Cursor‑Tasks)
- [ ] Backend: Suite‑Registry + Runner + Routes
- [ ] Tests: A1..E2 Unit/Integration
- [ ] Frontend: `ai-test.html` + `ai-test.js` + Abdock‑Button
- [ ] Persistenz & Cleanup + Pfad‑Picker
- [ ] Docs: `docs/ai-test-plan.md`, `docs/api/ai-test.md`

