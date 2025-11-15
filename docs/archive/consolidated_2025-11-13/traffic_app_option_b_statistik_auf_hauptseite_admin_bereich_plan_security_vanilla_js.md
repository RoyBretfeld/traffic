# Entscheidung & Scope

**Gewählt:** **Option B** – Statistik als **Read-only-Box auf der Hauptseite** + **Admin-Bereich** (Testboard, AI‑Test, Pfadverwaltung, Archiv).

**Technologie:** Bestand bleibt **Vanilla JS/HTML/CSS** + FastAPI. Abdockbare Panels in Vanilla JS (`window.open`, `postMessage`/`BroadcastChannel`). React-Migration wird nur als Ausblick erwähnt, keine Umsetzung jetzt.

---

# Architektur-Überblick

- **Frontend Dateien**
  - `frontend/index.html` (Hauptseite) → ergänzt um **Statistik-Box** & Indikatoren (Zeitbox-Overlay)
  - `frontend/js/main.js` → lädt `stats.summary` (read‑only), rendert Kennzahlen, Sparkline‑Minicharts
  - `frontend/js/detach.js` → Abdock-Logik (Karte/Tourliste), Msg‑Sync (BroadcastChannel), Window‑Lifecycle
  - `frontend/admin.html` (Admin-Bereich) → Tabs: *Testboard*, *AI-Test*, *Statistik & Archiv*, *Fenster & Docking*
  - `frontend/js/admin.js` → Admin-UI, Pfadwahl (File/Directory Picker), Archiv-Operationen, Test-Runner-Trigger
  - `frontend/css/stats.css`, `frontend/css/detach.css`

- **Backend (FastAPI)**
  - `routes/stats_api.py` → `GET /api/stats/summary`, `GET /api/stats/days`, `PUT/GET /api/stats/archive-path`, `POST /api/stats/rollup`
  - `routes/ui_admin.py` → Admin‑HTML/Assets (falls per FastAPI StaticFiles ausgeliefert)
  - `services/stats_store.py` → Lesen/Schreiben täglicher/monatlicher Artefakte, Rollups
  - `services/security.py` → AuthN/AuthZ (JWT), Rollen (`viewer`, `admin`), Pfadvalidierung
  - `schemas/stats.py` → Pydantic Modelle (Summary, TourDay, StorageSettings)

---

# UI/UX Spezifikation

## Navigation
- **Hauptseite** (bestehend) + **Statistik-Box** (sichtbar für alle)
- **ABI‑Talks** (wie gehabt)
- **Admin** (nur für Rolle `admin` sichtbar)

## Hauptseite – Statistik-Box (read‑only)
- **Kennzahlen Heute**: Touren (#), Stopps (#), **OSRM‑km** (Summe), **Fahrzeit** (Summe), **Ø Stopps/Tour**, **Geocoding‑Fails** (# heute)
- **Trend**: Mini‑Sparkline für 7 Tage (Touren, km, Fahrzeit)
- **Qualität**: % Routen mit echter OSRM‑Geometrie vs. Haversine‑Fallback
- **Zeitbox-Indikator**: Wenn eine Tour „Zeitbox gesprengt“, dann **gesamte Route leicht rot unterlegt** (CSS‑Overlay, z.B. `rgba(255,0,0,.08)`) und Badge `ZEITBOX` in der Tourkarte.
- **Interaktion**: Read‑only; Klick auf „Mehr“ führt in Admin→Statistik & Archiv (sofern Rolle `admin`).

## Admin-Bereich (Tabs)
1. **Testboard**: manuelle/automatische Tests starten, Ergebnisse, Logs
2. **AI‑Test**: orchestrierte Testläufe, Findings & Vorschläge (aus dem bereits geplanten AI‑Test‑Orchestrator)
3. **Statistik & Archiv**:
   - Pfad: anzeigen/ändern (lokal/UNC), Schreibtest, Freiplatzanzeige
   - Auflistung Tagesarchive (yyyy‑mm‑dd.json.gz), Monatsrollups (yyyy‑mm.json.gz)
   - „Rollup erzeugen“, „Archiv prüfen“, „Export CSV/Parquet“
4. **Fenster & Docking**: Default‑Positionen, „Karte abdocken“, „Tourliste abdocken“, Reset‑Layout

---

# Abdockbare Panels (Vanilla JS)

- **Ziele**: Karte und Tourübersicht separat auf eigenen Monitoren.
- **Technik**: `window.open()` → `mapWindow` / `listWindow`.
- **Sync**: `BroadcastChannel('trafficapp')` + `postMessage` zur Feinsynchronisation (Selektion, Hover, Bounds, akt. Tour).
- **Lebenszyklus**: Heartbeat/„ping“ alle 5s; wenn Kindfenster geschlossen → UI‑Status zurück auf eingebettet.
- **Persistenz**: `localStorage` Flags: `{ mapDetached: true, listDetached: false }`.
- **Sicherheit**: gleiche Origin; kein Zugriff über Datei‑Protokoll; CSP erlaubt nur gleiche Origin.
- **Fallback**: Wenn Browser Directory Picker nicht unterstützt → Pfadverwaltung nur serverseitig.

**Minimal‑API (Frontend, Pseudocode):**
```js
// detach.js
export function detachMap() {
  const w = window.open('/ui/map.html', 'TrafficApp_Map', 'width=1280,height=900');
  setupChannel(w, 'map');
}
export function detachList() {
  const w = window.open('/ui/tourlist.html', 'TrafficApp_List', 'width=600,height=900');
  setupChannel(w, 'list');
}
```

---

# Datenmodell & Speicherung

- **Tagesartefakt**: `stats/YYYY/MM/DD/<date>.json.gz`
  ```json
  {
    "date": "2025-09-11",
    "tours": 29,
    "stops": 286,
    "distance_km_osrm": 412.4,
    "distance_km_haversine": 433.1,
    "drive_time_min": 612,
    "with_geometry": 27,
    "fallback_geometry": 2,
    "geocode_fails": 6,
    "timebox_breaches": 5
  }
  ```
- **Monatsrollup**: `stats/YYYY/MM/<month>.json.gz` (Aggregationen + 30‑Tage‑Sparklines)
- **Pfad-Konfiguration**: `config/settings.json` → `{ "stats_path": "C:\\Workflow\\TrafficApp\\stats" }`
- **UNC/Samba**: z.B. `\\\\NAS01\\TrafficApp\\stats` (siehe Sicherheit)
- **Größenschätzung**:
  - Pro Tour **~5–150 KB** (Stops, Metadaten, ggf. OSRM‑Polyline komprimiert)
  - **Tag (29 Touren)**: ~**0.2–4 MB**
  - **Monat (30 Tage)**: ~**6–120 MB**
  - Mit GZip realistisch darunter; Spielraum für Logs/Tests: Reserve **≤ 250 MB/Monat**

---

# API‑Erweiterungen (FastAPI)

- `GET  /api/stats/summary?range=today|7d|30d` → Kennzahlen + Sparklines
- `GET  /api/stats/days?from=YYYY-MM-DD&to=YYYY-MM-DD` → tabellarische Tagesdaten
- `GET  /api/stats/archive-path` → aktueller Pfad & Status
- `PUT  /api/stats/archive-path` → `{ path: string }` (validiert, Schreibprobe, ACL‑Check)
- `POST /api/stats/rollup` → Monatsdatei erzeugen/aktualisieren

**Schemata (Auszug):**
```py
class StatsSummary(BaseModel):
    range: Literal['today','7d','30d']
    tours: int
    stops: int
    distance_km_osrm: float
    drive_time_min: int
    with_geometry: int
    fallback_geometry: int
    geocode_fails: int
    timebox_breaches: int
    sparkline_tours: list[int]
    sparkline_km: list[float]
```

---

# Sicherheit (Code, Daten, Zugriffe)

## AuthN / AuthZ
- **JWT** (HS256) via `Authorization: Bearer <token>`; Token‑Scope (`viewer`, `admin`).
- **Login‑Flow**: `POST /api/auth/login` (lokal: Benutzer aus `users.json` mit PBKDF2‑Hash; Prod: optional AD/OIDC später).
- **Admin-Bereich**: nur Rolle `admin`; Hauptseite Statistik read‑only öffentlich **oder** `viewer` (konfigurierbar).

## Transport & Browser Security
- **HTTPS** (Prod, über Reverse Proxy, HSTS),
- **CSP**: `default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'`
- **XSS‑Schutz**: `textContent` statt `innerHTML`, Escape für dynamische Strings
- **CORS**: nur eigene Origin (z.B. `http://127.0.0.1:8111`)

## API‑Sicherheit
- **Rate Limit**: z.B. 60 req/min je IP (Starlette‑Middleware)
- **Input Validation**: Pydantic; strikte Typen
- **Pfad‑Sicherheit**: Keine Pfadtraversal (`..`), `os.path.commonpath` gegen erlaubte Root
- **Logging/Audit**: Anmeldeversuche, Pfadänderungen, Admin‑Aktionen mit Zeitstempel

## Geheimnisse & Schlüssel
- **.env** nur lokal, **nie** commiten; Prod: OS‑Keyring/Credential Manager
- **Datei‑Verschlüsselung (optional)**: Archiv‑Artefakte **AES‑GCM** (z.B. Fernet) → Schlüssel im Windows Credential Manager / Linux Secret Service; Rotation alle 180 Tage

## Dateien & Netzwerkpfade
- **UNC**: Verbindung mit Dienstkonto; Vorab‑Schreibtest; Fallback auf lokal
- **Backup**: einfacher `zip`‑Snapshot (täglich) + Prüfsummen (SHA‑256)

## Code‑Schutz
- **Minify/Obfuscate** Frontend‑JS (Build‑Step); **keine Secrets im Frontend**
- **Serverseitige Kontrolle**: sensible Routen nur mit JWT

---

# Tests (inkl. AI‑Test‑Orchestrator)

- **Unit**: `test_stats_api.py`, `test_security.py`, `test_store.py`
- **Integration**: Pfadwechsel (lokal→UNC), Rollup, GZip‑Artefakte, JWT‑Rollen
- **E2E (Headless)**: Abdocken/Andocken, BroadcastChannel‑Sync, Zeitbox‑Overlay bei Grenzverletzung
- **Leistung**: 1.000 Touren/Tag synthetisch → Lesezeit < 200 ms für Summary
- **Security**: Pfadtraversal, Rate‑Limit, JWT‑Manipulation, CSP-Verstöße (Report‑Only zuerst)
- **AI‑Test**: geplanter Runner führt o.g. Suiten aus, bewertet & empfiehlt Fixes (Scorecards im Admin‑Tab)

---

# Akzeptanzkriterien
- Statistik‑Box zeigt heute/7d/30d; Zahlen plausibel, Sparklines passen zu Daten
- Zeitbox‑Verletzung färbt Routen (leichte Rotunterlegung) + Badge
- Admin: Pfad ändern (lokal/UNC), Schreibtest & Freiplatz ok, Rollup erzeugbar
- Abdock‑Fenster bleiben synchron; Schließen setzt eingebetteten Zustand korrekt
- Auth: Admin‑Tab verborgen ohne Admin‑Token

---

# Implementierungs-Reihenfolge (Inkremente)
1. **API Stats** (`/api/stats/*`) + `services/stats_store.py` (lokal) ✔
2. **Statistik‑Box** auf Hauptseite (read‑only) + CSS‑Overlay für Zeitbox ✔
3. **Admin-Bereich** Grundgerüst + Pfadverwaltung + Rollup
4. **Abdockbare Panels** (Karte/Tourliste) + Sync
5. **Security‑Härtung** (JWT, CSP, Rate‑Limit)
6. **Tests** (Unit/Integration/E2E) + **AI‑Test**‑Hook

---

# Cursor‑Tasks (umsetzungsfertig)

- **Backend**
  - [ ] `routes/stats_api.py`: Endpunkte + Schemas
  - [ ] `services/stats_store.py`: Lesen/Schreiben/Rollup, GZip, Pfadprüfung
  - [ ] `services/security.py`: JWT, Rollen, Rate‑Limit, Pfad‑Sanitizer
  - [ ] `.env.example` erstellen; Secrets auslesen

- **Frontend**
  - [ ] `index.html` → `<section id="stats-box">` + Tiles + Sparklines
  - [ ] `js/main.js` → Fetch `/api/stats/summary`, Render, Fehlerfälle
  - [ ] `css/stats.css` → Tiles, Badges, Rot‑Overlay (`.route-timebox-breach`)
  - [ ] `admin.html` + `js/admin.js` → Tabs, Pfadpicker, Rollup‑Trigger, Testboard‑Hook
  - [ ] `js/detach.js` → Abdocken/Andocken, BroadcastChannel, Heartbeat

- **Tests**
  - [ ] `tests/test_stats_api.py`, `tests/test_security.py`, `tests/test_detach_e2e.py`
  - [ ] Seed‑Generator für synthetische Tagesdaten

---

# Ausblick (React später, optional)
- Component‑basierte Statistik, Virtualized Lists, Drag‑Docking mit Libraries (Golden‑Layout/React‑Mosaic). Jetzt **nicht** Teil des Scopes.

---

# Rollout & Doku
- Doku unter `docs/statistics-plan.md` (aus diesem Canvas exportieren)
- CHANGELOG‑Eintrag; Feature‑Flags: `STATS_ENABLED`, `DETACH_ENABLED`
- „Report‑Only“ CSP 1 Woche → danach strikt

