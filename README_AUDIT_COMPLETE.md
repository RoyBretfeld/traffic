# Code-Audit-Paket – FAMO TrafficApp 3.0

**Stand:** 2025-11-16  
**Zweck:** Vollständiges Code-Audit für KI-Analyse (Backend + Frontend + DB + Infrastruktur)

---

## 1️⃣ Was dieses Paket ist

Dieses Dokument ist der **vollständige Leitfaden für strukturierte Audits**. Es ist so gebaut, dass **eine Audit-KI (z.B. Cursor)** ohne Ratespiel sofort loslegen kann.

Es beschreibt alles Wichtige – Inhalt, Lesereihenfolge, Hotspots, Workflows, Tests.

---

## 2️⃣ Inhalt (High-Level)

### ✅ Enthalten

* **Backend-Code**

  `backend/`, `routes/`, `services/`, `db/schema.py`, `start_server.py`

* **Frontend-Code**

  `frontend/` (HTML, JavaScript, CSS, Panel-Files, Sub-Routen-UI)

* **Datenbank & Schema**

  `db/` (Schema-Definitionen, Migrations, Helper)

* **Tests**

  `tests/` (Unit-/Integrationstests, Test-Hooks für neue Audits)

* **Scripts & Tools**

  `scripts/`, `tools/` (Audit-ZIP-Erstellung, Hilfstools)

* **Dokumentation & Regeln**

  `PROJECT_PROFILE.md` – Projektprofil

  `DOKUMENTATION.md` – Index aller wichtigen Docs

  `Global/GLOBAL_STANDARDS.md` – globale Standards

  `Regeln/STANDARDS.md` – Projekt-Standards

  `Regeln/STANDARDS_QUICK_REFERENCE.md` – Quick-Ref

  `Regeln/REGELN_AUDITS.md` – Audit-Regeln

  `Regeln/AUDIT_CHECKLISTE.md` – 9-Punkte-Checkliste

  `Regeln/AUDIT_FLOW_ROUTING.md` – Routing/OSRM-Audit

  `Regeln/CURSOR_PROMPT_TEMPLATE.md` – fertige Audit-Prompts

  `Regeln/LESSONS_LOG.md` – echte Fehler + Learnings

* **Konfiguration (ohne Secrets)**

  Sanitisiertes Config/ENV, Beispiel-Configs, OSRM-/DB-Settings

### ❌ Ausgeschlossen

* Virtuelle Umgebungen (`venv/`, `node_modules/`)

* Build-/Cache-Artefakte (`__pycache__/`, `dist/`, `build/`)

* Logs & temporäre Dateien (`logs/`, `*.log`, `*.tmp`)

* Reale Datenbanken (`*.sqlite3`, `*.db`)

* Git-Metadaten (`.git/`)

* Reale `.env` / API-Keys / Secrets

---

## 3️⃣ Einstieg für die Audit-KI

**⚠️ KRITISCH: Immer in dieser Reihenfolge lesen:**

1. **`Global/GLOBAL_STANDARDS.md`** – 7 Arbeitsregeln, Audit-Prozess, Safety

2. **`PROJECT_PROFILE.md`** – Stack, Infrastruktur, Module, Regeln

3. **`Regeln/STANDARDS_QUICK_REFERENCE.md`** – Schnellreferenz (kompakt)

4. **`Regeln/REGELN_AUDITS.md`** – 7 unverhandelbare Audit-Regeln

5. **`Regeln/AUDIT_CHECKLISTE.md`** – 9-Punkte-Checkliste

6. **`README_AUDIT_COMPLETE.md`** (dieses Dokument) – konkreter Audit-Kontext

**Für Routing- / Sub-Routen-Themen zusätzlich:**

* `Regeln/AUDIT_FLOW_ROUTING.md` – Routing/OSRM-Audit

* `Regeln/CURSOR_PROMPT_TEMPLATE.md` → Routing-/Sub-Routen-Templates

**Für bekannte Fehler:**

* `Regeln/LESSONS_LOG.md` – Lernbuch (bekannte Fehler)

---

## 4️⃣ Hotspots im Code (wo sich Audits lohnen)

### Touren-Workflow & Sub-Routen-Generator

* **Backend:**
  * `backend/routes/workflow_api.py` – CSV-Upload, Workflow-Orchestrierung
  * `backend/routes/tourplan_analysis.py` – Tourplan-Analyse
  * `backend/routes/tourplan_geofill.py` – Geocoding
  * `backend/services/osrm_client.py` – OSRM-Aufrufe
  * `backend/services/tour_optimizer.py` – Tour-Optimierung
  * `backend/parsers/tour_plan_parser.py` – CSV-Parsing, Synonym-Auflösung

* **Frontend:**
  * `frontend/index.html` – Haupt-UI (Tourenliste, Sub-Routen, Buttons)
  * `frontend/js/*.js` – Rendering, Event-Handler, API-Calls
  * Panel-Files: `frontend/panel-map.html`, `frontend/panel-tours.html`, `frontend/js/panel-ipc.js`

### OSRM / Routing / Infrastruktur

* `backend/services/osrm_client.py` – OSRM-Aufrufe, Timeouts, Fallbacks
* `backend/routes/health_check.py` / Health-Endpoints – OSRM-Status
* ENV/Config – `OSRM_BASE_URL`, Timeouts, Ports

### KI / LLM-Integration

* `backend/services/llm_optimizer.py`
* `backend/routes/ai_test.py`, `backend/routes/code_checker.py`

---

## 5️⃣ Wie ein Audit ideal abläuft (Kurz-Workflow)

Die Details stehen in `Regeln/REGELN_AUDITS.md` und `Regeln/AUDIT_CHECKLISTE.md`. Hier die Kurzform:

### 1. **Vorbereitung**

   * **Scope klar definieren** (z.B. „Sub-Routen-Generator zeigt keine Routen")
   * **Relevante Dateien einsammeln** (Backend + Frontend + ggf. DB/Infra)
   * **Audit-ZIP vorbereiten** (siehe `scripts/create_complete_audit_zip.py`)

### 2. **Analyse (ganzheitlich!)**

   * **Backend-Logik + Frontend-Rendering + API-Kontrakt zusammen prüfen**
   * **Besonders:** Response-Schema vs. Frontend-Erwartung (snake_case, Feldnamen)
   * **Multi-Layer-Pflicht:** Backend + Frontend + Config gemeinsam betrachten

### 3. **Diagnose**

   * **Root Cause klar benennen**, nicht nur Symptome
   * **API-Kontrakt prüfen:** Stimmen Endpunkte, Methoden, Payloads, Responses?

### 4. **Fix-Vorschläge mit Kontext**

   * Diffs pro Datei
   * Defensive Checks (Null-Checks, Array-Checks, Try/Except)
   * Verbesserte Logs (inkl. Korrelations-ID, Tour-IDs, etc.)

### 5. **Tests & Verifikation**

   * Mindestens **1 Backend-Test** + **1 Frontend-Test** vorschlagen
   * Ggf. konkrete `pytest`-/Browser-Commands nennen

### 6. **Dokumentation & ZIP**

   * Audit-Report nach `Regeln/REGELN_AUDITS.md` (Abschnitt 9)
   * Audit-ZIP nach Struktur aus `Regeln/REGELN_AUDITS.md` / `GLOBAL_STANDARDS.md`

---

## 6️⃣ Scope-Definition pro Audit

**⚠️ KRITISCH:** Für jedes Audit muss der Scope klar benannt werden.

**Beispiel: Sub-Routen / Routing / OSRM**

* **Backend:**
  * `backend/routes/workflow_api.py`
  * `backend/services/osrm_client.py`
  * `backend/services/tour_optimizer.py`

* **Frontend:**
  * `frontend/index.html`
  * `frontend/js/*.js`

* **Tests & Logs:**
  * Relevante Testdateien
  * Logauszüge / Fehlerberichte (500, 402, Sub-Routen-Fehler usw.)

**Cursor soll bei jedem Audit zuerst:**

1. Scope in Stichpunkten auflisten
2. Dateien nennen, die analysiert werden
3. Dann erst Änderungen vorschlagen

---

## 7️⃣ Pflicht: Backend UND Frontend prüfen

**⚠️ KRITISCH:** Cursor darf Routing-Themen niemals nur backendseitig betrachten.

**Immer prüfen:**

* Stimmen die API-Endpunkte (`/api/tour/route-details`, Sub-Routen-Endpunkte)?
* Passt der JSON-Response zur Frontend-Erwartung?
* Werden Fehler im Frontend korrekt angezeigt?
* Werden leere / fehlerhafte Antworten sauber behandelt?

**Besonders beim Sub-Routen-Generator:**

* Prüfen, ob die generierten Daten **vom Backend kommen**
* Prüfen, ob das Frontend sie **richtig rendert**
* Prüfen, ob die Route im UI **sichtbar** wird (Map-Layer, Marker, Linien)

---

## 8️⃣ Tests & Commands (Baseline)

Beispiele, die eine Audit-KI vorschlagen oder verwenden kann:

```bash
# Backend Syntax + Tests
python -m py_compile $(git ls-files "backend/*.py" "routes/*.py")
pytest -q

# Server lokal starten
python start_server.py
# Dann im Browser: http://localhost:8111/

# Health-Checks
curl http://localhost:8111/health
curl http://localhost:8111/health/osrm

# Optional: Audit-ZIP bauen
python scripts/create_complete_audit_zip.py
```

Frontend-Tests können z.B. als manuelle Schrittfolge beschrieben werden (Buttons klicken, erwartetes Verhalten, Konsole prüfen).

---

## 9️⃣ Sicherheit & Datenschutz

* **Keine echten Secrets in diesem Paket** (ENV ist sanitisiert).

* Audit-KI darf **niemals**:
  * reale API-Keys, Passwörter oder Tokens erzeugen oder loggen,
  * Konfiguration so umbauen, dass Secrets im Klartext im Code landen.

* Security-Fokus:
  * Input-Validierung (Backend + Frontend)
  * Fehler-Responses ohne Stacktrace nach außen
  * Logs ohne vollständige Adressen / personenbezogene Daten

Details: `Global/GLOBAL_STANDARDS.md` → Abschnitt „Security".

---

## 🔟 Erwartete Ausgabe einer Audit-KI

Ein gutes Audit auf Basis dieses Pakets sollte immer liefern:

1. **Executive Summary** – Was war kaputt, was wurde verbessert?
2. **Root Cause** – 1–3 Sätze, warum das Problem wirklich auftrat.
3. **Fix-Vorschläge** – Diffs pro Datei (Backend + Frontend, wenn betroffen).
4. **Tests** – Konkrete Vorschläge für Regressionstests.
5. **Lessons Learned** – Vorschlag für neuen Eintrag in `Regeln/LESSONS_LOG.md` (falls neuer Fehlertyp).
6. **Nächste Schritte** – Was als Nächstes gehärtet werden sollte.

---

## 1️⃣1️⃣ Meta / Version

**Projekt:** FAMO TrafficApp 3.0

**Stack:** Python 3.10, FastAPI, Vanilla JS, SQLite

**Infra:** Proxmox-LXC, Docker (OSRM), Leaflet

**Stand:** 2025-11-16

**Audit-Paket:** Wird automatisch von `scripts/create_complete_audit_zip.py` generiert

Aktuellen Gesamtstatus immer in `DOKUMENTATION.md` / `docs/STATUS_AKTUELL.md` nachlesen.

---

## 1️⃣2️⃣ Wirkung & Zielbild

Mit den aktuellen Dokumenten und Regeln existiert jetzt:

* Globale Standards (`Global/GLOBAL_STANDARDS.md`)
* Projekt-Standards (`Regeln/STANDARDS.md`)
* Audit-Regeln (`Regeln/REGELN_AUDITS.md`)
* Lessons-Log (`Regeln/LESSONS_LOG.md`)
* Vollständiges Audit-README (`README_AUDIT_COMPLETE.md` - dieses Dokument)

**Ziel:**

* Cursor arbeitet nachvollziehbar
* Audits sind reproduzierbar
* Änderungen sind eingegrenzt (kein Ghost-Refactor)
* Frontend + Backend werden gemeinsam betrachtet

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-16  
**Projekt:** FAMO TrafficApp 3.0

📚 **Vollständiger Leitfaden für strukturierte Code-Audits**

