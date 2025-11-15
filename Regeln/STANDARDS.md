# Entwicklungsstandards & Richtlinien

**Version:** 2.0 ⭐ **KI-Audit-Framework integriert**  
**Gültig für:** Alle FAMO-Projekte  
**Letzte Aktualisierung:** 2025-11-14

---

## 📋 Inhaltsverzeichnis

1. [Cursor KI Arbeitsrichtlinien](#cursor-ki-arbeitsrichtlinien)
2. [KI-Audit-Framework (PFLICHT)](#ki-audit-framework-pflicht) ⭐ **NEU**
3. [LLM-Integration im Programm](#llm-integration-im-programm) ⭐ **NEU**
4. [Coding Standards](#coding-standards)
5. [Architektur-Prinzipien](#architektur-prinzipien)
6. [API-Standards](#api-standards)
7. [Testing-Standards](#testing-standards)
8. [Git & Versionierung](#git--versionierung)
9. [Deployment & Operations](#deployment--operations)
10. [Audit & Compliance](#audit--compliance)
11. [Dokumentations-Standards](#dokumentations-standards)

---

## Cursor KI Arbeitsrichtlinien

### Grundprinzipien

1. **Commit early, commit often**
   - Jeder funktionierende Zwischenstand wird sofort versioniert
   - Stabiler Kontext für Cursor erhalten
   - Empfohlen: `git commit -m "Checkpoint: Modul X funktionsfähig"`

2. **Eine Aufgabe pro Prompt**
   - Pro Prompt nur **eine** Aufgabe
   - ❌ "Erstelle Logging, refactore DB und verbessere Auth"
   - ✅ "Erstelle Logging-Service mit File- und Console-Ausgabe"

3. **KI-Vorschläge sind Vorschläge, keine Wahrheit**
   - Vorschläge als Diff prüfen, nicht blind übernehmen
   - Import- und Typfehler entstehen oft durch Autovervollständigung

### Kontextmanagement

- **Kontext bewusst auswählen**: Nur relevante Dateien pinnen oder im Prompt benennen
- **Offene Tabs minimieren**: Zu viele offene Dateien führen zu veralteten Abhängigkeiten
- **Modular arbeiten**: Klare Schnittstellen definieren (TypeScript: `export interface`, Python: `TypedDict`/`Protocol`)

### Abhängigkeiten & Build-Konsistenz

- **Lockfiles nie manuell löschen**: Cursor bezieht API- und Typinformationen daraus
- **Lokaler Build ist maßgeblich**: Cursor validiert nur Syntax, nicht Laufzeit
- **Keine Silent-Renames**: Nach jedem größeren KI-Commit `git diff` prüfen

### Versionskontrolle

- **Commit vor jedem KI-Refactor**: Versehentlich zerstörte Module leicht zurückrollen
- **Commit-Messages mit Kontext**: `Refactor: Cursor Vorschlag zu AuthService angewendet`
- **Branching-Strategie**: Cursor-Experimente in eigenen Branches (`feature/ki-login-refactor`)

### Troubleshooting

Wenn nach einer KI-Aktion etwas "nicht mehr geht":
1. `git diff` prüfen – oft sind Barrel-Exports oder Pfade verändert
2. Lokalen Build laufen lassen
3. Cursor-Cache löschen (Command Palette → "Clear Editor Context")
4. Bei wiederkehrenden Fehlern: Datei explizit ausschließen (`# KI nicht ändern` Kommentar)

---

## KI-Audit-Framework (PFLICHT) ⭐

### 🎯 Grundprinzip: Ganzheitliches Denken

**IMMER prüfen:** Backend **UND** Frontend **UND** Datenbank **UND** Infrastruktur

> "Kein isolierter Fix mehr! Jede Änderung wird im Gesamtkontext bewertet."

### Zentrale Dokumentation

Alle KI-Audit-Regeln befinden sich in: **`docs/ki/`**

| Dokument | Zweck | Verbindlich |
|----------|-------|-------------|
| **[README.md](ki/README.md)** | Framework-Übersicht & Workflow | ✅ JA |
| **[REGELN_AUDITS.md](ki/REGELN_AUDITS.md)** | Grundregeln für alle Audits | ✅ JA |
| **[AUDIT_CHECKLISTE.md](ki/AUDIT_CHECKLISTE.md)** | 9-Punkte-Checkliste | ✅ JA |
| **[LESSONS_LOG.md](ki/LESSONS_LOG.md)** | Dokumentierte Fehler & Lösungen | ✅ JA |
| **[CURSOR_PROMPT_TEMPLATE.md](ki/CURSOR_PROMPT_TEMPLATE.md)** | 10 fertige Audit-Prompts | ✅ JA |

**Quick-Referenz:** [`KI_AUDIT_FRAMEWORK.md`](../KI_AUDIT_FRAMEWORK.md) (Projekt-Root)

### Die 7 Unverhandelbaren Regeln

#### 1. Scope explizit machen
Zu Beginn jedes Audits:
- Welches Feature/Endpoint/UI-Element?
- Welche Symptome (Fehler, Logs, Screenshots)?
- Reproduktionsschritte dokumentieren

#### 2. Immer ganzheitlich prüfen

**Backend (Python/FastAPI):**
- Routes, Services, Business Logic
- Exception-Handling, Logging
- Input-Validierung, Timeouts
- Konfiguration (ENV-Variablen)

**Frontend (HTML/CSS/JavaScript):**
- Entry Points, Event-Handler
- Alle `fetch()` API-Calls
- Request/Response-Kontrakt mit Backend
- Defensive Programmierung (Null-Checks, Array-Validierung)
- Browser-Konsole auf Fehler prüfen

**Datenbank (SQLite):**
- Schema-Konsistenz (Code vs. DB)
- Migrationen (ALTER TABLE, CREATE INDEX)
- Indizes für Performance
- Datenkonsistenz (Constraints)

**Infrastruktur:**
- OSRM: Erreichbarkeit, Timeouts, Health-Checks
- LLM-APIs: Verfügbarkeit, Fallback-Strategien
- ENV-Variablen: Vollständigkeit, Defaults
- Docker: Container-Status, Logs

#### 3. Keine isolierten Fixes

**Vor jeder Änderung prüfen:**
1. **Grep/Search:** Wo wird diese Funktion/API noch verwendet?
2. **Impact-Analyse:** Welche Module sind betroffen?
3. **Kontrakt-Prüfung:** Ändert sich ein API-Kontrakt (Request/Response)?
4. **Tests anpassen:** Schlagen existierende Tests fehl?

**Beispiel:**
```python
# ❌ FALSCH: Nur Backend ändern
# Backend: Response-Format geändert von camelCase zu snake_case
return {"sub_routes": [...]}  # Vorher: {"subRoutes": [...]}

# ✅ RICHTIG: Backend + Frontend + Tests
# 1. Backend: snake_case
# 2. Frontend: data.sub_routes statt data.subRoutes
# 3. Defensive Check: if (data && Array.isArray(data.sub_routes))
# 4. Tests: Erwartetes Format aktualisieren
```

#### 4. Tests sind Pflicht

**Für jeden Bugfix:**
- Mindestens **1 Regressionstest** schreiben
- Test soll sicherstellen, dass Bug nicht zurückkommt
- Test-Kategorien: Unit, Integration, E2E

**Test-Template:**
```python
def test_bugfix_xyz():
    """
    Regression-Test für Bug #XYZ:
    [Kurzbeschreibung des Bugs]
    """
    # Arrange: Setup
    payload = { ... }
    
    # Act: Aktion
    response = client.post("/api/endpoint", json=payload)
    
    # Assert: Validierung
    assert response.status_code == 200
    data = response.json()
    assert "expected_field" in data
    assert isinstance(data["expected_field"], expected_type)
```

#### 5. Dokumentation aktualisieren

**Nach jedem relevanten Fix:**
1. **LESSONS_LOG.md:** Eintrag für neue Fehlertypen
2. **API-Dokumentation:** Bei geänderten Endpoints
3. **Inline-Kommentare:** Komplexe Fixes erklären
4. **CHANGELOG.md:** Nutzer-relevante Änderungen

**LESSONS_LOG-Format:**
```md
## YYYY-MM-DD – [Kurzbeschreibung]

**Symptom:** [Was wurde beobachtet?]
**Ursache:** [Root Cause]
**Fix:** [Konkrete Lösung]
**Was die KI künftig tun soll:** [Lehren für Zukunft]
```

#### 6. Sicherheit und Robustheit

**Input-Validierung:**
- Backend: Pydantic-Modelle für alle Requests
- Frontend: Defensive Checks vor API-Calls
- SQL: Keine String-Konkatenation, nur Prepared Statements

**Fehlerbehandlung:**
- Try-Catch um externe Aufrufe (OSRM, LLM, DB)
- Strukturiertes Logging mit Kontext
- User-Feedback: Klare Fehlermeldungen im UI

**Timeouts:**
- OSRM: Max. 30 Sekunden
- LLM-APIs: Max. 60 Sekunden
- DB-Queries: Max. 10 Sekunden

**NIEMALS in Logs schreiben:**
- Passwörter, API-Keys
- Vollständige Kundenadressen
- Persönliche Daten (DSGVO)

#### 7. Transparenz bei Änderungen

**Jede Code-Änderung erfordert:**
1. **Erklärung:** Warum?
2. **Kontext:** Was wurde behoben?
3. **Diff:** Vorher/Nachher
4. **Impact:** Welche Teile sind betroffen?
5. **Erwartete Userwirkung:** Was ändert sich für den Benutzer?

### Audit-Workflow (6 Phasen)

#### Phase 1: Vorbereitung
1. Scope definieren
2. Relevante Dateien identifizieren
3. Logs sammeln
4. Screenshots anfertigen

#### Phase 2: Analyse
5. Backend prüfen
6. Frontend prüfen
7. Datenbank prüfen
8. Infrastruktur prüfen
9. API-Kontrakt validieren

#### Phase 3: Diagnose
10. Root Cause identifizieren
11. Seiteneffekte analysieren
12. Fix-Strategie planen

#### Phase 4: Umsetzung
13. Code ändern
14. Tests schreiben
15. Dokumentation aktualisieren
16. Änderungen erklären

#### Phase 5: Verifikation
17. Syntax-Check
18. Tests ausführen
19. Manuelle Tests
20. Logs prüfen

#### Phase 6: Abschluss
21. Audit-Dokument erstellen
22. ZIP-Archiv anlegen (bei größeren Audits)
23. LESSONS_LOG aktualisieren

### Code-Review Standards

**Jedes Code-Review muss:**

✅ **Backend prüfen:**
- Routes, Services, Error-Handling
- Logging, Timeouts, Validierung

✅ **Frontend prüfen:**
- API-Calls, Event-Handler
- Defensive Checks, Error-Boundaries
- Browser-Konsole (keine Fehler)

✅ **API-Kontrakt prüfen:**
- Request/Response-Format konsistent?
- Feldnamen identisch (Backend ↔ Frontend)?
- Datentypen kompatibel?

✅ **Datenbank prüfen:**
- Schema-Konsistenz
- Migrationen bei Schema-Änderungen
- Indizes für Performance

✅ **Tests prüfen:**
- Mindestens 1 Regressionstest
- Coverage ≥ 80%
- Edge Cases abgedeckt

✅ **Dokumentation prüfen:**
- Code-Kommentare aktualisiert
- LESSONS_LOG bei neuem Fehlertyp
- API-Docs bei Endpoint-Änderungen

### Verbotene Praktiken

**NIEMALS:**

1. ❌ Nur Symptom beheben, Root Cause ignorieren
2. ❌ Code ändern ohne zu testen
3. ❌ Breaking Changes ohne Dokumentation
4. ❌ Isolierte Fixes (nur Backend ODER nur Frontend)
5. ❌ Fehler stillschweigend verschlucken
6. ❌ Sensible Daten in Logs
7. ❌ Architektur ohne Rücksprache umbauen
8. ❌ Nicht reproduzierbare Fixes

### Erlaubte Praktiken

**IMMER:**

1. ✅ Ganzheitlich prüfen (Backend + Frontend + DB + Infra)
2. ✅ Defensive Programmierung (Null-Checks, Type-Checks)
3. ✅ Strukturiertes Logging mit Kontext
4. ✅ Input-Validierung auf allen Ebenen
5. ✅ Fehlerbehandlung mit User-Feedback
6. ✅ Tests für jeden Fix
7. ✅ Klare Commit-Messages
8. ✅ Root Cause identifizieren

### Standard-Prompts für Cursor

**Für vollständiges Audit:**
```
Führe einen vollständigen Code-Audit durch für: [FEATURE/BUG]

Folge strikt:
- docs/ki/REGELN_AUDITS.md
- docs/ki/AUDIT_CHECKLISTE.md

Prüfe ganzheitlich:
- Backend (Python/FastAPI)
- Frontend (HTML/CSS/JavaScript)
- Datenbank (SQLite)
- Infrastruktur (OSRM, ENV)

Identifiziere:
- Root Cause (nicht nur Symptom!)
- API-Kontrakte (Backend ↔ Frontend)
- Seiteneffekte

Liefere:
- Konkrete Fixes (mit Dateinamen und Zeilen)
- Mindestens 1 Regressionstest
- Audit-Dokument nach docs/ki/REGELN_AUDITS.md
- LESSONS_LOG-Eintrag (falls neuer Fehlertyp)
```

**Weitere Prompts:** Siehe `docs/ki/CURSOR_PROMPT_TEMPLATE.md`

### Audit-Dokumentation

**Jedes Audit erzeugt:**

1. **Audit-Dokument** (Markdown)
   - Executive Summary
   - Problem-Identifikation (Symptom + Root Cause)
   - Durchgeführte Fixes (Vorher/Nachher)
   - Tests & Verifikation
   - Code-Qualität Metriken
   - Lessons Learned
   - Nächste Schritte

2. **ZIP-Archiv** (bei größeren Audits)
   - Struktur: `ZIP/AUDIT_<THEMA>_YYYYMMDD_HHMMSS.zip`
   - Enthält: Logs, Code (Vorher/Nachher), Screenshots, Tests

3. **LESSONS_LOG-Eintrag** (bei neuem Fehlertyp)
   - Symptom, Ursache, Fix, Lehren für Zukunft

### Metriken & Monitoring

**Code-Qualität tracken:**

| Metrik | Ziel |
|--------|------|
| Syntax-Fehler | 0 |
| Defensive Checks | Alle kritischen Pfade |
| Memory Leaks | 0 |
| JSDoc/Docstring Coverage | ≥ 80% |
| Browser-Kompatibilität | Moderne Browser + Fallbacks |
| Test-Coverage | ≥ 80% |

**Häufigste Fehlertypen dokumentieren:**
- Schema-Drift (DB)
- Syntax-Fehler (Frontend/Backend)
- Missing Defensive Checks
- Memory Leaks
- API-Kontrakt-Inkonsistenzen

### Eskalation

**Bei Unsicherheit:**

1. **Dokumentieren:** Was ist unklar? Welche Optionen?
2. **Fragen:** Explizit nach Klärung fragen
3. **Alternativen:** Mehrere Lösungsansätze vorschlagen
4. **Risiken:** Potenzielle Seiteneffekte benennen

**Beispiel:**
```md
## Unsicherheit bei Fix-Strategie

**Problem:** API-Response-Format ändern

**Option 1:** Nur Backend ändern
- ✅ Einfach
- ❌ Bricht Frontend

**Option 2:** Backend + Frontend ändern
- ✅ Konsistent
- ❌ Aufwändiger

**Empfehlung:** Option 2 (ganzheitlich!)
```

---

## LLM-Integration im Programm ⭐

### 🤖 Übersicht: LLM im Produktions-Code

**Zweck:** Regeln für die Integration von Large Language Models (OpenAI/Ollama) in der FAMO TrafficApp

**Anwendungsfälle:**
- Adress-Erkennung (aus unstrukturierten Texten)
- Geocoding-Verbesserung
- Kunden-Matching
- Tour-Klassifizierung

**Wichtig:** LLM ist **Werkzeug**, keine Magie! Strikte Regeln befolgen!

---

### 🎯 Grundprinzip: LLM nur als letzter Fallback

**Defense-in-Depth Strategie:**

```
1. Blacklist      ← Bekannt fehlerhafte Adressen
2. Exact Match    ← Exakte Übereinstimmungen  
3. Regex          ← Musterbasierte Erkennung
4. Gazetteer      ← Ortsverzeichnis
5. Postal         ← Postleitzahlen-DB
6. Rules          ← Regelbasierte Logik
7. LLM (Fallback) ← NUR wenn alles andere fehlschlägt!
```

**Regel:** LLM ist **nicht** die erste Wahl, sondern die **letzte**!

**Warum?**
- Deterministisch > Probabilistisch
- Schnell > Langsam
- Kostenlos > Kostenpflichtig
- Nachvollziehbar > Black Box

---

### ⛔ Die 10 Verbote für LLM-Nutzung

#### 1. Kein LLM ohne Schema-Validierung

❌ **FALSCH:**
```python
result = llm.generate(prompt)
return result  # Blind vertrauen!
```

✅ **RICHTIG:**
```python
result = llm.generate(prompt)
validated = AddressSchema.parse(result)  # Pydantic-Validierung!
if not validated:
    raise ValidationError("LLM-Schema ungültig")
return validated
```

#### 2. Kein LLM ohne Verifikation

❌ **FALSCH:**
```python
address = llm.extract_address(text)
save_to_db(address)  # Keine Prüfung!
```

✅ **RICHTIG:**
```python
address = llm.extract_address(text)
if not is_plausible_address(address):
    log_to_quarantine(address, reason="LLM-Validation failed")
    metrics.increment("llm_invalid_result")
    raise ValidationError("Ungültige Adresse")
save_to_db(address)
```

#### 3. Kein LLM ohne Timeout

❌ **FALSCH:**
```python
response = llm_client.generate(prompt)  # Kann ewig dauern
```

✅ **RICHTIG:**
```python
response = llm_client.generate(
    prompt, 
    timeout=60  # Max. 60 Sekunden
)
```

#### 4. Kein LLM ohne Fehlerbehandlung

❌ **FALSCH:**
```python
try:
    result = llm.process(data)
except:
    result = None  # Silent fail
```

✅ **RICHTIG:**
```python
try:
    result = llm.process(data)
except LLMTimeout as e:
    logger.error(f"LLM Timeout: {e}", extra={"correlation_id": "..."})
    metrics.increment("llm_timeout")
    # Fallback auf regelbasierte Logik
    result = fallback_parser(data)
except LLMInvalidSchema as e:
    logger.error(f"LLM Invalid Schema: {e}")
    metrics.increment("llm_invalid_schema")
    result = fallback_parser(data)
```

#### 5. Kein LLM ohne Monitoring

✅ **PFLICHT: Metriken tracken**
```python
metrics.increment("llm_success")
metrics.increment("llm_failure")
metrics.increment("llm_timeout")
metrics.increment("llm_invalid_schema")
metrics.histogram("llm_latency_ms", value=latency)
metrics.gauge("llm_tokens_used", tokens)
metrics.gauge("llm_cost_usd", cost)
```

#### 6. Kein LLM ohne Rate-Limiting

✅ **PFLICHT: Rate-Limits setzen**
```python
if llm_rate_limiter.is_exceeded():
    logger.warning("LLM Rate-Limit erreicht")
    metrics.increment("llm_rate_limited")
    return fallback_parser(data)
```

#### 7. Kein LLM ohne Kosten-Kontrolle

✅ **PFLICHT: Budget überwachen**
```python
daily_cost = metrics.get("llm_cost_usd_today")
if daily_cost > DAILY_BUDGET:
    logger.error(f"LLM Budget überschritten: ${daily_cost}")
    alert("LLM-Kosten zu hoch!")
    # Deaktiviere LLM temporär
    ENABLE_LLM = False
```

#### 8. Kein LLM ohne Fallback

✅ **PFLICHT: Regelbasierter Fallback**
```python
def process_with_fallback(data):
    # 1. Versuche LLM
    if ENABLE_LLM:
        try:
            return llm_parser(data)
        except LLMError:
            pass
    
    # 2. Fallback: Regelbasiert
    return rule_based_parser(data)
```

#### 9. Kein LLM ohne Determinismus

✅ **PFLICHT: Temperature = 0.0**
```python
# Konfiguration
OPENAI_TEMPERATURE = 0.0  # Deterministisch!
OPENAI_SEED = 42          # Reproduzierbar

# Bei jedem Call
response = llm.generate(
    prompt=prompt,
    temperature=0.0,  # Gleicher Input = Gleicher Output
    seed=42
)
```

#### 10. Kein LLM ohne PII-Schutz

❌ **NIEMALS loggen:**
```python
logger.info(f"LLM Response: {full_customer_address}")  # PII!
logger.info(f"API Key: {OPENAI_API_KEY}")  # Secret!
```

✅ **RICHTIG:**
```python
logger.info("LLM erfolgreich", extra={
    "customer_id": "K123",  # Nur ID
    "plz": "01234",         # OK
    "city": "Dresden",      # OK  
    "street": "***",        # Anonymisiert!
    "latency_ms": 450
})
```

---

### 🔧 Sichere LLM-Integration (Template)

```python
from pydantic import BaseModel, ValidationError
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class AddressSchema(BaseModel):
    """Validiertes Schema für LLM-Antworten"""
    street: str
    number: str
    plz: str
    city: str
    confidence: float

def use_llm_safely(prompt: str, data: dict) -> Optional[AddressSchema]:
    """
    Sichere LLM-Nutzung mit allen Pflicht-Checks
    
    Returns:
        AddressSchema bei Erfolg
        None bei Fehler (Fallback nutzen!)
    """
    
    # 1. Pre-Check: Ist LLM verfügbar?
    if not llm_client.is_available():
        logger.warning("LLM nicht verfügbar, nutze Fallback")
        metrics.increment("llm_unavailable")
        return None
    
    # 2. Rate-Limiting prüfen
    if llm_rate_limiter.is_exceeded():
        logger.warning("LLM Rate-Limit erreicht")
        metrics.increment("llm_rate_limited")
        return None
    
    # 3. Budget-Check
    if daily_cost_exceeded():
        logger.error("LLM Budget überschritten")
        metrics.increment("llm_budget_exceeded")
        return None
    
    # 4. LLM-Call mit Timeout
    start_time = time.time()
    try:
        response = llm_client.generate(
            prompt=prompt,
            timeout=60,
            temperature=0.0,  # Deterministisch!
            max_tokens=500
        )
    except LLMTimeout as e:
        logger.error(f"LLM Timeout: {e}")
        metrics.increment("llm_timeout")
        return None
    except LLMError as e:
        logger.error(f"LLM Error: {e}")
        metrics.increment("llm_error")
        return None
    
    latency = (time.time() - start_time) * 1000
    
    # 5. Schema-Validierung (Pydantic)
    try:
        validated = AddressSchema.parse_raw(response)
    except ValidationError as e:
        logger.error(f"LLM Schema-Validierung fehlgeschlagen: {e}")
        metrics.increment("llm_invalid_schema")
        return None
    
    # 6. Business-Logic-Validierung
    if not is_plausible_address(validated):
        logger.warning("LLM-Adresse nicht plausibel")
        metrics.increment("llm_implausible")
        return None
    
    # 7. Confidence-Check
    if validated.confidence < LLM_CONFIDENCE_THRESHOLD:
        logger.warning(f"LLM Confidence zu niedrig: {validated.confidence}")
        metrics.increment("llm_low_confidence")
        return None
    
    # 8. Logging & Metriken (ohne PII!)
    logger.info("LLM erfolgreich", extra={
        "latency_ms": latency,
        "tokens": response.tokens,
        "confidence": validated.confidence,
        "plz": validated.plz,  # OK
        "city": validated.city  # OK
        # KEIN street, KEIN number!
    })
    metrics.increment("llm_success")
    metrics.histogram("llm_latency_ms", latency)
    metrics.gauge("llm_tokens", response.tokens)
    
    # 9. Kosten tracken
    cost = calculate_cost(response.tokens)
    metrics.gauge("llm_cost_usd", cost)
    
    return validated
```

---

### ⚙️ Konfiguration (ENV-Variablen)

**OpenAI:**
```bash
OPENAI_API_KEY=sk-...           # API-Key (secret!)
OPENAI_MODEL=gpt-4-turbo        # Modell
OPENAI_TIMEOUT=60               # Max. 60 Sekunden
OPENAI_MAX_TOKENS=500           # Token-Limit
OPENAI_TEMPERATURE=0.0          # Deterministisch!
OPENAI_SEED=42                  # Reproduzierbar
```

**Ollama (lokal):**
```bash
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
OLLAMA_TIMEOUT=60
```

**Feature-Flags:**
```bash
ENABLE_LLM_FALLBACK=true        # LLM als Fallback aktivieren?
LLM_CONFIDENCE_THRESHOLD=0.8    # Min. Confidence (0.0-1.0)
LLM_DAILY_BUDGET_USD=50         # Max. Kosten pro Tag
LLM_RATE_LIMIT=100              # Max. Calls pro Minute
```

---

### 📊 Monitoring & Alarme

**Metriken (Pflicht!):**

| Metrik | Zweck | Alarm bei |
|--------|-------|-----------|
| `llm_success` | Erfolgreiche Calls | - |
| `llm_failure` | Fehlgeschlagene Calls | > 10% aller Calls |
| `llm_timeout` | Timeouts | > 5 in 5min |
| `llm_invalid_schema` | Schema-Fehler | > 0 |
| `llm_latency_ms` | Response-Zeit | > 10s |
| `llm_tokens` | Token-Verbrauch | - |
| `llm_cost_usd` | Kosten (OpenAI) | > Budget |

**Alarme setzen:**
```python
# ⚠️ Schema-Fehler → Sofort Review!
if llm_invalid_schema > 0:
    alert("LLM Schema-Validation fehlgeschlagen → Prompt prüfen!")

# ⚠️ Viele Timeouts → Service down?
if llm_timeout > 5 in 5min:
    alert("Viele LLM Timeouts → OpenAI/Ollama down?")

# ⚠️ Hohe Kosten
if llm_cost_today > DAILY_BUDGET:
    alert(f"LLM Budget überschritten: ${llm_cost_today}")
    
# ⚠️ Niedrige Erfolgsrate
success_rate = llm_success / (llm_success + llm_failure)
if success_rate < 0.8:
    alert(f"LLM Erfolgsrate niedrig: {success_rate:.0%}")
```

---

### 🧪 Testing

**Unit Tests (mit Mocks):**
```python
def test_llm_with_mock():
    """LLM-Integration mit Mock testen (kein echtes LLM)"""
    
    mock_response = {
        "street": "Hauptstraße",
        "number": "123",
        "plz": "01234",
        "city": "Dresden",
        "confidence": 0.95
    }
    
    with patch('llm_client.generate', return_value=mock_response):
        result = use_llm_safely(prompt="...", data={})
        
        assert result.street == "Hauptstraße"
        assert result.confidence == 0.95

def test_llm_timeout_fallback():
    """LLM-Timeout → Fallback testen"""
    
    with patch('llm_client.generate', side_effect=LLMTimeout):
        result = process_with_fallback(data)
        
        # Sollte regelbasierten Fallback nutzen
        assert result is not None
        assert result.source == "fallback"

def test_llm_invalid_schema():
    """Ungültiges LLM-Schema → Exception"""
    
    invalid_response = {"invalid": "data"}
    
    with patch('llm_client.generate', return_value=invalid_response):
        result = use_llm_safely(prompt="...", data={})
        
        assert result is None  # Schema-Validierung schlägt fehl
```

**Golden Tests:**
```python
def test_llm_with_known_addresses():
    """Test mit bekannten Problem-Adressen"""
    
    golden_cases = [
        ("Hauptstr. 1, 01234 Dresden", "Hauptstraße", "1", "01234", "Dresden"),
        ("Am Markt 5, Heidenau", "Am Markt", "5", None, "Heidenau"),
        # ... mehr Fälle
    ]
    
    for input_text, expected_street, expected_nr, expected_plz, expected_city in golden_cases:
        result = use_llm_safely(prompt=input_text, data={})
        
        assert result.street == expected_street
        assert result.number == expected_nr
        # ...
```

---

### 💰 Kosten-Kontrolle

**OpenAI Kosten berechnen:**
```python
class CostTracker:
    """OpenAI Kosten tracken"""
    
    COSTS = {
        "gpt-4-turbo": {
            "input": 0.01,   # $ pro 1K tokens
            "output": 0.03   # $ pro 1K tokens
        }
    }
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """Kosten berechnen"""
        costs = self.COSTS[model]
        input_cost = (input_tokens / 1000) * costs["input"]
        output_cost = (output_tokens / 1000) * costs["output"]
        total = input_cost + output_cost
        
        # Loggen
        logger.info(f"LLM-Kosten: ${total:.4f}", extra={
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        })
        metrics.gauge("llm_cost_usd", total)
        
        return total
    
    def check_daily_budget(self, cost: float) -> bool:
        """Budget-Check"""
        today = date.today()
        daily_total = metrics.get(f"llm_cost_usd_total_{today}")
        
        if daily_total + cost > DAILY_BUDGET:
            logger.error(f"Budget überschritten: ${daily_total + cost:.2f}")
            return False
        
        return True
```

---

### 📚 Dokumentation

**Prompt-Dokumentation:**

Alle LLM-Prompts in `ai_models/pdf_ai_prompt.txt` oder ähnlich dokumentieren:

```markdown
# LLM-Prompt: Adress-Erkennung

## Zweck
Extrahiere strukturierte Adresse aus unstrukturiertem Text

## Input-Format
Text mit Adress-Informationen (Straße, Nummer, PLZ, Ort)

## Output-Format (JSON)
{
  "street": "Straßenname",
  "number": "Hausnummer",
  "plz": "Postleitzahl",
  "city": "Ort",
  "confidence": 0.0-1.0
}

## Beispiele
Input: "Hauptstr. 1, 01234 Dresden"
Output: {"street": "Hauptstraße", "number": "1", "plz": "01234", "city": "Dresden", "confidence": 0.95}

## Validierung
- street: nicht leer
- number: numerisch oder alphanumerisch (z.B. "12a")
- plz: 5 Ziffern (Deutschland)
- city: nicht leer
- confidence: 0.0-1.0
```

---

### 🔄 Fallback-Strategie

**Hierarchie:**

```
1. Regelbasierte Erkennung (schnell, deterministisch)
   ↓ Fehlschlag
2. Gazetteer/Postal-Lookup (mittel, deterministisch)
   ↓ Fehlschlag
3. LLM (langsam, probabilistisch)
   ↓ Fehlschlag
4. Quarantäne (manuell prüfen)
```

**Implementierung:**
```python
def process_address(text: str) -> Address:
    """
    Versuche mehrere Methoden in Reihenfolge
    """
    
    # 1. Regelbasiert (Regex, Pattern-Matching)
    try:
        address = rule_based_parser(text)
        if address.confidence > 0.9:
            metrics.increment("address_parsed_rules")
            return address
    except ParsingError:
        pass
    
    # 2. Gazetteer/Postal (Ortsverzeichnis, PLZ-DB)
    try:
        address = gazetteer_parser(text)
        if address.confidence > 0.85:
            metrics.increment("address_parsed_gazetteer")
            return address
    except ParsingError:
        pass
    
    # 3. LLM (falls aktiviert)
    if ENABLE_LLM_FALLBACK:
        address = use_llm_safely(prompt=text, data={})
        if address and address.confidence > LLM_CONFIDENCE_THRESHOLD:
            metrics.increment("address_parsed_llm")
            return address
    
    # 4. Quarantäne (manuell prüfen)
    logger.error("Adresse konnte nicht geparst werden", extra={
        "text_preview": text[:50] + "...",
        "correlation_id": "..."
    })
    quarantine.add(text, reason="Parsing failed (all methods)")
    metrics.increment("address_quarantine")
    raise ParsingError("Adresse nicht erkennbar")
```

---

### ✅ Checkliste: LLM-Integration

- [ ] **Schema-Validierung** (Pydantic)
- [ ] **Timeout** (60s max)
- [ ] **Fehlerbehandlung** (Try-Catch, Logging)
- [ ] **Monitoring** (Metriken, Alarme)
- [ ] **Rate-Limiting** (Calls pro Minute begrenzen)
- [ ] **Kosten-Kontrolle** (Budget, Alarme)
- [ ] **Fallback** (regelbasiert wenn LLM fehlschlägt)
- [ ] **PII-Schutz** (keine sensiblen Daten loggen)
- [ ] **Deterministisch** (Temperature = 0.0)
- [ ] **Tests** (Unit, Golden, Mocks)
- [ ] **Dokumentation** (Prompts, Schema, Beispiele)

---

## LLM für Code-Analyse & Code-Review ⭐

### 🔍 Übersicht: LLM als Code-Analyzer

**Zweck:** Regeln für die Nutzung von LLMs zur automatischen Code-Analyse und Code-Review

**Anwendungsfälle:**
- Automatische Code-Reviews (Qualität, Best Practices)
- Pattern-Erkennung (Anti-Patterns, Code Smells)
- Security-Analyse (Schwachstellen, Secrets)
- Dokumentations-Generierung (Docstrings, README)
- Refactoring-Vorschläge
- Test-Generierung

**Status:** 🚧 In Entwicklung / Experimentell

---

### 🎯 Grundprinzip: LLM als Assistent, nicht als Entscheider

**Regel:** LLM gibt **Vorschläge**, Entwickler **entscheidet**!

```
LLM-Analyse
    ↓
Vorschläge generieren
    ↓
Entwickler reviewt
    ↓
Entwickler akzeptiert/ablehnt
    ↓
Änderungen werden umgesetzt
```

**WICHTIG:** LLM ersetzt NICHT den menschlichen Code-Review!

---

### 📋 Anwendungsfall 1: Automatischer Code-Review

**Ziel:** LLM analysiert Code und gibt Feedback zu:
- Code-Qualität (Lesbarkeit, Wartbarkeit)
- Best Practices (PEP 8, FastAPI-Patterns)
- Potenzielle Bugs (Null-Checks, Error-Handling)
- Performance (ineffiziente Schleifen, DB-Queries)

**Implementierung:**

```python
def llm_code_review(file_path: str, code: str) -> CodeReviewResult:
    """
    LLM-basierter Code-Review
    
    Returns:
        CodeReviewResult mit Vorschlägen
    """
    
    prompt = f"""
Analysiere folgenden Python-Code und gib strukturiertes Feedback:

Datei: {file_path}

Code:
```python
{code}
```

Prüfe:
1. Code-Qualität (Lesbarkeit, Wartbarkeit)
2. Best Practices (PEP 8, Type-Hints, Docstrings)
3. Potenzielle Bugs (Null-Checks, Error-Handling, Edge Cases)
4. Performance (ineffiziente Operationen, N+1 Queries)
5. Security (SQL-Injection, XSS, Secrets im Code)

Format der Antwort (JSON):
{{
  "severity": "info|warning|error|critical",
  "category": "quality|best_practice|bug|performance|security",
  "line": 42,
  "message": "Kurzbeschreibung",
  "suggestion": "Konkreter Vorschlag zur Behebung",
  "example": "Code-Beispiel (optional)"
}}
"""
    
    # LLM-Call mit Validierung
    try:
        response = llm_client.generate(
            prompt=prompt,
            timeout=30,
            temperature=0.1,  # Leicht kreativ für Vorschläge
            max_tokens=2000
        )
        
        # Schema-Validierung
        results = CodeReviewSchema.parse(response)
        
        # Filtern: Nur relevante Vorschläge
        filtered = [r for r in results if r.severity in ['warning', 'error', 'critical']]
        
        return CodeReviewResult(
            file=file_path,
            suggestions=filtered,
            llm_used=True
        )
        
    except (LLMTimeout, ValidationError) as e:
        logger.warning(f"LLM Code-Review fehlgeschlagen: {e}")
        return CodeReviewResult(
            file=file_path,
            suggestions=[],
            llm_used=False,
            error=str(e)
        )
```

**Output-Schema:**

```python
from pydantic import BaseModel
from typing import Literal

class CodeReviewSuggestion(BaseModel):
    severity: Literal["info", "warning", "error", "critical"]
    category: Literal["quality", "best_practice", "bug", "performance", "security"]
    line: int
    message: str
    suggestion: str
    example: Optional[str] = None

class CodeReviewResult(BaseModel):
    file: str
    suggestions: List[CodeReviewSuggestion]
    llm_used: bool
    error: Optional[str] = None
```

---

### 📋 Anwendungsfall 2: Security-Analyse

**Ziel:** LLM findet potenzielle Sicherheitslücken

**Zu prüfen:**
- SQL-Injection (String-Konkatenation in Queries)
- XSS (Unescaped User-Input)
- Secrets im Code (API-Keys, Passwörter)
- Path-Traversal (User-Input in Dateipfaden)
- Command-Injection (User-Input in Shell-Befehlen)

**Implementierung:**

```python
def llm_security_scan(code: str) -> List[SecurityIssue]:
    """
    LLM-basierte Security-Analyse
    """
    
    prompt = f"""
Analysiere folgenden Code auf Sicherheitslücken:

```python
{code}
```

Prüfe insbesondere:
1. SQL-Injection (String-Konkatenation statt Prepared Statements)
2. XSS (Unescaped User-Input in Templates)
3. Secrets (API-Keys, Passwörter im Code)
4. Path-Traversal (User-Input in Dateipfaden ohne Validierung)
5. Command-Injection (User-Input in os.system, subprocess)
6. Fehlende Input-Validierung
7. Fehlende Authentication/Authorization

Format (JSON):
{{
  "issue_type": "sql_injection|xss|secrets|path_traversal|command_injection",
  "severity": "low|medium|high|critical",
  "line": 42,
  "description": "Beschreibung des Problems",
  "fix": "Konkrete Lösung",
  "cwe": "CWE-89" // Common Weakness Enumeration
}}
"""
    
    response = llm_client.generate(prompt, timeout=30)
    issues = SecurityIssueSchema.parse(response)
    
    # Filtern: Nur High + Critical
    critical_issues = [i for i in issues if i.severity in ['high', 'critical']]
    
    if critical_issues:
        alert(f"Security-Issues gefunden: {len(critical_issues)}")
    
    return critical_issues
```

---

### 📋 Anwendungsfall 3: Test-Generierung

**Ziel:** LLM generiert Unit-Tests für bestehenden Code

**Vorgehen:**

```python
def llm_generate_tests(function_code: str, function_name: str) -> str:
    """
    Generiere Unit-Tests für eine Funktion
    """
    
    prompt = f"""
Generiere Unit-Tests (pytest) für folgende Funktion:

```python
{function_code}
```

Anforderungen:
1. Teste Happy Path (normale Verwendung)
2. Teste Edge Cases (leere Inputs, None, etc.)
3. Teste Error-Handling (Exceptions)
4. Nutze pytest-Fixtures wo sinnvoll
5. Nutze Mocks für externe Dependencies
6. Teste alle Branches (if/else)

Format:
```python
import pytest
from unittest.mock import patch, Mock

def test_{function_name}_happy_path():
    # Arrange
    ...
    # Act
    ...
    # Assert
    ...

def test_{function_name}_edge_case_empty_input():
    ...

def test_{function_name}_error_handling():
    with pytest.raises(ValueError):
        ...
```
"""
    
    response = llm_client.generate(prompt, timeout=60, temperature=0.2)
    
    # Validiere generierten Code (Syntax-Check)
    try:
        compile(response, '<string>', 'exec')
    except SyntaxError as e:
        logger.error(f"LLM generierte ungültigen Code: {e}")
        return None
    
    return response
```

---

### 📋 Anwendungsfall 4: Dokumentations-Generierung

**Ziel:** LLM generiert Docstrings und README-Abschnitte

**Implementierung:**

```python
def llm_generate_docstring(function_code: str) -> str:
    """
    Generiere Google-Style Docstring für Funktion
    """
    
    prompt = f"""
Generiere einen Google-Style Docstring für folgende Funktion:

```python
{function_code}
```

Format:
```python
def function_name(...):
    \"\"\"Kurzbeschreibung (eine Zeile).
    
    Längere Beschreibung (optional).
    
    Args:
        param1 (type): Beschreibung
        param2 (type): Beschreibung
    
    Returns:
        return_type: Beschreibung
    
    Raises:
        ExceptionType: Wann wird diese Exception geworfen?
    
    Example:
        >>> function_name(param1, param2)
        expected_output
    \"\"\"
```
"""
    
    response = llm_client.generate(prompt, timeout=20)
    return response
```

---

### ⚠️ Einschränkungen & Risiken

**1. Halluzinationen:**
- LLM kann falsche Bugs "finden" (False Positives)
- LLM kann echte Bugs übersehen (False Negatives)
- **Lösung:** Immer durch Menschen validieren!

**2. Kontext-Limitierungen:**
- LLM sieht nur einen File, nicht das ganze System
- Kann Abhängigkeiten nicht vollständig verstehen
- **Lösung:** Kontext explizit mitgeben (Imports, Dependencies)

**3. Kosten:**
- Code-Review für große Codebase kann teuer werden
- OpenAI: ~$0.01 pro 1K Tokens
- **Lösung:** Nur für neue/geänderte Dateien, nicht ganze Codebase

**4. Datenschutz:**
- Code könnte sensible Informationen enthalten
- OpenAI speichert Anfragen (30 Tage)
- **Lösung:** Lokales LLM (Ollama) für sensiblen Code

---

### 🛠️ Best Practices für LLM-Code-Analyse

#### 1. Kontext mitgeben

```python
# ✅ RICHTIG: Kontext mitgeben
prompt = f"""
Projekt: FAMO TrafficApp
Framework: FastAPI + Pydantic
Datenbank: SQLite

Abhängigkeiten:
- from pydantic import BaseModel
- from fastapi import APIRouter

Code:
{code}

Prüfe auf Best Practices für FastAPI...
"""

# ❌ FALSCH: Kein Kontext
prompt = f"Prüfe diesen Code: {code}"
```

#### 2. Spezifische Prüfungen

```python
# ✅ RICHTIG: Spezifisch
prompt = "Prüfe auf SQL-Injection in DB-Queries"

# ❌ FALSCH: Zu allgemein
prompt = "Prüfe auf Fehler"
```

#### 3. Output validieren

```python
# ✅ RICHTIG: Schema-Validierung
results = CodeReviewSchema.parse(llm_response)

# Zusätzlich: Plausibilitäts-Check
for suggestion in results:
    if suggestion.line > total_lines:
        logger.warning(f"LLM gab ungültige Zeile an: {suggestion.line}")
        continue
```

#### 4. Menschliche Review-Pflicht

```python
# ✅ RICHTIG: LLM + Mensch
llm_suggestions = llm_code_review(code)
human_approved = []

for suggestion in llm_suggestions:
    if suggestion.severity == 'critical':
        # Automatisch akzeptieren
        human_approved.append(suggestion)
    else:
        # Zur manuellen Review
        review_queue.add(suggestion)

# ❌ FALSCH: Blind akzeptieren
for suggestion in llm_suggestions:
    apply_fix(suggestion)  # Ohne Review!
```

---

### 📊 Metriken für Code-Analyse

**Tracken:**

```python
# Erfolgsmetriken
metrics.increment("llm_code_review_completed")
metrics.gauge("llm_suggestions_count", len(suggestions))
metrics.gauge("llm_critical_issues", len(critical_issues))

# Akzeptanz-Rate
metrics.increment("llm_suggestions_accepted")
metrics.increment("llm_suggestions_rejected")

# False Positives
metrics.increment("llm_false_positive")  # Manuell markiert

# Kosten
metrics.gauge("llm_code_review_cost_usd", cost)
```

**Auswertung:**

```python
# Akzeptanz-Rate berechnen
acceptance_rate = accepted / (accepted + rejected)

if acceptance_rate < 0.5:
    logger.warning(f"LLM Akzeptanz-Rate niedrig: {acceptance_rate:.0%}")
    # Prompt optimieren!
```

---

### 🔄 Workflow: LLM-Code-Review Integration

**In CI/CD-Pipeline:**

```yaml
# .github/workflows/code-review.yml
name: LLM Code Review

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  llm-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Get changed files
        id: changed-files
        uses: tj-actions/changed-files@v35
      
      - name: LLM Code Review
        run: |
          for file in ${{ steps.changed-files.outputs.all_changed_files }}; do
            if [[ $file == *.py ]]; then
              python scripts/llm_code_review.py --file $file
            fi
          done
      
      - name: Post Review Comments
        uses: actions/github-script@v6
        with:
          script: |
            // Poste LLM-Vorschläge als PR-Kommentare
            const suggestions = JSON.parse(fs.readFileSync('review-results.json'));
            for (const suggestion of suggestions) {
              github.rest.pulls.createReviewComment({
                owner: context.repo.owner,
                repo: context.repo.repo,
                pull_number: context.issue.number,
                body: `🤖 LLM-Vorschlag: ${suggestion.message}\n\n${suggestion.suggestion}`,
                path: suggestion.file,
                line: suggestion.line
              });
            }
```

---

### ✅ Checkliste: LLM-Code-Analyse

- [ ] **Kontext mitgeben** (Projekt, Framework, Dependencies)
- [ ] **Spezifische Prüfungen** (Security, Performance, Best Practices)
- [ ] **Output-Validierung** (Schema, Plausibilität)
- [ ] **Menschliche Review** (Keine automatische Akzeptanz!)
- [ ] **Metriken tracken** (Akzeptanz-Rate, False Positives, Kosten)
- [ ] **False-Positive-Feedback** (LLM-Vorschläge bewerten)
- [ ] **Prompt-Optimierung** (Bei niedriger Akzeptanz-Rate)
- [ ] **Datenschutz** (Lokales LLM für sensiblen Code)
- [ ] **Kosten-Kontrolle** (Budget für Code-Reviews)
- [ ] **Integration in CI/CD** (Automatisch bei PRs)

---

### 🚧 Roadmap: Zukünftige Erweiterungen

**Phase 1: Proof of Concept (aktuell)**
- ✅ Basis-Code-Review (Qualität, Best Practices)
- ✅ Security-Scan (SQL-Injection, XSS, Secrets)
- ✅ Schema-Validierung

**Phase 2: Erweiterte Analyse**
- [ ] Performance-Analyse (N+1 Queries, ineffiziente Schleifen)
- [ ] Refactoring-Vorschläge (Code Smells, Duplikate)
- [ ] Test-Coverage-Analyse (Welche Branches fehlen?)
- [ ] Dependency-Analyse (veraltete Packages, Security-Alerts)

**Phase 3: Automatisierung**
- [ ] Auto-Fix für einfache Issues (z.B. Docstrings, Type-Hints)
- [ ] Test-Generierung für neue Funktionen
- [ ] Dokumentations-Generierung für APIs
- [ ] Code-Completion (kontextbezogen)

**Phase 4: Integration**
- [ ] IDE-Plugin (VS Code, Cursor)
- [ ] CI/CD-Integration (GitHub Actions, GitLab CI)
- [ ] Dashboard (Metriken, Trends, False-Positive-Rate)
- [ ] Feedback-Loop (Verbesserung durch User-Feedback)

---

### 📚 Weitere Ressourcen

- **Prompt-Templates:** `docs/ki/LLM_CODE_REVIEW_PROMPTS.md` (TODO)
- **Schema-Definitionen:** `backend/models/llm_schemas.py` (TODO)
- **CI/CD-Scripts:** `scripts/llm_code_review.py` (TODO)
- **Metriken-Dashboard:** `/admin/llm-metrics` (TODO)

---

## Coding Standards

### Python

- **Version**: Python ≥3.11
- **Pydantic**: v2 für Datenvalidierung
- **FastAPI**: Für REST-APIs
- **Zeitzone**: `TZ=UTC` in allen Services
- **Locale**: `LC_ALL=C.UTF-8` in allen Services

### Code-Qualität

- **Keine globalen Zustände**: Repos/Services als Konstruktor-Dependencies
- **Konfiguration**: Nur via ENV (12-Factor): `ENGINE_VERSION|RULESET_VERSION|REPAIR_VERSION|ROUTER_URL`
- **HTTP**: Zeitouts/Retry/Circuit-Breaker zentral in Client; keine Ad-hoc-Requests
- **Fehlerbehandlung**: 4xx für Userfehler, 5xx für Systemfehler; niemals 200 bei Fehlvalidierung
- **Logging**: Strukturiert (JSON), Felder: `correlation_id`, `tour_uid`, `stop_uid`, `phase`, `latency_ms`
- **Dependencies**: Versionsfix (`==`), kein Sniffing (CSV), kein `random` ohne Seed

### Encoding-Kontrakt

- **Lesen**: Heuristisch (cp850 / utf-8-sig / latin-1)
- **Schreiben/Export/Logs**: **Immer UTF-8**

### Unantastbare Bereiche

- `./Tourplaene/**` (Originale)
- `tools/orig_integrity.py`, `ingest/reader.py`
- Keine Änderungen durch Prompts ohne explizite Freigabe

---

## Architektur-Prinzipien

### Grundprinzipien

1. **Determinismus**: Gleicher Input ⇒ gleicher Output
   - Keine Zufallsquellen, keine kontextabhängigen Zeiten
   - Sortierung und Tie-Breaker festlegen

2. **Vertragstreue**: Eingehendes Format bleibt stabil
   - Keine Änderung/Umbenennung von Feldern upstream

3. **Defense-in-Depth**: 
   - Blacklist → Exact → Regex → Gazetteer/Postal → Rules → LLM (nur als Fallback)

4. **Transparenz**: 
   - Jede Änderung durch Events/Metriken belegbar (Audit-Log, Stats-API)
   - Kein "silent fix-up"

5. **Sicherheitsgurt**: 
   - Fehler ⇒ Quarantäne/HTTP-4xx, nicht heuristisch weiterrechnen

### Schichtarchitektur

```
Frontend (HTML/CSS/JS)
    ↓
API Layer (FastAPI Routes)
    ↓
Business Logic (Services)
    ↓
Data Access (Repositories)
    ↓
Database (SQLite/PostgreSQL)
```

### Modulare Struktur

- **Backend**: `backend/` - FastAPI Backend
- **Frontend**: `frontend/` - HTML/CSS/JS Frontend
- **Services**: `services/` - Business Logic
- **Repositories**: `repositories/` - Data Access
- **Database**: `db/` - Schema & Migrations
- **Scripts**: `scripts/` - Utility-Scripts
- **Tests**: `tests/` - Unit-Tests
- **Tools**: `tools/` - Development Tools

---

## API-Standards

### REST-Konventionen

- **GET**: Lesen (idempotent)
- **POST**: Erstellen/Ausführen (nicht idempotent)
- **PUT**: Vollständiges Update (idempotent)
- **PATCH**: Teilweises Update (idempotent)
- **DELETE**: Löschen (idempotent)

### Response-Format

```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-11-13T14:00:00Z",
    "version": "1.0.0"
  }
}
```

### Fehlerbehandlung

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Fehlerbeschreibung",
    "details": { ... }
  }
}
```

### HTTP-Status-Codes

- **200**: Erfolg
- **201**: Erstellt
- **400**: Client-Fehler (Validierung)
- **401**: Nicht authentifiziert
- **403**: Nicht autorisiert
- **404**: Nicht gefunden
- **422**: Unprocessable Entity (Validierungsfehler)
- **500**: Server-Fehler
- **503**: Service nicht verfügbar

### API-Dokumentation

- **OpenAPI/Swagger**: Automatisch generiert via FastAPI
- **Endpoint**: `/docs` (Swagger UI), `/openapi.json` (OpenAPI Schema)
- **Beispiele**: Jeder Endpoint sollte Beispiele enthalten

---

## Testing-Standards

### Test-Typen

1. **Unit-Tests**: Einzelne Funktionen/Klassen
2. **Integration-Tests**: Komponenten-Interaktion
3. **E2E-Tests**: Vollständige Workflows
4. **Golden-Tests**: Problemfälle (z.B. spezielle Adressen)
5. **Property-Tests**: Idempotenz, Set-Gleichheit
6. **Snapshot-Tests**: Optimize-Antworten (mit fixen Seeds)

### Coverage-Anforderungen

- **Minimum**: 80% Code-Coverage
- **Kritische Pfade**: 100% Coverage
- **CI-Fail**: Wenn Coverage unter 80% fällt

### Test-Struktur

```
tests/
├── unit/           # Unit-Tests
├── integration/    # Integration-Tests
├── e2e/            # End-to-End-Tests
└── fixtures/       # Test-Daten
```

### Test-Ausführung

```bash
# Alle Tests
pytest

# Mit Coverage
pytest --cov=backend --cov=repositories --cov=services

# Spezifische Tests
pytest tests/test_geocode_robust_simple.py -v
```

### Pre-commit-Hooks

- **Lint**: `ruff check`
- **Type-Check**: `mypy`
- **Tests**: `pytest` (schnelle Tests)
- **Format**: `ruff format`

---

## Git & Versionierung

### Branch-Strategie

- **main/master**: Produktions-Branch (immer deploybar)
- **develop**: Entwicklungs-Branch
- **feature/**: Feature-Entwicklung (`feature/engine-optimization`)
- **fix/**: Bugfixes (`fix/osrm-timeout`)
- **chore/**: Wartungsarbeiten (`chore/telemetry-update`)
- **governance/**: Governance-Änderungen (`governance/cursor-rules`)

### Commit-Messages (Conventional Commits)

```
feat: Neue Feature-Beschreibung
fix: Bugfix-Beschreibung
docs: Dokumentations-Änderung
test: Test-Änderung
refactor: Code-Refactoring
chore: Wartungsarbeit
```

### PR-Prozess

**PR-Checklist:**
- [ ] Keine Änderungen an unantastbaren Bereichen
- [ ] API-Kontrakte unverändert (oder Migrationsnotiz enthalten)
- [ ] Tests grün (Golden/Property/Snapshot) & Coverage ≥ 80%
- [ ] Timeouts/Retry/Circuit-Breaker konfiguriert
- [ ] LLM-Pfad strikt validiert (falls verwendet)
- [ ] Metriken & Logs erweitert
- [ ] Dokumentation aktualisiert

### CI/CD-Pipeline

- **Pre-commit**: Lint, Format, Type-Check
- **CI**: Tests, Coverage, Docker-Build
- **CD**: Automatisches Deployment (nach Review)

---

## Deployment & Operations

### Umgebungsvariablen (12-Factor)

Alle Konfiguration via ENV:
- `DATABASE_URL`
- `OSRM_BASE_URL`
- `OPENAI_API_KEY` (falls verwendet)
- `APP_ENV` (dev/staging/prod)
- `LOG_LEVEL`

### Docker

- **Dockerfile**: Multi-Stage Build
- **docker-compose.yml**: Service-Orchestrierung
- **Read-Only Mounts**: Original-Verzeichnisse read-only

### Logging

- **Format**: Strukturiert (JSON)
- **Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Felder**: `timestamp`, `level`, `message`, `correlation_id`, `context`
- **Ausgabe**: Console + File (rotierend)

### Monitoring

- **Health-Checks**: `/health/db`, `/health/osrm`
- **Metriken**: Prometheus-kompatibel
- **Alarme**: 
  - `osrm_unavailable > 0` in 5min ⇒ Warnung
  - `llm_invalid_schema > 0` ⇒ Review
  - `tours_pending_geo` steigt 3 Intervalle ⇒ GeoQueue prüfen

---

## Audit & Compliance

### ⭐ KI-Audit-Framework (PRIMÄR)

**Ziel**: Strukturierte, reproduzierbare, ganzheitliche Code-Audits mit Cursor AI

**Zentrale Dokumentation**: **`docs/ki/`**

| Dokument | Zweck |
|----------|-------|
| **[ki/README.md](ki/README.md)** | Framework-Übersicht & Workflow |
| **[ki/REGELN_AUDITS.md](ki/REGELN_AUDITS.md)** | Grundregeln für alle Audits |
| **[ki/AUDIT_CHECKLISTE.md](ki/AUDIT_CHECKLISTE.md)** | 9-Punkte-Checkliste |
| **[ki/LESSONS_LOG.md](ki/LESSONS_LOG.md)** | Dokumentierte Fehler & Lösungen |
| **[ki/CURSOR_PROMPT_TEMPLATE.md](ki/CURSOR_PROMPT_TEMPLATE.md)** | 10 fertige Prompts |

**Quick-Referenz**: [`KI_AUDIT_FRAMEWORK.md`](../KI_AUDIT_FRAMEWORK.md) (Projekt-Root)

**Alle Code-Reviews und Audits folgen diesem Framework!**

### Code-Audit Playbook (Legacy)

**Hinweis**: Wurde durch KI-Audit-Framework ersetzt. Für Altprojekte:

**Dokumentation**: Siehe **[CODE_AUDIT_PLAYBOOK.md](STANDARDS/CODE_AUDIT_PLAYBOOK.md)** für:
- Standard-Audit-Reihenfolge
- Fix-Vorschläge (Middleware, Frontend, Statuscodes, OSRM, DB)
- Cursor-Ablauf (deterministisch)
- PR-Template
- Artefakte-Packaging

### Audit-ZIP-Pipeline

**Ziel**: Ein Klick, ein ZIP. Alle audit-relevanten Dateien landen konsistent in `ZIP/` als `AUDIT_<YYYYMMDD_HHMMSS>_<shortsha>.zip`

**Verwendung**:
- **Linux/macOS**: `bash scripts/make_audit_zip.sh`
- **Windows**: `pwsh -File scripts/Make-AuditZip.ps1`
- **Direkt**: `python tools/make_audit_zip.py`

**Enthalten**:
- Manifest (Hashes, Commit, Branch)
- Logs, OpenAPI, Routenliste
- Sanitizierte `.env` (Secrets redacted)

**Details**: Siehe `tools/make_audit_zip.py`

### Secrets-Schutz

- **.env → .env.audit**: Ersetze Werte folgender Keys durch Platzhalter:
  - `OPENAI_API_KEY`, `DATABASE_URL`, `POSTGRES_PASSWORD`, `REDIS_URL`, `SMTP_PASSWORD`, `API_KEY`, `SECRET`, `TOKEN`
- **Nicht-geheim & hilfreich bleiben drin**: `OSRM_URL`, `OSRM_TIMEOUT`, `APP_ENV`

### Integritätsprüfung

- **SHA256-Hashes**: Für Original-Dateien
- **Pre-commit-Hooks**: Schutz vor versehentlichen Änderungen
- **CI/CD**: Automatische Validierung bei jedem Push/PR

---

## Dokumentations-Standards

### Struktur

```
docs/
├── STANDARDS.md           # Diese Datei (Zentrale Standards)
├── README.md              # Projekt-README
├── ARCHITECTURE.md        # System-Architektur
├── API.md                 # API-Dokumentation
├── DEVELOPMENT.md         # Entwickler-Guide
├── DEPLOYMENT.md          # Deployment-Guide
└── CHANGELOG.md           # Änderungsprotokoll
```

### Dokumentations-Prinzipien

1. **Aktuell halten**: Dokumentation muss mit Code synchronisiert sein
2. **Beispiele**: Jede Funktion sollte Beispiele enthalten
3. **Strukturiert**: Klare Gliederung, Inhaltsverzeichnis
4. **Wiederverwendbar**: Standards für alle Projekte

### Markdown-Standards

- **Überschriften**: H1 für Titel, H2 für Hauptabschnitte, H3 für Unterabschnitte
- **Code-Blöcke**: Mit Sprach-Tag (`python`, `bash`, `json`)
- **Links**: Relative Links zu anderen Dokumenten
- **Tabellen**: Für strukturierte Daten

### Changelog

- **Format**: [Keep a Changelog](https://keepachangelog.com/)
- **Kategorien**: Added, Changed, Deprecated, Removed, Fixed, Security
- **Datum**: ISO-Format (YYYY-MM-DD)

---

## Definition of Done (DoD)

Ein Feature ist "Done", wenn:

- [ ] Code implementiert und getestet
- [ ] Unit-Tests geschrieben (Coverage ≥ 80%)
- [ ] Integration-Tests bestanden
- [ ] Dokumentation aktualisiert
- [ ] Code-Review durchgeführt
- [ ] CI/CD-Pipeline grün
- [ ] Pre-commit-Hooks bestanden
- [ ] Metriken & Logs erweitert
- [ ] Keine Breaking Changes (oder Migrationsnotiz)

---

## Verbote (Anti-Anarchie-Liste)

- ❌ Keine Änderungen an unantastbaren Bereichen ohne explizite Freigabe
- ❌ Kein Index-Mapping/Koordinatenvergleich als Identität – nur UIDs
- ❌ Kein LLM ohne Schema/Validierung/Verifikation
- ❌ Keine externen HTTP-Calls ohne zentralen Client/Timeout/Retry
- ❌ Keine "silent fixes" – Fehler müssen sichtbar/quittiert sein
- ❌ Keine globalen Zustände
- ❌ Keine Ad-hoc-Requests im Codepfad
- ❌ Keine 200-Responses bei Fehlvalidierung

---

## Weiterführende Dokumentation

### KI-Audit-Framework (PRIMÄR) ⭐

- **Framework-Übersicht**: `docs/ki/README.md` ⭐ **NEU**
- **Audit-Grundregeln**: `docs/ki/REGELN_AUDITS.md` ⭐ **NEU**
- **Audit-Checkliste**: `docs/ki/AUDIT_CHECKLISTE.md` ⭐ **NEU**
- **Lessons Learned**: `docs/ki/LESSONS_LOG.md` ⭐ **NEU**
- **Cursor-Prompts**: `docs/ki/CURSOR_PROMPT_TEMPLATE.md` ⭐ **NEU**
- **Quick-Referenz**: `KI_AUDIT_FRAMEWORK.md` (Projekt-Root) ⭐ **NEU**

### Cursor AI

- **Cursor KI Betriebsordnung**: `docs/CURSOR_KI_BETRIEBSORDNUNG.md`
- **Cursor Arbeitsrichtlinie**: `docs/Cursor-Arbeitsrichtlinie.md`

### Code & Architektur

- **Code-Audit Playbook (Legacy)**: `docs/STANDARDS/CODE_AUDIT_PLAYBOOK.md`
- **Architektur**: `docs/Architecture.md`
- **API-Dokumentation**: `docs/Api_Docs.md`
- **Developer Guide**: `docs/DEVELOPER_GUIDE.md`

---

## Changelog

### Version 2.0 (2025-11-14) ⭐

**BREAKING CHANGE: KI-Audit-Framework ist jetzt PFLICHT!**

- ✅ **NEU:** Vollständiges KI-Audit-Framework in `docs/ki/`
- ✅ **NEU:** Ganzheitliche Code-Reviews (Backend + Frontend + DB + Infra)
- ✅ **NEU:** 7 unverhandelbare Audit-Regeln
- ✅ **NEU:** 10 fertige Cursor-Prompts für verschiedene Audit-Szenarien
- ✅ **NEU:** LESSONS_LOG für dokumentierte Fehler & Lösungen
- ✅ **NEU:** Strukturierter 6-Phasen-Audit-Workflow
- ✅ **NEU:** Code-Review-Standards (Backend + Frontend gemeinsam!)
- ✅ **ÄNDERUNG:** Alle Audits und Code-Reviews müssen ganzheitlich sein
- ✅ **ÄNDERUNG:** Isolierte Fixes sind verboten
- ✅ **ÄNDERUNG:** Tests sind Pflicht (mindestens 1 Regressionstest pro Fix)

**Migration:**
- Alle neuen Audits: Folgen Sie `docs/ki/REGELN_AUDITS.md`
- Alle Code-Reviews: Prüfen Sie Backend + Frontend + DB + Infrastruktur
- Bei Bugs: Schreiben Sie einen Regressionstest
- Bei neuen Fehlertypen: Aktualisieren Sie `docs/ki/LESSONS_LOG.md`

### Version 1.0 (2025-11-13)

- Initiale Version der zentralen Standards-Dokumentation
- Zusammenführung aller Best Practices

---

**Diese Standards gelten für alle FAMO-Projekte und sind verbindlich.**

**Ab Version 2.0: KI-Audit-Framework ist PFLICHT für alle Code-Reviews und Audits!**

