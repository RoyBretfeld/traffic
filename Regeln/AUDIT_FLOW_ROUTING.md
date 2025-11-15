# 🔍 Cursor Audit Flow – Routing + Frontend/Backend

**Version:** 1.0  
**Stand:** 2025-11-15  
**Zweck:** Gezielter, reproduzierbarer Code-Audit-Prozess für Routing-Module

---

## 🎯 Ziel

Gezielter, reproduzierbarer Code-Audit-Prozess für Cursor, der **Backend UND Frontend** betrachtet, mit klarer Begrenzung des Scopes und ohne ungeplante Massen-Umbauten.

---

## 📋 1. Scope für diesen Audit

### **✅ Fokus-Module:**

**Routing & OSRM:**
- `backend/services/osrm_client.py`
- `backend/services/routing_optimizer.py` (oder äquivalent)
- Subrouten-Generator (alle Services/Routes, die Subrouten erzeugen)
- `backend/routes/tourplan_*.py`
- `backend/routes/workflow_api.py` (Sub-Routen-Generator Logik)

**Fehlerbehandlung & Middleware:**
- `backend/error_handlers.py`
- `backend/middlewares/trace_id.py`

**Frontend, das Routing nutzt:**
- Alle JS/HTML-Dateien, die folgende Endpoints ansprechen:
  - `/api/tour/route-details`
  - `/api/tour/optimize` (Sub-Routen-Generator)
  - `/health/osrm`
  - Routing-Ergebnis anzeigen
  - Fehlerzustände beim Routing darstellen

**Konkret (Frontend):**
- `frontend/index.html` (Tour-Management, Sub-Routen-Button)
- `frontend/js/tourplan.js` (falls vorhanden)
- `frontend/panel-map.html` (Karten-Integration)
- `frontend/panel-tours.html` (Tour-Liste)

---

### **❌ Nicht im Scope dieses Durchlaufs:**

- Unabhängige Module, die nichts mit Routing/Subrouten zu tun haben
- DB-Migrationen außerhalb von Routing/Geo-Caching, außer wenn direkt betroffen
- Geocoding-Module (separater Audit)
- Statistik/Admin-UI (separater Audit)

---

## 🛡️ 2. Vorbedingungen (immer VOR dem Audit)

### **Schritt 1: Projekt-Snapshot anlegen**

**Option A: Git-Commit**
```bash
git add .
git commit -m "chore: Snapshot vor Routing-Audit"
git tag audit-routing-$(date +%Y%m%d-%H%M%S)
```

**Option B: Vollständiges ZIP**
```bash
# PowerShell
Compress-Archive -Path "E:\_____1111____Projekte-Programmierung\______Famo TrafficApp 3.0" -DestinationPath "backup_routing_audit_$(date +%Y%m%d_%H%M%S).zip"
```

---

### **Schritt 2: Standards laden (Pflicht für Cursor)**

**Cursor soll zuerst diese Dateien lesen:**

1. **Globale Standards:**
   - `Global/GLOBAL_STANDARDS.md`

2. **Projektprofil:**
   - `PROJECT_PROFILE.md` (→ Abschnitt 3.2: Touren-Workflow & Sub-Routen-Generator)

3. **Projekt-Standards:**
   - `Regeln/STANDARDS.md`
   - `Regeln/STANDARDS_QUICK_REFERENCE.md`
   - `Regeln/REGELN_AUDITS.md`
   - `Regeln/AUDIT_CHECKLISTE.md`

4. **Lessons Learned:**
   - `Regeln/LESSONS_LOG.md` (→ Eintrag #3: Sub-Routen-Generator)

---

### **Schritt 3: KI-Background-Job zähmen**

**`CODE-IMPROVEMENT-JOB` darf für diesen Audit KEINE Dateien ändern.**

**Akzeptabel:**
- ✅ Nur Reports/Logs schreiben (z. B. JSON, Markdown)
- ❌ Keine Commits/Schreibzugriffe auf Code

**Prüfung:**
```bash
# Prüfe, ob Background-Job läuft
curl http://localhost:8111/api/code-improvement-job/status

# Falls aktiv: Stoppen
curl -X POST http://localhost:8111/api/code-improvement-job/stop
```

---

## 📏 3. Audit-Regeln für Cursor (konkret)

### **Regel 1: Kein Full-Repo-Refactor** 🚫

**Erlaubt:**
- ✅ Nur Dateien im definierten Scope ändern
- ✅ Gezielte Bug-Fixes
- ✅ Fehlerbehandlung verbessern

**Verboten:**
- ❌ Framework-Migration
- ❌ Architektur-Umbau
- ❌ "Wir bauen alles neu"
- ❌ Globale Umbenennungen

---

### **Regel 2: Keine stillen Änderungen** 📢

**Jede Änderung muss als klarer Diff/Vorschlag kommen:**

**Format:**
```diff
# Datei: backend/services/osrm_client.py
# Zeilen: 123-130

- def get_route(self, start, end):
-     return requests.get(f"{self.base_url}/route/...")
+ def get_route(self, start, end):
+     try:
+         response = requests.get(
+             f"{self.base_url}/route/...",
+             timeout=self.timeout
+         )
+         response.raise_for_status()
+         return response.json()
+     except requests.Timeout:
+         logger.error(f"OSRM Timeout: {start} -> {end}")
+         raise OSRMTimeoutError("OSRM nicht erreichbar")
```

**Dazu immer:**
- **Warum?** "Fehlende Timeout-Behandlung führt zu hängenden Requests"
- **Risiko?** "Gering, nur Error-Handling verbessert"
- **Vorteil?** "User sieht klare Fehlermeldung statt 500er"

---

### **Regel 3: Backend + Frontend gemeinsam denken** 🔄

**Für jede relevante API-Route prüfen:**

**Beispiel: `/api/tour/optimize` (Sub-Routen-Generator)**

| Aspekt | Backend | Frontend |
|--------|---------|----------|
| **URL** | `@app.post("/api/tour/optimize")` | `fetch("/api/tour/optimize")` |
| **Method** | POST | POST |
| **Request** | `{ tour_id, stops, is_bar_tour }` | `JSON.stringify({ tour_id, stops, ... })` |
| **Response** | `{ sub_tours: [...], status: "ok" }` | `response.sub_tours.forEach(...)` |
| **Errors** | `raise HTTPException(422)` | `catch (e) { showError(...) }` |
| **Logging** | `logger.error(..., trace_id)` | `console.error(..., trace_id)` |

**Checkliste:**
- [ ] Backend-Handler existiert?
- [ ] Frontend ruft korrekte URL auf?
- [ ] Request-Shape stimmt überein?
- [ ] Response-Shape stimmt überein?
- [ ] Fehler werden beide Seiten behandelt?
- [ ] Trace-ID wird durchgereicht?

---

### **Regel 4: Fehlerrobustheit prüfen** 🛡️

**Für jede Änderung an Routing/Subrouten/OSRM:**

**Timeout-Szenario:**
- ❓ Was passiert bei OSRM-Timeout (>5s)?
- ❓ Backend: Exception gefangen? Fallback auf Haversine?
- ❓ Frontend: Error-Toast angezeigt? Retry-Button?
- ❓ Logging: Trace-ID + Error-Details?

**4xx/5xx-Szenario:**
- ❓ Backend: HTTPException mit sinnvollem Status-Code?
- ❓ Frontend: Unterscheidung zwischen 422 (User-Fehler) und 500 (Server-Fehler)?
- ❓ User: Verständliche Fehlermeldung?

**OSRM nicht erreichbar:**
- ❓ Circuit-Breaker aktiv?
- ❓ Fallback-Mechanismus (Haversine)?
- ❓ Health-Check zeigt OSRM-Status?

---

### **Regel 5: Tests vorschlagen** 🧪

**Für jede gefundene Schwachstelle:**

**Format:**
```markdown
### Test-Fall 1: Sub-Routen-Generator bei OSRM-Timeout

**Setup:**
- OSRM-Container stoppen: `docker stop osrm-backend`

**Backend-Test:**
```bash
curl -X POST http://localhost:8111/api/tour/optimize \
  -H "Content-Type: application/json" \
  -d '{"tour_id": "W-07.00", "stops": [...]}'

# Erwartung: 503 Service Unavailable
# Response: { "detail": "Routing-Service nicht erreichbar" }
```

**Frontend-Test:**
- CSV hochladen (W-07.00)
- "Sub-Routen generieren" klicken
- **Erwartung:** Error-Toast "Routing-Service nicht erreichbar"
- **Kein:** Unbehandelte Exception in Browser-Konsole

**Unit-Test-Skizze:**
```python
def test_osrm_timeout_fallback():
    """Test: Bei OSRM-Timeout wird Haversine-Fallback genutzt"""
    # Mock OSRM-Timeout
    with patch('requests.get', side_effect=requests.Timeout):
        result = routing_optimizer.optimize_tour(tour)
    
    # Erwartung: Fallback auf Haversine
    assert result.routing_method == "haversine"
    assert result.status == "ok_fallback"
```
```

---

### **Regel 6: Keine neuen Abhängigkeiten ohne Begründung** 📦

**Neue Libraries nur, wenn:**
- ✅ Klarer Nutzen (z.B. bessere Error-Handling-Lib)
- ✅ Kein massiver Eingriff in die Architektur
- ✅ Begründung im Audit-Report

**Verboten:**
- ❌ "Ich baue das jetzt mit Library X komplett neu"
- ❌ Breaking Changes in `requirements.txt` ohne Absprache

---

## 🤖 4. Beispiel-Prompt für Cursor (Routing-Audit)

**Kopiere diesen Prompt in Cursor:**

```
🔍 CONTEXT LADEN:

1. Lies zuerst diese Dokumente vollständig:
   - Global/GLOBAL_STANDARDS.md
   - PROJECT_PROFILE.md (→ Abschnitt 3.2: Touren-Workflow & Sub-Routen-Generator)
   - Regeln/STANDARDS.md
   - Regeln/REGELN_AUDITS.md
   - Regeln/AUDIT_CHECKLISTE.md
   - Regeln/LESSONS_LOG.md (→ Eintrag #3: Sub-Routen-Generator)
   - Regeln/AUDIT_FLOW_ROUTING.md (DIESE DATEI!)

2. Halte dich an die 6 Audit-Regeln aus AUDIT_FLOW_ROUTING.md

---

🎯 SCOPE (NUR DIESE DATEIEN):

Backend:
- backend/services/osrm_client.py
- backend/services/routing_optimizer.py (falls vorhanden)
- backend/routes/workflow_api.py (Sub-Routen-Generator)
- backend/routes/tourplan_*.py
- backend/error_handlers.py
- backend/middlewares/trace_id.py

Frontend:
- frontend/index.html (Tour-Management, Sub-Routen-Button)
- frontend/js/tourplan.js (falls vorhanden)
- frontend/panel-map.html
- frontend/panel-tours.html

---

🔍 ZIELE DES AUDITS:

Finde:
1. Inkonsistenzen zwischen Frontend und Backend
   - Request-/Response-Struktur
   - URLs
   - HTTP-Methoden
   - Error-Handling

2. Fehler in Fehlerbehandlung und Logging
   - 4xx/5xx-Behandlung
   - OSRM-Timeouts
   - Trace-ID-Propagierung

3. Stellen, an denen Sub-Routen-Generator oder Routing unerwartet 402/500 erzeugen könnten

---

⚠️ REGELN:

1. ❌ KEIN Full-Repo-Refactor
2. 📢 Alle Änderungen als Diffs (mit Begründung)
3. 🔄 Backend + Frontend gemeinsam prüfen
4. 🛡️ Fehlerrobustheit prüfen (Timeout, 4xx, 5xx)
5. 🧪 Tests vorschlagen (min. 2 pro Schwachstelle)
6. 📦 Keine neuen Dependencies ohne Begründung

---

📤 OUTPUT (STRUKTURIERTER REPORT):

1. **Gescannter Scope**
   - Welche Dateien hast du konkret analysiert?
   - Welche Dateien NICHT analysiert (außerhalb Scope)?

2. **Gefundene Probleme**
   - Punktliste mit:
     * Beschreibung
     * Dateipfad + Zeilenbereich
     * Schweregrad (Critical, High, Medium, Low)

3. **Änderungsvorschläge**
   - Diffs mit:
     * Begründung (Warum?)
     * Risiko (Niedrig/Mittel/Hoch)
     * Vorteil (Was wird besser?)

4. **Tests**
   - HTTP-Requests (curl-Beispiele)
   - UI-Schritte (Frontend-Testing)
   - Unit-Test-Skizzen (Testname + grober Inhalt)

5. **LESSONS_LOG-Update**
   - Falls neues Fehlermuster gefunden: Eintrag vorschlagen

---

Los geht's!
```

---

## 📊 5. Ergebnis-Erwartung

### **Nach diesem Audit-Lauf soll:**

**✅ Technisch:**
- Sub-Routen-Generator läuft stabil
- Routing-Endpoints behandeln alle Fehlerszenarien
- OSRM-Timeout führt zu Fallback (Haversine)
- Frontend zeigt verständliche Fehlermeldungen

**✅ Nachweisbar:**
- Cursor hat Backend **und** Frontend berücksichtigt
- Nur im definierten Scope geändert
- Transparent in Reportform gearbeitet
- Tests vorgeschlagen (Backend + Frontend)
- LESSONS_LOG aktualisiert (falls neues Pattern)

---

## 🔄 6. Wiederverwendbarkeit

**Dieses Dokument dient als wiederverwendbare Vorlage für weitere modulare Audits:**

**Weitere Audit-Flows (geplant):**
- `AUDIT_FLOW_GEOCODING.md` (Geocoding + Alias + Fail-Handling)
- `AUDIT_FLOW_STATISTICS.md` (Stats-Endpoints + Admin-UI)
- `AUDIT_FLOW_UPLOAD.md` (CSV-Upload + Workflow)
- `AUDIT_FLOW_DATABASE.md` (Schema + Migrationen + Indizes)

**Struktur bleibt gleich:**
1. Scope definieren (✅ Fokus / ❌ Nicht im Scope)
2. Vorbedingungen (Snapshot, Standards, Background-Job)
3. 6 Audit-Regeln (angepasst an Modul)
4. Beispiel-Prompt
5. Ergebnis-Erwartung

---

## 📝 7. Checkliste für Cursor-Audit

**Vor dem Audit:**
- [ ] Projekt-Snapshot erstellt (Git-Tag oder ZIP)
- [ ] Standards gelesen (Global + Projekt + Lessons)
- [ ] Background-Job gestoppt
- [ ] Scope klar definiert

**Während des Audits:**
- [ ] Nur Dateien im Scope analysiert
- [ ] Backend + Frontend gemeinsam geprüft
- [ ] Diffs mit Begründung erstellt
- [ ] Tests vorgeschlagen (min. 2 pro Problem)
- [ ] Keine neuen Dependencies ohne Absprache

**Nach dem Audit:**
- [ ] Report erstellt (strukturiert, siehe Abschnitt 4)
- [ ] Health-Checks geprüft (`/health`, `/health/osrm`)
- [ ] LESSONS_LOG aktualisiert (falls relevant)
- [ ] Audit-ZIP erstellt (Report + relevante Dateien)

---

## 🔗 Verwandte Dokumente

**Globale Standards:**
- [`../Global/GLOBAL_STANDARDS.md`](../Global/GLOBAL_STANDARDS.md) - Universelle Regeln

**Projektprofil:**
- [`../PROJECT_PROFILE.md`](../PROJECT_PROFILE.md) - Routing-Module (Abschnitt 3.2)

**Projekt-Standards:**
- [`REGELN_AUDITS.md`](REGELN_AUDITS.md) - 7 unverhandelbare Audit-Regeln
- [`AUDIT_CHECKLISTE.md`](AUDIT_CHECKLISTE.md) - 9-Punkte-Checkliste
- [`CURSOR_PROMPT_TEMPLATE.md`](CURSOR_PROMPT_TEMPLATE.md) - Template #10 (Sub-Routen-Generator)
- [`LESSONS_LOG.md`](LESSONS_LOG.md) - Eintrag #3 (Sub-Routen-Generator)

---

**Version:** 1.0  
**Stand:** 2025-11-15  
**Projekt:** FAMO TrafficApp 3.0

🔍 **Gezielt. Reproduzierbar. Modular.**

