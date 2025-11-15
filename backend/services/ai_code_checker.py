"""
KI-Engine für Code-Verbesserungen.
Nutzt GPT-4o-mini für intelligente Code-Analyse und Verbesserungsvorschläge.
"""
import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from openai import OpenAI
from backend.services.cost_tracker import get_cost_tracker
from backend.services.performance_tracker import get_performance_tracker
from backend.services.code_analyzer import CodeIssue, analyze_code_file

class AICodeChecker:
    """KI-basierter Code-Checker mit GPT-4o-mini."""
    
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
    
    def _create_analysis_prompt(self, code: str, file_path: Path) -> str:
        """Erstellt Prompt für KI-Analyse."""
        file_name = file_path.name
        
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
            "suggestion": "Konkreter Verbesserungsvorschlag"
        }}
    ],
    "score": 0-100,  // Code-Qualitäts-Score
    "summary": "Zusammenfassung der Analyse",
    "suggestions": [
        "Konkrete Verbesserungsvorschläge"
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

