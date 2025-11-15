# Grundregeln für KI-Code-Audits (Cursor)

**Projekt:** FAMO TrafficApp 3.0  
**Version:** 1.0  
**Datum:** 2025-11-14

---

## Einleitung

Dieses Dokument definiert die Grundregeln für alle Code-Audits, die von Cursor AI durchgeführt werden. Ziel ist es, strukturierte, reproduzierbare und ganzheitliche Audits zu gewährleisten, die Backend, Frontend, Datenbank und Infrastruktur gleichermaßen berücksichtigen.

---

## 1. Scope immer explizit machen

**Zu Beginn jedes Audits klären:**

- Welches Feature / welcher Endpoint / welches UI-Element ist betroffen?
- Welche Symptome liegen vor (Fehlermeldungen, Logs, Screenshots)?
- Welche User Story oder welcher Bug-Report liegt zugrunde?

**Dokumentation:**

```md
## Audit-Scope

- **Feature:** Sub-Routen-Generator
- **Betroffene Endpoints:** `/api/tour/optimize`, `/api/subroutes/generate`
- **Symptome:** 500 Internal Server Error, TypeError in Browser-Konsole
- **Reproduktion:** Button "Routen optimieren" → Fehler nach 3 Sekunden
```

---

## 2. Immer ganzheitlich prüfen

### 2.1 Backend (Python/FastAPI)

- **Routen:** `routes/`, `backend/routes/`
- **Services:** `services/`, `backend/services/`
- **Datenbank-Zugriff:** `db/`, `repositories/`
- **Modelle:** `backend/models/`, Pydantic-Schemas
- **Konfiguration:** `config.env`, `backend/config.py`

**Prüfungen:**

- Exception-Handling (try-catch, Error-Responses)
- Logging (strukturierte Logs mit Kontext)
- Input-Validierung (Pydantic, manuelle Checks)
- Timeouts bei externen Aufrufen (OSRM, LLM-APIs)

### 2.2 Frontend (HTML, CSS, JavaScript)

- **Entry Points:** `frontend/*.html`
- **JavaScript:** `frontend/js/*.js`, Inline-Scripts
- **API-Calls:** Alle `fetch()` Aufrufe
- **Event-Handler:** Button-Clicks, Form-Submissions

**Prüfungen:**

- Request/Response-Kontrakt mit Backend
- Fehlerbehandlung (catch-Blöcke, UI-Feedback)
- Defensive Programmierung (Null-Checks, Array-Validierung)
- Browser-Konsole auf Fehler prüfen

### 2.3 Datenbank (SQLite)

- **Schema:** `db/schema.py`, `db/migrations/*.sql`
- **Daten:** `data/traffic.db`, `data/customers.db`
- **Queries:** SQL-Statements in Services und Repositories

**Prüfungen:**

- Schema-Konsistenz (Code vs. reale DB)
- Migrationen (ALTER TABLE, CREATE INDEX)
- Indizes (Performance bei großen Tabellen)
- Datenkonsistenz (Constraints, Foreign Keys)

### 2.4 Infrastruktur / Externe Dienste

- **OSRM:** Docker-Container, Endpoints, Timeouts
- **LLM-APIs:** OpenAI, Ollama (falls genutzt)
- **Konfiguration:** ENV-Variablen, Ports, URLs
- **Health-Checks:** `/health/osrm`, `/api/osrm/metrics`

**Prüfungen:**

- Erreichbarkeit (Ping, Health-Endpoints)
- Timeouts und Retry-Logic
- Fehlerbehandlung bei Ausfall externer Dienste

---

## 3. Keine isolierten Fixes

**Regel:**

- Niemals nur eine einzelne Datei ändern, ohne zu prüfen, wo sie überall verwendet wird.
- Immer nach Seiteneffekten suchen (z.B. geänderte Response-Formate → Frontend anpassen).

**Vorgehen:**

1. **Grep/Search:** Finde alle Verwendungen der geänderten Funktion/Klasse/API
2. **Impact-Analyse:** Welche anderen Module sind betroffen?
3. **Kontrakt-Prüfung:** Ändert sich ein API-Kontrakt (Request/Response)?
4. **Tests anpassen:** Schlagen existierende Tests fehl?

**Beispiel:**

```python
# Backend: Response-Format geändert
# VORHER:
return {"subRoutes": [...]}

# NACHHER:
return {"sub_routes": [...]}  # snake_case statt camelCase

# → Frontend MUSS angepasst werden!
# → Alle Tests, die dieses Format erwarten, müssen angepasst werden!
```

---

## 4. Tests sind Pflicht

**Für jeden Bugfix:**

- Mindestens einen **Regressionstest** vorschlagen (und idealerweise anlegen)
- Der Test soll sicherstellen, dass der konkrete Fehler nicht zurückkommt

**Test-Kategorien:**

1. **Unit Tests:** Einzelne Funktionen/Services testen
2. **Integration Tests:** API-Endpoints End-to-End testen
3. **Frontend Tests:** UI-Interaktionen testen (optional: Playwright)

**Beispiel:**

```python
# Test für Sub-Routen-Generator Bug
def test_subroutes_generator_with_w_tours():
    """
    Regression-Test für Bug #XYZ:
    Sub-Routen-Generator wirft TypeError bei W-Touren mit >4 Kunden
    """
    payload = {
        "tours": [
            {"key": "W07", "customers": ["Kunde1", "Kunde2", "Kunde3", "Kunde4", "Kunde5"]}
        ]
    }
    response = client.post("/api/tour/optimize", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "sub_routes" in data
    assert isinstance(data["sub_routes"], list)
```

---

### 🎯 Golden Test Cases (für kritische Features)

**Zweck:** Kugelsicherer Modus für kritische Workflows

**Golden Tests sind:**
- Referenz-Testfälle mit bekanntem, erwartetem Output
- Müssen IMMER gleich bleiben (deterministisch)
- Decken reale, produktive Szenarien ab

**Für kritische Features pflegen:**
- Sub-Routen-Generator
- OSRM-Routing
- Tour-Upload & Parsing
- Adress-Matching

**Beispiel: Golden Test für Sub-Routen-Generator**

```python
# tests/golden/test_golden_subroutes.py

GOLDEN_TOUR_W01 = {
    "tour_name": "W01",
    "customers": ["Kunde A", "Kunde B", "Kunde C", "Kunde D", "Kunde E"],
    "expected_subroutes": 2,
    "expected_customer_split": {
        "sub_route_1": ["Kunde A", "Kunde B", "Kunde C"],
        "sub_route_2": ["Kunde D", "Kunde E"]
    }
}

def test_golden_w01_subroutes():
    """Golden Test: W01 muss immer identisch aufgeteilt werden"""
    result = generate_subroutes(GOLDEN_TOUR_W01)
    
    assert len(result["sub_routes"]) == GOLDEN_TOUR_W01["expected_subroutes"]
    assert result["sub_routes"][0]["customers"] == GOLDEN_TOUR_W01["expected_customer_split"]["sub_route_1"]
    assert result["sub_routes"][1]["customers"] == GOLDEN_TOUR_W01["expected_customer_split"]["sub_route_2"]
```

**Pflege:**
- Golden Tests in `tests/golden/` ablegen
- 3-5 Beispieltouren pflegen (W-Touren, große Touren, Edge Cases)
- Bei jedem Fix dokumentieren: Welche Golden Tests sind betroffen?
- Bei jedem Fix dokumentieren: Wie manuell prüfen (UI + Logs)?

**Cursor-Pflicht bei kritischen Fixes:**

```
OUTPUT MUSS ENTHALTEN:

1. Golden Tests, die betroffen sind
   - z.B. "test_golden_w01_subroutes"

2. Manuelle Testanleitung:
   - UI: "Sub-Routen Generator" Button klicken, W01 hochladen
   - Logs: "sub_routes" in Response prüfen
   - Erwartetes Ergebnis: 2 Sub-Routen, Kunden A-C in Route 1, D-E in Route 2
```

---

## 5. Dokumentation aktualisieren

**Nach jedem relevanten Fix:**

1. **LESSONS_LOG.md:** Neuer Eintrag für wiederkehrende Fehlertypen
2. **API-Dokumentation:** Bei geänderten Endpoints aktualisieren
3. **Inline-Kommentare:** Komplexe Fixes kommentieren
4. **CHANGELOG.md:** Nutzer-relevante Änderungen dokumentieren

**Format für LESSONS_LOG.md:**

```md
## YYYY-MM-DD – [Kurzbeschreibung]

**Symptom:** ...
**Ursache:** ...
**Fix:** ...
**Was die KI künftig tun soll:** ...
```

---

## 6. Sicherheit und Robustheit im Blick behalten

### Input-Validierung

- **Backend:** Pydantic-Modelle für alle Requests
- **Frontend:** Defensive Checks vor API-Calls
- **SQL:** Keine String-Konkatenation, immer Prepared Statements

### Fehlerbehandlung

- **Try-Catch:** Alle externen Aufrufe (OSRM, LLM, DB)
- **Logging:** Strukturiertes Logging mit Kontext (keine sensiblen Daten!)
- **User-Feedback:** Klare Fehlermeldungen im UI

### Timeouts

- **OSRM:** Max. 30 Sekunden
- **LLM-APIs:** Max. 60 Sekunden
- **DB-Queries:** Max. 10 Sekunden (Warnung bei Überschreitung)

### Sensitive Daten

**NIEMALS in Logs schreiben:**

- Passwörter
- API-Keys
- Vollständige Kundenadressen (nur Kürzel)
- Persönliche Daten (DSGVO)

**Erlaubt:**

- Request-IDs
- Fehler-Codes
- Anonymisierte Daten (z.B. "Kunde #123")

---

## 7. Cursor muss seine Änderungen transparent machen

**Jede Code-Änderung erfordert:**

1. **Erklärung:** Warum wurde diese Änderung vorgenommen?
2. **Kontext:** Was wurde behoben / verbessert?
3. **Diff:** Vorher/Nachher klar darstellen
4. **Impact:** Welche anderen Teile sind betroffen?

**Dokumentations-Format:**

```md
### Fix: [Kurzbeschreibung]

**Datei:** `path/to/file.py`
**Zeilen:** 123-145

**Problem:**
- [Was war kaputt]

**Lösung:**
- [Was wurde geändert]

**Vorher:**
```python
def broken_function():
    return None  # Bug
```

**Nachher:**
```python
def fixed_function():
    return {"data": []}  # Korrekter Rückgabewert
```

**Erwartete Userwirkung:**
- [Was sieht/erlebt der Benutzer nach dem Fix?]
```

---

## 8. Audit-Workflow (Schritt für Schritt)

### Phase 1: Vorbereitung

1. **Scope definieren** (siehe Regel 1)

2. **⚠️ PFLICHT: Multi-Layer-Kontext sicherstellen**
   
   **Jeder Audit MUSS mindestens eine Datei aus jedem betroffenen Layer im Kontext haben:**
   
   - [ ] **Backend:** Min. 1x `routes/*.py` oder `backend/routes/*.py` oder `services/*.py`
   - [ ] **Frontend:** Min. 1x `frontend/*.js` oder `frontend/*.html`
   - [ ] **Datenbank (falls beteiligt):** `db/schema.py` oder SQL-Dateien
   - [ ] **Infrastruktur (falls beteiligt):** `services/osrm_client.py`, ENV-Config
   
   **Faustregel:** Bug im UI sichtbar = Backend + Frontend PFLICHT!
   
   **Warum?** Verhindert isolierte Fixes, die andere Layer kaputt machen.

3. **Relevante Dateien identifizieren** (Backend, Frontend, DB)
4. **Logs sammeln** (Server-Logs, Browser-Konsole)
5. **Screenshots anfertigen** (falls UI-Bug)

### Phase 2: Analyse

5. **Backend prüfen** (siehe Regel 2.1)
6. **Frontend prüfen** (siehe Regel 2.2)
7. **Datenbank prüfen** (siehe Regel 2.3)
8. **Infrastruktur prüfen** (siehe Regel 2.4)
9. **API-Kontrakt validieren** (Request/Response)

### Phase 3: Diagnose

10. **Root Cause identifizieren** (nicht nur Symptom!)
11. **Seiteneffekte analysieren** (siehe Regel 3)
12. **Fix-Strategie planen** (Reihenfolge, Prioritäten)

### Phase 4: Umsetzung

13. **Code ändern** (Backend, Frontend, DB)
14. **Tests schreiben** (siehe Regel 4)
15. **Dokumentation aktualisieren** (siehe Regel 5)
16. **Änderungen erklären** (siehe Regel 7)

### Phase 5: Verifikation

17. **Syntax-Check** (`python -m compileall`, `npm run lint`)
18. **Tests ausführen** (`pytest`, `npm test`)
19. **Manuelle Tests** (UI durchklicken, API-Calls testen)
20. **Logs prüfen** (keine neuen Fehler)

### Phase 6: Abschluss

21. **Audit-Dokument erstellen** (siehe Regel 9)
22. **ZIP-Archiv anlegen** (siehe Regel 10)
23. **LESSONS_LOG aktualisieren** (falls neuer Fehlertyp)

---

## 9. Audit-Dokumentation (Pflicht-Format)

Jedes Audit erzeugt ein Markdown-Dokument mit folgender Struktur:

```md
# Code-Audit: [Titel]
**Datum:** YYYY-MM-DD
**Bereich:** Backend/Frontend/DB/Infrastruktur
**Dateien:** [Liste]

---

## Executive Summary
✅ [Anzahl] Fehler behoben
⚠️ [Anzahl] Warnungen
📊 Code-Qualität: [Vorher] → [Nachher]

---

## 1. Problem-Identifikation
### Symptome
### Root Cause

## 2. Durchgeführte Fixes
### Fix 1: [Titel]
### Fix 2: [Titel]
...

## 3. API-Kontrakt-Prüfung
### Backend-Response
### Frontend-Verarbeitung

## 4. Tests & Verifikation
### Syntax-Check
### Manuelle Tests

## 5. Code-Qualität Metriken
### Vorher
### Nachher

## 6. Lessons Learned

## 7. Nächste Schritte

## 8. Anhang: Geänderte Dateien

## 9. Checkliste (abgehakt)
```

---

## 10. ZIP-Archiv-Struktur

Jedes Audit erzeugt ein ZIP im Ordner `zip/` mit folgender Struktur:

```
AUDIT_<THEMA>_YYYYMMDD_HHMMSS_<SESSION_ID>.zip
├── AUDIT_REPORT.md          ← Haupt-Dokument (siehe Regel 9)
├── logs/
│   ├── server.log           ← Backend-Logs
│   ├── browser-console.txt  ← Frontend-Fehler
│   └── stacktraces.txt      ← Python-Tracebacks
├── code/
│   ├── before/              ← Code VOR dem Fix
│   │   ├── file1.py
│   │   └── file2.js
│   └── after/               ← Code NACH dem Fix
│       ├── file1.py
│       └── file2.js
├── screenshots/
│   ├── error-ui.png
│   └── fixed-ui.png
└── tests/
    └── regression_test.py   ← Neuer Test
```

**Dateinamen-Konvention:**

- `<THEMA>`: Kurzbeschreibung (z.B. `SubRoutenGenerator`, `OSRMTimeout`)
- `YYYYMMDD`: Datum (z.B. `20251114`)
- `HHMMSS`: Uhrzeit (z.B. `143022`)
- `<SESSION_ID>`: Eindeutige ID (optional, z.B. `abc123`)

**Beispiel:**

```
AUDIT_SubRoutenGenerator_20251114_143022_xyz.zip
```

---

## 11. Verbotene Praktiken

**NIEMALS:**

1. ❌ Nur Symptom beheben, Root Cause ignorieren
2. ❌ Code ändern, ohne zu testen
3. ❌ Breaking Changes ohne Dokumentation
4. ❌ Sensible Daten in Logs schreiben
5. ❌ Fehler stillschweigend verschlucken (`pass`, leere `except`)
6. ❌ Architektur ohne Rücksprache umbauen
7. ❌ Alte Bugs mit neuen Bugs überdecken
8. ❌ Nicht reproduzierbare Fixes ("hat bei mir funktioniert")

---

## 12. Erlaubte Praktiken

**IMMER:**

1. ✅ Defensive Programmierung (Null-Checks, Type-Checks)
2. ✅ Strukturiertes Logging mit Kontext
3. ✅ Input-Validierung auf allen Ebenen
4. ✅ Fehlerbehandlung mit User-Feedback
5. ✅ Tests für jeden Fix
6. ✅ Klare Commit-Messages / Dokumentation
7. ✅ Code-Reviews (bei kritischen Änderungen)
8. ✅ Performance-Messungen (bei Optimierungen)

---

## 13. Eskalation bei Unsicherheit

**Wenn Cursor sich unsicher ist:**

1. **Dokumentieren:** Was ist unklar? Welche Optionen gibt es?
2. **Fragen:** Explizit nach Klärung fragen, bevor Code geändert wird
3. **Alternativen:** Mehrere Lösungsansätze vorschlagen
4. **Risiken:** Potenzielle Seiteneffekte benennen

**Beispiel:**

```md
## Unsicherheit bei Fix-Strategie

**Problem:** API-Response-Format ändern (camelCase → snake_case)

**Option 1:** Nur Backend ändern
- ✅ Einfach
- ❌ Bricht Frontend

**Option 2:** Backend + Frontend ändern
- ✅ Konsistent
- ❌ Aufwändiger

**Option 3:** Beide Formate unterstützen (Deprecation)
- ✅ Abwärtskompatibel
- ❌ Komplexer

**Empfehlung:** Option 2 (Breaking Change ist akzeptabel in Dev-Phase)
```

---

## 14. Versionierung

Dieses Dokument wird fortlaufend aktualisiert. Änderungen werden dokumentiert:

| Version | Datum | Änderung |
|---------|-------|----------|
| 1.0 | 2025-11-14 | Initiale Version |

---

**Ende der Grundregeln**  
**Nächste Schritte:** `AUDIT_CHECKLISTE.md` und `LESSONS_LOG.md` lesen

