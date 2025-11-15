# Cursor Audit-Prompt Templates

**Projekt:** FAMO TrafficApp 3.0  
**Version:** 2.0  
**Stand:** 2025-11-14  
**Zweck:** Fertige Prompts für verschiedene Audit-Szenarien

---

## 📋 Übersicht: 12 Templates

1. **Ganzheitliches Audit - Kugelsicher** ⭐ (EMPFOHLEN - für alle Bug-Fixes)
2. Standard-Audit (Vollständig)
3. Quick-Audit (Gezielt)
4. Schema-Audit (Datenbank)
5. Frontend-Audit (JavaScript)
6. API-Kontrakt-Audit
7. Performance-Audit
8. Security-Audit
9. Regression-Test-Audit
10. Emergency-Audit (Production Down)
11. **Sub-Routen-Generator Audit** ⚙️ (SPEZIELL - für kritisches Feature)
12. Custom-Audit-Prompt (Vorlage zum Anpassen)

---

## 1. Ganzheitliches Audit - Kugelsicher ⭐ (EMPFOHLEN)

```
🎯 ROLLE: Senior-Fullstack-Reviewer für FAMO TrafficApp

ZIEL:
- Bug analysieren und fixen
- Backend + Frontend + DB + Infra GEMEINSAM betrachten
- Code so härten, dass der Fehler NICHT wiederkommt

SCOPE:
Backend:
- [HIER: konkrete Dateien z.B. backend/routes/tourplan_routes.py]

Frontend:
- [HIER: z.B. frontend/js/tourplan.js, frontend/index.html]

DB/Infra (falls relevant):
- db/schema.py
- services/osrm_client.py

⚠️ STRENGE REGELN:

1. MULTI-LAYER-PFLICHT:
   - [ ] Mindestens 1 Backend-Datei im Kontext
   - [ ] Mindestens 1 Frontend-Datei im Kontext
   - [ ] Falls DB beteiligt: db/schema.py
   - [ ] Falls OSRM beteiligt: services/osrm_client.py
   
   ➜ Wenn Bug im UI sichtbar: Backend + Frontend PFLICHT!

2. KEINE ÄNDERUNGEN außerhalb dieser Dateien, außer ich sage es EXPLIZIT

3. API-Kontrakt Backend ↔ Frontend darf nur geändert werden, wenn du:
   a) BEIDE Seiten anpasst UND
   b) den Kontrakt in der Antwort dokumentierst

4. SCHREIBE IMMER:
   - Root Cause (präzise, nicht nur Symptom)
   - Konkreten Fix (Datei, Funktion, Zeile)
   - Vorschlag für mindestens 1 Regressionstest
   - Golden Test Cases (falls verfügbar)

5. PRÜFE:
   - Backend-Logs (Stacktraces, HTTP-Status)
   - Browser-Konsole (gedanklich) → mögliche JS-Fehler
   - Response-Schema vs. Frontend-Erwartung
   - Defensive Programmierung (Null-Checks, Array-Checks, Try-Catch)

6. KEIN GHOST-REFACTORING:
   - Keine projekt-weiten Umbenennungen
   - Keine globalen Suchen-Ersetzen ohne separate Freigabe
   - Wenn Refactor nötig → eigener Prompt + Branch

OUTPUT:

1. Kurze Zusammenfassung der Ursache
2. Diffs pro Datei (kompakt)
3. Konkrete Testanleitung (Backend + Frontend)
4. Golden Test Cases (welche betroffen sind, wie manuell prüfen)
5. Erwartete Userwirkung (Was sieht der Benutzer?)

WICHTIG:
- Folge docs/ki/REGELN_AUDITS.md und docs/ki/AUDIT_CHECKLISTE.md
- Nutze docs/ki/LESSONS_LOG.md für bekannte Fehlertypen
- Kein blindes Übernehmen von Code-Vorschlägen
```

---

## 2. Standard-Audit (Vollständig)

```
Kontext:
- Projekt: FAMO TrafficApp 3.0
- Du bist eine Audit-KI für strukturierte Code-Audits
- Arbeite strikt nach den definierten Projektregeln

Aufgabe:
Führe einen vollständigen Code-Audit durch für: [FEATURE/BUG BESCHREIBUNG]

Vorgehen:
1. Lies zuerst:
   - docs/ki/REGELN_AUDITS.md
   - docs/ki/AUDIT_CHECKLISTE.md
   - docs/ki/LESSONS_LOG.md (für bekannte Fehlertypen)

2. Analysiere ganzheitlich:
   - Backend (Python/FastAPI)
   - Frontend (HTML/CSS/JavaScript)
   - Datenbank (SQLite)
   - Infrastruktur (OSRM, ENV-Variablen)

3. Identifiziere:
   - Root Cause (nicht nur Symptom!)
   - Betroffene Dateien
   - API-Kontrakte (Backend ↔ Frontend)
   - Seiteneffekte

4. Schlage vor:
   - Konkrete Fixes (mit Dateinamen und Zeilen)
   - Mindestens einen Regressionstest
   - Defensive Checks (wo sinnvoll)
   - Logging-Verbesserungen

5. Dokumentiere:
   - Erstelle ein Audit-Dokument nach docs/ki/REGELN_AUDITS.md (Abschnitt 9)
   - Falls neuer Fehlertyp: Eintrag für docs/ki/LESSONS_LOG.md vorbereiten
   - Falls größeres Audit: ZIP-Archiv-Struktur vorschlagen

WICHTIG:
- Ändere nicht unkontrolliert die Architektur
- Fasse alle Änderungen klar zusammen
- Folge der AUDIT_CHECKLISTE.md systematisch (alle 9 Punkte!)
- Teste Änderungen (Syntax-Check, manuelle Tests)

Erwartete Ausgabe:
1. Executive Summary (Fehler gefunden/behoben)
2. Problem-Identifikation (Symptom + Root Cause)
3. Durchgeführte Fixes (Vorher/Nachher)
4. Tests & Verifikation
5. Code-Qualität Metriken
6. Lessons Learned
7. Nächste Schritte
```

---

## 2. Quick-Audit (Gezielt)

```
Kontext:
- Projekt: FAMO TrafficApp 3.0
- Schnelles, gezieltes Audit für spezifisches Problem

Aufgabe:
Analysiere folgenden Fehler: [FEHLERMELDUNG]

Vorgehen:
1. Identifiziere betroffene Dateien (grep/search)
2. Prüfe Backend UND Frontend (API-Kontrakt!)
3. Finde Root Cause
4. Schlage konkreten Fix vor (mit Code-Beispiel)
5. Definiere einen Regressionstest

Ausgabe:
- Root Cause (1-2 Sätze)
- Fix (Code-Diff)
- Test (Python/JavaScript)
- Erwartete Userwirkung

Regel: Folge docs/ki/REGELN_AUDITS.md, aber ohne vollständiges Dokument.
```

---

## 3. Schema-Audit (Datenbank)

```
Kontext:
- Projekt: FAMO TrafficApp 3.0
- Audit für Datenbank-Schema-Probleme

Aufgabe:
Prüfe Schema-Konsistenz zwischen Code und DB für: [TABELLE/FEATURE]

Vorgehen:
1. Vergleiche:
   - db/schema.py (Code)
   - data/traffic.db (reale DB)
   - Verwende: sqlite3 data/traffic.db ".schema [TABELLE]"

2. Finde Schema-Drifts:
   - Fehlende Spalten in DB
   - Fehlende Indizes
   - Inkonsistente Constraints

3. Schlage vor:
   - Migration-Script (db/migrations/YYYY-MM-DD_beschreibung.sql)
   - Defensive Schema-Updates (PRAGMA table_info, IF NOT EXISTS)
   - Backup-Strategie für Production

4. Dokumentiere in docs/ki/LESSONS_LOG.md (wenn relevant)

Regel: Niemals Schema ohne Migration ändern!
```

---

## 4. Frontend-Audit (JavaScript)

```
Kontext:
- Projekt: FAMO TrafficApp 3.0
- Audit für Frontend-Fehler (JavaScript)

Aufgabe:
Analysiere Frontend-Fehler: [BROWSER-CONSOLE-FEHLER]

Vorgehen:
1. Identifiziere:
   - Betroffene HTML-Datei
   - JavaScript-Funktion
   - API-Call (fetch) zur Backend-Route

2. Prüfe:
   - Request/Response-Kontrakt mit Backend
   - Defensive Programmierung (Null-Checks, Array-Checks)
   - Fehlerbehandlung (try-catch, UI-Feedback)

3. Validiere:
   - Ist data.field definiert?
   - Ist data.field ein Array (falls .forEach() verwendet)?
   - Sind alle globalen Objekte (window.X) verfügbar?

4. Schlage vor:
   - Defensive Checks (if + Array.isArray)
   - Error-Boundaries
   - Klare Fehlermeldungen im UI

Regel: Folge AI_CODE_AUDIT_REGELN.md (Abschnitt 4: Defensive JS-Programmierung)
```

---

## 5. API-Kontrakt-Audit

```
Kontext:
- Projekt: FAMO TrafficApp 3.0
- Audit für Backend ↔ Frontend API-Kontrakt

Aufgabe:
Prüfe API-Kontrakt für Endpoint: [ENDPOINT-URL]

Vorgehen:
1. Backend:
   - Finde FastAPI-Route (routes/*.py oder backend/routes/*.py)
   - Dokumentiere Request-Schema (Pydantic-Modell)
   - Dokumentiere Response-Schema (Return-Type)

2. Frontend:
   - Finde fetch()-Call (grep "fetch.*[ENDPOINT-URL]")
   - Dokumentiere Request-Body (JSON.stringify)
   - Dokumentiere Response-Verarbeitung (await response.json())

3. Vergleiche:
   - Feldnamen identisch? (snake_case vs. camelCase?)
   - Datentypen kompatibel? (string, number, array, object)
   - Optionale Felder korrekt behandelt?

4. Fixe Inkonsistenzen:
   - Bevorzugt: Backend an Frontend anpassen (snake_case)
   - Defensive Checks im Frontend hinzufügen
   - Dokumentiere in docs/ki/LESSONS_LOG.md

Regel: API-Kontrakte sind heilig! Niemals stillschweigend brechen.
```

---

## 6. Performance-Audit

```
Kontext:
- Projekt: FAMO TrafficApp 3.0
- Audit für Performance-Probleme

Aufgabe:
Analysiere Performance-Problem: [BESCHREIBUNG]

Vorgehen:
1. Identifiziere Bottlenecks:
   - Langsame API-Endpoints (>1s Response-Zeit)
   - Langsame DB-Queries (EXPLAIN QUERY PLAN)
   - Langsame OSRM-Calls (Timeouts, große Routen)

2. Messe:
   - Aktuelle Performance (Logs, Timer)
   - Baseline definieren (akzeptable Werte)

3. Optimiere:
   - DB: Indizes hinzufügen
   - Backend: Caching (Redis, In-Memory)
   - OSRM: Batch-Requests, Parallelisierung
   - Frontend: Lazy Loading, Pagination

4. Validiere:
   - Performance vorher/nachher
   - Keine funktionalen Regressionen
   - Tests aktualisieren

Regel: Messe immer! Keine Optimierung ohne Baseline.
```

---

## 7. Security-Audit

```
Kontext:
- Projekt: FAMO TrafficApp 3.0
- Audit für Sicherheitsprobleme

Aufgabe:
Prüfe Sicherheit für Feature: [FEATURE]

Vorgehen:
1. Input-Validierung:
   - Backend: Pydantic-Modelle für alle Requests
   - SQL: Keine String-Konkatenation, nur Prepared Statements
   - Frontend: Sanitize User-Inputs (XSS-Schutz)

2. Sensitive Daten:
   - Logs: Keine Passwörter, API-Keys, vollständige Adressen
   - Fehler-Responses: Keine Stacktraces in Production
   - Datenbank: Passwörter gehasht (nie Plaintext)

3. Authentifizierung/Autorisierung:
   - Admin-Endpoints geschützt?
   - API-Keys sicher gespeichert? (config.env, nicht im Git)

4. Dependencies:
   - requirements.txt auf bekannte Vulnerabilities prüfen
   - Veraltete Packages aktualisieren

Regel: Security First! Niemals Sicherheit für Features opfern.
```

---

## 8. Regression-Test-Audit

```
Kontext:
- Projekt: FAMO TrafficApp 3.0
- Audit für existierende Tests

Aufgabe:
Prüfe Test-Coverage für Feature: [FEATURE]

Vorgehen:
1. Finde existierende Tests:
   - tests/*.py
   - tests/unit/*.py
   - tests/integration/*.py

2. Analysiere Coverage:
   - Welche Code-Pfade sind getestet?
   - Welche Edge Cases fehlen?
   - Welche Fehler-Szenarien fehlen?

3. Schlage neue Tests vor:
   - Unit Tests für Services/Functions
   - Integration Tests für API-Endpoints
   - Frontend Tests (optional: Playwright)

4. Implementiere:
   - Mindestens 1 Regressionstest für jeden Bug
   - Tests für Happy Path UND Edge Cases
   - Tests für Fehler-Handling

Regel: Kein Fix ohne Test! Tests dokumentieren erwartetes Verhalten.
```

---

## 9. Emergency-Audit (Production Down)

```
NOTFALL-AUDIT

Kontext:
- Projekt: FAMO TrafficApp 3.0
- Production ist DOWN! Schnelle Diagnose erforderlich.

Symptom: [FEHLERMELDUNG / STATUS]

Vorgehen (SCHNELL):
1. Logs prüfen (letzte 100 Zeilen):
   - Server-Logs: logs/*.log
   - OSRM-Logs: docker logs osrm-backend
   - System-Logs: journalctl -u trafficapp

2. Health-Checks:
   - curl http://localhost:8000/health
   - curl http://localhost:5000/route/v1/driving/13.7,51.0;13.8,51.1

3. Quick-Fixes (wenn offensichtlich):
   - Service neustarten: systemctl restart trafficapp
   - Docker neustarten: docker-compose restart
   - DB-Lock: rm data/traffic.db-wal

4. Eskalation:
   - Wenn nicht innerhalb 10 Minuten gelöst: Rollback zum letzten stabilen Stand
   - Vollständiges Audit NACH Wiederherstellung

Regel: Production First! Schnell stabilisieren, dann Root Cause analysieren.
```

---

## 10. Sub-Routen-Generator Audit (Backend + Frontend) ⚙️

```
🎯 ROLLE: Senior-Fullstack-Reviewer für FAMO TrafficApp

SPEZIALISIERUNG: Sub-Routen-Generator (kritisches Feature!)

PROBLEMKONTEXT:
Der Sub-Routen-Generator funktioniert nicht korrekt.

Symptome können sein:
- Fehler im UI (Button reagiert nicht / JS-Fehler in der Konsole)
- HTTP-Fehler (4xx/5xx) beim Aufruf der Subrouten-API
- Leere oder kaputte Antwortdaten (falsches JSON-Schema)

Ich brauche eine GANZHEITLICHE ANALYSE und einen STABILEN FIX.

SCOPE DIESES AUDITS (verbindlich):

Backend:
- backend/routes/tourplan_routes.py
- backend/services/tourplan/subroute_generator.py
- backend/services/osrm_client.py
- backend/services/routing_optimizer.py

Frontend:
- frontend/js/tourplan.js
- frontend/js/subroutes.js
- frontend/index.html

Tests (falls vorhanden):
- tests/test_subroutes_*.py

⚠️ Du darfst NUR in diesen Dateien Änderungen vornehmen, außer ich erweitere den Scope explizit!

STRENGE REGELN:

1. MULTI-LAYER SICHT:
   - Prüfe immer: Backend-Endpoint + Frontend-Aufruf + Antwort-Format
   - Vergleiche: FastAPI-Response-Model vs. Frontend-Erwartung
   - Feldnamen, Typen, verschachtelte Strukturen MÜSSEN übereinstimmen

2. KEIN GHOST-REFACTOR:
   - Kein globales Suchen/Ersetzen über das ganze Projekt
   - Keine stillen Umbenennungen von Endpoints, Feldern oder Funktionen
   - Wenn Refactor nötig → Vorschlag separat, aber klein und zielgerichtet

3. API-KONTRAKT IST HEILIG (aber anpassbar):
   Wenn du den API-Response änderst, MUSST du:
   a) Backend-Response anpassen
   b) Frontend-Verarbeitung/Rendering anpassen
   c) Neuen Kontrakt dokumentieren (z.B. subroutes: Array<{id, name, distance_km, geometry_polyline}>)

4. FEHLERROBUSTHEIT:
   - OSRM-Fehler (Timeout, 5xx, kein Route-Result): sauber behandeln
   - Sinnvolle Fehlermeldung
   - Fallback nur wenn fachlich passend (z.B. Haversine-Linie)
   - Sub-Routen-Generator darf bei Einzelfehlern nicht die komplette Tour sprengen

DEINE AUFGABEN (Schritt für Schritt):

1. ROOT CAUSE ANALYSE:
   - Erkläre, WARUM der Sub-Routen-Generator aktuell nicht funktioniert
   - Zeige konkrete Stellen im Code (Backend + Frontend), wo der Bruch passiert:
     * Falscher Endpoint?
     * Falsche HTTP-Methode?
     * Falsches JSON-Schema?
     * JS-Fehler (z.B. undefined-Zugriffe)?

2. ZIELBILD DEFINIEREN:
   Beschreibe in 3-5 Sätzen, wie der Sub-Routen-Flow idealerweise laufen soll:
   1. User klickt im UI (z.B. "Subrouten erzeugen")
   2. Frontend ruft Endpoint .../subroutes auf
   3. Backend berechnet Subrouten, nutzt OSRM, strukturiert Antwort
   4. Frontend rendert Subrouten (Liste + Karte)

3. KONKRETER FIX:
   - Passe die betroffenen Dateien an
   - Code ROBUST machen (Defensivprogrammierung, sinnvolle Defaults, Logging)
   - Bei kritischen Stellen: kurze Kommentare warum so gelöst

4. TESTS / VERIFIKATION:
   Backend-Testfall vorschlagen (oder vorhandene Tests anpassen):
   - Beispielinput
   - Erwartete Struktur der Subrouten
   
   Manueller Frontend-Testplan:
   - Welche Seite öffnen
   - Welche Aktion ausführen
   - Welche Logs/Fehler im Browser prüfen

5. KURZBERICHT AM ENDE (5 Punkte):
   1. Root Cause (1-2 Sätze)
   2. Welche Dateien geändert
   3. Was sich am API-Response geändert hat (falls relevant)
   4. Wie man prüft, dass es jetzt funktioniert (kurz)
   5. Welche Risiken es noch gibt / was man später verbessern kann

GOLDEN TEST CASES (kritisch für Sub-Routen!):
Falls vorhanden, dokumentiere:
- Welche Golden Tests betroffen sind (z.B. test_golden_w01_subroutes)
- Wie man sie manuell prüft (UI + Logs)
- Erwartetes Ergebnis (konkret)

WICHTIG:
- Folge docs/ki/REGELN_AUDITS.md und docs/ki/AUDIT_CHECKLISTE.md
- Nutze docs/ki/LESSONS_LOG.md für bekannte Sub-Routen-Fehler
- Multi-Layer-Pflicht: Backend + Frontend BEIDE prüfen!
```

**Hinweis zur Anpassung:**
Vor Nutzung in Cursor: Dateiliste im SCOPE anpassen (nur das, was im Bugkontext wirklich relevant ist).

---

## 11. Custom-Audit-Prompt

```
[Hier eigenen Prompt einfügen und an Bedürfnisse anpassen]

Kontext:
- Projekt: FAMO TrafficApp 3.0
- [Beschreibung]

Aufgabe:
[Spezifische Aufgabenstellung]

Vorgehen:
1. [Schritt 1]
2. [Schritt 2]
...

Regel: Folge docs/ki/REGELN_AUDITS.md und docs/ki/AUDIT_CHECKLISTE.md
```

---

## Verwendung

1. **Passenden Prompt wählen** (oder Custom erstellen)
2. **[PLATZHALTER] ersetzen** (Feature, Fehler, Endpoint, etc.)
3. **In Cursor einfügen** und ausführen
4. **Ergebnis reviewen** und Fixes übernehmen

---

## Best Practices

- ✅ Immer spezifische Platzhalter ausfüllen (nicht generisch lassen)
- ✅ Logs und Fehler konkret benennen (mit Zeilen, Stacktraces)
- ✅ Erwartete Ausgabe klar definieren
- ✅ Regeln und Checklisten referenzieren
- ❌ Nicht mehrere Audits parallel (Fokus!)
- ❌ Nicht zu vage formulieren ("prüfe mal alles")

---

**Ende der Prompt-Templates**  
**Viel Erfolg bei strukturierten Audits! 🚀**

