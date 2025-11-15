# 📘 FAMO TrafficApp - Regeln & Standards

**Version:** 2.0  
**Stand:** 2025-11-15  
**Zweck:** Projektspezifische Regeln, Standards und KI-Arbeitsrichtlinien

---

## 🌍 Globale Standards (projektübergreifend)

**Für alle Cursor-Projekte:**
- [`../Global/GLOBAL_STANDARDS.md`](../Global/GLOBAL_STANDARDS.md) - Universelle Entwicklungs-Standards
- [`../Global/PROJEKT_TEMPLATE.md`](../Global/PROJEKT_TEMPLATE.md) - Quick-Start für neue Projekte
- [`../Global/README.md`](../Global/README.md) - Übersicht globaler Dokumente

---

## 📋 Projektprofil (FAMO TrafficApp)

**Spezifische Regeln für dieses Projekt:**
- [`../PROJECT_PROFILE.md`](../PROJECT_PROFILE.md) - Technischer Überblick, Infrastruktur, Module, Teststrategie

**⚠️ Cursor:** Lies zuerst `PROJECT_PROFILE.md`, dann diese `Regeln/`-Dokumente!

---

## 📁 Übersicht: 8 Kern-Dokumente

### 1. **STANDARDS.md** ⭐ - Das Hauptdokument

**Vollständige Projekt-Standards für FAMO-Projekte**

Enthält:
- ✅ KI-Audit-Framework (7 unverhandelbare Regeln)
- ✅ Code-Review Standards (Backend, Frontend, API, DB, Tests)
- ✅ LLM-Integration (Schema-Validierung, Timeouts, Fallback)
- ✅ LLM für Code-Analyse & Code-Review
- ✅ Coding Standards (Python, JavaScript)
- ✅ Git-Workflow & Branching
- ✅ Deployment & Operations
- ✅ Audit & Compliance
- ✅ Changelog (Version 2.0)

**→ [STANDARDS.md](STANDARDS.md)** (für vollständige Referenz)

---

### 2. **STANDARDS_QUICK_REFERENCE.md** 🚀 - Die Schnellreferenz

**Kompakte Übersicht aller Regeln für schnellen Zugriff**

Perfekt für:
- ✅ Schnelles Nachschlagen
- ✅ Tägliche Arbeit
- ✅ Code-Review Checklisten
- ✅ Cursor-KI Arbeitsrichtlinien

**→ [STANDARDS_QUICK_REFERENCE.md](STANDARDS_QUICK_REFERENCE.md)** (für tägliche Nutzung)

---

### 3. **REGELN_AUDITS.md** 🔍 - KI-Audit-Regeln

**Die 7 unverhandelbaren Regeln für Code-Audits**

1. Scope explizit machen
2. Ganzheitlich prüfen (Backend + Frontend + DB + Infrastruktur)
3. Keine isolierten Fixes
4. Tests sind Pflicht
5. Dokumentation aktualisieren
6. Sicherheit & Robustheit
7. Transparenz

**Außerdem:**
- 6-Phasen-Workflow (Vorbereitung → Completion)
- Golden Test Cases
- Verbotene/Erlaubte Praktiken
- Multi-Layer-Pflicht

**→ [REGELN_AUDITS.md](REGELN_AUDITS.md)** (für Cursor-Audits)

---

### 4. **AUDIT_CHECKLISTE.md** ✅ - Standard-Checkliste

**9-Punkte-Checkliste für jeden Audit**

1. Kontext klären ⚠️ **+ Multi-Layer-Pflicht**
2. Backend prüfen
3. Frontend prüfen
4. Datenbank & Schema
5. Infrastruktur
6. Tests
7. Ergebnis-Dokumentation
8. Abschluss-Checkliste
9. Audit-Report

**→ [AUDIT_CHECKLISTE.md](AUDIT_CHECKLISTE.md)** (für systematisches Abarbeiten)

---

### 5. **CURSOR_PROMPT_TEMPLATE.md** 🤖 - Prompt-Vorlagen

**12 fertige Cursor-Prompt-Templates:**

1. **Ganzheitliches Audit - Kugelsicher** ⭐ (EMPFOHLEN)
2. Standard-Audit (Vollständig)
3. Quick-Audit (Gezielt)
4. Schema-Audit (Datenbank)
5. Frontend-Audit (JavaScript)
6. API-Kontrakt-Audit
7. Performance-Audit
8. Security-Audit
9. Regression-Test-Audit
10. Emergency-Audit (Production Down)
11. **Sub-Routen-Generator Audit** ⚙️ (Speziell für kritisches Feature)
12. Custom-Audit-Prompt (Vorlage)

**→ [CURSOR_PROMPT_TEMPLATE.md](CURSOR_PROMPT_TEMPLATE.md)** (für Copy & Paste in Cursor)

---

### 6. **LESSONS_LOG.md** 📝 - Lernbuch

**Dokumentation aller kritischen Fehler**

Format pro Eintrag:
- Symptom
- Root Cause
- Fix
- Was die KI künftig tun soll

**Aktuelle Einträge:**
1. Schema-Drift (geo_fail / next_attempt)
2. Panel IPC (Syntax-Fehler + Memory Leak)
3. Sub-Routen-Generator (API-Kontrakt-Bruch)

**→ [LESSONS_LOG.md](LESSONS_LOG.md)** (wächst mit der Zeit)

---

### 7. **CURSOR_WORKFLOW.md** 🔄 - Workflow-Leitfaden

**Fester Prozess für strukturierte Cursor-Arbeit**

Enthält:
- ✅ 4 Ziele: Stabilität, Nachvollziehbarkeit, Ganzheitlich, Lernend
- ✅ 4 Feste Regeln (Audit-ZIP, Template, Multi-Layer, Ghost-Verbot)
- ✅ 6-Schritt-Workflow (Problem → ZIP → Prompt → Fix → Test → Lessons)
- ✅ Health-Checks als Schutzschicht
- ✅ Ganzheitliches Testen (Backend + Frontend)
- ✅ Checkliste für jeden Audit

**Perfekt für:**
- Reproduzierbare Bug-Fixes
- Strukturierte Änderungen
- Nachvollziehbare Audits
- Kontinuierliches Lernen

**→ [CURSOR_WORKFLOW.md](CURSOR_WORKFLOW.md)** (für strukturierte Arbeit)

---

### 8. **Dieses README** 📖

Du liest es gerade! 😊

---

## 🚀 Schnellstart für verschiedene Szenarien

### **Szenario 1: Bug-Fix im Projekt**

1. Öffne: `CURSOR_PROMPT_TEMPLATE.md`
2. Nutze: **Template #1** (Ganzheitliches Audit - Kugelsicher)
3. Passe SCOPE an (betroffene Dateien)
4. Kopiere in Cursor
5. Folge der Checkliste

---

### **Szenario 2: Sub-Routen-Generator Problem**

1. Öffne: `CURSOR_PROMPT_TEMPLATE.md`
2. Nutze: **Template #10** (Sub-Routen-Generator Audit)
3. Passe SCOPE an
4. Kopiere in Cursor
5. Prüfe `LESSONS_LOG.md` → Eintrag #3 für bekannte Probleme

---

### **Szenario 3: Code-Review durchführen**

1. Öffne: `STANDARDS_QUICK_REFERENCE.md`
2. Nutze: "Ganzheitliche Code-Reviews" Checkliste
3. Prüfe alle Layers: Backend, Frontend, API, DB, Infra
4. Dokumentiere Ergebnisse

---

### **Szenario 4: Neue Standards nachschlagen**

1. Öffne: `STANDARDS.md`
2. Nutze Inhaltsverzeichnis
3. Springe zu relevanter Sektion

---

## 📊 Dokumentations-Hierarchie

```
Regeln/
│
├── STANDARDS.md                        ← Vollständig (alles)
│   └── Referenziert alle anderen Dokumente
│
├── STANDARDS_QUICK_REFERENCE.md        ← Kompakt (tägliche Nutzung)
│   └── Auszug aus STANDARDS.md
│
├── REGELN_AUDITS.md                    ← 7 Regeln + Workflow
│   └── Teil von STANDARDS.md
│
├── AUDIT_CHECKLISTE.md                 ← 9-Punkte-Checkliste
│   └── Ergänzt REGELN_AUDITS.md
│
├── CURSOR_PROMPT_TEMPLATE.md           ← 12 Templates
│   └── Nutzt REGELN_AUDITS.md + AUDIT_CHECKLISTE.md
│
├── CURSOR_WORKFLOW.md                  ← 🔄 Workflow-Leitfaden (NEU!)
│   └── 6-Schritt-Prozess für strukturierte Arbeit
│
├── LESSONS_LOG.md                      ← Lernbuch (wächst)
│   └── Wird von Cursor vor jedem Audit gelesen
│
└── README.md                           ← Diese Datei
    └── Übersicht aller Dokumente
```

---

## 🔄 Workflow-Empfehlung

### **Für Entwickler (Menschen):**

1. **Tägliche Arbeit:** `STANDARDS_QUICK_REFERENCE.md` griffbereit haben
2. **Code-Review:** Checkliste durchgehen
3. **Bei Fragen:** `STANDARDS.md` nachschlagen
4. **Vor Bug-Fix:** `LESSONS_LOG.md` nach ähnlichen Problemen suchen

---

### **Für Cursor-KI:**

**📖 Lies zuerst:** `CURSOR_WORKFLOW.md` für den kompletten Prozess!

1. **Vor jedem Audit:**
   - `CURSOR_WORKFLOW.md` → 6-Schritt-Prozess
   - `REGELN_AUDITS.md` lesen
   - `AUDIT_CHECKLISTE.md` lesen
   - `LESSONS_LOG.md` nach bekannten Fehlertypen durchsuchen

2. **Während Audit:**
   - Template aus `CURSOR_PROMPT_TEMPLATE.md` folgen
   - Multi-Layer-Pflicht beachten (Backend + Frontend + DB + Infra)
   - Kein Ghost-Refactoring
   - Audit-ZIP vorbereiten

3. **Nach Audit:**
   - Health-Checks prüfen (siehe `CURSOR_WORKFLOW.md`)
   - Bei neuem Fehlertyp: `LESSONS_LOG.md` aktualisieren
   - Ergebnis dokumentieren

---

## 📝 Wartung

### **Wann aktualisieren?**

- **STANDARDS.md:** Bei grundlegenden Änderungen (Breaking Changes)
- **STANDARDS_QUICK_REFERENCE.md:** Parallel zu STANDARDS.md
- **LESSONS_LOG.md:** Nach jedem kritischen Fehler
- **CURSOR_PROMPT_TEMPLATE.md:** Bei neuen Szenarien/Templates
- **REGELN_AUDITS.md:** Bei neuen Audit-Regeln
- **AUDIT_CHECKLISTE.md:** Bei neuen Checkpunkten

### **Versionierung:**

Siehe `STANDARDS.md` → Changelog

---

## 🗂️ Archiv

Alte/obsolete Dokumentation liegt in:
```
docs/archive/v1_legacy/
```

Siehe dort für:
- AI_CODE_AUDIT_REGELN.md (V1)
- KI_AUDIT_FRAMEWORK.md (V1)
- CODE_AUDIT_PLAYBOOK.md (Legacy)
- STANDARDS_V2_MIGRATION.md
- etc.

---

## 🎯 Wichtigste Regeln auf einen Blick

### **Die 3 goldenen Regeln:**

1. ✅ **Multi-Layer-Pflicht:** Backend + Frontend + DB + Infra IMMER gemeinsam prüfen
2. ❌ **Kein Ghost-Refactoring:** Nur explizit genannte Dateien ändern
3. 🎯 **Golden Tests:** Für kritische Features (Sub-Routen, OSRM, Tour-Upload)

---

## 📞 Bei Fragen

- Siehe: `STANDARDS_QUICK_REFERENCE.md` (schnell)
- Siehe: `STANDARDS.md` (vollständig)
- Neues Problem: `LESSONS_LOG.md` aktualisieren

---

**Version:** 2.0  
**Letzte Aktualisierung:** 2025-11-15  
**Projekt:** FAMO TrafficApp 3.0

---

## 🔗 Siehe auch

**Global (projektübergreifend):**
- [`../Global/`](../Global/) - Universelle Standards für alle Cursor-Projekte
- [`../PROJECT_PROFILE.md`](../PROJECT_PROFILE.md) - Projektprofil (FAMO TrafficApp)

---

🚀 **Viel Erfolg mit strukturierten, reproduzierbaren Code-Audits!**
