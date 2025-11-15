# 🤖 Cursor-Nutzung: Praktisches Beispiel

**Version:** 1.0  
**Stand:** 2025-11-15  
**Zweck:** Praktische Anleitung für die Nutzung der Standards mit Cursor

---

## 📋 **Aktuelle Datei-Struktur (FAMO TrafficApp)**

```
TrafficApp/
├── Global/                              ← 🌍 Für ALLE Projekte
│   ├── GLOBAL_STANDARDS.md              (= GLOBAL_DEV_STANDARDS.md)
│   ├── PROJEKT_TEMPLATE.md
│   └── README.md
│
├── PROJECT_PROFILE.md                   ← 📋 Für FAMO TrafficApp
│                                         (= PROJECT_PROFILE_TRAFFICAPP.md)
│
└── Regeln/                              ← 📘 Projekt-Standards
    ├── STANDARDS.md
    ├── STANDARDS_QUICK_REFERENCE.md
    ├── REGELN_AUDITS.md
    ├── AUDIT_CHECKLISTE.md
    ├── CURSOR_PROMPT_TEMPLATE.md
    ├── CURSOR_WORKFLOW.md
    ├── LESSONS_LOG.md
    └── README.md
```

---

## 🎯 **Praktische Nutzung mit Cursor**

### **Szenario 1: Bug-Fix (Standard)**

**Kopiere diesen Prompt in Cursor:**

```
🔍 CONTEXT LADEN:

1. Lies zuerst diese Dokumente komplett:
   - Global/GLOBAL_STANDARDS.md
   - PROJECT_PROFILE.md
   - Regeln/STANDARDS.md
   - Regeln/LESSONS_LOG.md

2. Prüfe: Gibt es in LESSONS_LOG.md einen ähnlichen Fehler?

---

🎯 AUFGABE:

Bug-Fix für: [BESCHREIBE DEN FEHLER]

Betroffene Dateien (vermutlich):
- Backend: backend/routes/[DATEI].py
- Frontend: frontend/[DATEI].js
- Weitere: [...]

---

📋 REGELN (aus GLOBAL_STANDARDS.md):

1. Multi-Layer-Pflicht: Backend + Frontend + DB + Infra
2. Kein Ghost-Refactoring
3. Nur explizit genannte Dateien ändern
4. Tests schreiben (min. 1 Regressionstest)
5. Health-Checks prüfen (vor Abschluss)

---

🔄 WORKFLOW (aus CURSOR_WORKFLOW.md):

1. Problem klarziehen (Logs, Screenshots)
2. Audit-ZIP vorbereiten (relevante Dateien)
3. Template wählen (CURSOR_PROMPT_TEMPLATE.md → #1)
4. Änderung einbauen
5. Tests & Health-Checks
6. LESSONS_LOG aktualisieren (falls neuer Fehlertyp)

---

📤 OUTPUT:

1. Root Cause Analysis
2. Code-Änderungen (Diffs)
3. Testplan (Backend + Frontend)
4. Health-Check-Befehle
5. LESSONS_LOG-Eintrag (falls relevant)

---

Los geht's!
```

---

### **Szenario 2: Sub-Routen-Generator Problem** ⚙️

**Kopiere diesen Prompt in Cursor:**

```
🔍 CONTEXT LADEN:

1. Lies zuerst:
   - Global/GLOBAL_STANDARDS.md
   - PROJECT_PROFILE.md (→ Abschnitt 3.2: Touren-Workflow)
   - Regeln/LESSONS_LOG.md (→ Eintrag #3: Sub-Routen-Generator)

2. Lies dann:
   - Regeln/CURSOR_PROMPT_TEMPLATE.md (→ Template #10)

---

🎯 AUFGABE:

Sub-Routen-Generator funktioniert nicht korrekt.

Symptome:
- [BESCHREIBE SYMPTOME, z.B. "Keine Sub-Touren generiert"]
- [Browser-Konsole Fehler, z.B. "TypeError: Cannot read property 'length'"]
- [Backend-Logs, z.B. "500 Internal Server Error"]

---

📋 SCOPE (aus PROJECT_PROFILE.md):

Backend:
- backend/routes/workflow_api.py (Sub-Routen-Generator Logik)
- backend/services/tour_optimizer.py
- backend/services/osrm_client.py

Frontend:
- frontend/index.html (Sub-Routen Button + Event Handler)
- frontend/js/tourplan.js (API-Call + Fehlerbehandlung)

---

⚠️ KRITISCHE PRÜFPUNKTE:

1. API-Kontrakt prüfen:
   - Backend sendet: { "sub_tours": [...], "status": "ok" }
   - Frontend erwartet: { "sub_tours": [...], "status": "ok" }
   - Stimmen die Felder überein?

2. Defensive Programmierung:
   - Backend: Sind alle Null-Checks vorhanden?
   - Frontend: Wird response.sub_tours vor .length geprüft?

3. OSRM-Integration:
   - Ist OSRM erreichbar? (Health-Check: /health/osrm)
   - Gibt es Timeout-Fehler in Logs?

---

🧪 TESTPLAN:

1. Backend-Tests:
   - pytest tests/backend/test_subroute_generator.py
   - curl -X POST http://localhost:8111/api/tour/optimize -H "Content-Type: application/json" -d '{"tour_id": "W-07.00", "stops": [...]}'

2. Frontend-Tests:
   - CSV hochladen (W-07.00)
   - Workflow starten
   - Sub-Routen generieren klicken
   - Browser-Konsole: Keine Fehler
   - Prüfe: Sub-Touren in Tour-Liste angezeigt

3. Health-Checks:
   - curl http://localhost:8111/health
   - curl http://localhost:8111/health/osrm

---

📤 OUTPUT:

1. Root Cause (was war kaputt?)
2. Code-Änderungen (Backend + Frontend)
3. API-Kontrakt-Dokumentation (falls geändert)
4. Testplan-Ergebnisse
5. LESSONS_LOG-Update (falls neues Pattern)

---

Los geht's!
```

---

### **Szenario 3: Routing-Audit (modular)** ⚙️

**Für gezielte Audits spezifischer Module**

**Kopiere diesen Prompt in Cursor:**

```
🔍 CONTEXT LADEN:

1. Lies zuerst:
   - Global/GLOBAL_STANDARDS.md
   - PROJECT_PROFILE.md (→ Abschnitt 3.2: Touren-Workflow)
   - Regeln/LESSONS_LOG.md (→ Eintrag #3)
   - Regeln/AUDIT_FLOW_ROUTING.md (KOMPLETTER AUDIT-FLOW!)

2. Halte dich an die 6 Audit-Regeln aus AUDIT_FLOW_ROUTING.md

---

🎯 SCOPE (NUR DIESE DATEIEN):

Backend:
- backend/services/osrm_client.py
- backend/routes/workflow_api.py
- backend/error_handlers.py

Frontend:
- frontend/index.html (Sub-Routen-Button)
- frontend/panel-map.html
- frontend/panel-tours.html

---

🔍 ZIELE:

1. Inkonsistenzen Backend ↔ Frontend
2. Fehler in Fehlerbehandlung (Timeout, 4xx, 5xx)
3. Potentielle 402/500-Quellen

---

⚠️ REGELN:

- ❌ KEIN Full-Repo-Refactor
- 📢 Änderungen als Diffs (mit Begründung)
- 🔄 Backend + Frontend gemeinsam
- 🧪 Tests vorschlagen (min. 2)

---

📤 OUTPUT:

1. Gescannter Scope
2. Gefundene Probleme (Schweregrad)
3. Änderungsvorschläge (Diffs + Begründung)
4. Tests (curl + UI-Schritte)
5. LESSONS_LOG-Update

Los!
```

**Siehe auch:** [`Regeln/AUDIT_FLOW_ROUTING.md`](../Regeln/AUDIT_FLOW_ROUTING.md) für vollständigen Flow

---

### **Szenario 4: Code-Review (umfassend)**

**Kopiere diesen Prompt in Cursor:**

```
🔍 CONTEXT LADEN:

1. Lies zuerst alle Standards:
   - Global/GLOBAL_STANDARDS.md
   - PROJECT_PROFILE.md
   - Regeln/STANDARDS.md
   - Regeln/REGELN_AUDITS.md
   - Regeln/AUDIT_CHECKLISTE.md

2. Lies bekannte Fehler:
   - Regeln/LESSONS_LOG.md (alle Einträge)

---

🎯 AUFGABE:

Umfassender Code-Review für:

SCOPE:
- Backend: [Liste der Dateien]
- Frontend: [Liste der Dateien]
- DB: [Schema-Änderungen?]
- Infra: [OSRM, Docker, etc.]

---

📋 CHECKLISTE (aus AUDIT_CHECKLISTE.md):

1. ✅ Kontext klären + Multi-Layer-Pflicht
2. ✅ Backend prüfen (Routes, Services, Validierung)
3. ✅ Frontend prüfen (API-Calls, Error-Handling, UI-Updates)
4. ✅ Datenbank & Schema (Indizes, Constraints)
5. ✅ Infrastruktur (OSRM, Health-Checks)
6. ✅ Tests (Unit, Integration, E2E)
7. ✅ Ergebnis-Dokumentation
8. ✅ Abschluss-Checkliste
9. ✅ Audit-Report (ZIP-Format)

---

⚠️ REGELN (aus REGELN_AUDITS.md):

1. Scope explizit machen
2. Ganzheitlich prüfen (Backend + Frontend + DB + Infra)
3. Keine isolierten Fixes
4. Tests sind Pflicht
5. Dokumentation aktualisieren
6. Sicherheit & Robustheit
7. Transparenz

---

🔍 PRÜFPUNKTE:

Backend:
- [ ] Pydantic-Validierung vorhanden?
- [ ] Error-Handling (Try-Catch)?
- [ ] Logging (strukturiert, JSON)?
- [ ] Defensive Programmierung (Null-Checks)?

Frontend:
- [ ] Fetch-API Error-Handling?
- [ ] JSON.parse in Try-Catch?
- [ ] UI-Updates nach API-Calls?
- [ ] Browser-Konsole: Keine Fehler?

DB:
- [ ] Indizes vorhanden?
- [ ] Foreign Keys definiert?
- [ ] Schema-Härtung bei Start?

Infra:
- [ ] Health-Checks funktionieren?
- [ ] OSRM erreichbar?
- [ ] Timeout-Handling?

---

📤 OUTPUT:

1. Audit-Report (Markdown)
2. Findings (Critical, High, Medium, Low)
3. Recommendations (Priorisiert)
4. Testplan
5. LESSONS_LOG-Updates (falls relevant)
6. Audit-ZIP (alle relevanten Dateien + README)

---

Los geht's!
```

---

## 🚀 **Für neue Projekte**

### **Schritt 1: Globale Standards kopieren**

```bash
# Neues Projekt erstellen
mkdir mein-neues-projekt
cd mein-neues-projekt
git init

# Globale Standards kopieren
cp -r /pfad/zu/trafficapp/Global ./Global
```

### **Schritt 2: Projektprofil erstellen**

**Datei:** `PROJECT_PROFILE.md`

```markdown
# 📋 Projektprofil – [PROJEKT-NAME]

**Version:** 1.0  
**Stand:** 2025-XX-XX  
**Zweck:** Projektspezifische Regeln und Kontext für Cursor AI

---

## 🛠️ 1. Technischer Überblick

* **Sprache:** [z.B. Python 3.11, TypeScript 5.0]
* **Backend:** [z.B. FastAPI, Express.js, Django]
* **Frontend:** [z.B. React, Vue, Vanilla JS]
* **Datenbank:** [z.B. PostgreSQL, MongoDB, SQLite]
* **Deployment:** [z.B. Docker, Kubernetes, Bare Metal]

---

## 🏗️ 2. Infrastruktur

[Beschreibe Infrastruktur, Netzwerk, externe Services]

---

## 📦 3. Wichtige Module / Bereiche

[Liste kritische Module und ihre Verantwortlichkeiten]

---

## 🔧 4. Projektspezifische Regeln für Cursor

[6-10 projektspezifische Regeln]

---

## 🔍 5. Typische Debug-Endpunkte

[Liste Debug-Endpoints]

---

## 🧪 6. Teststrategie

[Beschreibe Teststrategie]

---

## 📚 7. Verbindung zu den globalen Standards

Dieses Profil ergänzt die globalen Regeln aus:
- `Global/GLOBAL_STANDARDS.md`

---

## 🎯 Cursor-Arbeitsablauf

Bei Arbeiten an [PROJEKT-NAME] **immer**:
1. Zuerst: `PROJECT_PROFILE.md` lesen
2. Dann: `Global/GLOBAL_STANDARDS.md` lesen
3. Dann erst: Code anfassen
```

### **Schritt 3: Projekt-Standards anlegen**

```bash
mkdir -p Regeln
touch Regeln/STANDARDS.md
touch Regeln/LESSONS_LOG.md
touch Regeln/README.md
```

### **Schritt 4: Cursor-Prompt für neues Projekt**

```
🔍 CONTEXT LADEN:

1. Lies zuerst:
   - Global/GLOBAL_STANDARDS.md (universelle Regeln)
   - PROJECT_PROFILE.md (Projekt-Kontext)

2. Verstehe:
   - Technischer Stack
   - Infrastruktur
   - Projektspezifische Regeln

---

🎯 AUFGABE:

[BESCHREIBE AUFGABE]

---

📋 REGELN:

Aus GLOBAL_STANDARDS.md:
1. Dokumente zuerst lesen
2. Nie direkt auf main arbeiten
3. Kleine, fokussierte Änderungen
4. Kein Blind-Refactor
5. Immer Tests & Checks
6. Frontend + Backend gemeinsam
7. Kein Mockup-Regression

Aus PROJECT_PROFILE.md:
[Kopiere projektspezifische Regeln hier rein]

---

Los geht's!
```

---

## 📊 **Vergleich: Alt vs. Neu**

### **❌ Alt (ohne Standards):**

```
User: "Bitte behebe Bug X"
Cursor: *behebt Bug X, bricht dabei Frontend*
User: "Warum ist Frontend kaputt?"
Cursor: "Ups, hatte nur Backend angeschaut"
```

### **✅ Neu (mit Standards):**

```
User: "Bitte behebe Bug X. Lies zuerst:
       - Global/GLOBAL_STANDARDS.md
       - PROJECT_PROFILE.md
       - Regeln/LESSONS_LOG.md"

Cursor: *liest Standards*
        *sieht Multi-Layer-Pflicht*
        *prüft Backend + Frontend + DB*
        *findet Bug X + potentiellen Frontend-Bug*
        *behebt beide*
        *schreibt Tests*
        *prüft Health-Checks*
        *aktualisiert LESSONS_LOG*

User: "Perfekt! 🎉"
```

---

## 🎯 **Best Practices**

### **Immer tun:**

✅ Standards explizit im Prompt nennen  
✅ Lesereihenfolge vorgeben (Global → Projekt → Regeln)  
✅ LESSONS_LOG nach ähnlichen Fehlern durchsuchen lassen  
✅ Multi-Layer-Pflicht betonen  
✅ Health-Checks vor Abschluss fordern  

### **Nie tun:**

❌ Standards "stillschweigend voraussetzen"  
❌ Cursor ohne Kontext arbeiten lassen  
❌ Nur Backend oder nur Frontend nennen  
❌ LESSONS_LOG ignorieren  

---

## 📝 **Template für Cursor-Session**

**Kopiere dieses Template und fülle die Lücken:**

```
🔍 CONTEXT:
- Global/GLOBAL_STANDARDS.md
- PROJECT_PROFILE.md
- Regeln/LESSONS_LOG.md

🎯 AUFGABE:
[BESCHREIBUNG]

📋 SCOPE:
Backend: [DATEIEN]
Frontend: [DATEIEN]
DB: [SCHEMA?]
Infra: [OSRM, DOCKER, ETC.]

⚠️ REGELN:
- Multi-Layer-Pflicht
- Kein Ghost-Refactoring
- Tests schreiben
- Health-Checks prüfen

📤 OUTPUT:
1. Root Cause
2. Code-Änderungen
3. Tests
4. Health-Checks
5. LESSONS_LOG-Update

Los!
```

---

**Version:** 1.0  
**Stand:** 2025-11-15  

🤖 **Copy & Paste → Cursor → Profit!**

