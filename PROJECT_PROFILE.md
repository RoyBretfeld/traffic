# 📋 Projektprofil – FAMO TrafficApp 3.0

**Version:** 1.2  
**Stand:** 2025-11-18  
**Zweck:** Projektspezifische Regeln und Kontext für Cursor AI

---

## 📖 Einleitung

Dieses Dokument beschreibt die **projektspezifischen Regeln** und den Kontext der **FAMO TrafficApp**. Es baut auf den globalen Standards aus `Global/GLOBAL_STANDARDS.md` auf.

**Für Cursor:** Lies zuerst dieses Profil, dann `Regeln/STANDARDS.md`, dann `Regeln/LESSONS_LOG.md`.

---

## 🛠️ 1. Technischer Überblick

### **Backend:**
- **Sprache:** Python 3.10
- **Framework:** FastAPI
- **Hauptmodul:** `backend/app.py`
- **Startskript:** `start_server.py` (Port: 8111)

### **Frontend:**
- **Framework:** Vanilla JavaScript (ES6+) + HTML/CSS
- **Hauptseite:** `frontend/index.html`
- **Admin-/Testseiten:**
  - `/ui/test-dashboard` (Test-Dashboard)
  - `/ui/tourplan-management` (Tourplan-Management)
  - `/ui/ai-test` (AI-Test)

### **Datenbank:**
- **Typ:** SQLite
- **Datei:** `data/traffic.db`
- **Schema-Definition:** `db/schema.py` + `docs/database_schema.sql`
- **Weitere DBs:** `data/customers.db`, `data/secrets.vault` (geplant), `data/monitoring.db` (geplant)

### **Routing:**
- **OSRM:** Primary (Docker Container)
- **Fallback:** Haversine-Distanz bei Timeout

### **KI-Funktionen:**
- LLM-Optimizer für Touren (OpenAI GPT-4o-mini)
- Code-Checker / KI-Verbesserungs-Job
- Audit-/Analyse-Endpunkte (`/api/audit/*`, `/api/code-checker/*`)

---

## 🏗️ 2. Infrastruktur & OSRM

### **2.1 Arbeitsumgebung (Proxmox)**

**OSRM läuft in Proxmox-LXC:**
- **Container-ID:** 101
- **Hostname:** `OSRM`
- **Netzwerk:**
  - Bridge: `vmbr0`
  - IP: `172.16.1.191` (DHCP)
  - OSRM-Port: `5011`

**Backend-Konfiguration:**
```bash
OSRM_BASE_URL=http://172.16.1.191:5011
```

---

### **2.2 Heim-/Entwicklungsumgebung**

**OSRM lokal per Docker:**
```bash
# Docker Desktop
OSRM_BASE_URL=http://127.0.0.1:5000

# Oder:
OSRM_BASE_URL=http://localhost:5011
```

**Wichtig:** Die Backend-Konfiguration muss die passende URL kennen (über `config.env` oder `.env.local`).

---

### **2.3 Health & Monitoring**

**Health-Endpoints:**
- `GET /health` - Einfache Liveness-Probe
- `GET /health/status` - Kombinierter Status (Server, DB, OSRM, Systemregeln)
- `GET /health/app` - Feature-Flags & Konfiguration
- `GET /health/db` - DB-Verbindung (SELECT 1)
- `GET /health/osrm` - OSRM-Erreichbarkeit + Latenz + Circuit-Breaker
- `GET /health/osrm/sample-route` - OSRM Polyline6-Test

**OSRM-Metriken:**
- `GET /api/osrm/metrics` - Metriken-Übersicht
- `GET /api/osrm/metrics/errors` - Fehler-Details
- `POST /api/osrm/metrics/reset` - Metriken zurücksetzen

**⚠️ Regel:** Jede Änderung an Routing/OSRM muss diese Endpoints im Testplan berücksichtigen.

---

## 📦 3. Wichtige Module / Bereiche

### **3.1 Geocoding & Geo-Fail-Handling**

**Services:**
- `backend/services/geocode.py` - Hauptlogik
- `backend/services/geo_validator.py` - Validierung
- `services/geocode_fill.py` - Geo-Fill
- `services/geocode_persist.py` - Persistierung

**Repositories:**
- `repositories/geo_repo.py`
- `repositories/geo_alias_repo.py`
- `repositories/geo_fail_repo.py`

**Tabellen:**
- `geo_cache` - Geocoding-Cache
- `geo_alias` - Aliase
- `geo_fail` - Fehlgeschlagene Geocodes (mit Retry-Logic)
- `manual_queue` - Manuelle Geocoding-Queue

**Besondere Härtung:**
- `geo_fail` enthält `next_attempt` + Index `idx_geo_fail_next_attempt`
- Schema wird beim Start geprüft/gehärtet (siehe Logs: `[SCHEMA] geo_fail Härtung angewendet`)

**Siehe:** `Regeln/LESSONS_LOG.md` → Eintrag #1 (Schema-Drift)

---

### **3.2 Touren-Workflow & Sub-Routen-Generator** ⚙️ **KRITISCH**

**Engine-Endpunkte:**
- `POST /api/tour/optimize` - Tour-Optimierung (Sub-Routen-Generator)
- `POST /api/llm/optimize` - LLM-Optimierung
- `POST /engine/tours/ingest` - Tour-Ingest
- `POST /engine/tours/sectorize` - Sektorisierung
- `POST /engine/tours/split` - Sub-Routen-Generator (Legacy)
- `POST /engine/tours/optimize` - Optimierung
- `POST /engine/tours/pirna/cluster` - Pirna-Clustering

**OSRM-Integration:**
- `GET/POST /api/tour/route-details` - Route-Details mit Geometrie
- Fallback auf Haversine bei OSRM-Timeout

**⚠️ Regel:** Bei Fehlern im Sub-Routen-Generator immer **Backend + Frontend** analysieren:

**Backend:**
- Request/Response (Pydantic-Validierung)
- Exceptions (Try-Catch)
- Logs (Trace-ID, Error-Details)

**Frontend:**
- Aufruf-URL (`/api/tour/optimize`)
- Payload (tour_id, stops, is_bar_tour)
- Fehlerbehandlung im JS (Try-Catch, JSON.parse)
- UI-Status (Progress-Bar, Error-Toast)

**Siehe:** `Regeln/LESSONS_LOG.md` → Eintrag #3 (Sub-Routen-Generator)

---

### **3.3 Statistik & Admin**

**Statistik-Endpunkte:**
- `GET /api/stats/overview` - Übersicht
- `GET /api/stats/daily` - Täglich
- `GET /api/stats/monthly` - Monatlich
- `GET /api/stats/export/csv` - CSV-Export
- `GET /api/stats/export/json` - JSON-Export

**Admin-/KI-Bereich:**
- `/admin/ki-improvements` - KI-Verbesserungen-UI
- `POST /api/ki-improvements/*` - KI-Verbesserungen-API
- `GET /api/tests/*` - Test-API
- `GET /ui/test-dashboard` - Test-Dashboard

**⚠️ Regel:** Statistik soll produktionsnah, aber ressourcenschonend sein. Keine unnötigen Vollscans bei jedem Request.

---

## 🔧 4. Projektspezifische Regeln für Cursor

Zusätzlich zu den globalen Standards (`Global/GLOBAL_STANDARDS.md`) gelten hier:

### **Regel 1: Keine Framework-Migration ohne Auftrag**

**Frontend bleibt Vanilla JS:**
- ❌ Kein Umbau auf React/Vue/Angular
- ❌ Kein SPA-Refactor
- ❌ Kein Build-Tool (Webpack/Vite) ohne Freigabe

**Erlaubt:**
- ✅ Vanilla JS verbessern (ES6+)
- ✅ Modularisierung (imports)
- ✅ Code aufräumen (Funktionen extrahieren)

**Es sei denn:** Eigenes Ticket/Plan-Dokument für Migration existiert.

---

### **Regel 2: Routing & Workflow nicht „schön umschreiben"**

**Vorhandene Logik nur gezielt fixen:**
- ✅ Bug-Fixes (500er, Timeouts, etc.)
- ✅ Defensive Checks hinzufügen
- ✅ Logging verbessern

**Verboten:**
- ❌ Komplettes Redesign der Workflow-Pipeline
- ❌ "Schöner" machen ohne konkreten Grund
- ❌ Architektur-Änderungen ohne Plan

**Motto:** "Fix what's broken, don't fix what works."

---

### **Regel 3: Sub-Routen-Generator ist kritisch** ⚙️

**Änderungen an `/api/tour/optimize` immer mit:**

**Testplan:**
- [ ] Bekannte Test-Tour aus CSV (z.B. W-07.00)
- [ ] Erwartete Anzahl Sub-Routen (z.B. 3-4 für 30 Stopps)
- [ ] Visuelle Kontrolle im Frontend (Karte + Tour-Liste)
- [ ] Browser-Konsole: Keine Fehler
- [ ] Backend-Logs: Keine Exceptions

**Backend-Tests:**
```bash
pytest tests/backend/test_subroute_generator.py
```

**Frontend-Tests:**
- CSV hochladen → Workflow starten → Sub-Routen generieren
- Prüfe: Sub-Touren in Tour-Liste angezeigt
- Prüfe: Karte zeigt alle Stopps

**Siehe:** `Regeln/CURSOR_PROMPT_TEMPLATE.md` → Template #10 (Sub-Routen-Generator Audit)

---

### **Regel 4: OSRM-Abhängigkeit immer explizit prüfen**

**Bei Routing-Fehlern zuerst Health-Checks:**

```bash
# 1. Basis-Check
curl http://localhost:8111/health

# 2. OSRM-Check
curl http://localhost:8111/health/osrm

# 3. Sample-Route
curl http://localhost:8111/health/osrm/sample-route
```

**Backend-Logs beachten:**
```
[OSRM] Client initialisiert: base_url=http://172.16.1.191:5011, available=True
[OSRM] Sample-Route erfolgreich: 13.7373,51.0504 -> 13.7283,51.0615 (1.2 km)
```

**Bei Problemen:**
- Prüfe OSRM-Container: `docker ps | grep osrm`
- Prüfe Netzwerk: `ping 172.16.1.191`
- Prüfe Logs: `docker logs osrm-backend`

---

### **Regel 5: Code-Checker / Hintergrundjob vorsichtig anfassen**

**Job:** `/api/code-improvement-job/*`

**KI soll NICHT:**
- ❌ Unkontrolliert große Codebereiche umschreiben
- ❌ Produktions-Code durch Demo-Code ersetzen
- ❌ Breaking Changes ohne Review

**Jede Änderung an diesem Job muss:**
- ✅ Klar begrenzen, welche Dateien analysiert werden
- ✅ Whitelist von erlaubten Dateien
- ✅ Dry-Run-Modus für Testing
- ✅ Human-Review vor Anwendung

---

### **Regel 6: Fehlerbilder dokumentieren**

**Wiederkehrende Fehler dokumentieren:**

**Fehlertypen:**
- 500er (Internal Server Error)
- 402 (Payment Required - Legacy)
- Routing-Fehler (OSRM-Timeout)
- Geocoding-Fails (Address nicht gefunden)

**Prozess:**
1. Audit-ZIP erstellen (`audits/zip/` oder `ZIP/`)
2. README im ZIP mit Problem/Fix/Tests
3. Eintrag in `Regeln/LESSONS_LOG.md`

**Siehe:** `Regeln/LESSONS_LOG.md` für Beispiele

---

## 🔍 5. Typische Debug-Endpunkte

Bei Problemen **zuerst diese Endpoints prüfen:**

### **Server-Status:**
```bash
# Lebt der Server?
curl http://localhost:8111/

# Health-Check
curl http://localhost:8111/health

# Kombinierter Status
curl http://localhost:8111/health/status
```

### **Routen-Übersicht:**
```bash
# Alle registrierten Routen
curl http://localhost:8111/_debug/routes
```

### **Geo-/Audit-Diagnose:**
```bash
# Audit-Status
curl http://localhost:8111/api/audit/status

# Geo-Audit
curl http://localhost:8111/api/audit/geo

# Geo-Statistik
curl http://localhost:8111/debug/geo/stats
```

### **Upload/Workflow:**
```bash
# Upload-Status
curl http://localhost:8111/api/upload/status

# Workflow-Status
curl http://localhost:8111/api/workflow/status
```

---

## 🧪 6. Teststrategie (Projektspezifisch)

Bei **jedem größeren Change:**

### **Schritt 1: Backend-Startlog prüfen**

```bash
python start_server.py
```

**Prüfe Logs:**
- ✅ DB-Härtung: Keine Fehler bei `geo_*` Tabellen
- ✅ OSRM-Client: Basis-URL korrekt, Sample-Route erfolgreich
- ✅ Health-Endpoints: Alle erreichbar
- ✅ Routen registriert: Keine 404er

**Kritische Log-Zeilen:**
```
[SCHEMA] geo_fail Härtung angewendet
[OSRM] Client initialisiert: base_url=http://172.16.1.191:5011, available=True
[OSRM] Sample-Route erfolgreich
```

---

### **Schritt 2: Workflows testen**

**1. CSV hochladen:**
```bash
# Via API
curl -X POST http://localhost:8111/api/upload/csv \
  -F "file=@tourplaene/test_tour.csv"

# Oder: Via UI
# http://localhost:8111/ → "CSV hochladen"
```

**2. Workflow starten:**
```bash
# Via API
curl -X POST http://localhost:8111/api/workflow/upload \
  -H "Content-Type: application/json" \
  -d '{"file_id": "abc123"}'

# Oder: Via UI
# http://localhost:8111/ → "Workflow starten"
```

**3. Prüfe:**
- [ ] Geocoding erfolgreich (keine Fehler in Logs)
- [ ] Sub-Routen generiert (3-4 Sub-Touren für W-07.00)
- [ ] Optimierung erfolgreich (Stopps sortiert)
- [ ] UI zeigt Touren korrekt an

---

### **Schritt 3: Frontend End-to-End**

**Hauptseite (`http://localhost:8111/`):**
- [ ] CSV-Upload funktioniert
- [ ] Workflow startet
- [ ] Touren werden angezeigt (Tour-Liste)
- [ ] Sub-Routen generieren funktioniert
- [ ] Karte zeigt alle Stopps
- [ ] Browser-Konsole: Keine Fehler

**Admin/Test-Seiten:**
- [ ] Test-Dashboard: `http://localhost:8111/ui/test-dashboard`
- [ ] Tourplan-Management: `http://localhost:8111/ui/tourplan-management`
- [ ] AI-Test: `http://localhost:8111/ui/ai-test`

---

### **Schritt 4: Statistik prüfen**

```bash
# API
curl http://localhost:8111/api/stats/overview

# UI (falls vorhanden)
# http://localhost:8111/ui/stats
```

**Prüfe:**
- [ ] Keine unnötigen Vollscans
- [ ] Response-Time <500ms
- [ ] Keine Exceptions in Logs

---

## 📚 7. Verbindung zu den globalen Standards

Dieses Profil **ergänzt** die globalen Regeln aus:

**Global (für alle Projekte):**
- `Global/GLOBAL_STANDARDS.md` - Universelle Regeln
- `Global/PROJEKT_TEMPLATE.md` - Quick-Start für neue Projekte

**Projekt-spezifisch (FAMO TrafficApp):**
- `Regeln/STANDARDS.md` - Vollständige Standards
- `Regeln/STANDARDS_QUICK_REFERENCE.md` - Schnellreferenz
- `Regeln/REGELN_AUDITS.md` - 7 Audit-Regeln
- `Regeln/AUDIT_CHECKLISTE.md` - 9-Punkte-Checkliste
- `Regeln/CURSOR_PROMPT_TEMPLATE.md` - 12 Templates
- `Regeln/CURSOR_WORKFLOW.md` - 6-Schritt-Prozess
- `Regeln/LESSONS_LOG.md` - Lernbuch (3 Einträge)

---

## 🎯 Cursor-Arbeitsablauf für FAMO TrafficApp

**Bei Arbeiten an der FAMO TrafficApp IMMER:**

1. ✅ **Zuerst:** Dieses Projektprofil lesen (`PROJECT_PROFILE.md`)
2. ✅ **Dann:** Globale Standards (`Global/GLOBAL_STANDARDS.md`)
3. ✅ **Dann:** Projekt-Standards (`Regeln/STANDARDS.md`)
4. ✅ **Dann:** Lessons Learned (`Regeln/LESSONS_LOG.md`)
5. ✅ **Dann:** Audit-Checkliste (`Regeln/AUDIT_CHECKLISTE.md`)
6. ✅ **Dann erst:** Code anfassen

**Template wählen:**
- Standard-Bug-Fix: `Regeln/CURSOR_PROMPT_TEMPLATE.md` → Template #1
- Sub-Routen-Generator: `Regeln/CURSOR_PROMPT_TEMPLATE.md` → Template #10

---

## ✅ 8. Checkliste für Bug-Fixes

```markdown
[ ] PROJECT_PROFILE.md gelesen
[ ] Global/GLOBAL_STANDARDS.md gelesen
[ ] Regeln/LESSONS_LOG.md auf ähnliche Fehler geprüft
[ ] Template gewählt (CURSOR_PROMPT_TEMPLATE.md)
[ ] Multi-Layer-Pflicht beachtet (Backend + Frontend + DB + Infra)
[ ] Audit-ZIP vorbereitet (falls größerer Fix)
[ ] Backend-Startlog geprüft (nach Änderung)
[ ] Health-Checks geprüft (/health, /health/osrm)
[ ] Frontend End-to-End getestet
[ ] Browser-Konsole: Keine Fehler
[ ] Dokumentation aktualisiert (falls nötig)
[ ] LESSONS_LOG aktualisiert (falls neuer Fehlertyp)
[ ] Commit mit Conventional Commit Message
```

---

## 🎉 Zusammenfassung

**Mit diesem Rüstzeug:**
- ✅ Alle Fehler werden gefunden (Multi-Layer-Pflicht)
- ✅ Aus jedem Fehler wird gelernt (LESSONS_LOG)
- ✅ Änderungen sind nachvollziehbar (Audit-ZIP)
- ✅ Reproduzierbar über Audits hinweg (Standards)
- ✅ Cursor arbeitet strukturiert (Templates + Workflow)

**Damit bleibt Version 3+ kontrollierbar, nachvollziehbar und stabil.**

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-16  
**Projekt:** FAMO TrafficApp 3.0

🚀 **Strukturiert. Nachvollziehbar. Fehlerfrei!**

