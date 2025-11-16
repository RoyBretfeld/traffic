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

