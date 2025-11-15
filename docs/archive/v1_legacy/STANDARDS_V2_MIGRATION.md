# 🚀 STANDARDS Version 2.0 - Migration Guide

**Breaking Change:** KI-Audit-Framework ist jetzt PFLICHT!  
**Datum:** 2025-11-14  
**Status:** AKTIV

---

## 📢 Was ist neu?

### Das KI-Audit-Framework ist da!

Ab sofort ist das **vollständige KI-Audit-Framework** in `docs/ki/` der **verbindliche Standard** für alle Code-Reviews und Audits in der FAMO TrafficApp.

**Kernprinzip:**

> "Kein isolierter Fix mehr! Jede Änderung wird ganzheitlich bewertet: Backend + Frontend + Datenbank + Infrastruktur"

---

## 🎯 Die 7 Unverhandelbaren Regeln

1. **Scope explizit machen** - Feature, Endpoints, Symptome dokumentieren
2. **Immer ganzheitlich prüfen** - Backend + Frontend + DB + Infra (ALLE!)
3. **Keine isolierten Fixes** - Impact-Analyse, API-Kontrakt, Tests anpassen
4. **Tests sind Pflicht** - Min. 1 Regressionstest pro Bugfix
5. **Dokumentation aktualisieren** - LESSONS_LOG, API-Docs, Kommentare
6. **Sicherheit und Robustheit** - Input-Validierung, Error-Handling, Timeouts
7. **Transparenz bei Änderungen** - Erklärung, Kontext, Diff, Impact

---

## 📚 Neue Dokumentation

| Dokument | Zweck | Verbindlich |
|----------|-------|-------------|
| **[docs/ki/README.md](ki/README.md)** | Framework-Übersicht & Workflow | ✅ JA |
| **[docs/ki/REGELN_AUDITS.md](ki/REGELN_AUDITS.md)** | Grundregeln für alle Audits | ✅ JA |
| **[docs/ki/AUDIT_CHECKLISTE.md](ki/AUDIT_CHECKLISTE.md)** | 9-Punkte-Checkliste (systematisch) | ✅ JA |
| **[docs/ki/LESSONS_LOG.md](ki/LESSONS_LOG.md)** | Dokumentierte Fehler & Lösungen | ✅ JA |
| **[docs/ki/CURSOR_PROMPT_TEMPLATE.md](ki/CURSOR_PROMPT_TEMPLATE.md)** | 10 fertige Audit-Prompts | ✅ JA |
| **[KI_AUDIT_FRAMEWORK.md](../KI_AUDIT_FRAMEWORK.md)** | Quick-Referenz (Projekt-Root) | ✅ JA |

---

## ⚠️ Breaking Changes

### Was ändert sich konkret?

#### 1. Code-Reviews müssen ganzheitlich sein

**Vorher (Version 1.0):**
```
✅ Backend-Fix angewendet
✅ Tests grün
→ Merge
```

**Jetzt (Version 2.0):**
```
✅ Backend-Fix angewendet
✅ Frontend geprüft (API-Kontrakt?)
✅ Datenbank geprüft (Schema-Konsistenz?)
✅ Infrastruktur geprüft (OSRM erreichbar?)
✅ Defensive Checks eingebaut
✅ Tests grün (inkl. 1 Regressionstest)
✅ Dokumentation aktualisiert
→ Merge
```

**Beispiel:**

```python
# ❌ FALSCH (Version 1.0 - isoliert):
# Backend: Response-Format ändern
return {"sub_routes": [...]}  # Vorher: {"subRoutes": [...]}
# → Frontend bricht! (Keine Prüfung)

# ✅ RICHTIG (Version 2.0 - ganzheitlich):
# 1. Backend: snake_case
return {"sub_routes": [...]}

# 2. Frontend: Anpassen
if (data && Array.isArray(data.sub_routes)) {  # Defensive Check
    data.sub_routes.forEach(route => { ... });
}

# 3. Test schreiben:
def test_subroutes_response_format():
    response = client.post("/api/tour/optimize", json=payload)
    data = response.json()
    assert "sub_routes" in data  # Test für neues Format
    assert isinstance(data["sub_routes"], list)

# 4. Dokumentieren:
# docs/ki/LESSONS_LOG.md → Eintrag für "API-Kontrakt: snake_case vs. camelCase"
```

#### 2. Tests sind Pflicht

**Vorher:**
- Tests optional
- "Manuell getestet" reicht

**Jetzt:**
- **Mindestens 1 Regressionstest** pro Bugfix
- Test muss sicherstellen, dass Bug nicht zurückkommt
- Keine Ausnahmen!

**Template:**
```python
def test_bugfix_xyz():
    """
    Regression-Test für Bug #XYZ:
    [Kurzbeschreibung]
    """
    # Arrange
    payload = { ... }
    
    # Act
    response = client.post("/api/endpoint", json=payload)
    
    # Assert
    assert response.status_code == 200
    assert "expected_field" in response.json()
```

#### 3. Root Cause dokumentieren

**Vorher:**
- Bug fixen, fertig

**Jetzt:**
- Root Cause identifizieren
- In `docs/ki/LESSONS_LOG.md` dokumentieren
- "Was die KI künftig tun soll" definieren

**Format:**
```md
## 2025-11-14 – [Kurzbeschreibung]

**Symptom:** [Was wurde beobachtet?]
**Ursache:** [Root Cause]
**Fix:** [Konkrete Lösung]
**Was die KI künftig tun soll:** [Lehren für Zukunft]
```

#### 4. API-Kontrakte prüfen

**Vorher:**
- Backend ändern
- Frontend? "Wird schon passen"

**Jetzt:**
- **IMMER** Backend UND Frontend prüfen
- Request/Response-Format konsistent?
- Feldnamen identisch? (snake_case vs. camelCase?)
- Datentypen kompatibel?
- Defensive Checks einbauen!

#### 5. Defensive Programmierung

**Jetzt PFLICHT im Frontend:**

```javascript
// ✅ RICHTIG: Immer prüfen!
if (data && data.sub_routes && Array.isArray(data.sub_routes)) {
    data.sub_routes.forEach(route => { ... });
} else {
    console.error('[SUBROUTEN] Unerwartetes Response-Schema', data);
    showError('Fehler beim Laden der Subrouten');
}

// ❌ FALSCH: Blind vertrauen
data.sub_routes.forEach(route => { ... });  // TypeError wenn undefined!
```

---

## 🔄 Migration für bestehende Projekte

### Schritt 1: Dokumentation lesen

1. **Start:** [`docs/ki/README.md`](ki/README.md) - Übersicht
2. **Regeln:** [`docs/ki/REGELN_AUDITS.md`](ki/REGELN_AUDITS.md) - Grundregeln
3. **Checkliste:** [`docs/ki/AUDIT_CHECKLISTE.md`](ki/AUDIT_CHECKLISTE.md) - 9 Punkte

**Zeit:** ~20 Minuten

### Schritt 2: Nächster Bugfix nach neuem Standard

- Nutze Checkliste: `docs/ki/AUDIT_CHECKLISTE.md`
- Nutze Prompt: `docs/ki/CURSOR_PROMPT_TEMPLATE.md` (Template #1 oder #2)
- Prüfe ganzheitlich: Backend + Frontend + DB + Infra
- Schreibe mindestens 1 Regressionstest
- Dokumentiere in LESSONS_LOG (falls neuer Fehlertyp)

### Schritt 3: Code-Reviews anpassen

**Neue Review-Checkliste:**

- [ ] Backend geprüft (Routes, Services, Error-Handling)
- [ ] Frontend geprüft (API-Calls, Defensive Checks, Browser-Konsole)
- [ ] API-Kontrakt validiert (Request/Response konsistent?)
- [ ] Datenbank geprüft (Schema, Migrationen, Indizes)
- [ ] Infrastruktur geprüft (OSRM, ENV-Variablen, Health-Checks)
- [ ] Tests geschrieben (min. 1 Regressionstest)
- [ ] Dokumentation aktualisiert (LESSONS_LOG, API-Docs, Kommentare)

### Schritt 4: Cursor-Prompts nutzen

**Fertige Prompts verfügbar:**

1. Standard-Audit (vollständig)
2. Quick-Audit (gezielt)
3. Schema-Audit (Datenbank)
4. Frontend-Audit (JavaScript)
5. API-Kontrakt-Audit
6. Performance-Audit
7. Security-Audit
8. Regression-Test-Audit
9. Emergency-Audit (Production Down)
10. Custom-Audit (eigener Prompt)

**Siehe:** [`docs/ki/CURSOR_PROMPT_TEMPLATE.md`](ki/CURSOR_PROMPT_TEMPLATE.md)

---

## 🚀 Quick Start für neue Features

### Option 1: Cursor-Prompt verwenden

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

Liefere:
- Root Cause (nicht nur Symptom!)
- Konkrete Fixes (mit Dateinamen und Zeilen)
- Mindestens 1 Regressionstest
- Audit-Dokument nach docs/ki/REGELN_AUDITS.md
```

### Option 2: Checkliste abarbeiten

Öffne [`docs/ki/AUDIT_CHECKLISTE.md`](ki/AUDIT_CHECKLISTE.md) und arbeite die 9 Punkte systematisch ab:

1. Kontext klären
2. Backend prüfen
3. Frontend prüfen
4. Datenbank prüfen
5. Infrastruktur prüfen
6. Tests schreiben
7. Ergebnis dokumentieren
8. Abschluss-Checkliste
9. Audit-Completion-Report

---

## 📊 Erfolgsmetriken

**Was wir erreichen wollen:**

| Metrik | Vorher | Ziel (Q1 2025) |
|--------|--------|----------------|
| Isolierte Fixes | 60% | 0% ✅ |
| Fehler ohne Test | 40% | 0% ✅ |
| API-Kontrakt-Brüche | ~5/Monat | 0 ✅ |
| Schema-Drifts | ~2/Monat | 0 ✅ |
| Root Cause unbekannt | 30% | 0% ✅ |
| Code-Coverage | 45% | ≥ 80% ✅ |
| Dokumentierte Fehlertypen | 0 | ≥ 20 ✅ |

**Tracking:**

- Metriken in [`docs/ki/LESSONS_LOG.md`](ki/LESSONS_LOG.md) (Statistiken am Ende)
- Monatliches Review

---

## ❓ FAQs

### Muss ich wirklich IMMER Backend + Frontend + DB + Infra prüfen?

**JA!** Das ist das Kernprinzip von Version 2.0.

**Warum?**
- 80% aller Bugs in der Vergangenheit waren API-Kontrakt-Probleme (Backend ↔ Frontend)
- Schema-Drifts (DB) haben 3x Production-Outages verursacht
- Isolierte Fixes führen zu Seiteneffekten

**Ausnahme:**
- Nur bei reinen Dokumentations-Änderungen oder Refactorings ohne Funktionsänderung

### Was, wenn ich unsicher bin?

**Eskalieren!**

1. Dokumentiere: Was ist unklar? Welche Optionen?
2. Frage explizit nach Klärung
3. Schlage mehrere Lösungsansätze vor
4. Benenne Risiken und Seiteneffekte

**Siehe:** [`docs/ki/REGELN_AUDITS.md`](ki/REGELN_AUDITS.md) - Abschnitt "Eskalation"

### Wie lange dauert ein Audit nach dem neuen Standard?

**Quick-Audit (kleine Bugfixes):** 30-60 Minuten
**Standard-Audit (Features):** 2-4 Stunden
**Complex-Audit (Architektur-Änderungen):** 1-2 Tage

**ABER:** Langfristig **sparen** wir Zeit, weil:
- Weniger Regressions-Bugs
- Weniger Hotfixes
- Weniger Production-Outages
- Bessere Code-Qualität

### Gilt das auch für Prototypen / Experimente?

**Nein!**

- **Prototypen:** Lockere Regeln, schnelles Experimentieren
- **Experimente:** Eigene Branches, kein Merge in main ohne Audit
- **Production-Code:** Voller Standard (keine Ausnahmen!)

**Kennzeichnung:**

```python
# PROTOTYPE: Nicht für Production!
# Autor: Max Mustermann
# Datum: 2025-11-14
# Zweck: Testen einer neuen Routing-Strategie
```

---

## 📞 Support & Hilfe

### Dokumentation

- 📚 **Start:** [`docs/ki/README.md`](ki/README.md)
- 📋 **Regeln:** [`docs/ki/REGELN_AUDITS.md`](ki/REGELN_AUDITS.md)
- ✅ **Checkliste:** [`docs/ki/AUDIT_CHECKLISTE.md`](ki/AUDIT_CHECKLISTE.md)
- 📖 **Lessons:** [`docs/ki/LESSONS_LOG.md`](ki/LESSONS_LOG.md)
- 🚀 **Prompts:** [`docs/ki/CURSOR_PROMPT_TEMPLATE.md`](ki/CURSOR_PROMPT_TEMPLATE.md)

### Standards

- 📘 **Zentral:** [`docs/STANDARDS.md`](STANDARDS.md) ⭐ Version 2.0
- 📑 **Index:** [`docs/STANDARDS/INDEX.md`](STANDARDS/INDEX.md)

### Quick-Referenz

- 🎯 **Root:** [`KI_AUDIT_FRAMEWORK.md`](../KI_AUDIT_FRAMEWORK.md)

---

## ✅ Checkliste: Ich bin bereit für Version 2.0!

- [ ] Dokumentation gelesen (`docs/ki/README.md`, `docs/ki/REGELN_AUDITS.md`)
- [ ] Checkliste verstanden (`docs/ki/AUDIT_CHECKLISTE.md`)
- [ ] Cursor-Prompts angeschaut (`docs/ki/CURSOR_PROMPT_TEMPLATE.md`)
- [ ] Erste Code-Review nach neuem Standard durchgeführt
- [ ] LESSONS_LOG-Eintrag geschrieben (bei neuem Fehlertyp)
- [ ] Regressions-Test geschrieben (bei Bugfix)
- [ ] Ganzheitlich geprüft (Backend + Frontend + DB + Infra)

**Wenn alle Punkte abgehakt: Willkommen in STANDARDS V2! 🎉**

---

**Version:** 1.0  
**Datum:** 2025-11-14  
**Status:** AKTIV  
**Gültigkeit:** Ab sofort für alle Projekte

