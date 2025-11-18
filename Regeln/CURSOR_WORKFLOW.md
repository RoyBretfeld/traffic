# Cursor Workflow – Grundpfeiler & fester Prozess

**Version:** 1.0  
**Stand:** 2025-11-14  
**Projekt:** FAMO TrafficApp 3.0

---

Dieser Leitfaden beschreibt, wie mit Cursor an der FAMO TrafficApp gearbeitet wird. Ziel: reproduzierbare, nachvollziehbare, möglichst fehlerarme Änderungen.

---

## 1. Ziele

- **Stabilität**: Backend + Frontend müssen nach jeder Änderung lauffähig sein.
- **Nachvollziehbarkeit**: Jede größere Änderung hat ein Audit-ZIP und eine kurze Begründung.
- **Ganzheitlich**: Cursor betrachtet Backend (Python), Frontend (JS/HTML/CSS) und Konfiguration gemeinsam.
- **Lernend**: Aus jedem größeren Problem entsteht eine Regel oder ein Eintrag im Lessons-Log.

---

## 2. Zentrale Dateien (müssen gepflegt werden)

Alle zentralen Regeln und Standards befinden sich im **`Regeln/`-Ordner**:

```
Regeln/
├── STANDARDS.md                      ⭐ Vollständige Projekt-Standards
├── STANDARDS_QUICK_REFERENCE.md      🚀 Kompakte Schnellreferenz
├── REGELN_AUDITS.md                  🔍 7 unverhandelbare Audit-Regeln
├── AUDIT_CHECKLISTE.md               ✅ 9-Punkte-Checkliste
├── CURSOR_PROMPT_TEMPLATE.md         🤖 12 fertige Templates
├── LESSONS_LOG.md                    📝 Lernbuch für kritische Fehler
└── CURSOR_WORKFLOW.md                🔄 Dieser Workflow-Guide
```

**⚠️ Wichtig:** Diese Dateien sind **Teil des Systems**, nicht nur Doku. Änderungen an ihnen sind genauso ernst zu nehmen wie Code-Änderungen.

---

## 3. Standard-Ablauf für Cursor bei Audits

**⚠️ KRITISCH: Lesereihenfolge für Cursor (Pflicht):**

1. `Global/GLOBAL_STANDARDS.md`
2. `PROJECT_PROFILE.md`
3. `Regeln/STANDARDS.md`
4. `Regeln/STANDARDS_QUICK_REFERENCE.md`
5. `Regeln/REGELN_AUDITS.md`
6. `Regeln/AUDIT_CHECKLISTE.md`
7. `README_AUDIT_COMPLETE.md` (konkreter Audit-Kontext)

**Cursor soll diese Reihenfolge explizit im Prompt erwähnt bekommen.**

### Scope-Definition pro Audit

Für jedes Audit muss Cursor den Scope klar benennen, z.B.:

**Beispiel: Sub-Routen / Routing / OSRM**

* **Backend:**
  * `backend/routes/...`
  * `backend/services/...`
  * `backend/engine/...`

* **Frontend:**
  * `frontend/index.html`
  * `frontend/js/...`

* **Tests & Logs:**
  * Relevante Testdateien
  * Logauszüge / Fehlerberichte (500, 402, Sub-Routen-Fehler usw.)

**Cursor soll bei jedem Audit zuerst:**

1. Scope in Stichpunkten auflisten
2. Dateien nennen, die analysiert werden
3. Dann erst Änderungen vorschlagen

### Pflicht: Backend UND Frontend prüfen

Cursor darf Routing-Themen niemals nur backendseitig betrachten.

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

## 3. Feste Regeln für Code-Audits mit Cursor

### 1. **Audit-ZIP Pflicht**

Vor größeren Änderungen wird ein ZIP erzeugt, z.B. in `ZIP/` oder `audit_zips/`.

**Enthalten sein müssen:**
- Betroffene Python-Module (`backend/routes/*.py`, `backend/services/*.py`)
- Relevante JS/HTML/CSS-Dateien (`frontend/*.js`, `frontend/*.html`)
- Konfig (z.B. `config.env`, relevante `config/*.json`)
- Logs/Auszüge von Fehlermeldungen
- README im ZIP mit Problem-Beschreibung

**Naming-Convention:**
```
ZIP/AUDIT_YYYYMMDD_HHMMSS_<kurzer_name>.zip
```

**Beispiel:**
```
ZIP/AUDIT_20251114_143022_SubRouten_500_Error.zip
```

---

### 2. **Cursor bekommt immer denselben Rahmen**

**Startprompt basiert auf:** [`CURSOR_PROMPT_TEMPLATE.md`](CURSOR_PROMPT_TEMPLATE.md)

**Im Prompt steht klar:**
- **Projektkontext** (FAMO TrafficApp, Python/FastAPI, Vanilla JS)
- **Ziele** (Stabilität, keine Mockups, keine halbfertigen Refactors)
- **Verbotene Patterns** (keine „mal schnell alles umbauen"-Aktionen)
- **Erwartete Outputs** (saubere Diffs, Tests, Logging, keine toten Endpunkte)

**Empfohlene Templates:**
- **Standard-Bug-Fix:** Template #1 (Ganzheitliches Audit - Kugelsicher)
- **Sub-Routen-Generator:** Template #10 (speziell für dieses kritische Feature)

---

### 3. **Ganzheitlicher Blick (Multi-Layer-Pflicht)**

Cursor wird explizit angewiesen:

✅ **Backend prüfen:**
- FastAPI-Routes (`backend/routes/*.py`)
- Services (`backend/services/*.py`)
- DB-Schema (`db/schema.py`)
- Pydantic-Models (`backend/models/*.py`)

✅ **Frontend prüfen:**
- JavaScript (`frontend/*.js`, `frontend/js/*.js`)
- HTML-Templates (`frontend/*.html`)
- CSS (`frontend/css/*.css`)
- Fetch-Calls, Event-Handler, DOM-Manipulation

✅ **Glue-Code/Konfig prüfen:**
- URLs, Ports, ENV-Variablen
- OSRM-URL und Health-Checks
- API-Endpoints und Payloads

**Beispiel:** Bei Fehlern wie „Sub-Routen Generator geht nicht" muss Cursor **explizit** Backend + Frontend + Request-Flow analysieren.

➡️ **Siehe:** [`REGELN_AUDITS.md`](REGELN_AUDITS.md) → Multi-Layer-Pflicht

---

### 4. **Keine verdeckten Groß-Umbauten (Ghost-Refactor-Verbot)**

❌ **Verboten:**
- Massive Refactorings (z.B. auf React migrieren) ohne explizite Freigabe
- Projekt-weite Umbenennungen ohne separate Session
- Globale Suchen-Ersetzen-Aktionen
- Änderungen außerhalb des definierten Scopes

✅ **Erlaubt:**
- Bugs fixen
- Code härten (Defensive Programming)
- Logging/Fehlerbehandlung verbessern
- Tests hinzufügen

➡️ **Siehe:** [`STANDARDS_QUICK_REFERENCE.md`](STANDARDS_QUICK_REFERENCE.md) → Ghost-Refactor-Verbot

---

## 4. Standard-Workflow für Änderungen mit Cursor

### **Schritt 0 – Problem klarziehen**

**Kurze Beschreibung erstellen:**
- Was genau funktioniert nicht / soll verbessert werden?
- Wenn möglich: Screenshot + Log-Auszug + Beispiel-Request/Response

**Beispiel-Template:**
```markdown
## Problem
Sub-Routen-Generator wirft 500er Fehler bei großen Touren (>15 Stopps).

## Kontext
- Route: POST /api/optimize/sub-routes
- Eingabe: Tour mit 18 Stopps
- Error-Log: "KeyError: 'osrm_distance'" (siehe Anhang)
- Browser-Konsole: Network-Tab zeigt 500 Internal Server Error

## Gewünschtes Ziel
- Fehler beheben
- Defensive Validierung hinzufügen
- Logging verbessern
- Regressionstest schreiben
```

---

### **Schritt 1 – Audit-ZIP vorbereiten**

**Neues ZIP erzeugen:**
```
ZIP/AUDIT_20251114_143022_SubRouten_500.zip
```

**Relevante Dateien einpacken:**
- ✅ Python-Module:
  - `backend/routes/optimize_routes.py`
  - `backend/services/sub_route_generator.py`
  - `backend/services/osrm_client.py`
- ✅ Frontend-Dateien:
  - `frontend/js/optimize.js`
  - `frontend/panel-tours.html`
- ✅ Config:
  - `config.env` (Beispiel)
  - `config/app.yaml`
- ✅ Logs:
  - `error_log_snippet.txt`
- ✅ README im ZIP:
  - `README.md` mit Problem-Beschreibung (siehe Schritt 0)

---

### **Schritt 2 – Cursor-Prompt aufsetzen**

**1. Template öffnen:**
```
Regeln/CURSOR_PROMPT_TEMPLATE.md
```

**2. Template wählen:**
- **Standard-Bug-Fix:** Template #1 (Ganzheitliches Audit)
- **Sub-Routen-Generator:** Template #10 (speziell)

**3. Template anpassen:**

Folgendes für diese Session ergänzen:

```markdown
## Konkretes Problem
Sub-Routen-Generator 500er Fehler bei großen Touren (>15 Stopps).

## Betroffene Dateien
### Backend:
- backend/routes/optimize_routes.py
- backend/services/sub_route_generator.py
- backend/services/osrm_client.py

### Frontend:
- frontend/js/optimize.js
- frontend/panel-tours.html

### Config:
- config.env (OSRM_URL)

## Wichtige Hinweise
- ⚠️ Backend + Frontend + Config gemeinsam prüfen
- ❌ Keine großen Umbauten, nur gezielte Fixes und Härtung
- ✅ Defensive Validierung hinzufügen (osrm_distance null-checks)
- ✅ Logging verbessern (Request/Response)
- ✅ Regressionstest schreiben
```

**4. Prompt in Cursor kopieren und Session starten**

---

### **Schritt 3 – Änderung einbauen**

Cursor erzeugt Vorschläge (Diffs oder komplette Dateien).

**Änderungen werden nur übernommen, wenn:**
- ✅ Sie verständlich sind (klare Erklärung)
- ✅ Sie zum Problem passen (keine Off-Topic-Änderungen)
- ✅ Sie die Standards nicht verletzen (siehe `STANDARDS.md`)
- ✅ Tests/Logging vorhanden sind

**Ablehnen, wenn:**
- ❌ Cursor macht Ghost-Refactorings
- ❌ Änderungen außerhalb des Scopes
- ❌ Keine Tests/Logging hinzugefügt
- ❌ API-Kontrakt gebrochen ohne Frontend-Anpassung

---

### **Schritt 4 – Tests & Health-Checks**

Nach jeder relevanten Änderung:

#### **4.1 Server starten**
```powershell
python start_server.py
```

#### **4.2 Health-Checks prüfen**
```bash
# Basis-Health
curl http://localhost:5000/health

# OSRM-Health
curl http://localhost:5000/health/osrm

# API-Summary
curl http://localhost:5000/summary

# Debug-Routes
curl http://localhost:5000/_debug/routes
```

#### **4.3 Kritische Flows testen**

**Manuelle Tests:**
1. **CSV-Upload:**
   - Öffne UI: `http://localhost:5000`
   - Upload einer Test-CSV (`tourplaene/test_*.csv`)
   - Prüfe: Geocoding erfolgreich, keine 500er

2. **Touren-Workflow:**
   - Öffne Tourplan-Panel
   - Wähle Tour mit >15 Stopps
   - Klicke "Sub-Routen generieren"
   - Prüfe: Keine Fehler in Browser-Konsole, Korrekte Sub-Routen

3. **OSRM-Aufruf:**
   - Öffne Map-Panel
   - Berechne Route zwischen 2 Punkten
   - Prüfe: Route wird angezeigt, keine 500er

4. **UI-Seiten:**
   - Tourplan-Panel (`panel-tours.html`)
   - Map-Panel (`panel-map.html`)
   - Test-Dashboard (`test-dashboard.html`)

**Automatisierte Tests (falls vorhanden):**
```bash
# Backend-Tests
pytest tests/

# Frontend-Tests (falls vorhanden)
npm test
```

#### **4.4 Wenn etwas rot ist:**
- Änderung zurückdrehen (`git checkout -- <file>`)
- Oder gezielt nachbessern (mit Cursor)

---

### **Schritt 5 – Lessons & Regeln aktualisieren**

Wenn ein Bug oder Chaos-Situation aufgetreten ist:

#### **5.1 Eintrag in `LESSONS_LOG.md`**

```markdown
### Eintrag #4: Sub-Routen OSRM Distance Null

**Datum:** 2025-11-14  
**Bereich:** Sub-Routen-Generator  
**Häufigkeit:** 3× in letzten 2 Wochen  

**Symptom:**
- 500er Fehler bei großen Touren (>15 Stopps)
- Backend-Log: `KeyError: 'osrm_distance'`
- Frontend: Keine Fehlerbehandlung, UI friert ein

**Root Cause:**
- OSRM-Client gibt bei Timeout `None` zurück
- Sub-Routen-Generator erwartet immer `osrm_distance`-Key
- Keine Defensive Validierung

**Fix:**
- Null-Checks in `sub_route_generator.py` hinzugefügt
- Timeout-Fehler explizit abgefangen
- Frontend: Try-Catch + Fehler-Toast

**Was die KI künftig tun soll:**
- IMMER Null-Checks bei OSRM-Daten
- IMMER Frontend-Fehlerbehandlung prüfen
- IMMER Timeout-Szenarien testen
```

#### **5.2 Falls nötig: `REGELN_AUDITS.md` erweitern**

Wenn ein neues Pattern erkannt wurde:

```markdown
### Neue Regel: OSRM-Defensive-Modus

**Bei allen OSRM-abhängigen Features:**
- ✅ Null-Checks für `distance`, `duration`, `geometry`
- ✅ Timeout-Handling (max. 10s)
- ✅ Fallback-Werte (z.B. Luftlinie)
- ✅ Frontend-Fehler-Toast
```

---

## 5. Health-/Audit-Checks als Schutzschicht

**Idee:** Bestimmte Aktionen sind nur erlaubt, wenn ein kurzer Health-/Audit-Check grün ist.

### **Beispiele für Pre-Checks:**

#### **Vor Sub-Routen-Generator:**
```python
# Checkliste
✅ DB erreichbar (schema ok)
✅ OSRM erreichbar (Health-Endpoint oder Test-Route)
✅ Keine kritischen Fehler in letzten 10 Logs
✅ Frontend-Bundle vorhanden
```

#### **Vor OSRM-Routenberechnung:**
```python
✅ OSRM-Service läuft (Port 5000)
✅ Mindestens 2 gültige Koordinaten
✅ Max. 100 Waypoints (OSRM-Limit)
```

#### **Vor KI-Code-Verbesserungsjob:**
```python
✅ LLM-API erreichbar (OpenAI/Ollama)
✅ API-Keys konfiguriert
✅ Cost-Limit nicht überschritten
```

**Wenn etwas fehlschlägt:**
- ❌ Aktion blocken
- 📢 Hinweis an Benutzer (UI-Toast oder Log)
- 📝 Error-Log mit Details

---

## 6. Ganzheitliches Testen (Backend + Frontend)

Damit Cursor den Code **wirklich ganzheitlich** betrachtet:

### **In jedem Audit-Prompt explizit erwähnen:**

```markdown
## Analyse-Scope
Analysiere Python-Backend, JS-Frontend und Konfiguration gemeinsam.

## API-Kontrakt prüfen
Prüfe, ob die Frontend-Aufrufe zu den FastAPI-Routen passen:
- Pfad (z.B. `/api/optimize/sub-routes`)
- Methode (GET/POST/PUT/DELETE)
- Payload (Request-Body)
- Response-Schema (Status, Daten, Fehler)

## End-to-End-Szenario
Beschreibe den kompletten Workflow:
1. CSV-Upload → Parsing
2. Geocoding → DB-Speicherung
3. Routen-Berechnung → OSRM-Aufruf
4. Sub-Routen-Generierung → Optimierung
5. Anzeige auf Map → Frontend-Rendering
```

### **Beispiel-Szenarien:**

#### **Szenario 1: CSV-Upload**
```
1. User wählt CSV-Datei (frontend/index.html)
2. JavaScript sendet File → POST /api/upload (frontend/js/upload.js)
3. Backend parst CSV → ingest/csv_reader.py
4. Geocoding → services/geocoding_service.py
5. DB-Speicherung → db/schema.py
6. Response → Frontend zeigt Erfolg
```

#### **Szenario 2: Sub-Routen-Generator**
```
1. User klickt "Sub-Routen generieren" (frontend/panel-tours.html)
2. JavaScript sendet Tour-ID → POST /api/optimize/sub-routes
3. Backend lädt Tour → services/tour_service.py
4. OSRM-Distanzen → services/osrm_client.py
5. Optimierung → services/sub_route_generator.py
6. Response → Frontend zeigt Sub-Routen
```

---

## 7. Checkliste für jeden Audit

Vor Abschluss eines Audits:

```markdown
## Pre-Audit
- [ ] Problem klar beschrieben (inkl. Logs/Screenshots)
- [ ] Audit-ZIP vorbereitet (relevante Dateien + README)
- [ ] Template gewählt (CURSOR_PROMPT_TEMPLATE.md)
- [ ] Scope definiert (Backend + Frontend + Config)

## Während Audit
- [ ] Multi-Layer-Pflicht beachtet (Backend + Frontend + DB + Infra)
- [ ] Keine Ghost-Refactorings
- [ ] API-Kontrakt geprüft (Backend ↔ Frontend)
- [ ] Defensive Programming (Null-Checks, Try-Catch)
- [ ] Logging hinzugefügt/verbessert

## Post-Audit
- [ ] Tests geschrieben (min. 1 Regressionstest)
- [ ] Health-Checks laufen grün
- [ ] Kritische Flows manuell getestet
- [ ] LESSONS_LOG aktualisiert (bei neuem Fehlertyp)
- [ ] REGELN erweitert (bei neuem Pattern)
- [ ] Git-Commit mit Conventional Commit Message
```

➡️ **Vollständige Checkliste:** [`AUDIT_CHECKLISTE.md`](AUDIT_CHECKLISTE.md)

---

## 8. Zielbild

Wenn dieser Prozess konsequent genutzt wird:

✅ **Weniger Überraschungsfehler** (500er/402 etc.)  
✅ **Cursor arbeitet reproduzierbar und nachvollziehbar**  
✅ **Jede harte Störung führt zu Verbesserung der Regeln**  
✅ **Version 3+ hat eingebaute Sicherheitsgurte** statt „wir hoffen, dass es gut geht"

---

## 9. Quick-Links

| **Was brauchst du?** | **Wohin?** |
|----------------------|------------|
| **Audit-Regeln** | [`REGELN_AUDITS.md`](REGELN_AUDITS.md) |
| **Checkliste** | [`AUDIT_CHECKLISTE.md`](AUDIT_CHECKLISTE.md) |
| **Templates** | [`CURSOR_PROMPT_TEMPLATE.md`](CURSOR_PROMPT_TEMPLATE.md) |
| **Lessons** | [`LESSONS_LOG.md`](LESSONS_LOG.md) |
| **Standards** | [`STANDARDS.md`](STANDARDS.md) |
| **Schnellreferenz** | [`STANDARDS_QUICK_REFERENCE.md`](STANDARDS_QUICK_REFERENCE.md) |

---

## 10. Zusammenfassung in 3 Sätzen

1. **Vor jedem größeren Fix:** Audit-ZIP + Template aus `CURSOR_PROMPT_TEMPLATE.md` nutzen.
2. **Während des Fixes:** Multi-Layer-Pflicht beachten (Backend + Frontend + Config), keine Ghost-Refactorings.
3. **Nach dem Fix:** Tests schreiben, Health-Checks prüfen, `LESSONS_LOG.md` aktualisieren.

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-14  
**Projekt:** FAMO TrafficApp 3.0

🔄 **Reproduzierbare, nachvollziehbare, fehlerarme Änderungen – jeden Tag!**

