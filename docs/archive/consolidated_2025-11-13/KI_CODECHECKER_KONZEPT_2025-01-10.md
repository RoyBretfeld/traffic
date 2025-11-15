# KI-CodeChecker Konzept und Implementierungsplan
**Datum:** 2025-01-10  
**Status:** 📋 PLANUNG - Noch nicht implementiert  
**Priorität:** HOCH

---

## 🎯 Ziel

Ein automatisiertes KI-System entwickeln, das:
1. **Code prüft** - Fehler, Probleme und Verbesserungspotenziale identifiziert
2. **Code kontinuierlich verbessert** - KI arbeitet ständig am Code weiter (nicht nur optional)
3. **Als "Gegenchecker" fungiert** - Sicherstellt dass Code-Qualität hoch bleibt
4. **Benachrichtigungssystem** - Informiert Entwickler über alle Änderungen
5. **Sicherheit garantiert** - Software bleibt immer funktionsfähig (schrittweise Verbesserungen)

---

## 📋 Anforderungen

### Funktionale Anforderungen
1. **Automatische Code-Analyse**
   - Code auf Fehler prüfen
   - Best Practices überprüfen
   - Potenzielle Bugs identifizieren
   - Performance-Probleme erkennen

2. **Probleme-Kategorisierung**
   - Kritische Fehler (🔴)
   - Warnungen (🟡)
   - Verbesserungsvorschläge (🟢)

3. **Integration in Workflow**
   - Automatische Prüfung bei Code-Änderungen
   - Prüfung vor Commits
   - Regelmäßige Prüfung aller Dateien

4. **Reporting**
   - Detaillierte Berichte generieren
   - Probleme priorisieren
   - Fix-Vorschläge anbieten

5. **Kontinuierliche Code-Verbesserung** ⭐ NEU
   - KI arbeitet ständig am Code weiter (nicht nur auf Anfrage)
   - Automatische Fixes für einfache Probleme
   - Schrittweise Verbesserungen (nicht alles auf einmal)
   - Diff-Vorschau vor Anwendung
   - Backup vor Änderungen

6. **Benachrichtigungssystem** ⭐ NEU
   - Informiert Entwickler über alle Code-Änderungen
   - E-Mail-Benachrichtigungen
   - Dashboard mit Live-Updates
   - Log-Dateien mit Änderungshistorie
   - Webhook-Integration (optional)

7. **Safety-Mechanismen** ⭐ NEU
   - Tests vor/nach jeder Änderung
   - Rollback bei Fehlern
   - Schrittweise Verbesserungen (max. X Änderungen pro Tag)
   - Software bleibt immer funktionsfähig
   - Mitlernen und Weiterentwicklung in sicheren Schritten

---

## 🏗️ Architektur

### Komponenten

#### 1. Code-Analyzer
- **Zweck:** Code-Dateien analysieren
- **Eingabe:** Python/JavaScript-Dateien
- **Ausgabe:** Strukturierte Analyse-Ergebnisse

#### 2. KI-Engine
- **Zweck:** KI-basierte Code-Prüfung
- **Technologie:** OpenAI API, Claude API, oder lokales Modell
- **Funktionen:**
  - Code-Verständnis
  - Fehler-Erkennung
  - Best-Practices-Prüfung
  - Code-Qualität-Bewertung

#### 3. Rule-Engine
- **Zweck:** Regelbasierte Prüfungen
- **Regeln:**
  - Syntax-Fehler
  - Import-Fehler
  - Typ-Fehler
  - Security-Issues

#### 4. Report-Generator
- **Zweck:** Berichte generieren
- **Formate:**
  - Markdown-Reports
  - JSON-Reports
  - HTML-Dashboards

#### 5. Code-Fixer (Kontinuierliche Verbesserung) ⭐ NEU
- **Zweck:** Kontinuierliche automatische Code-Verbesserungen
- **Funktionen:**
  - KI arbeitet ständig am Code weiter
  - Schrittweise Verbesserungen (nicht alles auf einmal)
  - Diff-Vorschau erstellen
  - Backup vor Änderungen
  - Tests vor/nach Änderungen
  - Rollback bei Fehlern

#### 6. Benachrichtigungssystem ⭐ NEU
- **Zweck:** Entwickler über alle Änderungen informieren
- **Kanäle:**
  - E-Mail-Benachrichtigungen
  - Dashboard mit Live-Updates
  - Log-Dateien
  - Webhook-Integration (optional)

#### 7. Safety-Manager ⭐ NEU
- **Zweck:** Sicherstellen dass Software immer funktionsfähig bleibt
- **Funktionen:**
  - Tests vor/nach jeder Änderung
  - Rollback bei Fehlern
  - Schrittweise Verbesserungen (max. X Änderungen pro Tag)
  - Qualitäts-Check nach Änderungen
  - Mitlernen und Weiterentwicklung in sicheren Schritten

---

## 🔧 Implementierungsplan

### Phase 1: Grundlagen (Diese Woche)
- [ ] **1.1:** Code-Analyzer erstellen
  - [ ] Datei-Parsing (Python AST, JavaScript Parser)
  - [ ] Code-Struktur extrahieren
  - [ ] Abhängigkeiten analysieren

- [ ] **1.2:** Rule-Engine implementieren
  - [ ] Basis-Regeln definieren
  - [ ] Syntax-Checker
  - [ ] Import-Checker
  - [ ] Type-Checker (für TypeScript/Python)

- [ ] **1.3:** Reporting-System
  - [ ] Markdown-Report-Generator
  - [ ] Problem-Kategorisierung
  - [ ] Priorisierung

**Dateien:**
- `backend/services/code_checker.py` - Haupt-Service
- `backend/services/rule_engine.py` - Regel-Engine
- `backend/services/report_generator.py` - Report-Generator
- `scripts/run_code_check.py` - CLI-Tool

- [ ] **1.4:** Code-Fixer Grundstruktur ⭐ NEU
  - [ ] Backup-System
  - [ ] Diff-Generator
  - [ ] Review-Modus

- [ ] **1.5:** Benachrichtigungssystem ⭐ NEU
  - [ ] E-Mail-Versand
  - [ ] Dashboard-Integration
  - [ ] Log-System
  - [ ] Änderungshistorie

- [ ] **1.6:** Safety-Manager ⭐ NEU
  - [ ] Test-Runner (vor/nach Änderungen)
  - [ ] Rollback-Mechanismus
  - [ ] Schrittweise Verbesserungen (Rate-Limiting)
  - [ ] Qualitäts-Check

---

### Phase 2: KI-Integration (Nächste Woche)
- [ ] **2.1:** KI-API-Integration
  - [ ] OpenAI API Client
  - [ ] Prompt-Templates für Code-Prüfung
  - [ ] Response-Parsing

- [ ] **2.2:** KI-basierte Prüfungen
  - [ ] Code-Qualität-Bewertung
  - [ ] Best-Practices-Prüfung
  - [ ] Potenzielle Bugs identifizieren
  - [ ] Performance-Optimierungen vorschlagen

- [ ] **2.3:** Caching-System
  - [ ] Ergebnisse cachen (um API-Calls zu sparen)
  - [ ] Nur geänderte Dateien prüfen

- [ ] **2.4:** Code-Fixer (Kontinuierliche Verbesserung) ⭐ NEU
  - [ ] KI generiert verbesserten Code
  - [ ] Kontinuierliche Verbesserung (Background-Job)
  - [ ] Schrittweise Verbesserungen (max. X pro Tag)
  - [ ] Diff-Vorschau erstellen
  - [ ] Backup-System vor Änderungen
  - [ ] Tests vor/nach Änderungen
  - [ ] Rollback bei Fehlern

- [ ] **2.5:** Benachrichtigungssystem Integration ⭐ NEU
  - [ ] E-Mail bei Code-Änderungen
  - [ ] Dashboard-Updates
  - [ ] Log-Einträge
  - [ ] Änderungshistorie speichern

- [ ] **2.6:** Safety-Manager Integration ⭐ NEU
  - [ ] Automatische Tests vor Änderung
  - [ ] Automatische Tests nach Änderung
  - [ ] Rollback bei Test-Fehlern
  - [ ] Rate-Limiting (max. X Änderungen pro Tag)
  - [ ] Qualitäts-Check nach Änderungen

**Dateien:**
- `backend/services/ai_code_checker.py` - KI-Service
- `backend/services/prompt_templates.py` - Prompt-Templates
- `backend/services/code_check_cache.py` - Cache-System
- `backend/services/code_fixer.py` - Code-Fixer (KI-basierte Verbesserungen) ⭐ NEU

---

### Phase 3: Integration in Workflow (Übernächste Woche)
- [ ] **3.1:** Pre-Commit-Hook
  - [ ] Git-Hook erstellen
  - [ ] Automatische Prüfung vor Commit
  - [ ] Commit blockieren bei kritischen Fehlern

- [ ] **3.2:** CI/CD-Integration
  - [ ] GitHub Actions / GitLab CI
  - [ ] Automatische Prüfung bei Pull Requests
  - [ ] Kommentare in PRs

- [ ] **3.3:** Dashboard
  - [ ] Web-Dashboard für Ergebnisse
  - [ ] Trend-Analyse
  - [ ] Metriken

**Dateien:**
- `.git/hooks/pre-commit` - Git-Hook
- `.github/workflows/code-check.yml` - GitHub Actions
- `frontend/code-check-dashboard.html` - Dashboard

---

## 📝 Beispiel-Implementierung

### Code-Analyzer (Grundstruktur)

```python
# backend/services/code_checker.py
from pathlib import Path
import ast
import json
from typing import List, Dict, Any

class CodeChecker:
    def __init__(self):
        self.rules = []
        self.ai_checker = None  # Wird in Phase 2 implementiert
    
    def check_file(self, file_path: Path) -> Dict[str, Any]:
        """Prüft eine einzelne Datei."""
        results = {
            "file": str(file_path),
            "errors": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Syntax-Check
        syntax_errors = self._check_syntax(file_path)
        results["errors"].extend(syntax_errors)
        
        # Import-Check
        import_errors = self._check_imports(file_path)
        results["errors"].extend(import_errors)
        
        # Rule-basierte Prüfungen
        rule_results = self._check_rules(file_path)
        results["warnings"].extend(rule_results)
        
        # KI-basierte Prüfung (Phase 2)
        if self.ai_checker:
            ai_results = self.ai_checker.check(file_path)
            results["suggestions"].extend(ai_results)
        
        return results
    
    def _check_syntax(self, file_path: Path) -> List[Dict]:
        """Prüft Syntax-Fehler."""
        errors = []
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                if file_path.suffix == '.py':
                    ast.parse(f.read())
        except SyntaxError as e:
            errors.append({
                "type": "syntax_error",
                "severity": "error",
                "message": str(e),
                "line": e.lineno
            })
        return errors
    
    def _check_imports(self, file_path: Path) -> List[Dict]:
        """Prüft Import-Fehler."""
        errors = []
        # TODO: Implementierung
        return errors
    
    def _check_rules(self, file_path: Path) -> List[Dict]:
        """Prüft regelbasierte Probleme."""
        warnings = []
        # TODO: Implementierung
        return warnings
```

### KI-CodeChecker (Phase 2)

```python
# backend/services/ai_code_checker.py
import openai
from pathlib import Path
from typing import List, Dict

class AICodeChecker:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4"
    
    def check(self, file_path: Path) -> List[Dict]:
        """Prüft Code mit KI."""
        with open(file_path, 'r', encoding='utf-8') as f:
            code = f.read()
        
        prompt = f"""
Prüfe folgenden Code auf:
1. Fehler und Bugs
2. Best Practices
3. Performance-Probleme
4. Sicherheitsprobleme
5. Code-Qualität

Code:
```python
{code}
```

Antworte im JSON-Format:
{{
    "errors": [{{"type": "...", "severity": "error/warning/suggestion", "message": "...", "line": X}}],
    "score": 0-100,
    "summary": "..."
}}
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du bist ein Experte für Code-Review und Qualitätssicherung."},
                {"role": "user", "content": prompt}
            ],
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return result.get("errors", [])
```

### Code-Fixer (Phase 2.4) ⭐ NEU

```python
# backend/services/code_fixer.py
import openai
from pathlib import Path
from typing import Dict, Optional
import difflib
import shutil
from datetime import datetime

class CodeFixer:
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = "gpt-4"
        self.backup_dir = Path("data/code_fixes_backup")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    def fix_file(self, file_path: Path, issues: list, mode: str = "review") -> Dict:
        """
        Verbessert Code basierend auf gefundenen Problemen.
        
        Args:
            file_path: Pfad zur Datei
            issues: Liste der gefundenen Probleme
            mode: "review" (nur Vorschlag) oder "auto" (automatisch anwenden)
        
        Returns:
            Dict mit: original_code, fixed_code, diff, backup_path
        """
        # Original-Code lesen
        with open(file_path, 'r', encoding='utf-8') as f:
            original_code = f.read()
        
        # Backup erstellen
        backup_path = self._create_backup(file_path)
        
        # KI-Prompt für Code-Verbesserung
        prompt = f"""
Verbessere folgenden Code basierend auf diesen Problemen:
{self._format_issues(issues)}

Original-Code:
```python
{original_code}
```

Antworte NUR mit dem verbesserten Code (keine Erklärungen, kein Markdown):
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "Du bist ein Experte für Code-Verbesserung. Antworte NUR mit dem verbesserten Code, keine Erklärungen."},
                {"role": "user", "content": prompt}
            ]
        )
        
        fixed_code = response.choices[0].message.content.strip()
        
        # Entferne Markdown-Code-Blöcke falls vorhanden
        if fixed_code.startswith("```"):
            lines = fixed_code.split("\n")
            fixed_code = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        
        # Diff erstellen
        diff = self._create_diff(original_code, fixed_code, str(file_path))
        
        result = {
            "file": str(file_path),
            "original_code": original_code,
            "fixed_code": fixed_code,
            "diff": diff,
            "backup_path": str(backup_path),
            "issues_fixed": len(issues),
            "mode": mode
        }
        
        # Auto-Fix-Modus: Code direkt anwenden
        if mode == "auto":
            self._apply_fix(file_path, fixed_code)
            result["applied"] = True
        else:
            result["applied"] = False
        
        return result
    
    def _create_backup(self, file_path: Path) -> Path:
        """Erstellt Backup der Datei."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        backup_path = self.backup_dir / backup_name
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def _create_diff(self, original: str, fixed: str, filename: str) -> str:
        """Erstellt Diff zwischen Original und Fix."""
        original_lines = original.splitlines(keepends=True)
        fixed_lines = fixed.splitlines(keepends=True)
        diff = difflib.unified_diff(
            original_lines,
            fixed_lines,
            fromfile=f"original/{filename}",
            tofile=f"fixed/{filename}",
            lineterm=""
        )
        return "".join(diff)
    
    def _apply_fix(self, file_path: Path, fixed_code: str):
        """Wendet Fix auf Datei an."""
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(fixed_code)
    
    def _format_issues(self, issues: list) -> str:
        """Formatiert Issues für Prompt."""
        formatted = []
        for issue in issues:
            formatted.append(f"- Zeile {issue.get('line', '?')}: {issue.get('message', 'Unbekannt')}")
        return "\n".join(formatted)
    
    def review_fix(self, fix_result: Dict) -> bool:
        """
        Zeigt Diff-Vorschau und fragt nach Bestätigung.
        
        Returns:
            True wenn Fix angewendet werden soll
        """
        print(f"\n{'='*60}")
        print(f"Fix-Vorschau für: {fix_result['file']}")
        print(f"{'='*60}")
        print(fix_result['diff'])
        print(f"{'='*60}")
        print(f"Backup erstellt: {fix_result['backup_path']}")
        print(f"Issues behoben: {fix_result['issues_fixed']}")
        
        # In echter Implementierung: UI-Dialog oder CLI-Prompt
        # Hier: Rückgabe für manuelle Bestätigung
        return False  # Muss vom Benutzer bestätigt werden
```

### CLI-Tool (Erweitert mit Auto-Fix)

```python
# scripts/run_code_check.py
#!/usr/bin/env python3
"""CLI-Tool für Code-Prüfung und -Verbesserung."""
import sys
import argparse
from pathlib import Path
from backend.services.code_checker import CodeChecker
from backend.services.code_fixer import CodeFixer
from backend.services.report_generator import ReportGenerator

def main():
    parser = argparse.ArgumentParser(description="Code-Checker mit KI-Verbesserung")
    parser.add_argument("--fix", action="store_true", help="Automatisch Fixes anwenden")
    parser.add_argument("--review", action="store_true", help="Fix-Vorschläge anzeigen (Review-Modus)")
    parser.add_argument("--auto-fix-safe", action="store_true", help="Nur sichere Fixes automatisch anwenden")
    args = parser.parse_args()
    
    checker = CodeChecker()
    report_gen = ReportGenerator()
    fixer = None
    
    if args.fix or args.review or args.auto_fix_safe:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY nicht gesetzt für Code-Fixes")
            sys.exit(1)
        fixer = CodeFixer(api_key)
    
    # Dateien prüfen
    files_to_check = [
        Path("frontend/index.html"),
        Path("routes/upload_csv.py"),
        Path("routes/health_check.py"),
        # ... weitere Dateien
    ]
    
    all_results = []
    fixes_applied = []
    
    for file_path in files_to_check:
        if not file_path.exists():
            continue
        
        # Code prüfen
        results = checker.check_file(file_path)
        all_results.append(results)
        
        # Fixes anwenden (wenn gewünscht)
        if fixer and (results["errors"] or results["warnings"]):
            issues = results["errors"] + results["warnings"]
            
            # Bestimme Modus
            if args.auto_fix_safe:
                # Nur sichere Fixes (z.B. Formatierung, einfache Bugs)
                safe_issues = [i for i in issues if i.get("severity") == "warning"]
                if safe_issues:
                    fix_result = fixer.fix_file(file_path, safe_issues, mode="auto")
                    fixes_applied.append(fix_result)
            elif args.fix:
                # Alle Fixes automatisch anwenden
                fix_result = fixer.fix_file(file_path, issues, mode="auto")
                fixes_applied.append(fix_result)
            elif args.review:
                # Review-Modus: Vorschläge anzeigen
                fix_result = fixer.fix_file(file_path, issues, mode="review")
                if fixer.review_fix(fix_result):
                    # Benutzer hat bestätigt
                    fixer._apply_fix(file_path, fix_result["fixed_code"])
                    fixes_applied.append(fix_result)
    
    # Report generieren
    report = report_gen.generate(all_results, fixes_applied)
    
    # Report speichern
    report_path = Path("docs/CODE_CHECK_REPORT.md")
    report_path.write_text(report, encoding='utf-8')
    
    # Zusammenfassung ausgeben
    total_errors = sum(len(r["errors"]) for r in all_results)
    total_warnings = sum(len(r["warnings"]) for r in all_results)
    
    print(f"\n{'='*60}")
    print(f"Code-Prüfung abgeschlossen:")
    print(f"  Fehler: {total_errors}")
    print(f"  Warnungen: {total_warnings}")
    print(f"  Fixes angewendet: {len(fixes_applied)}")
    print(f"  Report: {report_path}")
    print(f"{'='*60}\n")
    
    if total_errors > 0 and not fixes_applied:
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Verwendung:

```bash
# Nur prüfen (keine Änderungen)
python scripts/run_code_check.py

# Fix-Vorschläge anzeigen (Review-Modus)
python scripts/run_code_check.py --review

# Nur sichere Fixes automatisch anwenden
python scripts/run_code_check.py --auto-fix-safe

# Alle Fixes automatisch anwenden (Vorsicht!)
python scripts/run_code_check.py --fix
```

---

## 🧪 Test-Plan

### Phase 1 Tests
- [ ] Code-Analyzer prüft Syntax-Fehler korrekt
- [ ] Rule-Engine findet bekannte Probleme
- [ ] Report-Generator erstellt korrekte Reports
- [ ] Backup-System funktioniert ⭐ NEU
- [ ] Diff-Generator erstellt korrekte Diffs ⭐ NEU

### Phase 2 Tests
- [ ] KI-API-Integration funktioniert
- [ ] KI findet tatsächliche Probleme
- [ ] Caching funktioniert korrekt
- [ ] **KI generiert verbesserten Code** ⭐ NEU
- [ ] **Auto-Fix wendet Änderungen korrekt an** ⭐ NEU
- [ ] **Review-Modus zeigt Diff-Vorschau** ⭐ NEU
- [ ] **Backup wird vor Änderungen erstellt** ⭐ NEU

### Phase 3 Tests
- [ ] Pre-Commit-Hook blockiert bei Fehlern
- [ ] CI/CD-Integration funktioniert
- [ ] Dashboard zeigt korrekte Daten
- [ ] **Auto-Fix in Pre-Commit-Hook integriert** ⭐ NEU

---

## 📊 Metriken und KPIs

### Code-Qualität
- Anzahl gefundener Fehler
- Anzahl behobener Fehler
- Code-Qualitäts-Score (0-100)
- **Anzahl automatisch behobener Probleme** ⭐ NEU
- **Verbesserungsrate (vorher/nachher)** ⭐ NEU

### Performance
- Prüfungszeit pro Datei
- API-Call-Kosten (KI)
- Cache-Hit-Rate
- **Fix-Generierungszeit** ⭐ NEU

### Adoption
- Anzahl genutzter Checks
- Anzahl behobener Probleme durch KI
- Zufriedenheit der Entwickler
- **Anzahl Auto-Fixes vs. manuelle Fixes** ⭐ NEU
- **Akzeptanzrate der KI-Fixes** ⭐ NEU

## 🔒 Sicherheitsaspekte

### Auto-Fix Sicherheit
1. **Backup vor jeder Änderung**
   - Automatisches Backup in `data/code_fixes_backup/`
   - Timestamp im Dateinamen
   - Rollback möglich

2. **Review-Modus (Standard)**
   - Diff-Vorschau vor Anwendung
   - Manuelle Bestätigung erforderlich
   - Keine automatischen Änderungen ohne Zustimmung

3. **Auto-Fix-Modi**
   - `--auto-fix-safe`: Nur sichere Fixes (Formatierung, einfache Bugs)
   - `--fix`: Alle Fixes (mit Vorsicht verwenden)
   - `--review`: Standard (nur Vorschläge)

4. **Validierung**
   - Syntax-Check nach Fix
   - Tests ausführen nach Fix
   - Rollback bei Fehlern

5. **Whitelist/Blacklist**
   - Bestimmte Dateien/Ordner ausschließen
   - Bestimmte Fix-Typen erlauben/verbieten

---

## 🔗 Integration in bestehende Checkliste

Die KI-CodeChecker sollte in die `CHECKLIST_PROBLEME_VERIFIZIERUNG_2025-01-10.md` integriert werden:

### Neuer Abschnitt: "KI-CodeChecker"

- [ ] **Test KI.1:** Code-Checker ausführen
  - [ ] `python scripts/run_code_check.py` ausführen
  - [ ] Report wird generiert
  - [ ] Keine kritischen Fehler gefunden

- [ ] **Test KI.2:** KI-Prüfung durchführen
  - [ ] KI-Checker prüft alle relevanten Dateien
  - [ ] KI findet bekannte Probleme
  - [ ] Fix-Vorschläge sind hilfreich

---

## 🚀 Nächste Schritte

### Sofort (Diese Woche)
1. **Phase 1 starten:**
   - [ ] Code-Analyzer-Grundstruktur erstellen
   - [ ] Rule-Engine implementieren
   - [ ] Report-Generator erstellen
   - [ ] CLI-Tool entwickeln

2. **Erste Tests:**
   - [ ] Code-Checker auf bestehende Dateien anwenden
   - [ ] Report prüfen
   - [ ] Probleme beheben

### Kurzfristig (Nächste Woche)
3. **Phase 2:**
   - [ ] KI-API-Integration
   - [ ] Prompt-Templates erstellen
   - [ ] Caching implementieren

4. **Integration:**
   - [ ] In Checkliste integrieren
   - [ ] In Workflow integrieren

---

## 📚 Verwandte Dokumente

- `docs/TEST_STRATEGIE_2025-01-10.md` - Test-Strategie
- `docs/ZUSAMMENFASSUNG_TESTS_KI_CHECKS.md` - KI-Checks Zusammenfassung
- `docs/CHECKLIST_PROBLEME_VERIFIZIERUNG_2025-01-10.md` - Haupt-Checkliste

---

**Erstellt:** 2025-01-10  
**Status:** 📋 PLANUNG  
**Nächste Überprüfung:** Nach Phase 1 Implementierung

