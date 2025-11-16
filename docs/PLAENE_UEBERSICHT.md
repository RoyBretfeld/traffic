# Pläne-Übersicht für FAMO TrafficApp

**Letzte Aktualisierung:** 2025-01-10

Diese Datei listet alle aktiven Implementierungspläne auf, damit Cursor sie schnell finden kann.

---

## Aktive Pläne

### 1. Statistik-Box & Navigations-Admin-Plan
**Datei:** `docs/STATISTIK_NAV_ADMIN_PLAN.md`  
**Status:** Geplant  
**Erstellt:** 2025-01-10  
**Beschreibung:** Implementierung einer Statistik-Box auf der Hauptseite (Read-only), reduzierter Navigation (Hauptseite, ABI-Talks, Admin), separatem Admin-Bereich (Testboard, AI-Test, Statistik & Archiv, Fenster & Docking), abdockbaren Panels und Zeitbox-Visualisierung im Vanilla-JS/HTML-Frontend.

**Technologie:** Vanilla JS/HTML/CSS + FastAPI

---

### 2. Lizenzierungssystem
**Datei:** `docs/licensing-plan.md`  
**Status:** Geplant  
**Erstellt:** 2025-01-10  
**Beschreibung:** Sichere, verkaufbare Auslieferung mit Online-Lizenzprüfung, Offline-Fallback, Revocation, minimaler Telemetrie. Ed25519-basierte JWT-Lizenzen, Device-Fingerprinting, Grace-Period, Admin-UI für Lizenzverwaltung.

**Technologie:** FastAPI (Client & Server), Ed25519/EdDSA, PyInstaller, Authenticode

---

### 3. Umbau-Liste & React-Plan
**Datei:** `docs/UMBAU_REACT_PLAN.md`  
**Status:** Geplant  
**Erstellt:** 2025-01-10  
**Beschreibung:** Konkrete To-Dos für Umbau/Ergänzungen plus klarer Pfad für abdockbare Panels und (später) React-Migration. Alle Punkte sind Cursor-fähig mit klaren Acceptance-Kriterien.

**Technologie:** Vanilla JS/HTML/CSS (Phase 1), React (Phase 2, optional)

**Hauptkomponenten:**
- Hotfix & Stabilität (Blocker)
- Statistik – MVP jetzt (Hauptseite) + Detail im Admin
- AI-Testboard
- Abdockbare Panels (Phase 1: Vanilla JS, Phase 2: React optional)
- React-Migrationspfad (nur Planung)
- Sicherheit & Lizenzen
- Tests & Monitoring

**Todos:** C-001 bis C-012 (12 konkrete Aufgaben)

---

### 4. Deployment-, Update- & AI-Ops-Plan
**Datei:** `docs/DEPLOYMENT_AI_OPS_PLAN.md`  
**Status:** Geplant  
**Erstellt:** 2025-01-10  
**Beschreibung:** Reproduzierbare Installation (auch offline), klare Update-Strategie (manuell/LTS), plus KI-gestützte Überwachung & Alarmierung (E-Mail). Produktion stabil, Rollbacks jederzeit möglich.

**Technologie:** PyInstaller, NSIS, Windows-Dienst, SQLCipher (optional), SMTP

**Hauptkomponenten:**
- Paketierung & Installation (NSIS-Installer, Portable ZIP)
- Konfiguration & Geheimnisse (DPAPI, SQLCipher)
- Update-Strategie (LTS, manuell, Rollback)
- KI-gestützte Überwachung (AI-Ops mit E-Mail-Alerts)
- Tests & Smoke-Checks
- Sicherheit & Zugriff
- Lizenzierung
- Rollout-Prozess

**Todos:** Deployment-Scripts, AI-Healthcheck, Smoke-Tests, Installer-Build

---

### 5. Export & Live-Daten-Plan
**Datei:** `docs/EXPORT_LIVE_DATA_PLAN.md`  
**Status:** Geplant  
**Erstellt:** 2025-01-10  
**Beschreibung:** Die "letzten drei" Bausteine: Maps-Export (Google/Apple mit QR), Baustellen-Overlay (Autobahn API), Speedcams-Overlay (mit Legal-Guard, opt-in).

**Technologie:** Vanilla JS, QR-Code-Generierung, Overpass API, Autobahn API

**Hauptkomponenten:**
- Maps-Export (Google/Apple URLs + QR-Codes)
- Baustellen-Overlay (Live-Daten von Autobahn API)
- Speedcams-Overlay (OpenStreetMap, mit rechtlichem Hinweis § 23 StVO)

**Todos:** Export-Endpoints, QR-Generierung, Overlay-Layer, Legal-Guard

---

## Weitere relevante Pläne

### Multi-Monitor & Routen-Export
**Datei:** `docs/PLAN_MULTI_MONITOR_ROUTEN_EXPORT.md`  
**Status:** Geplant  
**Beschreibung:** Multi-Monitor-Support, manuelle Routen-Bearbeitung (Drag & Drop), Export zu Maps (Google Maps, GPX, QR-Code).

---

## Verwendung für Cursor

Wenn du einen Plan benötigst, verweise auf die entsprechende Datei:

```
Bitte lies den Plan in docs/STATISTIK_NAV_ADMIN_PLAN.md
```

oder

```
Bitte implementiere gemäß docs/licensing-plan.md
```

Cursor kann diese Dateien direkt aus dem Workspace lesen.

---

---

## Vollständiger Umbau-Plan (eingebettet)

<details>
<summary><strong>TrafficApp – Umbau-Liste & React-Plan (vollständig)</strong></summary>

# TrafficApp – Umbau-Liste & React-Plan

**Erstellt:** 2025-01-10  
**Status:** Geplant  
**Zweck:** Konkrete To-Dos für Umbau/Ergänzungen plus klarer Pfad für abdockbare Panels und (später) React-Migration

---

## TL;DR Entscheidungen

* **Frontend aktuell:** Vanilla JS/HTML/CSS bleibt. Code/Assets "auf Knopfdruck" = schnelle Bereitstellung, direkte Integration ins bestehende UI ohne Frameworkwechsel.
* **Abdockbare Panels:** **Phase 1 in Vanilla JS** (window.open + postMessage + persistentes Layout). **Phase 2 optional in React** (wenn Multi-Window/State komplex wird).
* **React-Migration:** **geplant, aber nicht sofort.** Start, sobald Abdocken/Layouts/State-Sharing oder Komponenten-Wiederverwendung die Komplexität rechtfertigen.

---

## Vollständiger Plan

Der vollständige Plan mit allen Details, Entscheidungen und Todos ist im Cursor-Plan-Tool gespeichert.

**Zugriff:** Der Plan ist über das Cursor-Plan-Tool verfügbar und enthält:

1. **Hotfix & Stabilität (Blocker)**
   - Endpoint-Fix + Startup-Health
   - OSRM-Geometrie End-to-End
   - SQLite-Härtung & Schema-Migration (mit präzisen Entscheidungen)
   - Encoding/Mojibake-Guard konsolidieren
   - Logging & PII

2. **Statistik – MVP jetzt (Hauptseite) + Detail im Admin**
   - Read-only Stats-Box
   - Admin-Stats-Detailseite
   - Datenmodell & Retention
   - Tests

3. **AI-Testboard**
   - Runner, Auswertung, Reports

4. **Abdockbare Panels**
   - Phase 1 (Vanilla JS)
   - Phase 2 (React, optional)

5. **React-Migrationspfad** (nur Planung)

6. **Sicherheit & Lizenzen**

7. **Tests & Monitoring**

8. **Dokumentation & Artefakte**

---

## Schema-Migration: Präzise Entscheidungen

### Schemastrategie: c) Beides
- Neues Referenz-Schema in `docs/database_schema.sql` + Migration-Script in `scripts/migrate_YYYYMMDD.py`
- Doku & Code sauber versioniert, keine Datenverluste

### Umgang mit bestehenden Daten: a) Automatische Migration
- Tabellen/Spalten automatisch gemappt (kunden → customers, touren → tours, …)
- Fallback: Bei PRAGMA integrity_check-Fehler → iterdump → Rekonstruktion (automatisiert)

### Aktualisierung im Code: c) Beides aktualisieren
- `db/schema.py` erhält neue Struktur (Python-DDL/SQL Builder + SCHEMA_VERSION)
- `docs/database_schema.sql` bleibt "Single Source of Truth" in SQL-Form
- Beide synchron halten (CI-Check)

### Einführung neuer Tabellen: c) Schrittweise
- **Phase 1:** Schema erstellen + schreiben in osrm_cache, lesen weiterhin wie bisher
- **Phase 2:** Backend auf routes/route_legs umstellen (nur Lesen), dann Schreiben aktivieren
- **Phase 3:** stats_* füllen (täglich/monatlich), Frontend-Statistik binden

---

## Konkrete Aufgaben für Cursor

### A. Migration & Schema
- `docs/database_schema.sql`: Neue Tabellen & Indizes ergänzen
- `db/schema.py`: Struktur spiegeln, SCHEMA_VERSION = 3 einführen
- `scripts/migrate_2025_11_06.py`: Backup, Integrity-Check, Migration in-place, Fallback bei Defekt
- Mapping: kunden → customers, touren → tours, touren_positionen → tour_stops
- CI-Check: Script vergleicht db/schema.py gegen docs/database_schema.sql

### B. Indizes (Performance)
- idx_tours_date, idx_stops_tour, idx_osrm_cache_key, idx_route_legs_route

### C. Schrittweiser Code-Umbau
- Phase 1: OSRM-Ergebnisse in osrm_cache persistieren
- Phase 2: route-details liest aus routes/route_legs
- Phase 3: Stats-Writer (tägliche/monatliche Aggregation)

### D. Tests
- test_migration.py, test_osrm_cache.py, test_routes_legs.py, test_stats.py

---

## Todos (C-001 bis C-012)

- **C-001** Endpoint-Fix + Startup-Health
- **C-002** OSRM-Parametrisierung + Polyline6-Decode im Frontend
- **C-003** Route/Geocode-Cache (TTL + Persist)
- **C-004** SQLite WAL/Integrity/Repair + Backup-Rotation + Schema-Migration
- **C-005** Mojibake-Sanitizer vereinheitlichen
- **C-006** Stats-Box (Hauptseite) + Aggregator + API
- **C-007** Admin/Stats Detailseite + Export + Pfad-Konfig
- **C-008** AI-Testboard + Runner + Reports
- **C-009** Abdocken Phase 1 (Vanilla) + Persistentes Layout
- **C-010** Security-Baseline (Secrets, Rollen, Logging-PII)
- **C-011** Lizenzprüfung (JWT) + Offline-Grace
- **C-012** Test-Suite (Unit/Integration/E2E) + CI-Scripts

---

## Implementierungsreihenfolge

1. **Phase 1 (Blocker):** Hotfixes (1.1-1.5) - Stabilität sicherstellen
2. **Phase 2 (MVP):** Statistik-Box (2.1) - Schneller Wert
3. **Phase 3 (Erweiterung):** Admin-Stats (2.2-2.4) - Vollständige Statistik
4. **Phase 4 (Features):** AI-Testboard (3) - Qualitätssicherung
5. **Phase 5 (UX):** Abdockbare Panels Phase 1 (4.1) - Multi-Monitor
6. **Phase 6 (Sicherheit):** Security & Lizenzen (6) - Produktionsreife
7. **Phase 7 (Qualität):** Tests & Monitoring (7) - Robustheit
8. **Phase 8 (Zukunft):** React-Migration (5) - Optional, wenn nötig

---

## Artefakte & Ablage

* **Docs:** `docs/ROADMAP.md`, `docs/SECURITY.md`, `docs/LICENSING.md`, `docs/STATS_SPEC.md`, `docs/AI_TESTBOARD.md`
* **Konfig:** `config/app.yaml` (Speicherpfad, Cache, Retention, Lizenz-Server-URL)
* **Skripte:** `scripts/smoke.ps1`, `scripts/e2e.ps1`, `scripts/repair_sqlite.py`

---

**Vollständiger Plan:** Verfügbar im Cursor-Plan-Tool mit allen Details, Dateien, Aufgaben und Acceptance-Kriterien.

</details>

---

## Vollständiger Deployment-Plan (eingebettet)

<details>
<summary><strong>Deployment-, Update- & AI-Ops-Plan (vollständig)</strong></summary>

# Deployment-, Update- & AI-Ops-Plan (TrafficApp)

**Erstellt:** 2025-01-10  
**Status:** Geplant  
**Ziel:** Reproduzierbare Installation (auch offline), klare Update-Strategie (manuell/LTS), plus KI-gestützte Überwachung & Alarmierung (E-Mail). Alles so, dass Produktion stabil bleibt und Rollbacks jederzeit möglich sind.

---

## 1) Rahmen & Annahmen

* Zielsysteme: **Windows 10/11 Pro** (x64), Single-Host, optional Netzwerkshare.
* Backend: Python + Uvicorn/FastAPI. Frontend: Vanilla JS/HTML (später optional React).
* Datenbank: SQLite (optional SQLCipher/SEE für Verschlüsselung).
* Routing: OSRM über externen Endpoint (z. B. `router.project-osrm.org` oder eigener OSRM-Host).
* Kein Auto-Update im Feld: **LTS-Releases** + **manuelle Updates** (nur bei Bedarf).

---

## 2) Paketierung & Installation

### 2.1 Artefakte

* **Backend-Bundle (EXE)** via PyInstaller (one-dir): `TrafficApp-<version>\backend\…`
* **Frontend statisch**: `TrafficApp-<version>\frontend\index.html` etc.
* **Konfigs**: `config\app.yaml`, `config\secrets.ini`, `.env` (Ports, OSRM-URL, Pfade, SMTP, Lizenz).
* **DB-Pfad**: `data\trafficapp.db` (per Config variabel; Netzwerkpfad möglich).

### 2.2 Installer-Varianten

* **NSIS-Installer** (empfohlen): Startmenü-Einträge, Desktop-Link, optional Dienstinstallation.
* **Portable ZIP** (für USB-Verteilung/offline): Entpacken & Start-Script ausführen.

### 2.3 Dienst/Autostart

* **Windows-Dienst** mittels NSSM/SC:
  * Dienstname: `FamoTrafficApp` → `python start_server.py` im App-Verzeichnis.
  * Log-Rotation (max Größe, 7 Tage).

### 2.4 Signierung & Integrität

* Optional **Code Signing** (Authenticode) für EXE + Hash-Datei (`SHA256SUMS.txt`).

---

## 3) Konfiguration & Geheimnisse

* `config/app.yaml` (öffentlich): Ports, Pfade, Feature-Flags, UI-Optionen.
* `config/secrets.ini` (sensibel): SMTP-Passwort, Lizenz-Token.
* **Verschlüsselung**:
  * Datenbank: **SQLCipher** (AES-256) oder Windows **DPAPI** für Secret-Storage.
  * Secrets nur im Dateisystem des Hosts, Zugriffsrechte (NTFS ACLs) einschränken.

---

## 4) Update-Strategie (LTS / manuell)

* **Kanal**: `stable-lts` (Quartal) + `hotfix` (nur kritische Bugs/Security).
* **Ablauf (manuell):**
  1. Backup: `trafficapp.db` → `backup\trafficapp_<date>.db.bak`.
  2. Installer/ZIP entpacken → In-Place Update.
  3. **Migration-Script** ausführen (`scripts\migrate_YYYYMMDD.py`).
  4. Smoke-Tests (siehe §7).
  5. Rollback-Pfad: Dienst stoppen → alte Version + Backup-DB wiederherstellen.
* **Kein Auto-Update in Produktion.** Admin entscheidet, wann ein Update sinnvoll ist.

---

## 5) Transfer/Verteilung

* **USB-Stick**: Portable ZIP + Prüfsumme, optional Offline-Lizenzdatei.
* **Netzwerkshare**: Freigabe `\\server\TrafficApp\releases\…` (Read-Only), lokaler Copy-Job zur Workstation.

---

## 6) KI-gestützte Überwachung (AI-Ops)

### 6.1 Ziele

* Frühwarnungen bei:
  * 404/5xx Häufungen (z. B. `/api/tour/route-details`).
  * OSRM-Timeouts/Geometrie-Fehlern.
  * DB-Integritätsproblemen (z. B. *database disk image is malformed*).
  * Performance-Regress (Latenz/CPU/RAM).

### 6.2 Komponenten

* **ai_healthcheck.py** (Windows-Aufgabenplanung jede 5–10 Minuten):
  * Parsen der Logs (`logs\app.log`, `logs\access.log`),
  * `PRAGMA quick_check`, DB-Größe/Fragmentierung,
  * Ping OSRM/Health-Endpoints,
  * Heuristiken + Regeln (Thresholds) → **Befund + Vorschlag** erzeugen.
* **Notifier**: E-Mail via SMTP.
  * `smtp.host`, `port`, `tls`, `user`, `pass`, `from`, `to[]`.
  * Betreff: `[TrafficApp][ALERT][<severity>] <short>`.
  * Body: Kontext (Ausschnitte aus Log), empfohlene Maßnahmen, Link zur Doku.
* **Schweregrade**: info, warn, error, critical.

### 6.3 Beispiel-Regeln

* `error_rate_5xx > 2% / 15min` ⇒ **warn**; `> 5%` ⇒ **error**.
* `route-details 404` > 10 in 10min ⇒ **warn** mit Checkliste (Router Reload, Routenregistrierung, Cache invalidieren).
* `PRAGMA integrity_check != 'ok'` ⇒ **critical** + automatisches Shadow-Backup.
* `OSRM latency p95 > 1.5s` 30min ⇒ **warn** (Provider-Check).

---

## 7) Tests & Smoke-Checks (nach Installation/Update)

* **Smoke** (Script `scripts\smoke_post_install.ps1`):
  * `GET /health/db` == OK
  * `GET /api/traffic/construction/bbox` → 200 + JSON
  * `POST /api/upload/csv` (Sample) → 200 + `DataFrame`-Log
  * `GET /api/tour/route-details?tour_id=demo` → 200 + Polyline vorhanden
* **AI-Ops Tests**:
  * künstliche 404/Timeouts erzeugen → E-Mail trifft ein, Betreff/Body korrekt.
  * DB-Backup & `integrity_check` → Ergebnis im Report.

---

## 8) Sicherheit & Zugriff

* **Admin-Bereich** abgesichert (Basic-Auth oder JWT, Rollen: user/admin).
* **TLS**: Lokales Zertifikat (self-signed) oder Reverse-Proxy (Caddy/Nginx) mit HTTPS.
* **PII-Minimierung**: Nur nötige Felder speichern; Log-Redaktion (keine vollständigen Adressen im Access-Log).
* **DB-Verschlüsselung** (optional): SQLCipher; Key aus DPAPI-geschützter Secret-Datei laden.

---

## 9) Lizenzierung (kurz umrissen)

* **Lizenz-Key** (JWT/Signatur) im Installer oder als Datei `license.lic`.
* **Prüfung offline** (Signatur/Claims) + optional Online-Verifikation beim ersten Start.
* Lizenz-Claim enthält: Edition, Ablaufdatum, Gerätelimit, Support-Kontakt.

---

## 10) Rollout-Prozess (Checkliste)

1. Version bauen (CI): Tests, Lint, Paket, Hashes.
2. NSIS-Installer + Portable ZIP erzeugen, signieren.
3. Release-Notes + Migrationshinweise generieren.
4. Staging-Install, Smoke-Tests, Freigabe.
5. Produktion: Backup → Installation/Update → Migration → Smoke → Abnahme.

---

## 11) Cursor-Tasks (To-Do-Blöcke)

* **/scripts/**
  * `ai_healthcheck.py` (Log-Scans, DB-Checks, OSRM-Ping, E-Mail Versand).
  * `migrate_YYYYMMDD.py` (Backup, Schema-Migration, Fallback-Rebuild via iterdump).
  * `smoke_post_install.ps1` (Health-/API-Checks).
* **/config/**
  * `app.example.yaml`, `secrets.example.ini` mit SMTP/Lizenz-Platzhaltern.
* **/installer/**
  * `TrafficApp.nsi` (NSIS-Script), `build_installer.ps1`.
* **/docs/**
  * `DEPLOYMENT.md` (Kurzleitfaden), `AI_OPS.md` (Regeln, Schwellwerte, Triage), `UPDATE_ROLLOUT.md`.

---

## 12) Offene Punkte (später)

* Zentralisiertes Monitoring (Prometheus/Grafana) optional.
* Eigener OSRM-Knoten für deterministische Performance.
* Spätere React-Migration: gleicher Plan gültig (Installer/AI-Ops bleiben).

---

**Vollständiger Plan:** Verfügbar im Cursor-Plan-Tool mit allen Details, Dateien, Aufgaben und Acceptance-Kriterien.

</details>

---

## Vollständiger Export & Live-Daten-Plan (eingebettet)

<details>
<summary><strong>Export & Live-Daten-Plan (vollständig)</strong></summary>

# Export & Live-Daten-Plan (TrafficApp)

**Erstellt:** 2025-01-10  
**Status:** Geplant  
**Zweck:** Die "letzten drei" Bausteine: Maps-Export, Baustellen-Overlay, Speedcams (mit Legal-Guard)

---

## 1) "An Fahrer schicken": Google-/Apple-Maps-Export

### Ziel
Aus einer (Unter-)Route klickbare Navigations-Links generieren und bequem aufs Handy bekommen.

### Backend

**Endpoints:**
- `GET /api/export/maps?tour_id=...&provider=google|apple&max_stops=20`
- `GET /api/export/maps/qr?...` (QR-Code PNG je Segment)

**Logik:**
- Wegpunkte aus DB (Subtour) → (lat,lon)-Liste
- In handliche Chunks teilen (z.B. 20 Stopps pro Link; Limit ist plattformabhängig, daher konfigurierbar)
- URLs bauen:
  - **Google:** `https://www.google.com/maps/dir/?api=1&origin=...&destination=...&waypoints=...&travelmode=driving`
  - **Apple:** `http://maps.apple.com/?saddr=...&daddr=...&dirflg=d`
- Rückgabe: `[{segment:1, url:"..."}, ...]`

**Optional:** QR-Code (PNG) je Segment

### Frontend

- In der Tourübersicht: Button "Export" → Auswahl Google / Apple / QR
- QR-Dialog je Segment; Copy-Link
- (Später) SMS/E-Mail

### (Später) SMS/E-Mail

- `POST /api/export/send-sms` (Twilio/SMTP via .env)
- Logging in `route_exports`

### Tests

- **Unit:** URL-Encoding, Chunking, ≤ max_stops
- **Integration:** `/api/export/maps` für 3 Beispiel-Touren
- **E2E:** QR scannen → Handy öffnet korrekte Route

---

## 2) Live-Daten: Baustellen & "Blitzer" (mit Legal-Guard)

### Baustellen (Autobahn)

**Quelle:** Offizielle Autobahn API (roadworks, closures). Cachen, dann auf der Karte als Overlay zeigen.

**Endpoints:**
- `GET /api/traffic/autobahn/bbox?...` (aus Cache)
- `POST /api/traffic/autobahn/refresh` (pull + persist)

### Speedcams ("Blitzer") – vorsichtig & optional

**Quelle:** OpenStreetMap (`highway=speed_camera`) über Overpass API; regelmäßig cachen.

**⚠️ Rechtlicher Hinweis (DE):**
Die Nutzung von Geräten/Apps zur Warnung während der Fahrt ist nach **§ 23 StVO unzulässig** (Geräte/Funktionen zur Anzeige von Verkehrsüberwachung). Gerichte bestätigen das (z. B. OLG-Rechtsprechung).

**Deshalb:**
- Feature **opt-in**, standardmäßig **aus**
- Klare Warnung im UI
- UI/Settings: Toggle "Speedcams (rechtlich heikel in DE)" + Hinweis
- Auto-Deaktivierung, wenn "Fahrmodus aktiv" gesetzt ist

### Tests

- Smoke-Fetch (Autobahn/Overpass) + Schema-Validierung
- Map-Overlay-Rendering bei 100/1000 Markern
- Toggle respektiert (DE-Legal-Mode an/aus)

---

## 3) Akzeptanzkriterien & Mini-Schema

### Akzeptanz

- Export erzeugt für jede Unterroute ≥1 funktionierende Link-/QR-Variante
- Baustellen erscheinen binnen ≤15 min nach Refresh im Overlay
- Speedcam-Overlay ist **off by default**; Einschalten zeigt Warn-Dialog

### DB (leichtgewichtig ergänzen)

```sql
CREATE TABLE IF NOT EXISTS route_exports (
    id INTEGER PRIMARY KEY,
    tour_id TEXT NOT NULL,
    segment_idx INTEGER NOT NULL,
    provider TEXT NOT NULL,  -- 'google' | 'apple'
    url TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS live_roadworks (
    id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,  -- 'autobahn_api'
    payload_json TEXT NOT NULL,
    geom TEXT,  -- GeoJSON oder BBox
    valid_to TEXT,
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS speed_cameras (
    osm_id TEXT PRIMARY KEY,
    lat REAL NOT NULL,
    lon REAL NOT NULL,
    meta_json TEXT,  -- direction, maxspeed, etc.
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

---

## 4) Tasks für Cursor (sofort startklar)

### Backend

- `routes/export_maps.py` – Endpoints `GET /api/export/maps`, `GET /api/export/maps/qr`
- `services/exporter.py` – URL-Builder (Google/Apple), Chunking
- `services/qr.py` – PNG-QR erzeugen
- `services/autobahn_client.py` – Pull + Cache
- `services/overpass_client.py` – Speedcams Pull + Cache
- Migrations-Snip für 3 Tabellen oben

### Frontend (Vanilla)

- `frontend/index.html` – Export-Button in Tourliste
- `frontend/js/export.js` – Modal, QR anzeigen, Copy-Link
- `frontend/js/overlays.js` – Layer "Baustellen/Speedcams" + Toggles + Warnhinweis

### Tests

- Pytests: `test_exporter_url.py`, `test_export_chunking.py`
- API-Tests: `/api/export/maps` (200, Links gültig)
- Overlay-Smoke: Mock-Payload → Marker-Count

---

## Kurzer Realitätscheck & Empfehlungen

### Waypoints-Limit
- Variiert je Plattform/Client – wir gehen defensiv mit `max_stops` (Default 20) und splitten automatisch

### Recht & Haftung (Speedcams)
- Feature ist hilfreich, in DE aber heikel
- **Default aus**, klarer Disclaimer im UI
- Admin-Schalter "Legal-Mode=DE" erzwingt OFF
- (Siehe § 23 StVO und gängige Auslegung)

### "Senden ans Handy"
- QR-Codes jetzt
- SMS/E-Mail später per .env aktivierbar

---

## Implementierungsreihenfolge

1. **Phase 1:** Maps-Export (Google/Apple URLs + QR)
2. **Phase 2:** Baustellen-Overlay (Autobahn API)
3. **Phase 3:** Speedcams-Overlay (mit Legal-Guard, opt-in)

---

**Vollständiger Plan:** Verfügbar im Cursor-Plan-Tool mit allen Details, Dateien, Aufgaben und Acceptance-Kriterien.

</details>

---

## Sync-Status

Alle Pläne sind in der Cloud synchronisiert:
- ✅ `docs/STATISTIK_NAV_ADMIN_PLAN.md`
- ✅ `docs/licensing-plan.md`
- ✅ `docs/UMBAU_REACT_PLAN.md`
- ✅ `docs/DEPLOYMENT_AI_OPS_PLAN.md`
- ✅ `docs/EXPORT_LIVE_DATA_PLAN.md`
- ✅ `docs/PLAENE_UEBERSICHT.md` (diese Datei)

Verfügbar auf:
- Lokal: `E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0\docs\`
- Cloud: `G:\Meine Ablage\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0\docs\`

