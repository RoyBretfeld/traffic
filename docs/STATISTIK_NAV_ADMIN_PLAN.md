# Statistik-Box & Navigations-Admin-Plan (Vanilla JS)

**Erstellt:** 2025-01-10  
**Status:** Geplant  
**Technologie:** Vanilla JS/HTML/CSS + FastAPI  
**Option:** B - Statistik als Read-only-Box auf Hauptseite + Admin-Bereich

---

## Übersicht

Implementierung einer vollständigen Statistik- und Navigationslösung im bestehenden Vanilla-JS/HTML-Frontend:
- **Reduzierte Navigation**: Hauptseite, ABI-Talks, Admin (gated)
- **Statistik-Box auf Hauptseite**: Read-only KPIs und Mini-Charts für alle Nutzer
- **Admin-Bereich**: Testboard, AI-Test, Statistik & Archiv, Fenster & Docking (nur für Admins)
- **Zeitbox-Visualisierung**: Rote Unterlegung der Route bei Überschreitung (CSS-Overlay)
- **Abdockbare Panels**: Karte und Tourübersicht via `window.open` + BroadcastChannel/postMessage
- **Backend-API**: Minimale Endpoints für Stats-Summary, Days, Archive-Path, Rollup
- **Sicherheit**: JWT-basierte Auth, CSP, Rate-Limiting, Pfad-Validierung

---

## Architektur-Entscheidungen

- **Frontend**: Vanilla JS/HTML mit Hash-Routing (`#/`, `#/abi`, `#/admin`)
- **Navigation**: Reduziert auf Hauptseite + ABI-Talks + Admin (nur sichtbar für Admins)
- **Statistik**: Read-only auf Hauptseite, keine separate Seite
- **Admin**: Separater Bereich mit Rollen-Guard (`GET /api/auth/me`)
- **Kommunikation**: BroadcastChannel mit postMessage-Fallback für Panel-Sync
- **Speicherung**: JSON-Dateien in hierarchischer Struktur (`YYYY/MM/DD/`) mit GZip-Kompression
- **Pfad-Support**: Lokale Pfade und UNC-Pfade (Windows-Netzwerkfreigaben)

---

## Backend-Implementierung

### 1. Datenmodelle (`backend/models/stats.py`)

Pydantic-Modelle:
- `StatsSummary`: Aggregierte KPIs (range: today|7d|30d, tours, stops, distance_km_osrm, drive_time_min, with_geometry, fallback_geometry, geocode_fails, timebox_breaches, sparkline_tours, sparkline_km)
- `TourDay`: Tagesartefakt (date, tours, stops, distance_km_osrm, distance_km_haversine, drive_time_min, with_geometry, fallback_geometry, geocode_fails, timebox_breaches)
- `StorageSettings`: Pfad-Konfiguration (stats_path)
- `ArchivePathPayload`: Pfad-Payload für PUT

### 2. Storage-Service (`backend/services/stats_store.py`)

- `get_base_path()`: Liest Pfad aus `config/settings.json` oder ENV `STATS_STORAGE_PATH`
- `set_base_path(path)`: Validiert und speichert Pfad in `config/settings.json`
- `save_day_snapshot(date, data)`: Speichert Tagesdaten als `YYYY/MM/DD/<date>.json.gz`
- `load_day_snapshot(date)`: Lädt Tagesdaten
- `validate_storage_path(path)`: Prüft Schreibrechte, UNC-Support, Pfadtraversal-Schutz
- `list_available_dates(from_date, to_date)`: Listet verfügbare Tage
- `create_month_rollup(year, month)`: Erstellt Monatsrollup `YYYY/MM/<month>.json.gz`
- `export_to_csv(from_date, to_date)`: Exportiert als CSV

### 3. Rollup-Service (`backend/services/stats_rollup.py`)

- `aggregate_tours(tours)`: Berechnet Gesamt-km, Dauer, Stopanzahl
- `calculate_timebox_violations(tours)`: Zählt Zeitbox-Überschreitungen
- `get_summary(range)`: Aggregiert KPIs für today/7d/30d + Sparklines
- `get_days(from_date, to_date)`: Tabellarische Tagesdaten

### 4. Security-Service (`backend/services/security.py`)

- `generate_jwt(user, roles)`: JWT-Token-Generierung (HS256)
- `verify_jwt(token)`: Token-Verifikation
- `check_role(token, required_role)`: Rollen-Check
- `validate_path(path)`: Pfad-Sanitizer (kein Traversal, erlaubte Root)
- `rate_limit_middleware`: Starlette-Middleware (60 req/min je IP)

### 5. API-Routen (`routes/stats_api.py`)

Endpoints:
- `GET /api/stats/summary?range=today|7d|30d` → Aggregierte KPIs + Sparklines
- `GET /api/stats/days?from=YYYY-MM-DD&to=YYYY-MM-DD` → Tabellarische Tagesdaten
- `GET /api/stats/archive-path` → Aktueller Pfad & Status
- `PUT /api/stats/archive-path` → Pfad setzen (mit Validierung, Schreibprobe)
- `POST /api/stats/rollup` → Monatsrollup erzeugen/aktualisieren

### 6. Auth-API (`routes/auth_api.py`)

Endpoints:
- `POST /api/auth/login` → Login (lokal: `users.json` mit PBKDF2-Hash)
- `GET /api/auth/me` → Aktueller Benutzer mit Rollen `{user, roles: ['viewer'|'admin']}`

### 7. UI-Admin-Route (`routes/ui_admin.py`)

- `GET /ui/admin` → Admin-HTML ausliefern (FastAPI StaticFiles)

### 8. App-Registrierung (`backend/app.py`)

- Importiere `routes.stats_api`, `routes.auth_api`, `routes.ui_admin`
- Registriere Router: `app.include_router(stats_api.router)`, etc.
- CSP-Middleware hinzufügen
- Rate-Limit-Middleware hinzufügen

---

## Frontend-Implementierung

### 1. Navigation & Routing (`frontend/js/main.js`)

- Hash-Router implementieren (`#/`, `#/abi`, `#/admin`)
- Navigation reduzieren: Hauptseite, ABI-Talks, Admin (nur sichtbar wenn `isAdmin == true`)
- Aktive Menüpunkt-Markierung
- Rollen-Check: `GET /api/auth/me` → `isAdmin` Flag

### 2. Hauptseite (`frontend/index.html`)

Erweitern um:
- **Statistik-Box-Section** (`<section id="stats-box">`):
  - KPI-Kacheln: Heute (Touren, Stopps, OSRM-km, Fahrzeit, Ø Stopps/Tour, Geocoding-Fails)
  - Trend: Mini-Sparkline für 7 Tage (Touren, km, Fahrzeit)
  - Qualität: % Routen mit echter OSRM-Geometrie vs. Haversine-Fallback
  - Fetch: `GET /api/stats/summary?range=today|7d|30d`
- **Zeitbox-Indikator**: 
  - Wenn Tour "Zeitbox gesprengt" → gesamte Route leicht rot unterlegt (CSS-Overlay `rgba(255,0,0,.08)`)
  - Badge `ZEITBOX` in der Tourkarte
- **Abdock-Buttons**: Für Karte und Tourübersicht

### 3. Statistik-JavaScript (`frontend/js/stats.summary.js`)

- `loadStatsSummary(range)`: Fetch `/api/stats/summary`
- `renderKPIs(data)`: Rendert KPI-Kacheln
- `renderSparklines(data)`: Rendert Mini-Charts (Canvas)
- `renderQualityIndicator(data)`: Zeigt OSRM vs. Haversine %

### 4. ABI-Talks (`frontend/abi.html` oder Hash-View)

- Feed-View mit Auto-Refresh (Intervall 30-60s, abbricht bei Tab-Hidden)
- Long-Polling oder Fetch mit ETag
- Kein State-Reset der App

### 5. Admin-Bereich (`frontend/admin.html`)

**Guard**: Vor Render prüfen `GET /api/auth/me` → Rolle `admin`. Sonst Redirect `/#/`

**Tabs**:
- **Testboard**: Buttons für definierte Checks, Ergebnis-Tabelle, Download Logs
- **AI-Test**: Ping/Smoke-Tests gegen LLM-Optimizer/Services, Konfig-Anzeige, manuelle Test-Prompts
- **Statistik & Archiv**:
  - Pfad: anzeigen/ändern (lokal/UNC), Schreibtest, Freiplatzanzeige
  - Auflistung Tagesarchive (`yyyy-mm-dd.json.gz`), Monatsrollups (`yyyy-mm.json.gz`)
  - "Rollup erzeugen", "Archiv prüfen", "Export CSV/Parquet"
- **Fenster & Docking**: Default-Positionen, "Karte abdocken", "Tourliste abdocken", Reset-Layout

### 6. Admin-JavaScript (`frontend/js/admin.js`)

- `initAdminTabs()`: Tab-Verwaltung
- `loadArchivePath()`: Pfad anzeigen
- `setArchivePath(path)`: Pfad setzen mit Validierung
- `triggerRollup()`: Monatsrollup erzeugen
- `exportArchive()``: Export CSV/Parquet
- `runTestboard()`: Test-Runner-Trigger

### 7. Abdockbare Panels (`frontend/js/detach.js`)

- `detachMap()`: Öffnet `/ui/map.html` in neuem Fenster
- `detachList()`: Öffnet `/ui/tourlist.html` in neuem Fenster
- `setupChannel(window, type)`: BroadcastChannel-Setup
- `syncWithDetached()`: Heartbeat alle 5s, Sync (Selektion, Hover, Bounds, akt. Tour)
- `handleDetachedClose()`: Wenn Kindfenster geschlossen → UI-Status zurück auf eingebettet
- `persistDetachState()`: `localStorage` Flags: `{ mapDetached: true, listDetached: false }`

### 8. Zeitbox-Overlay (`frontend/js/overlays.js`)

- `renderTimeboxOverlay(map, tour, polyline)`: Rote Unterlegung bei `timebox_breaches > 0`
- CSS-Overlay: `rgba(255,0,0,.08)` auf Leaflet-Layer
- Badge: `ZEITBOX +Xm` am Routen-Header

### 9. CSS (`frontend/css/`)

- `stats.css`: KPI-Kacheln, Sparklines, Badges, Rot-Overlay (`.route-timebox-breach`)
- `detach.css`: Minimal-Styling für Dock-Fenster
- `admin.css`: Admin-Dashboard-Styling

### 10. Abdockbare Panel-Seiten

- `frontend/map.html`: Eigenständige HTML-Seite für Karte
- `frontend/tourlist.html`: Eigenständige HTML-Seite für Tourliste
- Live-Sync via `BroadcastChannel('trafficapp')`, Fallback `postMessage`

---

## Datenmodell & Speicherung

### Tagesartefakt (`stats/YYYY/MM/DD/<date>.json.gz`)

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

### Monatsrollup (`stats/YYYY/MM/<month>.json.gz`)

Aggregationen + 30-Tage-Sparklines

### Pfad-Konfiguration (`config/settings.json`)

```json
{
  "stats_path": "C:\\Workflow\\TrafficApp\\stats"
}
```

### Größenordnung

- Pro Tour: ~5–150 KB (Stops, Metadaten, ggf. OSRM-Polyline komprimiert)
- Tag (29 Touren): ~0.2–4 MB
- Monat (30 Tage): ~6–120 MB
- Mit GZip realistisch darunter; Reserve ≤ 250 MB/Monat

---

## Sicherheit

### AuthN / AuthZ

- **JWT** (HS256) via `Authorization: Bearer <token>`
- Token-Scope (`viewer`, `admin`)
- Login-Flow: `POST /api/auth/login` (lokal: Benutzer aus `users.json` mit PBKDF2-Hash)

### Transport & Browser Security

- **HTTPS** (Prod, über Reverse Proxy, HSTS)
- **CSP**: `default-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none'`
- **XSS-Schutz**: `textContent` statt `innerHTML`, Escape für dynamische Strings
- **CORS**: nur eigene Origin

### API-Sicherheit

- **Rate Limit**: 60 req/min je IP (Starlette-Middleware)
- **Input Validation**: Pydantic; strikte Typen
- **Pfad-Sicherheit**: Keine Pfadtraversal (`..`), `os.path.commonpath` gegen erlaubte Root
- **Logging/Audit**: Anmeldeversuche, Pfadänderungen, Admin-Aktionen mit Zeitstempel

### Geheimnisse & Schlüssel

- **.env** nur lokal, **nie** commiten
- Prod: OS-Keyring/Credential Manager

---

## Tests

### Backend-Tests (`tests/test_stats_*.py`)

- `test_stats_api.py`: Endpoints (summary, days, archive-path, rollup)
- `test_security.py`: JWT, Rollen, Rate-Limit, Pfad-Sanitizer
- `test_store.py`: Lesen/Schreiben/Rollup, GZip-Artefakte, Pfadwechsel (lokal→UNC)

### Frontend-Tests (`tests/frontend/`)

- `stats.test.js`: KPI-Formatierung, Sparkline-Rendering
- `detach.test.js`: BroadcastChannel-Events, postMessage-Fallback, Heartbeat
- `overlays.test.js`: Zeitbox-Overlay-Entscheidung (timebox_breaches > 0)
- `admin.test.js`: Admin-Guard, Tab-Wechsel, Pfad-Validierung

### E2E-Tests (`tests/e2e/`)

- `e2e_navigation.spec.ts`: Navigation zwischen Seiten, Admin-Guard
- `e2e_stats_flow.spec.ts`: Statistik-Box lädt, KPIs korrekt, Sparklines rendern
- `e2e_detach.spec.ts`: Abdocken/Andocken, BroadcastChannel-Sync, Heartbeat
- `e2e_timebox.spec.ts`: Tour mit Überschreitung → Overlay sichtbar
- `e2e_admin.spec.ts`: Admin-Bereich zugänglich, Pfad-Änderung, Rollup, Export

### Leistung

- 1.000 Touren/Tag synthetisch → Lesezeit < 200 ms für Summary

### Security-Tests

- Pfadtraversal, Rate-Limit, JWT-Manipulation, CSP-Verstöße (Report-Only zuerst)

---

## Akzeptanzkriterien

- [ ] Statistik-Box zeigt heute/7d/30d; Zahlen plausibel, Sparklines passen zu Daten
- [ ] Zeitbox-Verletzung färbt Routen (leichte Rotunterlegung) + Badge
- [ ] Admin: Pfad ändern (lokal/UNC), Schreibtest & Freiplatz ok, Rollup erzeugbar
- [ ] Abdock-Fenster bleiben synchron; Schließen setzt eingebetteten Zustand korrekt
- [ ] Auth: Admin-Tab verborgen ohne Admin-Token
- [ ] Top-Nav zeigt nur Hauptseite & ABI-Talks (Admin erscheint bei Admin-Rolle)
- [ ] Statistik-Box rendert ohne Fehler und nutzt OSRM-km/zeit (nicht Haversine)
- [ ] Tests laufen grün (Backend, Frontend-Unit, E2E Smoke)

---

## Implementierungs-Reihenfolge (Inkremente)

1. **API Stats** (`/api/stats/*`) + `services/stats_store.py` (lokal) ✔
2. **Statistik-Box** auf Hauptseite (read-only) + CSS-Overlay für Zeitbox ✔
3. **Admin-Bereich** Grundgerüst + Pfadverwaltung + Rollup
4. **Abdockbare Panels** (Karte/Tourliste) + Sync
5. **Security-Härtung** (JWT, CSP, Rate-Limit)
6. **Tests** (Unit/Integration/E2E) + **AI-Test**-Hook

---

## Cursor-Tasks (umsetzungsfertig)

### Backend

- [ ] `routes/stats_api.py`: Endpunkte + Schemas
- [ ] `services/stats_store.py`: Lesen/Schreiben/Rollup, GZip, Pfadprüfung
- [ ] `services/stats_rollup.py`: Aggregationen, Sparklines
- [ ] `services/security.py`: JWT, Rollen, Rate-Limit, Pfad-Sanitizer
- [ ] `routes/auth_api.py`: Login, `/api/auth/me`
- [ ] `routes/ui_admin.py`: Admin-HTML ausliefern
- [ ] `backend/app.py`: Router registrieren, CSP, Rate-Limit-Middleware
- [ ] `.env.example` erstellen; Secrets auslesen

### Frontend

- [ ] `index.html` → `<section id="stats-box">` + Tiles + Sparklines
- [ ] `js/main.js` → Router, Navigation, Rollen-Check
- [ ] `js/stats.summary.js` → Fetch `/api/stats/summary`, Render, Fehlerfälle
- [ ] `css/stats.css` → Tiles, Badges, Rot-Overlay (`.route-timebox-breach`)
- [ ] `admin.html` + `js/admin.js` → Tabs, Pfadpicker, Rollup-Trigger, Testboard-Hook
- [ ] `js/detach.js` → Abdocken/Andocken, BroadcastChannel, Heartbeat
- [ ] `js/overlays.js` → Zeitbox-Overlay-Rendering
- [ ] `map.html` + `tourlist.html` → Abdockbare Panel-Seiten
- [ ] `css/detach.css` + `css/admin.css` → Styling

### Tests

- [ ] `tests/test_stats_api.py`, `tests/test_security.py`, `tests/test_store.py`
- [ ] `tests/frontend/stats.test.js`, `tests/frontend/detach.test.js`, `tests/frontend/overlays.test.js`, `tests/frontend/admin.test.js`
- [ ] `tests/e2e/e2e_navigation.spec.ts`, `tests/e2e/e2e_stats_flow.spec.ts`, `tests/e2e/e2e_detach.spec.ts`, `tests/e2e/e2e_timebox.spec.ts`, `tests/e2e/e2e_admin.spec.ts`
- [ ] Seed-Generator für synthetische Tagesdaten

---

## Rollout & Doku

- Doku unter `docs/STATISTIK_NAV_ADMIN_PLAN.md` (dieses Dokument)
- CHANGELOG-Eintrag
- Feature-Flags: `STATS_ENABLED`, `DETACH_ENABLED`
- "Report-Only" CSP 1 Woche → danach strikt

---

## Ausblick (React später, optional)

- Component-basierte Statistik, Virtualized Lists, Drag-Docking mit Libraries (Golden-Layout/React-Mosaic)
- Jetzt **nicht** Teil des Scopes

