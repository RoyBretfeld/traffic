# TrafficApp – Navigations- & Admin-Plan (Vanilla JS)

> **Kernentscheidung**
> - Die **Top-Navigation** enthält nur: **Hauptseite** und **ABI‑Talks**.
> - Ein separater **Admin‑Bereich** bündelt: **Testboard** und **AI‑Test** (wieder lauffähig machen).
> - Die **Statistik** ist **sichtbar auf der Hauptseite** (Read‑only für alle Nutzer), Administratives (Export/Retention/Pfade) liegt im Admin‑Bereich.
> - Umsetzung **jetzt in Vanilla JS/HTML/CSS**. React bleibt optionale Migration, deshalb strukturieren wir migrationsfreundlich.

---

## 1) Informationsarchitektur & Routen

**Öffentliche Routen**
- `/` → **Hauptseite**
  - Sektionen: *Workflow*, *Karte/Route*, *Tourübersicht*, **Statistik (Read‑only)**
- `/abi` → **ABI‑Talks** (kann live aktualisieren, ohne die App zu stören)

**Admin-Routen**
- `/admin` → **Admin-Dashboard** (geschützt)
  - Tabs:
    - **Testboard** (manuelle/automatisierte Tests aus UI)
    - **AI‑Test** (wieder in Betrieb nehmen; Health, Logs, Testaufrufe)
    - **Speicher/Export** (Statistik‑Export, Pfad/UNC‑Konfiguration)

**Interne Helfer/Pseudo‑Routen (Vanilla)**
- Hash‑Routing: `/#/`, `/#/abi`, `/#/admin` (Fallback, falls ohne echten Server‑Router)

---

## 2) Frontend – Umsetzung (Vanilla JS)

**2.1 Navigation (reduziert)**
- Links: **Hauptseite**, **ABI‑Talks**, **Admin** (nur sichtbar, wenn `isAdmin == true`).
- Markierung des aktiven Menüpunkts.

**2.2 Hauptseite Layout**
- Grid-Layout (CSS) mit flexiblen Panels (Karte, Tourübersicht, Workflow‑Box, **Statistik‑Box**).
- **Statistik‑Box**: kleine KPI‑Kacheln + Mini‑Charts (Canvas/Chart.js optional, ohne externe Abhängigkeiten möglich).
- **Zeitbox‑Regel**: Wird die Zeitbox „gesprengt“, unterlegen wir die **gesamte rote Route leicht rot** (CSS‑Overlay auf der Karten‑Canvas oder Leaflet‑Layer). Diese Sichtbarkeit bleibt auch auf der Hauptseite aktiv.

**2.3 ABI‑Talks**
- Einfache Liste/Feed mit Auto‑Refresh (Long‑Polling oder Fetch mit ETag). Kein State‑Reset der App.

**2.4 Admin‑Bereich (Vanilla, geschützt)**
- **Guard**: vor Render prüfen `GET /api/auth/me` → Rolle `admin`. Sonst Redirect `/#/`.
- **Tabs**: Testboard | AI‑Test | Speicher/Export.
  - *Testboard*: Buttons zum Ausführen definierter Checks (siehe Kapitel 5 & 7), Ergebnis‑Tabelle, Download Logs.
  - *AI‑Test*: Ping/Smoke‑Tests gegen LLM‑Optimizer/Services; Konfig‑Anzeige; manuelle Test‑Prompts.
  - *Speicher/Export*: Anzeige **aktueller Statistik‑Speicherpfad** (lokal/UNC), Button **Ändern**, Validierung (Erreichbarkeit, Schreibrechte), `Export Now`.

**2.5 Abdockbare Panels (bleibt kompatibel)**
- Weiterhin per `window.open` + `BroadcastChannel`/`postMessage` realisieren (Karte/Tourübersicht). Navigation ändert daran nichts.

---

## 3) Statistik auf der Hauptseite (Read‑only)

**Ziele**
- Sofortiger Überblick für alle: Tourenanzahl, gefahrene km (OSRM‑Geometrie), Zeitabweichungen (Zeitbox), Stopps, mittl. Stopp‑Dauer, Auslastung Fahrer.
- **Retention**: mind. **1 Monat** (rollierend). Export/Archiv über Admin steuerbar.

**Datenquellen**
- Fahrten/Routen (persistiert pro Tag/Tour → km/zeit aus OSRM‑Geometrie, nicht Haversine).
- Geocoding‑Erfolg/Miss, Fehlerraten.
- Zeitbox‑Events (‚gesprengt‘ true/false je Route + Dauer der Überschreitung).

**UI‑Elemente**
- KPI‑Kacheln (heute, Woche, Monat)
- Mini‑Charts (Linie/Balken) für tägliche km, Anzahl Touren, % gesprengte Zeitboxen.
- Download CSV (letzte 30 Tage) – Trigger über Admin, Anzeige Link auf Hauptseite optional.

**Speicherpfad/UNC (Admin)**
- Konfigurierbarer Basis‑Pfad, z.B. `C:\Workflow\TrafficApp\stats` oder `\\SERVER\Share\TrafficApp\stats`.
- UI‑Validierung: Existenz, Schreibtest (Temp‑Datei), Freigabe‑Fehler klar anzeigen.

---

## 4) Backend – Endpoints (minimal)

- `GET /api/stats/snapshot?range=day|week|month` → KPIs (aggregiert)
- `GET /api/stats/series?metric=km|tours|timebox_breaches&from=YYYY‑MM‑DD&to=YYYY‑MM‑DD` → Zeitreihen
- `GET /api/config/storage-path` / `PUT /api/config/storage-path` → Statistik‑Speicherpfad
- `POST /api/stats/export` → erzeugt CSV/ZIP im konfigurierten Pfad, liefert Dateinamen/Link zurück
- `GET /api/auth/me` → `{ user, roles: ['admin'|...] }`

> Hinweis: Der bestehende `/api/tour/route-details`‑Fix bleibt unabhängig davon Pflicht, damit Kilometer/Zeiten aus OSRM zuverlässig in die Statistik fließen.

---

## 5) Dateistruktur (Vanilla JS)

```
frontend/
  index.html               # Hauptseite inkl. Statistik-Section
  abi.html                 # (optional) oder per Hash-View in index.html
  admin.html               # Admin-Dashboard (oder Hash-View)
  css/
    app.css
    stats.css              # KPI/Charts/Overlays
  js/
    app.js                 # Router (hash), nav, role-check
    stats.js               # Fetch & Render KPIs/Series
    charts.js              # Simple Chart-Helper (Canvas)
    admin.js               # Tabs: Testboard, AI-Test, Speicher
    docking.js             # Abdockbare Panels (window.open + BroadcastChannel)
```

---

## 6) Sicherheit & Rollen
- **Admin‑Link** nur rendern, wenn `roles.includes('admin')`.
- Admin‑Routen serverseitig absichern (401/403 ohne Rolle).
- Speicherkonfiguration/Export **nur** für Admin.

---

## 7) Telemetrie & Logging
- Frontend: `console.warn/error` → optional POST `/api/client-log` (Sampling), um UI‑Fehler bei Statistik‑Fetch sichtbar zu machen.
- Backend: Logs mit Event‑IDs für `stats.export`, `stats.snapshot`, `storage-path.write`.

---

## 8) Tests (möglichst ohne React; Jest optional, sonst reine Browser‑Tests via Playwright/Cypress)

**Unit (JS, Kopfzeile)**
- `stats.formatKpi(data)` formatiert Zahlen, Zeitspannen.
- `charts.renderLine(canvas, series)` rendert ohne Exceptions.
- `timebox.overlay(route, breach)` setzt korrektes CSS‑Overlay.

**Integration (Backend‑Mocks)**
- `GET /api/stats/snapshot` → korrektes Merge/Render in KPI‑Kacheln.
- `PUT /api/config/storage-path` (UNC) → Validierungsfehler/Erfolg.

**E2E**
- Navigation: `/` → `/#/admin` (ohne Admin) blockiert, mit Admin erlaubt.
- Statistik lädt automatisch (Spinner → Kacheln).
- Export im Admin → erzeugt Datei, Link sichtbar.

**Manuelle Checks**
- Zeitbox „gesprengt“ → rote Unterlegung der Route auf Karte sichtbar.
- Abdocken Karte/Tourübersicht → Live‑Sync via BroadcastChannel.

---

## 9) Rollout & Feature‑Flags
- Flag `FEATURE_STATS_HOME=true` → Statistik auf Hauptseite aktivieren.
- Flag `FEATURE_ADMIN_AREA=true` → Admin-Dashboard sichtbar.
- Fallback: Bei API‑Fehlern Platzhalter/„—“ anzeigen, App bleibt nutzbar.

---

## 10) Aufgabenliste für Cursor (To‑Dos)

**Navigation & Routing**
- [ ] Navbar auf **Hauptseite + ABI‑Talks + (Admin, gated)** reduzieren.
- [ ] Hash‑Router implementieren (`#/`, `#/abi`, `#/admin`).

**Hauptseite (Statistik-Box)**
- [ ] KPI‑Kacheln (heute/woche/monat) + Mini‑Charts.
- [ ] Fetch: `GET /api/stats/snapshot`, `GET /api/stats/series`.
- [ ] Zeitbox‑Overlay mit leichter roter Unterlegung der Route bei Überschreitung.

**ABI‑Talks**
- [ ] Feed‑View mit Auto‑Refresh (Intervall 30–60s; abbruch auf Tab‑Hidden).

**Admin‑Bereich**
- [ ] Guard: `GET /api/auth/me` + Redirect.
- [ ] Tabs: **Testboard**, **AI‑Test**, **Speicher/Export**.
- [ ] `PUT /api/config/storage-path` UI mit Validierung (UNC/lokal) & Schreibtest.
- [ ] `POST /api/stats/export` Button + Ergebnisanzeige.

**Backend‑Arbeit (Minimal für Statistik)**
- [ ] Endpoints aus Kapitel 4 implementieren.
- [ ] `route-details` 404‑Fix finalisieren (für echte km/zeit).

**Tests**
- [ ] Unit‑Tests JS (KPI, Charts, Overlay).
- [ ] Integration (Mocks) + E2E Flows (Guest/Admin).

**Dokumentation**
- [ ] `docs/NAV_ADMIN_STATS_PLAN.md` erzeugen.
- [ ] README‑Abschnitt „Navigation & Admin“ aktualisieren.

---

## 11) Akzeptanzkriterien (DoD)
- Top‑Nav zeigt **nur** Hauptseite & ABI‑Talks (Admin erscheint bei Admin‑Rolle).
- Statistik‑Box rendert **ohne Fehler** und nutzt **OSRM‑km/zeit** (nicht Haversine).
- Zeitbox‑Verletzung erzeugt **rote Unterlegung** der gesamten roten Route.
- Admin kann Speicherpfad (lokal/UNC) setzen, Testen und Export auslösen.
- E2E: Gäste sehen Admin nicht / werden beim Aufruf von `/#/admin` sicher blockiert.
- Dokumentation im `docs/` liegt vor und beschreibt Verhalten, Endpoints, Tests.

