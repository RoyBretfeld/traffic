"""
KI-Engine für Code-Verbesserungen.
Nutzt GPT-4o-mini für intelligente Code-Analyse und Verbesserungsvorschläge.
Lernt aus dem Fehlerkatalog (ERROR_CATALOG.md) und der Fehlerhistorie (LESSONS_LOG.md).
"""
import os
import json
import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from openai import OpenAI
from backend.services.cost_tracker import get_cost_tracker
from backend.services.performance_tracker import get_performance_tracker
from backend.services.code_analyzer import CodeIssue, analyze_code_file

logger = logging.getLogger(__name__)

class AICodeChecker:
    """KI-basierter Code-Checker mit GPT-4o-mini + Fehlerhistorie + Auto-Reload."""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialisiert den AI Code Checker.
        
        Args:
            api_key: OpenAI API-Key (falls None, wird aus Umgebungsvariable gelesen)
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY nicht gesetzt")
        
        self.client = OpenAI(api_key=self.api_key)
        self.cost_tracker = get_cost_tracker()
        self.performance_tracker = get_performance_tracker()
        
        # GPT-4o-mini als Standard-Modell
        self.model = self.cost_tracker.default_model  # "gpt-4o-mini"
        
        # Lade Fehlerhistorie beim Start
        self.learned_patterns = self._load_learned_patterns()
        self.last_reload = datetime.now()
        self._reload_lock = asyncio.Lock()
        
        # Starte Background-Task für Auto-Reload (alle 6 Stunden)
        self._start_auto_reload_task()
    
    def analyze_and_improve(self, file_path: Path) -> Dict[str, Any]:
        """
        Analysiert Code und generiert Verbesserungsvorschläge.
        
        Args:
            file_path: Pfad zur Python-Datei
            
        Returns:
            Dict mit Analyse-Ergebnissen und Verbesserungsvorschlägen
        """
        # 1. Lokale Code-Analyse (schnell, kostenlos)
        local_issues = analyze_code_file(file_path)
        
        # 2. KI-Analyse (kostenpflichtig, aber intelligent)
        with self.performance_tracker.track_operation("ai_code_analysis", str(file_path)):
            ai_result = self._analyze_with_ai(file_path)
        
        # 3. Kombiniere Ergebnisse
        return {
            "file": str(file_path),
            "local_issues": [self._issue_to_dict(issue) for issue in local_issues],
            "ai_analysis": ai_result,
            "total_issues": len(local_issues) + len(ai_result.get("issues", [])),
            "improvement_score": ai_result.get("score", 0)
        }
    
    def _analyze_with_ai(self, file_path: Path) -> Dict[str, Any]:
        """Analysiert Code mit GPT-4o-mini."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                code = f.read()
        except Exception as e:
            return {
                "error": f"Fehler beim Lesen der Datei: {e}",
                "issues": [],
                "score": 0
            }
        
        # Prüfe ob Verbesserung erlaubt ist (Rate-Limiting)
        can_improve, message = self.cost_tracker.can_improve_code()
        if not can_improve:
            return {
                "error": f"Limit erreicht: {message}",
                "issues": [],
                "score": 0
            }
        
        # Erstelle Prompt
        prompt = self._create_analysis_prompt(code, file_path)
        
        # API-Aufruf mit Tracking
        try:
            with self.performance_tracker.track_operation("api_call", str(file_path)):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Du bist ein Experte für Python-Code-Review und Qualitätssicherung. "
                                     "Analysiere Code auf Fehler, Probleme und Verbesserungspotenziale. "
                                     "Antworte immer im JSON-Format."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.3,  # Niedrige Temperatur für konsistente Ergebnisse
                    response_format={"type": "json_object"}
                )
            
            # Tracke Kosten
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self.cost_tracker.track_api_call(
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                file_path=str(file_path),
                operation="code_analysis"
            )
            
            # Parse Antwort
            result = json.loads(response.choices[0].message.content)
            
            return {
                "issues": result.get("issues", []),
                "score": result.get("score", 0),
                "summary": result.get("summary", ""),
                "suggestions": result.get("suggestions", []),
                "cost_eur": cost,
                "tokens_used": input_tokens + output_tokens
            }
            
        except Exception as e:
            return {
                "error": f"Fehler bei KI-Analyse: {e}",
                "issues": [],
                "score": 0
            }
    
    def _load_learned_patterns(self) -> Dict[str, str]:
        """
        Lädt bekannte Fehlermuster aus ERROR_CATALOG und LESSONS_LOG.
        
        Returns:
            Dict mit 'error_catalog' und 'lessons_log' (jeweils relevante Auszüge)
        """
        project_root = Path(__file__).parent.parent.parent
        
        patterns = {
            "error_catalog": "",
            "lessons_log": "",
            "loaded": False
        }
        
        try:
            # ERROR_CATALOG.md laden
            error_catalog_path = project_root / "docs" / "ERROR_CATALOG.md"
            if error_catalog_path.exists():
                with open(error_catalog_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extrahiere relevante Abschnitte (erste 3000 Zeichen für Token-Limit)
                    patterns["error_catalog"] = content[:3000]
            
            # LESSONS_LOG.md laden
            lessons_log_path = project_root / "Regeln" / "LESSONS_LOG.md"
            if lessons_log_path.exists():
                with open(lessons_log_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    # Extrahiere "Was die KI künftig tun soll" Abschnitte
                    lessons = self._extract_lessons(content)
                    patterns["lessons_log"] = lessons
            
            patterns["loaded"] = True
            
        except Exception as e:
            print(f"[AI-CodeChecker] Fehler beim Laden der Fehlermuster: {e}")
        
        return patterns
    
    def _extract_lessons(self, content: str) -> str:
        """
        Extrahiert die wichtigsten Lektionen aus LESSONS_LOG.
        
        Args:
            content: Vollständiger LESSONS_LOG Inhalt
            
        Returns:
            Zusammengefasste Lektionen (max. 2000 Zeichen)
        """
        lines = content.split('\n')
        lessons = []
        in_lesson_section = False
        
        for line in lines:
            # Finde "Was die KI künftig tun soll" Abschnitte
            if "Was die KI künftig tun soll" in line or "### Was die KI künftig tun soll" in line:
                in_lesson_section = True
                lessons.append("\n---")
                continue
            
            # Ende eines Abschnitts
            if in_lesson_section and (line.startswith("##") or line.startswith("---")):
                in_lesson_section = False
                continue
            
            # Sammle Lektion-Zeilen
            if in_lesson_section and line.strip():
                lessons.append(line)
        
        result = '\n'.join(lessons)
        # Begrenze auf 2000 Zeichen (Token-Limit)
        return result[:2000] if len(result) > 2000 else result
    
    def _start_auto_reload_task(self):
        """Startet Background-Task für automatisches Reload alle 6 Stunden."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                loop.create_task(self._auto_reload_loop())
                logger.info("[AI-CodeChecker] Auto-Reload Task gestartet (alle 6 Stunden)")
            else:
                logger.warning("[AI-CodeChecker] Event Loop nicht aktiv - Auto-Reload nicht gestartet")
        except Exception as e:
            logger.error(f"[AI-CodeChecker] Fehler beim Starten des Auto-Reload Tasks: {e}")
    
    async def _auto_reload_loop(self):
        """Background-Task: Lädt Fehlerhistorie alle 6 Stunden neu."""
        while True:
            try:
                # Warte 6 Stunden (21600 Sekunden)
                await asyncio.sleep(21600)
                
                # Reload mit Lock (damit nicht mehrere Reloads gleichzeitig laufen)
                async with self._reload_lock:
                    logger.info("[AI-CodeChecker] Starte automatisches Reload der Fehlerhistorie...")
                    self.learned_patterns = self._load_learned_patterns()
                    self.last_reload = datetime.now()
                    logger.info(f"[AI-CodeChecker] Fehlerhistorie neu geladen: {self.last_reload}")
                    
            except asyncio.CancelledError:
                logger.info("[AI-CodeChecker] Auto-Reload Task beendet")
                break
            except Exception as e:
                logger.error(f"[AI-CodeChecker] Fehler beim Auto-Reload: {e}")
                # Warte 5 Minuten bei Fehler, dann retry
                await asyncio.sleep(300)
    
    async def reload_patterns(self) -> Dict[str, Any]:
        """
        Lädt Fehlerhistorie manuell neu (für API-Endpoint).
        
        Returns:
            Dict mit Reload-Status
        """
        async with self._reload_lock:
            try:
                old_loaded = self.learned_patterns.get("loaded", False)
                self.learned_patterns = self._load_learned_patterns()
                self.last_reload = datetime.now()
                
                return {
                    "success": True,
                    "loaded": self.learned_patterns.get("loaded", False),
                    "previous_loaded": old_loaded,
                    "last_reload": self.last_reload.isoformat(),
                    "error_catalog_length": len(self.learned_patterns.get("error_catalog", "")),
                    "lessons_log_length": len(self.learned_patterns.get("lessons_log", ""))
                }
            except Exception as e:
                logger.error(f"[AI-CodeChecker] Fehler beim manuellen Reload: {e}")
                return {
                    "success": False,
                    "error": str(e),
                    "last_reload": self.last_reload.isoformat()
                }
    
    def add_lesson_to_log(
        self, 
        title: str, 
        category: str, 
        severity: str,
        symptom: str,
        cause: str,
        fix: str,
        lessons: List[str],
        files: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Trägt einen neuen Fehler automatisch in LESSONS_LOG.md ein.
        
        Args:
            title: Kurzbeschreibung des Fehlers
            category: Backend/Frontend/DB/Infrastruktur
            severity: 🔴 KRITISCH / 🟡 MEDIUM / 🟢 LOW / 🟣 ENHANCEMENT
            symptom: Was wurde beobachtet?
            cause: Root Cause
            fix: Wie wurde es behoben?
            lessons: Liste von Lektionen ("Was die KI künftig tun soll")
            files: Optional - Liste betroffener Dateien
            
        Returns:
            Dict mit Success-Status
        """
        try:
            project_root = Path(__file__).parent.parent.parent
            lessons_log_path = project_root / "Regeln" / "LESSONS_LOG.md"
            
            # Erstelle neuen Eintrag
            date = datetime.now().strftime("%Y-%m-%d")
            files_str = f"\n**Dateien:** {', '.join([f'`{f}`' for f in files])}" if files else ""
            
            new_entry = f"""
## {date} – {title}

**Kategorie:** {category}  
**Schweregrad:** {severity}{files_str}

### Symptom

{symptom}

### Ursache

{cause}

### Fix

{fix}

### Was die KI künftig tun soll

{chr(10).join([f"{i+1}. {lesson}" for i, lesson in enumerate(lessons)])}

---

"""
            
            # Lese existierende Datei
            if not lessons_log_path.exists():
                logger.error(f"[AI-CodeChecker] LESSONS_LOG.md nicht gefunden: {lessons_log_path}")
                return {
                    "success": False,
                    "error": "LESSONS_LOG.md nicht gefunden"
                }
            
            with open(lessons_log_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Finde Einfügepunkt (vor "## Template für neue Einträge")
            insert_marker = "## Template für neue Einträge"
            if insert_marker in content:
                parts = content.split(insert_marker)
                new_content = parts[0] + new_entry + insert_marker + parts[1]
            else:
                # Fallback: Am Ende einfügen (vor Statistiken)
                stats_marker = "## Statistiken"
                if stats_marker in content:
                    parts = content.split(stats_marker)
                    new_content = parts[0] + new_entry + stats_marker + parts[1]
                else:
                    # Fallback 2: Ganz am Ende
                    new_content = content + "\n" + new_entry
            
            # Schreibe zurück
            with open(lessons_log_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            logger.info(f"[AI-CodeChecker] Neuer Eintrag in LESSONS_LOG.md: {title}")
            
            # Reload Patterns (damit neue Lektion sofort verfügbar ist)
            self.learned_patterns = self._load_learned_patterns()
            self.last_reload = datetime.now()
            
            return {
                "success": True,
                "title": title,
                "date": date,
                "lessons_count": len(lessons),
                "reloaded": True
            }
            
        except Exception as e:
            logger.error(f"[AI-CodeChecker] Fehler beim Eintragen in LESSONS_LOG: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _create_analysis_prompt(self, code: str, file_path: Path) -> str:
        """Erstellt Prompt für KI-Analyse mit Fehlerhistorie."""
        file_name = file_path.name
        
        # Füge Fehlerhistorie hinzu, wenn verfügbar
        learned_context = ""
        if self.learned_patterns.get("loaded"):
            learned_context = f"""

**🔍 BEKANNTE FEHLERMUSTER (aus Fehlerhistorie):**

{self.learned_patterns.get('lessons_log', '')}

**⚠️ ACHTE BESONDERS AUF:**
- Schema-Drift (DB-Spalten prüfen, Migration-Scripts)
- Syntax-Fehler (String-Quotes, Klammern)
- Defensive Programmierung (Null-Checks, Type-Checks, Array-Checks)
- Memory Leaks (Event Listener entfernen)
- API-Kontrakt-Brüche (Backend ↔ Frontend)
- OSRM-Timeout-Handling (Fallback auf Haversine)
- Browser-Kompatibilität (Feature Detection)

"""
        
        return f"""Analysiere folgenden Python-Code auf:

1. **Fehler und Bugs:**
   - Syntax-Fehler
   - Logik-Fehler
   - Potenzielle Runtime-Fehler

2. **Code-Qualität:**
   - Lesbarkeit
   - Wartbarkeit
   - Performance-Probleme

3. **Best Practices:**
   - Pythonic Code
   - Fehlerbehandlung
   - Dokumentation
   - Sicherheit

4. **Verbesserungsvorschläge:**
   - Konkrete Verbesserungen
   - Refactoring-Möglichkeiten

{learned_context}

**Datei:** {file_name}

**Code:**
```python
{code}
```

**Antworte im JSON-Format:**
{{
    "issues": [
        {{
            "type": "error|warning|suggestion",
            "severity": "error|warning|suggestion",
            "message": "Beschreibung des Problems",
            "line": Zeilennummer (optional),
            "suggestion": "Konkreter Verbesserungsvorschlag",
            "pattern_match": "Falls das Problem einem bekannten Fehlermuster entspricht"
        }}
    ],
    "score": 0-100,  // Code-Qualitäts-Score
    "summary": "Zusammenfassung der Analyse",
    "suggestions": [
        "Konkrete Verbesserungsvorschläge"
    ],
    "known_patterns_found": [
        "Liste der gefundenen bekannten Fehlermuster"
    ]
}}
"""
    
    def generate_improved_code(self, file_path: Path, issues: List[Dict]) -> Dict[str, Any]:
        """
        Generiert verbesserten Code basierend auf gefundenen Problemen.
        
        Args:
            file_path: Pfad zur Datei
            issues: Liste von gefundenen Problemen
            
        Returns:
            Dict mit verbessertem Code und Diff
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                original_code = f.read()
        except Exception as e:
            return {
                "error": f"Fehler beim Lesen der Datei: {e}",
                "improved_code": None,
                "diff": None
            }
        
        # Prüfe ob Verbesserung erlaubt ist
        can_improve, message = self.cost_tracker.can_improve_code()
        if not can_improve:
            return {
                "error": f"Limit erreicht: {message}",
                "improved_code": None,
                "diff": None
            }
        
        # Erstelle Prompt für Code-Verbesserung
        issues_summary = "\n".join([
            f"- {issue.get('type', 'unknown')}: {issue.get('message', '')} (Zeile {issue.get('line', '?')})"
            for issue in issues[:10]  # Max. 10 Issues
        ])
        
        prompt = f"""Verbessere folgenden Python-Code basierend auf den gefundenen Problemen:

**Gefundene Probleme:**
{issues_summary}

**Original-Code:**
```python
{original_code}
```

**Anforderungen:**
1. Behebe alle gefundenen Probleme
2. Verbessere Code-Qualität
3. Behalte Funktionalität bei
4. Füge Fehlerbehandlung hinzu wo nötig
5. Verbessere Dokumentation

**Antworte im JSON-Format:**
{{
    "improved_code": "Der vollständige verbesserte Code",
    "changes": [
        {{
            "line": Zeilennummer,
            "old": "Alter Code",
            "new": "Neuer Code",
            "reason": "Grund für Änderung"
        }}
    ],
    "summary": "Zusammenfassung der Verbesserungen"
}}
"""
        
        try:
            with self.performance_tracker.track_operation("api_call", str(file_path)):
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "Du bist ein Experte für Python-Code-Verbesserung. "
                                     "Verbessere Code basierend auf gefundenen Problemen. "
                                     "Antworte immer im JSON-Format."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.2,  # Sehr niedrige Temperatur für konsistente Verbesserungen
                    response_format={"type": "json_object"}
                )
            
            # Tracke Kosten
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = self.cost_tracker.track_api_call(
                model=self.model,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                file_path=str(file_path),
                operation="code_improvement"
            )
            
            result = json.loads(response.choices[0].message.content)
            
            # Generiere Diff
            diff = self._generate_diff(original_code, result.get("improved_code", ""))
            
            return {
                "improved_code": result.get("improved_code", ""),
                "changes": result.get("changes", []),
                "summary": result.get("summary", ""),
                "diff": diff,
                "cost_eur": cost,
                "tokens_used": input_tokens + output_tokens
            }
            
        except Exception as e:
            return {
                "error": f"Fehler bei Code-Verbesserung: {e}",
                "improved_code": None,
                "diff": None
            }
    
    def _generate_diff(self, old_code: str, new_code: str) -> str:
        """Generiert Diff zwischen altem und neuem Code."""
        import difflib
        
        old_lines = old_code.splitlines(keepends=True)
        new_lines = new_code.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile='original',
            tofile='improved',
            lineterm=''
        )
        
        return ''.join(diff)
    
    def _issue_to_dict(self, issue: CodeIssue) -> Dict[str, Any]:
        """Konvertiert CodeIssue zu Dict."""
        return {
            "type": issue.type,
            "severity": issue.severity.value,
            "message": issue.message,
            "line": issue.line,
            "column": issue.column,
            "code_snippet": issue.code_snippet,
            "suggestion": issue.suggestion
        }

# Singleton-Instanz
_ai_code_checker = None

def get_ai_code_checker(api_key: Optional[str] = None) -> Optional[AICodeChecker]:
    """
    Gibt Singleton-Instanz zurück.
    
    Args:
        api_key: Optional API-Key
        
    Returns:
        AICodeChecker-Instanz oder None wenn API-Key fehlt
    """
    global _ai_code_checker
    try:
        if _ai_code_checker is None:
            _ai_code_checker = AICodeChecker(api_key=api_key)
        return _ai_code_checker
    except ValueError:
        return None

