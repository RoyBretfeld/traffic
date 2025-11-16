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

