# 🗄️ Legacy-Dokumentation (Version 1.0)

**Archiviert am:** 2025-11-14  
**Grund:** Konsolidierung zu STANDARDS V2.0

---

## Dateien in diesem Archiv

### Aus Root:

1. **`AI_CODE_AUDIT_REGELN.md`**
   - **Status:** Obsolet
   - **Ersetzt durch:** `docs/ki/REGELN_AUDITS.md`
   - **Inhalt:** Frühe Version der Audit-Regeln (nur Backend + Frontend)

2. **`KI_AUDIT_FRAMEWORK.md`**
   - **Status:** Obsolet
   - **Ersetzt durch:** `docs/STANDARDS.md` (KI-Audit-Framework Sektion)
   - **Inhalt:** Framework-Übersicht, Ordnerstruktur, Cursor-Prompts

3. **`STANDARDS_V2_RELEASE_NOTES.md`**
   - **Status:** Archiviert (Release-Doku)
   - **Ersetzt durch:** `docs/STANDARDS.md` (Changelog Sektion)
   - **Inhalt:** Release Notes für STANDARDS Version 2.0

---

### Aus `docs/`:

4. **`STANDARDS_V2_MIGRATION.md`**
   - **Status:** Archiviert (Migration-Doku)
   - **Relevant für:** Migration von V1 → V2 (nicht mehr aktuell)
   - **Inhalt:** Breaking Changes, Migration-Schritte

---

### Aus `docs/STANDARDS/`:

5. **`INDEX.md`**
   - **Status:** Obsolet
   - **Ersetzt durch:** `docs/STANDARDS_QUICK_REFERENCE.md`
   - **Inhalt:** Index-Datei für alten STANDARDS-Ordner

6. **`CODE_AUDIT_PLAYBOOK.md`**
   - **Status:** Legacy (als veraltet markiert in STANDARDS.md)
   - **Ersetzt durch:** `docs/ki/` Framework (REGELN_AUDITS.md + AUDIT_CHECKLISTE.md)
   - **Inhalt:** Alte Audit-Prozess-Beschreibung

---

## Migration nach V2.0

Alle Inhalte aus diesen Dateien wurden in die neue Struktur integriert:

### Neue Kern-Dokumente:

```
docs/
├── STANDARDS.md                        # ← Vollständige Standards (mit KI-Audit-Framework)
├── STANDARDS_QUICK_REFERENCE.md        # ← Kompakte Schnellreferenz
└── ki/
    ├── REGELN_AUDITS.md                # ← 7 Regeln + 6-Phasen-Workflow
    ├── AUDIT_CHECKLISTE.md             # ← 9-Punkte-Checkliste
    ├── CURSOR_PROMPT_TEMPLATE.md       # ← 10 Prompt-Templates
    ├── LESSONS_LOG.md                  # ← Lernbuch
    └── README.md                       # ← Übersicht
```

---

## Wichtige Änderungen (V1 → V2):

### ✅ NEU in V2:

1. **Multi-Layer-Pflicht:** Backend + Frontend + DB + Infra MUSS geprüft werden
2. **Ghost-Refactor-Verbot:** Keine heimlichen Umbenennungen mehr
3. **Golden Tests:** Referenz-Tests für kritische Features
4. **LLM-Code-Analyse:** Framework für LLM-basierten Code-Review
5. **Kugelsicherer Cursor-Prompt:** Template #1 in CURSOR_PROMPT_TEMPLATE.md

### ❌ ENTFERNT in V2:

- Verstreute Dokumentation (konsolidiert)
- Redundante INDEX-Dateien
- Separate Release-Notes (in STANDARDS.md integriert)

---

## Wiederherstellung

Falls Inhalte aus diesen Dateien benötigt werden:

1. **Datei öffnen** (aus diesem Archiv)
2. **Relevanten Abschnitt kopieren**
3. **In neue Struktur integrieren** (STANDARDS.md oder docs/ki/)

**Hinweis:** Alle wichtigen Inhalte wurden bereits migriert!

---

## Kontakt

Bei Fragen zur Migration oder fehlenden Inhalten:
- Siehe `docs/STANDARDS_QUICK_REFERENCE.md`
- Siehe `docs/STANDARDS.md` (Version 2.0)

---

**Archiviert durch:** Konsolidierungs-Prozess  
**Datum:** 2025-11-14  
**Grund:** Aufräumen der Dokumentations-Struktur für STANDARDS V2.0

