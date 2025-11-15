# Entscheidung & Ziel

**Kurzentscheidung:**
- **Statistik-Seite:** Jetzt **im bestehenden Vanilla-JS/HTML**-Frontend (\`/ui/\`, \`frontend/index.html\`). React ist eine **spätere Migration**; wir gestalten den Code migrationsfreundlich (ES-Module + Web Components, keine Framework-Bindung).
- **Abdockbare Panels:** Ebenfalls **in Vanilla JS** via \`window.open\` + \`BroadcastChannel\`/\`postMessage\`. Spätere Migration nach React ohne Bruch möglich, weil die Kommunikationsschicht framework-agnostisch ist.

**Warum so?**
- Schnell einsatzfähig ohne Rewrite.
- Minimale Risiken, keine Build-Tool-Kaskade.
- Saubere Schichten (API/Storage/UI) → späteres React nur als Austausch der View.

---

# Umfang (MVP)
1. **Statistik-Unterseite** (\`/ui/stats.html\`):
   - Tages-/Monatsübersichten (Touren, Stops, OSRM-km, Haversine-km, Dauer,
     Zeitbox-Über-/Unterschreitung, Sektoren).
   - **Auto-Speicherung** der Tagesdaten (JSON/GeoJSON) + **Monatszip** optional.
   - **Konfiguration**: Speicherpfad (lokal/UNC), Aufbewahrungsdauer, Autosave an/aus,
     Sampling von Geometrien.
   - **Pfad-Validierung** (Server), Test-Button mit Feedback.
2. **Abdockbare Panels**:
   - **Karte abdocken** (eigenes Fenster): \`/ui/map_dock.html\`.
   - **Tourübersicht abdocken**: \`/ui/tourlist_dock.html\`.
   - Live-Sync via \`BroadcastChannel('trafficapp')\`, Fallback \`postMessage\`.
3. **Zeitbox-Visualisierung**:
   - Wird die geplante Zeit **überschritten**, erhält die Route eine **rote, leicht transparente Unterlage** (Layer unter der Polyline) + Badge „Zeitbox +Xm“.
4. **Tests** (Backend + Frontend + E2E) – siehe Abschnitt *Tests*.

---

# Architektur & Dateien
```
frontend/
  index.html
  stats.html                 # Statistik-Unterseite (neu)
  map_dock.html              # Abdockbare Karte (neu)
  tourlist_dock.html         # Abdockbare Tourübersicht (neu)
  css/
    stats.css
    docking.css
  js/
    app_bus.js               # BroadcastChannel / postMessage Wrapper
    stats_page.js            # UI-Logik Statistikseite
    stats_charts.js          # Canvas-Diagramme (Chart.js optional)
    storage_client.js        # REST-Client für Stats/Config
    docking.js               # Abdock-/Andock-Logik
    overlays.js              # Zeitbox-Overlay unter der Polyline

backend/
  routes/
    routes.stats.py          # neue Endpoints (FastAPI)
  services/
    stats_store.py           # Schreiben/Lesen (Pfad, UNC, ZIP)
    stats_rollup.py          # Aggregationen
  config/
    stats_config.json        # persistente Konfiguration

scripts/
  compress_monthly.py        # optional: Monats-Archivierung als Zip
```

---

# REST-API (FastAPI)
**Konfiguration**
- `GET /api/stats/config` → `{root_path, retention_days, autosave, simplify_tolerance}
- `POST /api/stats/config` body: `{root_path, retention_days, autosave, simplify_tolerance}`
  - Validierung: Pfad existiert/erstellbar, Schreibrechte, UNC (\\\\server\\share) erlaubt,
    Windows-sichere Normalisierung (\`pathlib\`).

**Speichern/Auslesen**
- `POST /api/stats/save-day` body: `{date, tours: [...], meta: {...}}` → schreibt `root_path/YYYY/MM/DD/summary.json` (+ optional `routes.geojson`).
- `GET  /api/stats/tours?from=YYYY-MM-DD&to=YYYY-MM-DD` → aggregierte Kennzahlen.
- `GET  /api/stats/day/:date` → Rohdaten für einen Tag.
- `POST /api/stats/compact-month` `{year, month}` → erzeugt `YYYY-MM.zip` (optional).

**Datenmodell (Auszug)**
```json
{
  "date": "2025-09-11",
  "tours": [
    {
      "tour_id": "W-09:00-01",
      "sector": "W",
      "stops": 27,
      "distance_osrm_km": 124.8,
      "distance_haversine_km": 111.2,
      "duration_osrm_s": 16320,
      "timebox_planned_s": 14400,
      "timebox_delta_s": 1920,               
      "polyline": "enc...",                 
      "bbox": [minLon,minLat,maxLon,maxLat],
      "notes": ""
    }
  ],
  "meta": {
    "source": "TrafficApp",
    "version": "1.0",
    "created_at": "2025-11-06T20:40:00Z"
  }
}
```

---

# UI – Statistikseite (Vanilla)
**Abschnitte**
1) **Header**: Datumsbereich, Tour-Filter (Sektor, Fahrer, Depot), Export (CSV/JSON/ZIP), Autosave-Schalter.
2) **KPI-Row**: Gesamt-km (OSRM vs. Haversine), Dauer, Stopanzahl, Ø/Median, % Zeitbox-Verletzungen.
3) **Charts**: km/Tag, Dauer/Tag, Verletzungen/Tag, Sankey nach Sektor (optional).
4) **Tabelle**: Touren mit Sort/Filter, Link „Route anzeigen“.
5) **Konfiguration**: Speicherpfad (Textfeld), **„Pfad testen“** (Servercheck), Aufbewahrung, Toleranz Geometrievereinfachung.

**Barrierefrei & Migrationsfreundlich**
- Web Components (z. B. `<stats-kpi>`, `<stats-table>`), reine ES-Module, kein Build nötig.
- Später in React als Wrapper weiterverwendbar.

---

# Abdocken (Karte/Tourliste)
**Mechanik**
- Button „Abdocken“ öffnet `window.open(url, 'mapDock', '...')`.
- Hauptfenster ↔ Dock-Fenster über `BroadcastChannel('trafficapp')`:
  - Ereignisse: `ROUTE_UPDATE`, `SELECTION_CHANGE`, `CONFIG_UPDATE`, `PING/PONG`.
- Fallback für alte Browser: `postMessage` mit `window.opener`/`childWindow`.
- Beim Schließen sendet Dock `DOCK_CLOSED` → Hauptfenster zeigt Panel wieder an.

**Zeitbox-Overlay**
- Unterhalb der OSRM-Polyline wird – bei `timebox_delta_s > 0` – ein halbtransparenter **roter Polygon-Shadow** gerendert (Leaflet/MapLibre: eigener Layer, z-index < polyline).
- Badge am Routen-Header: „Zeitbox +12 min“.

---

# Speicher & Größenordnung
- **Pro Tour** (Polyline, Stats): ~5–25 KB.
- **Tag** (z. B. 25–35 Touren): **~200–800 KB**.
- **Monat** (30 Tage): **~6–24 MB** (ungezipt). Mit Zip ~40–60 % kleiner.

---

# Tests
**Backend (pytest)**
- `test_stats_config_paths.py`: Pfadvalidierung (lokal/UNC), Rechte, Erstellung.
- `test_stats_save_and_load.py`: Tag speichern → lesen → Hash vergleichen.
- `test_stats_rollup.py`: Aggregation (km, Dauer, Verletzungen).
- `test_osrm_geometry_passthrough.py`: Sicherstellen, dass Polyline ungeändert durchgereicht wird.

**Frontend (Jest + jsdom / Vitest)**
- `stats_page.test.js`: Parsing, Rendering KPIs, Filterlogik.
- `docking.test.js`: Kanal-Events, Fallback `postMessage`, Reattach-Verhalten.
- `overlays.test.js`: Zeitbox-Overlay-Entscheidung (delta > 0 → rot).

**E2E (Playwright)**
- `e2e_stats_flow.spec.ts`: Pfad setzen → Tagesdaten laden → Export.
- `e2e_docking.spec.ts`: Karte abdocken, Route auswählen, Sync prüfen.
- `e2e_timebox.spec.ts`: Tour mit Überschreitung → Overlay sichtbar.

---

# Migrationsleitplanke (optional später)
- React einführen, aber **API unverändert** lassen. Web Components können in React gehüllt werden.
- Docking-Kommunikation bleibt identisch, nur Rendering wechselt.

---

# Akzeptanzkriterien (MVP)
- Pfad kann per UI gesetzt und **serverseitig validiert** werden (lokal/UNC).
- Tagesdaten werden beim Klick „Speichern“ und (wenn aktiv) automatisch am Tagesende persistiert.
- Statistikseite zeigt aggregierte KPIs, Tabelle und mind. ein Diagramm.
- Abdocken/Andocken funktioniert; Fenster bleiben synchron.
- Zeitbox-Überschreitungen sind klar visuell erkennbar (rote Unterlage + Badge).
- Tests laufen grün (Backend, Unit-Frontend, E2E Smoke).

---

# To‑Dos für Cursor (nach Ordnern gruppiert)
**backend/**
- [ ] `routes.stats.py` mit Endpoints (GET/POST Config, Save/Load, Rollup).
- [ ] `stats_store.py` (Windows/UNC, Zip), `stats_rollup.py`.
- [ ] Tests: `test_stats_*`, `test_osrm_geometry_passthrough.py`.

**frontend/**
- [ ] `stats.html`, `stats.css`, `stats_page.js`, `stats_charts.js`.
- [ ] `app_bus.js` (BroadcastChannel Wrapper), `docking.js`, `overlays.js`.
- [ ] `map_dock.html`, `tourlist_dock.html`.
- [ ] Frontend-Tests (`*.test.js`).

**e2e/**
- [ ] Playwright Grundgerüst + drei Specs (siehe oben).

**docs/**
- [ ] `STATISTIK_MVP.md` (dieses Dokument) + Screenshots/Wireframes.

---

# Offene Punkte (können nach MVP kommen)
- Monats-Reports (PDF) mit Highlights.
- Fahrer-/Fahrzeug-IDs verknüpfen, Schichtkalender.
- Delta-Ansicht OSRM vs. Haversine pro Tour.
- Gröbere Geometrievereinfachung für Archiv (Douglas–Peucker).

