# AI Code-Audit Regeln (Backend + Frontend)

Ziel: Cursor soll **immer** Backend *und* Frontend gemeinsam prüfen, statt nur Python.

---

## 1. Geltungsbereich

**Backend (Python)**

* `backend/`
* `routes/`
* `services/`
* `db/`

**Frontend (Vanilla JS + HTML/CSS)**

* `frontend/` (oder aktueller Frontend-Ordner)
* inkl. `index.html`, `*.js`, `*.css`

Cursor soll Codeänderungen immer im Kontext **beider** Seiten bewerten.

---

## 2. Standard-Befehle für jeden Audit

Cursor soll vor jedem größeren Audit / Fix die folgenden Checks ausführen (oder gedanklich simulieren):

### 2.1 Backend-Checks (Python)

1. Syntax-Check:

   * `python -m compileall backend db routes services`

2. Tests (falls konfiguriert):

   * `pytest`

3. Optional: Linting (wenn eingerichtet):

   * `ruff check` oder `flake8` (falls vorhanden)

### 2.2 Frontend-Checks (JS)

Voraussetzung: Im Frontend-Ordner existiert ein `package.json` mit Lint-Script.

1. Lint ausführen:

   * `cd frontend`
   * `npm run lint`

2. Falls es später Tests gibt:

   * `npm test`

**Regel:** Cursor muss JS-Lint-Warnungen und -Fehler **genauso ernst** nehmen wie Python-Fehler.

---

## 3. API-Kontrakt-Prüfung (Backend ↔ Frontend)

Bei Fehlern im Browser (DevTools-Konsole, Netzwerk-Tab) gilt:

1. **Request identifizieren**

   * Welcher Endpoint? (z.B. `/api/tour/optimize`, `/api/tour/route-details`, `/api/subroutes/...`)

2. **Backend-Response-Schema prüfen**

   * In der FastAPI-Route nachsehen, welches JSON-Schema tatsächlich zurückgegeben wird.
   * Beispiel: `{"tours": [...], "sub_routes": [...]}`

3. **Frontend-Verarbeitung vergleichen**

   * Im JS die Stelle suchen, wo `fetch(...)` die Antwort verarbeitet.
   * Prüfen, ob dort **dieselben** Feldnamen (`sub_routes`, `tours`, etc.) verwendet werden.

4. **Konflikte behandeln**

   * Wenn Backend und Frontend unterschiedliche Feldnamen oder Strukturen nutzen, **Frontend und/oder Route korrigieren**, statt nur irgendwo im Backend zu refaktorisieren.

Cursor soll explizit festhalten, wenn ein Bug ein **Kontrakt-Problem** ist und nicht ein reines Backend-Thema.

---

## 4. Spezieller Fokus: Sub-Routen-Generator

Für alle Bugs rund um den "Sub-Routen Generator" gelten zusätzliche Regeln:

1. **Frontend-Entry-Point**

   * JS-Funktion für den Button "Routen optimieren (W-Touren & >4 Kunden)" identifizieren.
   * Fetch-Call und Response-Verarbeitung dokumentieren.

2. **Backend-Endpoint**

   * Zugehörige Route suchen (z.B. in `routes/` oder `backend/routes/`):

     * `@router.post("/api/tour/optimize")` oder ähnliches.
   * Response-Format mit Beispiel-JSON kommentieren.

3. **Defensive JS-Programmierung**

   * Vor jedem `.map()`, `.forEach()` etc. prüfen:

     * `Array.isArray(data.sub_routes)`
   * Bei unerwartetem Schema:

     * Klarer Fehler im UI (z.B. "Unerwartete Antwort vom Server (sub_routes fehlt)")
     * `console.error("SUBROUTEN: Unerwartetes Response-Schema", data)`

4. **Fehleranalyse-Priorität**

   * Wenn in DevTools `TypeError: Cannot read properties of undefined` o.ä. steht →

     * **JS und API-Response zuerst prüfen**, bevor im Backend groß umgebaut wird.

---

## 5. Audit-Workflow für Cursor (Schritt für Schritt)

1. **Problem identifizieren**

   * Fehlerbeschreibung aus Logs, Browser-Konsole und Audit-Notizen sammeln.

2. **Relevante Dateien aus dem ZIP ziehen**

   * Backend: betroffene Routen, Services, Modelle
   * Frontend: zugehörige JS-Files, HTML-Buttons/Events

3. **Checks ausführen**

   * `python -m compileall ...`
   * `pytest` (falls vorhanden)
   * `cd frontend && npm run lint`

4. **API-Kontrakt prüfen**

   * Request & Response (Backend) vs. Verarbeitung (Frontend) vergleichen.

5. **Fix planen**

   * Reihenfolge:

     1. Falsche Response-Feldnamen / Strukturen korrigieren
     2. Frontend-Parsing anpassen
     3. Defensive Checks einbauen (Frontend)
     4. Zusätzliche Logs bei Fehlerfällen

6. **Fix umsetzen & verifizieren**

   * Codeänderung kurz begründen (Was war kaputt? Wo? Warum so gefixt?)
   * Tests + Lint noch einmal laufen lassen
   * Erwartete Userwirkung beschreiben (z.B. "Sub-Routen Generator zeigt jetzt keine TypeErrors mehr und generiert Routen für alle W-Touren mit >4 Kunden.")

---

## 6. ZIP-Regel für Audits

Für jede Audit-Session:

* Audit-Dateien in `ZIP/` ablegen (z.B. `ZIP/AUDIT_YYYYMMDD_HHMMSS_ID.zip`).
* ZIP soll **immer** enthalten:

  * Relevante Backend-Dateien (Routen, Services, Schema etc.)
  * Relevante Frontend-Dateien (JS, HTML, CSS für den betroffenen Bereich)
  * Logs / Screenshots / Fehlermeldungs-Zusammenfassungen
  * Eine kurze README mit:

    * Problem-Beschreibung
    * Reproduktionsschritten
    * Erwartetes vs. aktuelles Verhalten

Cursor soll bei einem Audit immer von dieser ZIP-Struktur ausgehen und Backend + Frontend gleichwertig berücksichtigen.

---

## 7. Checkliste für jeden Audit

Bei jedem Code-Audit diese Punkte abhaken:

- [ ] Backend-Syntax geprüft (`python -m compileall`)
- [ ] Frontend-Lint ausgeführt (falls `package.json` vorhanden)
- [ ] API-Endpoint identifiziert
- [ ] Backend-Response-Schema dokumentiert
- [ ] Frontend-Request/Response-Verarbeitung geprüft
- [ ] API-Kontrakt zwischen Backend und Frontend validiert
- [ ] Defensive Checks im Frontend eingebaut
- [ ] Fehlerbehandlung auf beiden Seiten vorhanden
- [ ] Tests ausgeführt (falls vorhanden)
- [ ] ZIP-Archiv mit allen relevanten Dateien erstellt
- [ ] Erwartete Userwirkung dokumentiert

---

## 8. Prioritäten bei der Fehlersuche

1. **Browser DevTools zuerst**
   * Console-Errors
   * Network-Tab (Request/Response)
   * Sources/Debugger (JS-Breakpoints)

2. **API-Kontrakt prüfen**
   * Backend-Response vs. Frontend-Erwartung

3. **Backend-Logs prüfen**
   * Python-Exceptions
   * Logische Fehler in Services

4. **Datenbank-State prüfen**
   * Falls notwendig: SQL-Queries validieren

---

## 9. Dokumentations-Anforderungen

Jeder Fix muss dokumentieren:

* **Was war kaputt?**
  * Symptom (z.B. "TypeError in Zeile 123 von tour_manager.js")
  
* **Wo war es kaputt?**
  * Backend-Datei und Zeile
  * Frontend-Datei und Zeile
  
* **Warum ist es aufgetreten?**
  * Root Cause (z.B. "Backend lieferte `subRoutes` statt `sub_routes`")
  
* **Wie wurde es gefixt?**
  * Konkrete Änderungen in Backend und/oder Frontend
  
* **Wie wird es getestet?**
  * Manuelle Tests oder automatische Tests
  
* **Erwartete Userwirkung**
  * Was sieht/erlebt der Benutzer nach dem Fix?

---

## 10. Best Practices

### Backend (Python/FastAPI)

* Konsistente Feldnamen in JSON-Responses (snake_case: `sub_routes`, nicht `subRoutes`)
* Pydantic-Modelle für Request/Response verwenden
* Aussagekräftige HTTP-Statuscodes (200, 400, 404, 500)
* Logging bei Fehlern mit Kontext

### Frontend (Vanilla JS)

* Defensive Programmierung: Immer prüfen, ob Daten existieren
* `Array.isArray()` vor `.map()`, `.forEach()` etc.
* Fehler im UI anzeigen, nicht nur in Console
* Konsistente Feldnamen wie im Backend (snake_case oder camelCase, aber konsistent)
* Klare Error-Messages für Endbenutzer

### API-Design

* Klare Request/Response-Schemas
* Versionierung bei Breaking Changes
* Dokumentation (OpenAPI/Swagger)
* Konsistente Error-Responses mit `{"error": "...", "detail": "..."}`

---

## Anhang: Typische Fehlerquellen

### 1. Feldnamen-Mismatch

**Problem:** Backend sendet `sub_routes`, Frontend erwartet `subRoutes`

**Lösung:** Konsistente Namenskonvention festlegen und einhalten

### 2. Fehlende Null-Checks

**Problem:** `data.tours.map(...)` schlägt fehl, wenn `data.tours` undefined ist

**Lösung:** `if (data.tours && Array.isArray(data.tours)) { ... }`

### 3. Falsche Content-Type Header

**Problem:** Backend sendet HTML statt JSON

**Lösung:** `return JSONResponse(...)` statt `return Response(...)`

### 4. CORS-Probleme

**Problem:** Browser blockt Request

**Lösung:** CORS-Middleware korrekt konfigurieren

### 5. Encoding-Probleme

**Problem:** Umlaute werden falsch dargestellt

**Lösung:** UTF-8 konsequent verwenden (Backend, Frontend, Datenbank)

---

---

## ⚠️ WICHTIGER HINWEIS

Dieses Dokument wurde durch ein **umfassenderes KI-Audit-Framework** ergänzt.

**Für vollständige Audits siehe:**

- 📚 **`docs/ki/README.md`** – Framework-Übersicht
- 📋 **`docs/ki/REGELN_AUDITS.md`** – Erweiterte Grundregeln
- ✅ **`docs/ki/AUDIT_CHECKLISTE.md`** – Systematische Checkliste
- 📖 **`docs/ki/LESSONS_LOG.md`** – Dokumentierte Fehler & Lösungen
- 🚀 **`docs/ki/CURSOR_PROMPT_TEMPLATE.md`** – Fertige Prompts

**Verwendung:**

- Dieses Dokument: Fokus auf **Backend ↔ Frontend API-Kontrakt**
- `docs/ki/`: Vollständiges Framework für **alle Audit-Typen**

---

**Erstellt:** 2025-11-14  
**Version:** 1.0  
**Erweitert:** 2025-11-14 (siehe docs/ki/)  
**Für:** Famo TrafficApp 3.0 - Code-Audits mit Cursor AI

