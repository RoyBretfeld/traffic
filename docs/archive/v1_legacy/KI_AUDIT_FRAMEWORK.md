# 🤖 KI-Audit-Framework – Quick Reference

**Projekt:** FAMO TrafficApp 3.0  
**Für:** Strukturierte Code-Audits mit Cursor AI

---

## 📚 Vollständige Dokumentation

Alle Audit-Regeln, Checklisten und Templates befinden sich in:

### **`docs/ki/`**

| Datei | Beschreibung |
|-------|--------------|
| **[README.md](docs/ki/README.md)** | Übersicht & Workflow |
| **[REGELN_AUDITS.md](docs/ki/REGELN_AUDITS.md)** | Grundregeln für alle Audits |
| **[AUDIT_CHECKLISTE.md](docs/ki/AUDIT_CHECKLISTE.md)** | Systematische 9-Punkte-Checkliste |
| **[LESSONS_LOG.md](docs/ki/LESSONS_LOG.md)** | Dokumentierte Fehler & Lösungen |
| **[CURSOR_PROMPT_TEMPLATE.md](docs/ki/CURSOR_PROMPT_TEMPLATE.md)** | 10 fertige Prompts für verschiedene Szenarien |

---

## 🚀 Quick Start

### 1. Standard-Audit starten

```
Führe einen vollständigen Code-Audit durch für: [FEATURE/BUG]
Folge docs/ki/REGELN_AUDITS.md und docs/ki/AUDIT_CHECKLISTE.md
```

### 2. Cursor arbeitet systematisch

- ✅ Liest Regeln, Checkliste und Lessons Log
- ✅ Prüft Backend, Frontend, DB, Infrastruktur
- ✅ Identifiziert Root Cause
- ✅ Schlägt Fixes + Tests vor
- ✅ Dokumentiert Ergebnis

### 3. Review & Commit

- Fixes akzeptieren/anpassen
- Tests ausführen
- Bei neuem Fehlertyp: LESSONS_LOG aktualisieren
- Bei großem Audit: ZIP-Archiv erstellen

---

## 📋 Audit-Typen (Prompts verfügbar)

1. **Standard-Audit** – Vollständig (Backend + Frontend + DB + Infra)
2. **Quick-Audit** – Gezielt für spezifisches Problem
3. **Schema-Audit** – Datenbank-Konsistenz
4. **Frontend-Audit** – JavaScript/Browser-Fehler
5. **API-Kontrakt-Audit** – Backend ↔ Frontend Konsistenz
6. **Performance-Audit** – Bottlenecks identifizieren
7. **Security-Audit** – Sicherheitsprüfung
8. **Regression-Test-Audit** – Test-Coverage prüfen
9. **Emergency-Audit** – Production Down (schnell)
10. **Custom-Audit** – Eigener Prompt

**Alle Prompts:** [docs/ki/CURSOR_PROMPT_TEMPLATE.md](docs/ki/CURSOR_PROMPT_TEMPLATE.md)

---

## ✅ Checkliste für jedes Audit

- [ ] **Kontext klären** (Feature, Endpoints, Fehlermeldungen)
- [ ] **Backend prüfen** (Routes, Services, Logging, Config)
- [ ] **Frontend prüfen** (HTML/JS, API-Calls, Defensive Checks)
- [ ] **Datenbank prüfen** (Schema, Migrationen, Indizes)
- [ ] **Infrastruktur prüfen** (OSRM, LLM-APIs, ENV-Variablen)
- [ ] **Tests schreiben** (mindestens 1 Regressionstest)
- [ ] **Dokumentieren** (Root Cause, Fix, Erwartete Userwirkung)
- [ ] **LESSONS_LOG aktualisieren** (falls neuer Fehlertyp)
- [ ] **ZIP-Archiv erstellen** (bei größeren Audits)

---

## 📦 ZIP-Archiv-Struktur

Größere Audits erzeugen ein ZIP in `ZIP/`:

```
AUDIT_<THEMA>_YYYYMMDD_HHMMSS.zip
├── AUDIT_REPORT.md          ← Haupt-Dokument
├── logs/                    ← Server-Logs, Browser-Console
├── code/
│   ├── before/             ← Code VOR dem Fix
│   └── after/              ← Code NACH dem Fix
├── screenshots/            ← UI-Screenshots
└── tests/                  ← Neue Regressionstests
```

---

## 🎯 Best Practices

### ✅ DO

- Immer ganzheitlich prüfen (Backend + Frontend + DB + Infra)
- Root Cause identifizieren (nicht nur Symptom)
- Tests für jeden Fix
- Änderungen transparent dokumentieren
- LESSONS_LOG bei neuen Fehlertypen aktualisieren

### ❌ DON'T

- Isolierte Fixes ohne Impact-Analyse
- Code ändern ohne zu testen
- Breaking Changes ohne Dokumentation
- Sensible Daten in Logs
- Fehler stillschweigend verschlucken
- Architektur ohne Rücksprache umbauen

---

## 📊 Aktuelle Statistiken

| Metrik | Wert |
|--------|------|
| Durchgeführte Audits | 2 |
| Kritische Fehler behoben | 2 |
| Code-Qualität Δ | +40% |
| Test-Coverage Δ | +17% |

**Häufigste Fehlertypen:**

1. Schema-Drift (DB)
2. Syntax-Fehler (Frontend)
3. Missing Defensive Checks
4. Memory Leaks

---

## 🔗 Weitere Ressourcen

- **[AI_CODE_AUDIT_REGELN.md](AI_CODE_AUDIT_REGELN.md)** – Fokus auf API-Kontrakt (Backend ↔ Frontend)
- **[CURSOR_RULES.md](CURSOR_RULES.md)** – Allgemeine Cursor-Regeln
- **[docs/STANDARDS/](docs/STANDARDS/)** – Code-Standards & Playbooks

---

## 📞 Support

Bei Fragen oder Problemen:

1. **Dokumentation lesen:** `docs/ki/README.md`
2. **Lessons Log prüfen:** `docs/ki/LESSONS_LOG.md` (bekannte Fehler?)
3. **Custom Prompt erstellen:** `docs/ki/CURSOR_PROMPT_TEMPLATE.md` (Template anpassen)

---

**Version:** 1.0  
**Stand:** 2025-11-14  
**Erstellt für:** Strukturierte, reproduzierbare Code-Audits mit Cursor AI 🚀

