# Standards-Index

**Zentrale Standards-Dokumentation für alle FAMO-Projekte**

**Version:** 2.0 ⭐ **KI-Audit-Framework integriert**  
**Letzte Aktualisierung:** 2025-11-14

---

## 📚 Hauptdokumentation

### [STANDARDS.md](../STANDARDS.md) ⭐ **Version 2.0**
**Zentrale Standards-Dokumentation** - Alle wichtigen Richtlinien in einem Dokument:
- **Cursor KI Arbeitsrichtlinien**
- **KI-Audit-Framework (PFLICHT)** ⭐ **NEU**
- Coding Standards
- Architektur-Prinzipien
- API-Standards
- Testing-Standards
- Git & Versionierung
- Deployment & Operations
- Audit & Compliance
- Dokumentations-Standards

---

## ⭐ KI-Audit-Framework (PFLICHT - NEU!)

### Vollständiges Framework in `docs/ki/`

**Ab sofort VERBINDLICH für alle Code-Reviews und Audits!**

| Dokument | Zweck | Status |
|----------|-------|--------|
| **[ki/README.md](../ki/README.md)** | Framework-Übersicht & Workflow | ✅ PFLICHT |
| **[ki/REGELN_AUDITS.md](../ki/REGELN_AUDITS.md)** | Grundregeln für alle Audits | ✅ PFLICHT |
| **[ki/AUDIT_CHECKLISTE.md](../ki/AUDIT_CHECKLISTE.md)** | 9-Punkte-Checkliste | ✅ PFLICHT |
| **[ki/LESSONS_LOG.md](../ki/LESSONS_LOG.md)** | Dokumentierte Fehler & Lösungen | ✅ PFLICHT |
| **[ki/CURSOR_PROMPT_TEMPLATE.md](../ki/CURSOR_PROMPT_TEMPLATE.md)** | 10 fertige Audit-Prompts | ✅ PFLICHT |

**Quick-Referenz:** [KI_AUDIT_FRAMEWORK.md](../../KI_AUDIT_FRAMEWORK.md) (Projekt-Root)

**Kernprinzip:**  
> "Kein isolierter Fix mehr! Jede Änderung wird ganzheitlich bewertet: Backend + Frontend + DB + Infrastruktur"

**Die 7 Unverhandelbaren Regeln:**
1. Scope explizit machen
2. Immer ganzheitlich prüfen (Backend + Frontend + DB + Infra)
3. Keine isolierten Fixes
4. Tests sind Pflicht (min. 1 Regressionstest pro Fix)
5. Dokumentation aktualisieren
6. Sicherheit und Robustheit
7. Transparenz bei Änderungen

---

## 🔧 Spezifische Standards

### Development
- **[Cursor-Arbeitsrichtlinie.md](../Cursor-Arbeitsrichtlinie.md)** - Cursor-spezifische Best Practices
- **[CURSOR_KI_BETRIEBSORDNUNG.md](../CURSOR_KI_BETRIEBSORDNUNG.md)** - Detaillierte Cursor-KI Betriebsordnung

### Architektur
- **[Architecture.md](../Architecture.md)** - System-Architektur
- **[ARCHITEKTUR_KOMPLETT.md](../ARCHITEKTUR_KOMPLETT.md)** - Vollständige Architektur-Dokumentation

### API
- **[Api_Docs.md](../Api_Docs.md)** - API-Dokumentation
- **[MULTI_TOUR_GENERATOR_API.md](../MULTI_TOUR_GENERATOR_API.md)** - Multi-Tour-Generator API

### Testing
- **[TEST_STRATEGIE_2025-01-10.md](../TEST_STRATEGIE_2025-01-10.md)** - Test-Strategie

### Deployment
- **[INSTALLATION_GUIDE.md](../INSTALLATION_GUIDE.md)** - Installations-Anleitung
- **[SETUP_ANLEITUNG.md](../SETUP_ANLEITUNG.md)** - Setup-Anleitung
- **[DEVELOPER_GUIDE.md](../DEVELOPER_GUIDE.md)** - Entwickler-Guide

### Operations
- **[RUNBOOK_ROUTING.md](../RUNBOOK_ROUTING.md)** - Routing-Runbook
- **[LOGGING_GUIDE.md](../LOGGING_GUIDE.md)** - Logging-Guide
- **[PERFORMANCE_OPTIMIERUNG.md](../PERFORMANCE_OPTIMIERUNG.md)** - Performance-Optimierung

### Audit & Compliance

#### Primär (aktuell)
- **[ki/README.md](../ki/README.md)** ⭐ **KI-Audit-Framework** - Vollständiges Framework (PFLICHT)
- **[tools/make_audit_zip.py](../../tools/make_audit_zip.py)** - Audit-ZIP-Pipeline

#### Legacy (Altprojekte)
- **[CODE_AUDIT_PLAYBOOK.md](CODE_AUDIT_PLAYBOOK.md)** - Code-Audit Playbook (ersetzt durch KI-Framework)

---

## 📋 Verwendung

### Für neue Projekte

1. **Kopiere `STANDARDS.md`** in das neue Projekt
2. **Passe projektspezifische Abschnitte an**
3. **Verweise auf diese Standards** in der Projekt-README

### Für bestehende Projekte

1. **Prüfe Einhaltung** der Standards
2. **Aktualisiere projektspezifische Dokumentation**
3. **Führe Audit-ZIP** aus für Compliance-Check

---

## 🔄 Aktualisierung

Diese Standards werden regelmäßig aktualisiert. Bei Änderungen:

1. **Änderung in `STANDARDS.md`** dokumentieren
2. **Changelog** aktualisieren
3. **Betroffene Projekte** informieren

---

## 📊 Breaking Changes in Version 2.0

### ⚠️ Ab sofort PFLICHT: KI-Audit-Framework

**Was ändert sich:**

1. **Alle Code-Reviews müssen ganzheitlich sein:**
   - ✅ Backend UND Frontend UND Datenbank UND Infrastruktur
   - ❌ Keine isolierten Fixes mehr (nur Backend ODER nur Frontend)

2. **Tests sind Pflicht:**
   - ✅ Mindestens 1 Regressionstest pro Bugfix
   - ❌ Kein Fix ohne Test

3. **Root Cause identifizieren:**
   - ✅ Nicht nur Symptom beheben
   - ✅ Ursache dokumentieren in LESSONS_LOG

4. **API-Kontrakte prüfen:**
   - ✅ Request/Response-Format Backend ↔ Frontend
   - ✅ Feldnamen, Datentypen, Null-Checks

5. **Dokumentation aktualisieren:**
   - ✅ LESSONS_LOG bei neuem Fehlertyp
   - ✅ API-Docs bei Endpoint-Änderungen
   - ✅ Inline-Kommentare bei komplexen Fixes

**Migration:**
- **Neue Projekte:** Folgen Sie `docs/ki/REGELN_AUDITS.md` von Anfang an
- **Bestehende Projekte:** Nächster Bugfix → KI-Audit-Framework anwenden
- **Cursor-Prompts:** Nutzen Sie `docs/ki/CURSOR_PROMPT_TEMPLATE.md`

**Hilfe & Support:**
- 📚 Lesen Sie: `docs/ki/README.md` (Start hier!)
- ✅ Nutzen Sie: `docs/ki/AUDIT_CHECKLISTE.md` (systematisch abarbeiten)
- 🚀 Prompts: `docs/ki/CURSOR_PROMPT_TEMPLATE.md` (10 fertige Templates)

---

**Letzte Aktualisierung:** 2025-11-14

