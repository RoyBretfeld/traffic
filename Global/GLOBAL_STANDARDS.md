# 🌍 Globale Entwicklungs-Standards mit Cursor

**Version:** 1.0  
**Stand:** 2025-11-14  
**Zweck:** Universelle Regeln für **alle Projekte** mit Cursor AI  
**Gültigkeit:** Projektübergreifend (Sprache, Framework, Infrastruktur unabhängig)

---

## 📋 Übersicht

Diese Datei beschreibt **allgemeine Regeln**, die in *jedem* Projekt mit Cursor gelten sollen – unabhängig von Sprache, Framework oder Infrastruktur.

**Ziel:** Änderungen sollen **nachvollziehbar**, **testbar** und **reproduzierbar** sein.

---

## 🎯 1. Ziel

- ✅ Änderungen sollen **nachvollziehbar**, **testbar** und **reproduzierbar** sein.
- ✅ Cursor (oder eine andere LLM-KI) arbeitet immer nach dem gleichen, klar definierten Ablauf.
- ✅ Fehler führen zu **Lessons Learned**, nicht zu Chaos-Rewrites.

---

## 📁 2. Verzeichnisse & Dateien (Standard-Struktur)

Folgende Dateien/Struktur werden in **jedem Projekt** erwartet:

```
<Projekt-Root>/
│
├── Regeln/                                    ← Zentrale Standards (NEU!)
│   ├── STANDARDS.md                          ⭐ Ausführliche Standards & Prinzipien
│   ├── STANDARDS_QUICK_REFERENCE.md          🚀 Kurzreferenz (Checkliste-Style)
│   ├── REGELN_AUDITS.md                      🔍 Wie Code-Audits ablaufen müssen
│   ├── AUDIT_CHECKLISTE.md                   ✅ Konkrete Prüfpunkte
│   ├── CURSOR_PROMPT_TEMPLATE.md             🤖 Vorlage, wie Cursor gebrieft wird
│   ├── CURSOR_WORKFLOW.md                    🔄 6-Schritt-Workflow für Änderungen
│   ├── LESSONS_LOG.md                        📝 Logbuch für Fehler & Learnings
│   └── README.md                             📖 Übersicht aller Regeln
│
├── audits/                                    ← Arbeitsordner für laufende Audits
│   └── zip/                                  📦 Fertige Audit-ZIP-Pakete
│
├── PROJECT_PROFILE.md                         ← Projektspezifisches Profil
├── README.md                                  ← Projekt-Übersicht
└── REGELN_HIER.md                            ← Wegweiser zu Regeln/ (optional)
```

**Diese Struktur ist global** und soll in allen Repos gleich aussehen.

---

## 🔧 3. Allgemeine Arbeitsregeln für Cursor

### **Regel 1: Dokumente zuerst lesen**

**Immer zuerst diese Dateien lesen:**
1. `README.md` - Projekt-Übersicht
2. `Regeln/STANDARDS.md` - Vollständige Standards
3. `Regeln/REGELN_AUDITS.md` - Audit-Regeln
4. `Regeln/LESSONS_LOG.md` - Bekannte Fehler & Lösungen
5. `PROJECT_PROFILE.md` - Projektspezifische Details (falls vorhanden)

**Niemals blind coden ohne diese Dokumente gelesen zu haben!**

---

### **Regel 2: Nie direkt auf `main`/`master` arbeiten**

**Branching-Strategie:**
- ✅ Immer Feature-/Fix-Branch verwenden
- ✅ In Cursor: Änderungen als Patch/Commit-Vorschlag
- ❌ Niemals direkt auf `main`/`master` committen

**Branch-Naming:**
```
feature/kurze-beschreibung
fix/bug-beschreibung
refactor/bereich-beschreibung
docs/dokumentations-update
```

**Commit-Messages:** Conventional Commits verwenden
```
feat: Neue Feature hinzugefügt
fix: Bug XYZ behoben
docs: README aktualisiert
refactor: Code-Struktur verbessert
test: Tests für Feature X hinzugefügt
```

---

### **Regel 3: Kleine, fokussierte Änderungen**

**Prinzip:** One Thing At A Time

- ✅ Pro Audit/Commit nur **eine** klar abgegrenzte Änderung
- ✅ Ein Bug-Fix = Ein Commit
- ✅ Ein Feature = Ein Feature-Branch
- ❌ Kein Big-Bang-Refactor
- ❌ Keine vermischten Änderungen (z.B. Bug-Fix + Feature + Refactor in einem Commit)

**Beispiel (GUT):**
```
Commit 1: fix: Sub-Routen-Generator 500er Fehler behoben
Commit 2: test: Unit-Tests für Sub-Routen-Generator hinzugefügt
Commit 3: docs: Sub-Routen-Generator Dokumentation aktualisiert
```

**Beispiel (SCHLECHT):**
```
Commit 1: Verschiedene Fixes und Verbesserungen
  - Sub-Routen-Generator gefixt
  - Frontend aufgeräumt
  - React migriert
  - Tests hinzugefügt
```

---

### **Regel 4: Kein „Blind-Refactor" (Ghost-Refactor-Verbot)**

**Verboten:**
- ❌ Projekt-weite Umbenennungen ohne Freigabe
- ❌ Framework-Migration ohne ausdrücklichen Auftrag
- ❌ Globale Code-Style-Änderungen (außer mit Linter)
- ❌ Umbenennung von API-Endpoints ohne API-Kontrakt-Update

**Erlaubt:**
- ✅ Lokales Refactoring innerhalb eines Moduls (wenn nötig für Fix)
- ✅ Code-Style-Fixes via Linter (Black, ESLint, etc.)
- ✅ Dokumentation verbessern

**Cursor ändert nur Dateien, die im jeweiligen Audit-Kontext relevant sind.**

---

### **Regel 5: Immer Tests & Checks**

**Wenn Tests existieren:**
- ✅ Nach jeder Änderung Tests ausführen
- ✅ Neue Tests für neue Features
- ✅ Regressionstest für Bug-Fixes

**Wenn keine Tests existieren:**
- ✅ Vorschlag machen, welche minimalen Tests angelegt werden sollten
- ✅ Mindestens manuelle Test-Anleitung dokumentieren

**Test-Checkliste:**
```
[ ] Syntax-Checks (python -m py_compile, node --check)
[ ] Unit-Tests (pytest, jest)
[ ] Integration-Tests (API-Endpoints)
[ ] Manuelle Tests (UI-Workflows)
[ ] Health-Checks (Server-Start, DB-Verbindung)
```

---

### **Regel 6: Frontend + Backend immer gemeinsam denken (Multi-Layer-Pflicht)**

**Prinzip:** Ganzheitliche Betrachtung

**Betroffene Layer immer prüfen:**
- ✅ **Backend** (Python, Node.js, etc.)
- ✅ **Frontend** (JavaScript, HTML, CSS)
- ✅ **Datenbank** (Schema, Migrationen)
- ✅ **Infrastruktur** (Config, ENV-Variablen, externe Services)

**Niemals nur Backend fixen, wenn der Fehler klar einen Frontend-Anteil hat.**

**API-Änderungen:**
- ✅ Backend + Frontend gemeinsam anpassen
- ✅ API-Kontrakt dokumentieren (Request/Response-Schema)
- ✅ Beide Seiten testen

**Siehe:** `Regeln/REGELN_AUDITS.md` → Regel 2 (Ganzheitlich prüfen)

---

### **Regel 7: Kein Mockup-Regression**

**Verboten:**
- ❌ Cursor darf nicht auf alte Mockups/Prototypen zurückfallen
- ❌ Funktionierende Logik überschreiben, nur weil Beispielcode „schöner" aussieht
- ❌ Produktions-Code durch Demo-Code ersetzen

**Erlaubt:**
- ✅ Code verbessern (Performance, Lesbarkeit)
- ✅ Bugs fixen
- ✅ Defensive Checks hinzufügen

**Regel:** Production-Code hat Vorrang vor Mockups/Demos!

---

## 📝 4. Standard-Ablauf für ein Audit

Jedes Audit (egal welches Projekt) folgt diesem **6-Schritt-Muster**:

### **Schritt 1: Kontext sammeln**

**Input:**
- Fehlerbeschreibung / Ticket / Screenshot
- Log-Auszüge (Backend-Logs, Browser-Konsole)
- Reproduktionsschritte

**Aktion:**
- Relevante Dateien identifizieren
- Projektprofil lesen (`PROJECT_PROFILE.md` o.ä.)
- `LESSONS_LOG.md` auf ähnliche Fehler prüfen

**Output:**
- Liste der betroffenen Dateien (Backend, Frontend, Config, DB)

---

### **Schritt 2: Hypothese formulieren**

**Fragen:**
- Was ist *wahrscheinlich* die Ursache?
- Welche Teile des Systems sind betroffen? (Backend, Frontend, DB, Infra)
- Gibt es ähnliche Fehler in `LESSONS_LOG.md`?

**Output:**
- Hypothese: "Sub-Routen-Generator wirft 500er wegen fehlendem OSRM-Fallback"
- Betroffene Layer: Backend (workflow_api.py), Frontend (index.html), OSRM (Infra)

---

### **Schritt 3: Code-Analyse**

**Aktion:**
- Betroffene Module/Dateien Schritt für Schritt durchgehen
- Logging, Exceptions, HTTP-Statuscodes, DB-Zugriffe checken
- API-Kontrakt prüfen (Backend ↔ Frontend)

**Defensive Checks prüfen:**
- Null-Checks vorhanden?
- Try-Catch-Blöcke vorhanden?
- Timeout-Handling?
- Error-Messages sinnvoll?

**Output:**
- Root Cause identifiziert
- Liste der zu ändernden Dateien

---

### **Schritt 4: Fix-Vorschlag**

**Aktion:**
- Konkrete Änderungen mit Begründung
- Keine unnötigen Stil-/Format-Rewrites
- Defensive Programmierung hinzufügen (Null-Checks, Try-Catch)

**Output:**
- Diff pro Datei (kompakt)
- Begründung pro Änderung
- API-Kontrakt-Update (falls relevant)

**Beispiel:**
```
Datei: backend/routes/workflow_api.py
Zeile: 1234-1250

Änderung: OSRM-Timeout-Handling hinzugefügt

Vorher:
  route = await osrm_client.get_route(coords)

Nachher:
  try:
      route = await osrm_client.get_route(coords)
  except OSRMTimeout:
      # Fallback: Haversine-Distanz
      route = calculate_haversine_fallback(coords)

Begründung: Verhindert 500er bei OSRM-Timeout
```

---

### **Schritt 5: Tests / Verifikation**

**Automatische Tests:**
- Unit-Tests schreiben (pytest, jest)
- Integration-Tests (API-Calls)
- Syntax-Checks

**Manuelle Tests:**
- Server starten
- Workflow durchklicken (z.B. CSV-Upload → Sub-Routen-Generator)
- Health-Checks prüfen

**Testplan dokumentieren:**
```markdown
## Testplan

### Automatisch:
- [ ] pytest tests/backend/test_workflow.py
- [ ] python -m py_compile backend/routes/*.py

### Manuell:
- [ ] Server starten: python start_server.py
- [ ] Health-Check: http://localhost:8111/health
- [ ] UI-Test: CSV hochladen → Sub-Routen generieren
- [ ] Browser-Konsole: Keine Fehler
```

---

### **Schritt 6: Audit-ZIP erstellen**

**Zielordner:** `audits/zip/` oder `ZIP/`

**Dateiname:** `AUDIT_<THEMA>_<YYYYMMDD_HHMMSS>.zip`

**Beispiel:** `AUDIT_SubRouten_500_20251114_153022.zip`

**Inhalt:**
- ✅ Fehlerbeschreibung (`README.md` im ZIP)
- ✅ Relevante Quellcode-Dateien (Backend + Frontend)
- ✅ Log-Auszüge (wenn vorhanden)
- ✅ Screenshots / Ablaufbeschreibung
- ✅ Vorher/Nachher-Diffs
- ✅ Testplan

**Cursor soll immer darauf achten, dass genug Kontext in diesem ZIP landet**, damit eine zweite KI oder ein Mensch die Situation nachvollziehen kann.

---

### **Schritt 7: Lessons eintragen**

**Wenn neuer Fehlertyp:**
- Eintrag in `Regeln/LESSONS_LOG.md` erstellen

**Template:**
```markdown
## YYYY-MM-DD – [Kurzbeschreibung]

**Kategorie:** Backend/Frontend/DB/Infrastruktur  
**Schweregrad:** 🔴 KRITISCH / 🟡 MEDIUM / 🟢 LOW  
**Dateien:** [Liste]

### Symptom
- [Was wurde beobachtet?]
- [Fehlermeldungen, Logs]

### Ursache
- [Root Cause identifizieren]
- [Warum ist das passiert?]

### Fix
- [Konkrete Codeänderungen]
- [Dateinamen, Zeilen, Funktionen]

### Ergebnis
- [Code-Qualität Vorher/Nachher]
- [Erwartete Userwirkung]

### Was die KI künftig tun soll
1. [Lehre 1]
2. [Lehre 2]
3. [Lehre 3]
```

---

## 📦 5. Vorgaben für Audit-ZIP-Pakete

### **Struktur:**

```
AUDIT_SubRouten_500_20251114_153022.zip
│
├── README.md                          ← Audit-Report (Problem, Fix, Tests)
├── backend/
│   ├── routes/
│   │   └── workflow_api.py           ← Betroffene Backend-Datei
│   └── services/
│       └── osrm_client.py            ← Betroffene Service-Datei
├── frontend/
│   └── index.html                     ← Betroffene Frontend-Datei (Auszug)
├── logs/
│   └── error_log_snippet.txt         ← Log-Auszüge
└── screenshots/
    └── error_500.png                  ← Screenshot des Fehlers
```

### **README.md im ZIP (Beispiel):**

```markdown
# Audit: Sub-Routen-Generator 500er Fehler

**Datum:** 2025-11-14  
**Audit-ID:** AUDIT_SubRouten_500_20251114_153022

## Problem
Sub-Routen-Generator wirft 500 Internal Server Error bei großen Touren (>15 Stopps).

## Root Cause
OSRM-Timeout bei großen Touren → kein Fallback → 500er

## Fix
- OSRM-Timeout-Handling in workflow_api.py (Zeile 1234-1250)
- Haversine-Fallback bei Timeout
- Frontend: Try-Catch um API-Call

## Tests
- [x] pytest tests/backend/test_workflow.py
- [x] Manuell: CSV mit 20 Stopps → Sub-Routen generieren
- [x] Health-Check: /health/osrm

## Dateien
- backend/routes/workflow_api.py (geändert)
- backend/services/osrm_client.py (geändert)
- frontend/index.html (geändert, Zeile 4406-4475)
```

---

## 🛡️ 6. Safety & Robustheit (Globale Prinzipien)

Diese Prinzipien gelten in **jedem Projekt**, unabhängig von Technologie:

### **Defensive Programmierung**

**Immer:**
- ✅ Null-Checks vor Zugriff auf Objekte/Arrays
- ✅ Try-Catch um externe API-Calls
- ✅ Timeout-Handling (max. 10-30s)
- ✅ Input-Validierung (Pydantic, Joi, etc.)
- ✅ Sinnvolle Error-Messages (nicht nur "Error" oder "Fehler")

**Beispiele:**

**Python:**
```python
# BAD
route = osrm_client.get_route(coords)

# GOOD
try:
    route = await asyncio.wait_for(
        osrm_client.get_route(coords),
        timeout=10.0
    )
except asyncio.TimeoutError:
    route = calculate_haversine_fallback(coords)
except Exception as e:
    logger.error(f"OSRM-Fehler: {e}")
    raise HTTPException(500, detail=f"Routing fehlgeschlagen: {str(e)}")
```

**JavaScript:**
```javascript
// BAD
const data = response.json();
data.results.forEach(r => ...);

// GOOD
let data;
try {
    data = await response.json();
} catch (e) {
    console.error('JSON-Parse-Fehler:', e);
    showError('Ungültige Server-Antwort');
    return;
}

if (!Array.isArray(data.results)) {
    console.error('results ist kein Array:', data);
    return;
}

data.results.forEach(r => ...);
```

---

### **Explizite Checks statt Magie**

**Immer prüfen, niemals annehmen:**
- ✅ Health-Endpoints für externe Services (DB, OSRM, APIs)
- ✅ Status-Seiten (z.B. `/health`, `/status`)
- ✅ Explizite Validierung (nicht: "wird schon passen")

**Beispiel:**
```python
# BAD
def process_data(data):
    return data['results'][0]['name']  # Kann crashen!

# GOOD
def process_data(data):
    if not data or 'results' not in data:
        raise ValueError("Ungültige Daten: 'results' fehlt")
    
    if not isinstance(data['results'], list) or len(data['results']) == 0:
        raise ValueError("'results' ist leer oder kein Array")
    
    return data['results'][0].get('name', 'Unbekannt')
```

---

### **Logs statt Schweigen**

**Jede unerwartete Abweichung soll logbar sein:**
- ✅ Strukturierte Logs (JSON wenn möglich)
- ✅ Log-Level korrekt verwenden (DEBUG, INFO, WARNING, ERROR)
- ✅ Trace-IDs für Request-Tracking
- ✅ Kontext in Logs (User-ID, Request-ID, Timestamp)

**Beispiel:**
```python
import logging
logger = logging.getLogger(__name__)

# BAD
logger.info("Fehler")

# GOOD
logger.error(
    "OSRM-Timeout bei Route-Berechnung",
    extra={
        "trace_id": trace_id,
        "tour_id": tour_id,
        "stops_count": len(stops),
        "osrm_url": osrm_client.base_url,
        "timeout_s": 10
    }
)
```

---

### **Keine stillen Breaking Changes**

**API-Änderungen immer dokumentieren:**
- ✅ Changelog führen (CHANGELOG.md)
- ✅ API-Versionierung (z.B. `/api/v1/`, `/api/v2/`)
- ✅ Deprecation Warnings (min. 1 Version vorher)

**Beispiel:**
```python
# Wenn API-Endpoint geändert wird:

# Alt (deprecated):
@router.post("/api/optimize")  # ⚠️ DEPRECATED
async def optimize_tour_old(...):
    warnings.warn("Dieser Endpoint ist deprecated. Nutze /api/v2/optimize", DeprecationWarning)
    return await optimize_tour_new(...)

# Neu:
@router.post("/api/v2/optimize")
async def optimize_tour_new(...):
    # Neue Implementierung
    pass
```

---

## 🚀 7. Verwendung in neuen Projekten

Um diese Standards in einem **neuen Projekt** zu nutzen:

### **Schritt 1: Struktur kopieren**

```bash
# Erstelle Regeln-Ordner
mkdir -p Regeln audits/zip

# Kopiere Standard-Dateien
cp <altes-projekt>/Regeln/GLOBAL_STANDARDS.md Regeln/
cp <altes-projekt>/Regeln/STANDARDS.md Regeln/
cp <altes-projekt>/Regeln/STANDARDS_QUICK_REFERENCE.md Regeln/
cp <altes-projekt>/Regeln/REGELN_AUDITS.md Regeln/
cp <altes-projekt>/Regeln/AUDIT_CHECKLISTE.md Regeln/
cp <altes-projekt>/Regeln/CURSOR_PROMPT_TEMPLATE.md Regeln/
cp <altes-projekt>/Regeln/CURSOR_WORKFLOW.md Regeln/
cp <altes-projekt>/Regeln/LESSONS_LOG.md Regeln/  # Leere Vorlage
```

---

### **Schritt 2: Standards projektspezifisch anpassen**

**Datei:** `Regeln/STANDARDS.md`

**Was anpassen:**
- Technologie-Stack (Python/Node.js/etc.)
- Framework-spezifische Regeln (FastAPI/Django/Express/etc.)
- Projekt-spezifische Konventionen

**Was NICHT anpassen:**
- Globale Prinzipien (Defensive Programmierung, etc.)
- Audit-Workflow (6 Schritte)
- Ghost-Refactor-Verbot

---

### **Schritt 3: PROJECT_PROFILE.md erstellen**

**Datei:** `PROJECT_PROFILE.md` (im Projekt-Root)

```markdown
# Projekt-Profil: <Projektname>

**Technologie-Stack:**
- Backend: Python 3.10 + FastAPI
- Frontend: Vanilla JavaScript + HTML/CSS
- Datenbank: SQLite (Production: PostgreSQL)
- Infrastruktur: Docker + OSRM

**Architektur:**
- API-First (REST)
- Microservices: Nein (Monolith)
- Deployment: Docker Compose

**Kritische Features:**
- Sub-Routen-Generator
- CSV-Upload + Geocoding
- OSRM-Integration

**Bekannte Schwachstellen:**
- OSRM-Timeouts bei großen Touren
- Encoding-Probleme bei CSV (UTF-8 vs ISO-8859-1)

**Lessons Learned:**
- Siehe: Regeln/LESSONS_LOG.md

**Ansprechpartner:**
- Backend: [Name]
- Frontend: [Name]
- DevOps: [Name]
```

---

### **Schritt 4: Cursor-Prompt anpassen**

**Datei:** `Regeln/CURSOR_PROMPT_TEMPLATE.md`

Passe Template #1 (Ganzheitliches Audit) an:
- Füge projektspezifische Dateien hinzu
- Füge projektspezifische Regeln hinzu

---

### **Schritt 5: .gitignore erweitern**

```bash
# .gitignore
audits/zip/*.zip
.master.key
.env.local
data/*.db
```

---

### **Schritt 6: README.md aktualisieren**

Füge Abschnitt "Standards & Regeln" hinzu:

```markdown
## 📘 Standards & Regeln

**Zentrale Dokumentation:** [`Regeln/`](Regeln/)

**Für Entwickler:**
- [STANDARDS_QUICK_REFERENCE.md](Regeln/STANDARDS_QUICK_REFERENCE.md) - Tägliche Arbeit
- [CURSOR_WORKFLOW.md](Regeln/CURSOR_WORKFLOW.md) - 6-Schritt-Prozess

**Für Cursor-KI:**
- [CURSOR_PROMPT_TEMPLATE.md](Regeln/CURSOR_PROMPT_TEMPLATE.md) - Bug-Fix-Templates
- [REGELN_AUDITS.md](Regeln/REGELN_AUDITS.md) - 7 unverhandelbare Regeln
- [LESSONS_LOG.md](Regeln/LESSONS_LOG.md) - Bekannte Fehler & Lösungen
```

---

## ✅ 8. Checkliste für neues Projekt

Vor dem ersten Code-Commit:

```markdown
[ ] Regeln/-Ordner erstellt
[ ] GLOBAL_STANDARDS.md kopiert
[ ] STANDARDS.md projektspezifisch angepasst
[ ] PROJECT_PROFILE.md erstellt
[ ] LESSONS_LOG.md (leer) erstellt
[ ] CURSOR_PROMPT_TEMPLATE.md angepasst
[ ] audits/zip/ erstellt
[ ] .gitignore erweitert
[ ] README.md aktualisiert (Verweis auf Regeln/)
[ ] Erster Commit: "docs: Standards & Regeln-Struktur initialisiert"
```

---

## 📖 9. Verwandte Dokumente

**In diesem Projekt:**
- `Regeln/STANDARDS.md` - Projektspezifische Standards
- `Regeln/CURSOR_WORKFLOW.md` - 6-Schritt-Workflow
- `Regeln/REGELN_AUDITS.md` - 7 Audit-Regeln
- `Regeln/LESSONS_LOG.md` - Lernbuch

**Projektübergreifend:**
- Diese Datei (`GLOBAL_STANDARDS.md`) - Universelle Regeln

---

## 🎯 10. Zusammenfassung

**Diese Standards machen Cursor zu einem reproduzierbaren, nachvollziehbaren Entwicklungs-Tool.**

**Die 7 wichtigsten Regeln:**
1. ✅ Dokumente zuerst lesen
2. ✅ Nie direkt auf `main` arbeiten
3. ✅ Kleine, fokussierte Änderungen
4. ❌ Kein Ghost-Refactoring
5. ✅ Immer Tests & Checks
6. ✅ Frontend + Backend gemeinsam denken
7. ❌ Kein Mockup-Regression

**Der 6-Schritt-Audit-Prozess:**
1. Kontext sammeln
2. Hypothese formulieren
3. Code-Analyse
4. Fix-Vorschlag
5. Tests / Verifikation
6. Audit-ZIP erstellen
7. Lessons eintragen

**Damit werden diese Regeln zu wiederverwendbaren Grundpfeilern für jede zukünftige App.**

---

**Version:** 1.0  
**Letzte Aktualisierung:** 2025-11-14  
**Gültigkeit:** Projektübergreifend

🌍 **Universell. Reproduzierbar. Nachvollziehbar.**

