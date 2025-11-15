# 📘 STANDARDS V2.0 - Quick Reference

**Kompakte Übersicht aller Regeln**  
**Version:** 2.0  
**Stand:** 2025-11-14

> Vollständige Dokumentation: [`docs/STANDARDS.md`](STANDARDS.md)

---

## 🎯 **NEU: KI-Audit-Framework (PFLICHT!)** ⭐

### Die 7 Unverhandelbaren Regeln

1. **Scope explizit machen** → Feature, Endpoints, Symptome dokumentieren
2. **Immer ganzheitlich prüfen** → Backend + Frontend + DB + Infrastruktur (ALLE!)
3. **Keine isolierten Fixes** → Impact-Analyse, API-Kontrakt, Seiteneffekte prüfen
4. **Tests sind Pflicht** → Min. 1 Regressionstest pro Bugfix
5. **Dokumentation aktualisieren** → LESSONS_LOG, API-Docs, Kommentare
6. **Sicherheit & Robustheit** → Input-Validierung, Error-Handling, Timeouts
7. **Transparenz** → Erklärung, Kontext, Diff, Impact dokumentieren

**Mehr:** [`Regeln/REGELN_AUDITS.md`](REGELN_AUDITS.md)

---

### Ganzheitliche Code-Reviews (NEUE CHECKLISTE)

#### ✅ IMMER prüfen:

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

**API-Kontrakt:**
- Request/Response-Format konsistent?
- Feldnamen identisch (Backend ↔ Frontend)?
- Datentypen kompatibel?

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

#### ❌ VERBOTEN:

1. Isolierte Fixes (nur Backend ODER nur Frontend)
2. Code ändern ohne Tests
3. Breaking Changes ohne Dokumentation
4. Fehler stillschweigend verschlucken
5. Sensible Daten in Logs
6. Architektur ohne Rücksprache umbauen

#### 🎯 Golden Test Cases (Kugelsicherer Modus)

**Für kritische Features (Sub-Routen, OSRM, Tour-Upload):**

- Golden Tests pflegen (3-5 Referenz-Beispiele mit bekanntem Output)
- Tests in `tests/golden/` ablegen
- Bei jedem Fix dokumentieren:
  - Welche Golden Tests betroffen sind
  - Wie man sie manuell prüft (UI + Logs)
  - Erwartetes Ergebnis

**Cursor-Pflicht bei kritischen Fixes:**
```
OUTPUT MUSS ENTHALTEN:
1. Golden Tests, die betroffen sind (z.B. "test_golden_w01_subroutes")
2. Manuelle Testanleitung (UI-Schritte + Log-Checks)
3. Erwartetes Ergebnis (konkret)
```

**Mehr:** [`Regeln/AUDIT_CHECKLISTE.md`](AUDIT_CHECKLISTE.md)

---

## 1️⃣ **Cursor KI Arbeitsrichtlinien**

### Grundprinzipien

- ✅ **Commit early, commit often** (stabiler Kontext)
- ✅ **Eine Aufgabe pro Prompt** (keine Vermischung)
- ✅ **KI-Vorschläge prüfen** (nicht blind übernehmen)
- ❌ **KEIN Ghost-Refactoring** (siehe unten)

### Kontextmanagement

- ✅ Kontext bewusst auswählen (nur relevante Dateien)
- ✅ Offene Tabs minimieren (veraltete Abhängigkeiten vermeiden)
- ✅ Modular arbeiten (klare Schnittstellen)

### Versionskontrolle

- ✅ Commit vor jedem KI-Refactor
- ✅ Commit-Messages mit Kontext
- ✅ Branching: `feature/ki-*` für Experimente

### ⛔ KEIN Ghost-Refactoring!

**Regel:** Cursor darf NUR die explizit genannten Dateien anfassen.

**VERBOTEN:**
- ❌ Projekt-weite Umbenennungen (ohne separate Freigabe)
- ❌ Globales Suchen-Ersetzen (über mehrere Dateien)
- ❌ Architektur-Änderungen (ohne explizite Anfrage)
- ❌ "Kreative" Verbesserungen (außerhalb des Scopes)

**Wenn Refactor WIRKLICH nötig ist:**
1. **Eigener Prompt** ("Refactor [X] in [Y]")
2. **Eigener Branch** (`refactor/...`)
3. **Scope explizit** (z.B. "nur osrm_client + aufrufende Services")
4. **Review-Pflicht** (vor Merge)

**Checkliste nach jedem KI-Fix:**
- [ ] Wurden nur die angeforderten Dateien geändert?
- [ ] Gab es irgendwelche globalen Refactors?
- [ ] Falls ja → REJECT / genau überprüfen!

**Warum?** Verhindert: "Cursor hat heimlich was umbenannt und jetzt ist alles kaputt"

### Troubleshooting

Wenn nach KI-Aktion etwas "nicht mehr geht":
1. `git diff` prüfen (Barrel-Exports oder Pfade verändert?)
2. Lokalen Build laufen lassen
3. Cursor-Cache löschen (Command Palette → "Clear Editor Context")
4. Datei explizit ausschließen (`# KI nicht ändern` Kommentar)

---

## 2️⃣ **Coding Standards**

### Python

- **Version:** ≥3.11
- **Framework:** FastAPI + Pydantic v2
- **Zeitzone:** TZ=UTC (alle Services)
- **Locale:** LC_ALL=C.UTF-8
- **Encoding:** UTF-8 (immer beim Schreiben!)

### Code-Qualität

- ❌ Keine globalen Zustände
- ✅ Konfiguration via ENV (12-Factor)
- ✅ HTTP: Timeouts/Retry/Circuit-Breaker zentral
- ✅ Fehlerbehandlung: 4xx für User-Fehler, 5xx für System-Fehler
- ✅ Logging: Strukturiert (JSON), Felder: `correlation_id`, `tour_uid`, `stop_uid`
- ✅ Dependencies: Versionsfix (`==`), kein Sniffing

### Defensive Programmierung

**Backend:**
```python
# ✅ RICHTIG: Pydantic + Try-Catch
@router.post("/api/endpoint")
async def endpoint(payload: RequestModel):
    try:
        result = await service.process(payload)
        return {"success": True, "data": result}
    except ValidationError as e:
        return JSONResponse(status_code=400, content={"error": str(e)})
```

**Frontend:**
```javascript
// ✅ RICHTIG: Defensive Checks
if (data && data.sub_routes && Array.isArray(data.sub_routes)) {
    data.sub_routes.forEach(route => { ... });
} else {
    console.error('[ERROR] Unerwartetes Response-Schema', data);
    showError('Fehler beim Laden');
}
```

### Encoding-Kontrakt

- **Lesen:** Heuristisch (cp850 / utf-8-sig / latin-1)
- **Schreiben/Export/Logs:** **Immer UTF-8**

---

## 3️⃣ **Architektur-Prinzipien**

### Die 5 Grundprinzipien

1. **Determinismus** → Gleicher Input = Gleicher Output
2. **Vertragstreue** → Eingehendes Format bleibt stabil
3. **Defense-in-Depth** → Mehrere Validierungsebenen
4. **Transparenz** → Jede Änderung durch Events/Metriken belegbar
5. **Sicherheitsgurt** → Fehler → Quarantäne/HTTP-4xx

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

```
backend/          # FastAPI Backend
frontend/         # HTML/CSS/JS Frontend
services/         # Business Logic
repositories/     # Data Access
db/               # Schema & Migrations
scripts/          # Utility-Scripts
tests/            # Unit-Tests
tools/            # Development Tools
```

---

## 4️⃣ **API-Standards**

### REST-Konventionen

| Methode | Zweck | Idempotent |
|---------|-------|------------|
| GET | Lesen | ✅ Ja |
| POST | Erstellen/Ausführen | ❌ Nein |
| PUT | Vollständiges Update | ✅ Ja |
| PATCH | Teilweises Update | ✅ Ja |
| DELETE | Löschen | ✅ Ja |

### HTTP-Status-Codes

| Code | Bedeutung | Verwendung |
|------|-----------|------------|
| **200** | Erfolg | Normale Antwort |
| **201** | Erstellt | POST erfolgreich |
| **400** | Client-Fehler | Validierung fehlgeschlagen |
| **401** | Nicht authentifiziert | Login erforderlich |
| **403** | Nicht autorisiert | Keine Berechtigung |
| **404** | Nicht gefunden | Resource existiert nicht |
| **422** | Unprocessable Entity | Validierungsfehler (Details) |
| **500** | Server-Fehler | Interner Fehler |
| **503** | Service nicht verfügbar | OSRM/LLM down |

### Response-Format

**Erfolg:**
```json
{
  "success": true,
  "data": { ... },
  "meta": {
    "timestamp": "2025-11-14T14:00:00Z",
    "version": "1.0.0"
  }
}
```

**Fehler:**
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

### API-Dokumentation

- **OpenAPI/Swagger:** Automatisch via FastAPI
- **Endpoints:** `/docs` (Swagger UI), `/openapi.json` (Schema)
- **Beispiele:** Jeder Endpoint sollte Beispiele enthalten

---

## 5️⃣ **Testing-Standards**

### Test-Typen

1. **Unit-Tests** → Einzelne Funktionen/Klassen
2. **Integration-Tests** → Komponenten-Interaktion
3. **E2E-Tests** → Vollständige Workflows
4. **Golden-Tests** → Problemfälle (spezielle Adressen)
5. **Property-Tests** → Idempotenz, Set-Gleichheit
6. **Snapshot-Tests** → Optimize-Antworten (mit fixen Seeds)

### Coverage-Anforderungen

| Bereich | Minimum | Kritisch |
|---------|---------|----------|
| Gesamt | 80% | - |
| Kritische Pfade | - | 100% |
| CI-Fail | < 80% | - |

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

- **Lint:** `ruff check`
- **Type-Check:** `mypy`
- **Tests:** `pytest` (schnelle Tests)
- **Format:** `ruff format`

---

## 6️⃣ **Git & Versionierung**

### Branch-Strategie

| Branch | Zweck | Deploybar |
|--------|-------|-----------|
| `main/master` | Production | ✅ Immer |
| `develop` | Entwicklung | ⚠️ Testing |
| `feature/*` | Features | ❌ Nein |
| `fix/*` | Bugfixes | ❌ Nein |
| `chore/*` | Wartung | ❌ Nein |
| `governance/*` | Governance | ❌ Nein |

### Commit-Messages (Conventional Commits)

```
feat: Neue Feature-Beschreibung
fix: Bugfix-Beschreibung
docs: Dokumentations-Änderung
test: Test-Änderung
refactor: Code-Refactoring
chore: Wartungsarbeit
style: Code-Formatierung
perf: Performance-Verbesserung
```

### PR-Checklist

- [ ] Keine Änderungen an unantastbaren Bereichen (`./Tourplaene/**`)
- [ ] API-Kontrakte unverändert (oder Migrationsnotiz)
- [ ] Tests grün (Golden/Property/Snapshot) & Coverage ≥ 80%
- [ ] Timeouts/Retry/Circuit-Breaker konfiguriert
- [ ] LLM-Pfad strikt validiert (falls verwendet)
- [ ] Metriken & Logs erweitert
- [ ] Dokumentation aktualisiert
- [ ] **NEU:** Ganzheitliches Code-Review (Backend + Frontend + DB + Infra)
- [ ] **NEU:** Mindestens 1 Regressionstest (bei Bugfix)

---

## 7️⃣ **Deployment & Operations**

### Umgebungsvariablen (12-Factor)

**Pflicht:**
- `DATABASE_URL` → Datenbank-Verbindung
- `OSRM_BASE_URL` → OSRM-Server URL
- `APP_ENV` → dev/staging/prod
- `LOG_LEVEL` → DEBUG/INFO/WARNING/ERROR

**Optional:**
- `OPENAI_API_KEY` → Falls LLM verwendet
- `REDIS_URL` → Falls Caching aktiv

### Logging

**Format:** Strukturiert (JSON)

```json
{
  "timestamp": "2025-11-14T14:00:00Z",
  "level": "INFO",
  "message": "Tour optimiert",
  "correlation_id": "abc-123",
  "tour_uid": "T001",
  "latency_ms": 450
}
```

**Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL

**Felder (Pflicht):**
- `timestamp`, `level`, `message`
- `correlation_id` (für Tracing)
- Kontext (`tour_uid`, `stop_uid`, `phase`)

### Monitoring

**Health-Checks:**
- `/health` → Backend-Status
- `/health/db` → Datenbank-Status
- `/health/osrm` → OSRM-Status

**Alarme:**
- `osrm_unavailable > 0` in 5min → Warnung
- `llm_invalid_schema > 0` → Review
- `tours_pending_geo` steigt 3 Intervalle → GeoQueue prüfen

---

## 8️⃣ **Audit & Compliance**

### KI-Audit-Framework (PRIMÄR) ⭐

**Zentrale Dokumentation:** `docs/ki/`

| Dokument | Zweck |
|----------|-------|
| [`ki/README.md`](ki/README.md) | Framework-Übersicht |
| [`ki/REGELN_AUDITS.md`](ki/REGELN_AUDITS.md) | 14 Grundregeln |
| [`ki/AUDIT_CHECKLISTE.md`](ki/AUDIT_CHECKLISTE.md) | 9-Punkte-Checkliste |
| [`ki/LESSONS_LOG.md`](ki/LESSONS_LOG.md) | Dokumentierte Fehler |
| [`ki/CURSOR_PROMPT_TEMPLATE.md`](ki/CURSOR_PROMPT_TEMPLATE.md) | 10 fertige Prompts |

**Quick-Referenz:** [`KI_AUDIT_FRAMEWORK.md`](../KI_AUDIT_FRAMEWORK.md)

### 6-Phasen-Audit-Workflow

1. **Vorbereitung** → Scope, Dateien, Logs, Screenshots
2. **Analyse** → Backend, Frontend, DB, Infra, API-Kontrakt
3. **Diagnose** → Root Cause, Seiteneffekte, Fix-Strategie
4. **Umsetzung** → Code ändern, Tests, Doku, Erklärung
5. **Verifikation** → Syntax, Tests, Manuelle Tests, Logs
6. **Abschluss** → Audit-Dokument, ZIP, LESSONS_LOG

### Audit-ZIP-Pipeline

**Verwendung:**
```bash
# Linux/macOS
bash scripts/make_audit_zip.sh

# Windows
pwsh -File scripts/Make-AuditZip.ps1

# Direkt
python tools/make_audit_zip.py
```

**Format:** `AUDIT_<YYYYMMDD_HHMMSS>_<shortsha>.zip`

**Enthält:**
- Manifest (Hashes, Commit, Branch)
- Logs, OpenAPI, Routenliste
- Sanitizierte `.env` (Secrets redacted)

### Secrets-Schutz

**NIEMALS in Logs/Audits:**
- `OPENAI_API_KEY`
- `DATABASE_URL`
- `POSTGRES_PASSWORD`
- `REDIS_URL`
- `SMTP_PASSWORD`
- API-Keys, Tokens, Secrets

**Erlaubt:**
- `OSRM_URL`
- `OSRM_TIMEOUT`
- `APP_ENV`

---

## 9️⃣ **Dokumentations-Standards**

### Struktur

```
docs/
├── STANDARDS.md                    # Diese Standards (Zentral)
├── STANDARDS_QUICK_REFERENCE.md   # Diese Datei
├── ki/                            # KI-Audit-Framework
├── README.md                      # Projekt-README
├── ARCHITECTURE.md                # System-Architektur
├── API.md                         # API-Dokumentation
├── DEVELOPMENT.md                 # Entwickler-Guide
├── DEPLOYMENT.md                  # Deployment-Guide
└── CHANGELOG.md                   # Änderungsprotokoll
```

### Markdown-Standards

- **Überschriften:** H1 für Titel, H2 für Hauptabschnitte, H3 für Unterabschnitte
- **Code-Blöcke:** Mit Sprach-Tag (`python`, `bash`, `json`)
- **Links:** Relative Links zu anderen Dokumenten
- **Tabellen:** Für strukturierte Daten
- **Listen:** Für Aufzählungen

### Changelog-Format

**Format:** [Keep a Changelog](https://keepachangelog.com/)

**Kategorien:**
- Added (Neu)
- Changed (Geändert)
- Deprecated (Veraltet)
- Removed (Entfernt)
- Fixed (Behoben)
- Security (Sicherheit)

**Datum:** ISO-Format (YYYY-MM-DD)

---

## 🔟 **Definition of Done (DoD)**

Ein Feature ist "Done", wenn:

- [ ] Code implementiert und getestet
- [ ] Unit-Tests geschrieben (Coverage ≥ 80%)
- [ ] Integration-Tests bestanden
- [ ] Dokumentation aktualisiert
- [ ] **NEU:** Code-Review ganzheitlich (Backend + Frontend + DB + Infra)
- [ ] CI/CD-Pipeline grün
- [ ] Pre-commit-Hooks bestanden
- [ ] Metriken & Logs erweitert
- [ ] Keine Breaking Changes (oder Migrationsnotiz)
- [ ] **NEU:** Mindestens 1 Regressionstest (bei Bugfix)
- [ ] **NEU:** LESSONS_LOG aktualisiert (bei neuem Fehlertyp)

---

## ⛔ **Verbote (Anti-Anarchie-Liste)**

### Code-Qualität

1. ❌ Keine globalen Zustände
2. ❌ Keine Ad-hoc-Requests im Codepfad
3. ❌ Keine 200-Responses bei Fehlvalidierung
4. ❌ Keine "silent fixes" – Fehler müssen sichtbar sein

### Daten & Identität

5. ❌ Kein Index-Mapping/Koordinatenvergleich als Identität – nur UIDs
6. ❌ Keine Änderungen an unantastbaren Bereichen (`./Tourplaene/**`)

### Externe Services

7. ❌ Keine externen HTTP-Calls ohne zentralen Client/Timeout/Retry
8. ❌ Kein LLM ohne Schema/Validierung/Verifikation

### Audit & Testing (NEU in V2.0)

9. ❌ **Keine isolierten Fixes** (nur Backend ODER nur Frontend)
10. ❌ **Kein Fix ohne Test** (Mindestens 1 Regressionstest)
11. ❌ **Keine Breaking Changes ohne Dokumentation**
12. ❌ **Keine sensiblen Daten in Logs**

---

## 📊 **Zusammenfassung in Zahlen**

- **10 Hauptbereiche** (inkl. KI-Audit-Framework)
- **7 Unverhandelbare Audit-Regeln**
- **12 Verbote** (Anti-Anarchie)
- **5 Architektur-Prinzipien**
- **6 Test-Typen**
- **6 Phasen** im Audit-Workflow
- **10 Fertige Cursor-Prompts**
- **80%** Minimum Code-Coverage
- **~900 Zeilen** Standards-Dokumentation
- **~80 Seiten** KI-Audit-Framework

---

## 🎯 **Top 5 Regeln (Auswendig lernen!)**

### 1. Ganzheitlich denken

> Backend + Frontend + DB + Infra – **ALLE** zusammen prüfen!

**Warum?** 80% aller Bugs waren API-Kontrakt-Probleme (Backend ↔ Frontend)

### 2. Tests sind Pflicht

> **Mindestens 1 Regressionstest** pro Bugfix – **KEINE AUSNAHMEN!**

**Warum?** Ohne Test kommt der Bug zurück (garantiert).

### 3. Root Cause finden

> Nicht nur Symptom beheben – **Ursache** in LESSONS_LOG dokumentieren

**Warum?** Aus Fehlern lernen, nicht wiederholen.

### 4. API-Kontrakt prüfen

> Request/Response Backend ↔ Frontend **IMMER** validieren

**Warum?** Feldnamen-Mismatch (`subRoutes` vs. `sub_routes`) = TypeErrors im Frontend

### 5. Defensive Programmierung

> **Null-Checks, Try-Catch, Input-Validierung** – überall!

**Warum?** Fehler elegant behandeln, nicht abstürzen.

---

## 🚀 **Schnellstart für Entwickler**

### 1. Dokumentation lesen (15 Min)

```bash
# Quick-Referenz (diese Datei)
cat docs/STANDARDS_QUICK_REFERENCE.md

# Vollständige Standards
cat docs/STANDARDS.md

# KI-Audit-Framework
cat docs/ki/README.md
```

### 2. Nächster Bugfix nach V2.0-Standard

**Cursor-Prompt verwenden:**

```
Führe einen vollständigen Code-Audit durch für: [DEIN BUG]

Folge strikt:
- docs/ki/REGELN_AUDITS.md
- docs/ki/AUDIT_CHECKLISTE.md

Prüfe ganzheitlich:
- Backend (Python/FastAPI)
- Frontend (HTML/CSS/JavaScript)
- Datenbank (SQLite)
- Infrastruktur (OSRM, ENV)

Liefere:
- Root Cause
- Konkrete Fixes
- Mindestens 1 Regressionstest
- Audit-Dokument
```

**Oder Checkliste nutzen:**

Öffne [`docs/ki/AUDIT_CHECKLISTE.md`](ki/AUDIT_CHECKLISTE.md) und arbeite die 9 Punkte ab.

### 3. Code-Review durchführen

**Neue Checkliste verwenden:**

- [ ] Backend geprüft
- [ ] Frontend geprüft
- [ ] API-Kontrakt validiert
- [ ] Datenbank geprüft
- [ ] Infrastruktur geprüft
- [ ] Tests geschrieben
- [ ] Dokumentation aktualisiert

**Siehe:** Code-Review-Standards in [`docs/STANDARDS.md`](STANDARDS.md)

---

## 💡 **Das Motto für 2025**

> **"Quality first, speed second. Ganzheitlich denken, systematisch arbeiten, aus Fehlern lernen."**

---

## 📞 **Support & Hilfe**

### Dokumentation

- 📘 **Zentral:** [`docs/STANDARDS.md`](STANDARDS.md) (Vollständig, ~900 Zeilen)
- 🎯 **Quick-Ref:** [`docs/STANDARDS_QUICK_REFERENCE.md`](STANDARDS_QUICK_REFERENCE.md) (Diese Datei)
- 📑 **Index:** [`docs/STANDARDS/INDEX.md`](STANDARDS/INDEX.md)

### KI-Audit-Framework

- 📚 **Start:** [`docs/ki/README.md`](ki/README.md)
- 📋 **Regeln:** [`docs/ki/REGELN_AUDITS.md`](ki/REGELN_AUDITS.md)
- ✅ **Checkliste:** [`docs/ki/AUDIT_CHECKLISTE.md`](ki/AUDIT_CHECKLISTE.md)
- 📖 **Lessons:** [`docs/ki/LESSONS_LOG.md`](ki/LESSONS_LOG.md)
- 🚀 **Prompts:** [`docs/ki/CURSOR_PROMPT_TEMPLATE.md`](ki/CURSOR_PROMPT_TEMPLATE.md)

### Quick-Referenzen

- 🎯 **Root:** [`KI_AUDIT_FRAMEWORK.md`](../KI_AUDIT_FRAMEWORK.md)
- 🔗 **API-Kontrakt:** [`AI_CODE_AUDIT_REGELN.md`](../AI_CODE_AUDIT_REGELN.md)

### Migration

- 🔄 **Migration Guide:** [`docs/STANDARDS_V2_MIGRATION.md`](STANDARDS_V2_MIGRATION.md)
- 📢 **Release Notes:** [`STANDARDS_V2_RELEASE_NOTES.md`](../STANDARDS_V2_RELEASE_NOTES.md)

---

## ✅ Checkliste: Ich bin bereit für V2.0!

- [ ] Quick-Reference gelesen (diese Datei)
- [ ] Vollständige Standards verstanden (`docs/STANDARDS.md`)
- [ ] KI-Audit-Framework kennenlernen (`docs/ki/README.md`)
- [ ] Erste Code-Review nach neuem Standard durchgeführt
- [ ] Ganzheitlich geprüft (Backend + Frontend + DB + Infra)
- [ ] Test geschrieben (bei Bugfix)

**Wenn alle Punkte abgehakt: Willkommen in STANDARDS V2! 🎉**

---

**Version:** 2.0  
**Datum:** 2025-11-14  
**Status:** ✅ PRODUKTIV  
**Für:** Alle FAMO-Projekte (verbindlich)

