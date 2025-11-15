"""
Automatischer Fehler-Logger - Speichert ALLE nachgewiesenen Fehler automatisch in LESSONS_LOG.md.

PFLICHT: Jeder nachgewiesene Fehler muss gespeichert werden!
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
# Import wird dynamisch gemacht, um Zirkel-Import zu vermeiden

logger = logging.getLogger(__name__)


class ErrorAutoLogger:
    """
    Automatischer Logger für alle Fehler (Syntax, Runtime, API, etc.).
    Speichert jeden Fehler automatisch in LESSONS_LOG.md.
    """
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.lessons_log_path = self.project_root / "Regeln" / "LESSONS_LOG.md"
    
    def log_error(
        self,
        error_type: str,
        error_message: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        stack_trace: Optional[str] = None,
        user_agent: Optional[str] = None,
        url: Optional[str] = None,
        severity: str = "🔴 KRITISCH"
    ) -> Dict[str, Any]:
        """
        Speichert einen Fehler automatisch in LESSONS_LOG.md.
        
        Args:
            error_type: Art des Fehlers (SyntaxError, ReferenceError, TypeError, etc.)
            error_message: Fehlermeldung
            file_path: Datei in der der Fehler auftrat
            line_number: Zeilennummer
            stack_trace: Stack-Trace (optional)
            user_agent: Browser-Info (optional)
            url: URL wo Fehler auftrat (optional)
            severity: Schweregrad (🔴 KRITISCH / 🟡 MEDIUM / 🟢 LOW)
            
        Returns:
            Dict mit Success-Status
        """
        try:
            # Kategorisiere Fehler automatisch
            category = self._categorize_error(error_type, file_path)
            
            # Erstelle Titel
            title = f"{error_type} – {self._extract_short_message(error_message)}"
            
            # Erstelle Symptom
            symptom = f"- Browser-Konsole zeigt: `{error_type}: {error_message}`"
            if file_path:
                symptom += f"\n- Datei: `{file_path}`"
            if line_number:
                symptom += f"\n- Zeile: {line_number}"
            if url:
                symptom += f"\n- URL: {url}"
            if user_agent:
                symptom += f"\n- Browser: {user_agent}"
            
            # Erstelle Ursache (automatisch basierend auf Fehlertyp)
            cause = self._generate_cause(error_type, error_message, file_path, line_number)
            
            # Erstelle Fix (automatisch basierend auf Fehlertyp)
            fix = self._generate_fix(error_type, error_message, file_path, line_number)
            
            # Erstelle Lessons (automatisch basierend auf Fehlertyp)
            lessons = self._generate_lessons(error_type, error_message)
            
            # Dateien-Liste
            files = [file_path] if file_path else []
            
            # Nutze AI Codechecker zum Eintragen (dynamischer Import)
            try:
                from backend.services.ai_code_checker import get_ai_code_checker
                ai_checker = get_ai_code_checker()
            except Exception as e:
                logger.error(f"[ErrorAutoLogger] AI Codechecker nicht verfügbar: {e}")
                ai_checker = None
            
            if ai_checker:
                result = ai_checker.add_lesson_to_log(
                    title=title,
                    category=category,
                    severity=severity,
                    symptom=symptom,
                    cause=cause,
                    fix=fix,
                    lessons=lessons,
                    files=files
                )
                
                if result.get("success"):
                    logger.info(f"[ErrorAutoLogger] Fehler automatisch gespeichert: {title}")
                    return {
                        "success": True,
                        "title": title,
                        "message": "Fehler automatisch in LESSONS_LOG.md eingetragen"
                    }
                else:
                    logger.error(f"[ErrorAutoLogger] Fehler beim Speichern: {result.get('error')}")
                    return result
            else:
                logger.error("[ErrorAutoLogger] AI Codechecker nicht verfügbar")
                return {
                    "success": False,
                    "error": "AI Codechecker nicht verfügbar"
                }
                
        except Exception as e:
            logger.error(f"[ErrorAutoLogger] Exception beim Loggen: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e)
            }
    
    def _categorize_error(self, error_type: str, file_path: Optional[str]) -> str:
        """Kategorisiert Fehler automatisch."""
        if file_path:
            if file_path.endswith('.html') or file_path.endswith('.js'):
                return "Frontend"
            elif file_path.endswith('.py'):
                return "Backend"
            elif file_path.endswith('.sql') or 'database' in file_path.lower():
                return "Datenbank"
        
        # Fallback basierend auf Fehlertyp
        if error_type in ['SyntaxError', 'ReferenceError', 'TypeError']:
            return "Frontend"
        elif error_type in ['ImportError', 'ModuleNotFoundError']:
            return "Backend"
        else:
            return "Frontend"  # Default
    
    def _extract_short_message(self, message: str) -> str:
        """Extrahiert kurze Fehlermeldung (max. 60 Zeichen)."""
        if len(message) <= 60:
            return message
        return message[:57] + "..."
    
    def _generate_cause(self, error_type: str, message: str, file_path: Optional[str], line_number: Optional[int]) -> str:
        """Generiert automatisch Ursache basierend auf Fehlertyp."""
        causes = {
            "SyntaxError": f"**Syntax-Fehler im Code:**\n- {message}\n- Code kann nicht ausgeführt werden",
            "ReferenceError": f"**Undeclared Variable oder Function:**\n- {message}\n- Variable/Funktion wurde nicht definiert oder ist außerhalb des Scopes",
            "TypeError": f"**Falscher Datentyp:**\n- {message}\n- Variable hat nicht den erwarteten Typ",
            "Uncaught": f"**Unbehandelte Exception:**\n- {message}\n- Fehler wurde nicht mit try-catch abgefangen"
        }
        
        # Spezifische Ursachen für bekannte Fehler
        if "already been declared" in message:
            return f"**Doppelte Variablen-Deklaration:**\n- Variable wurde im gleichen Scope mehrfach deklariert\n- `const`/`let` sind block-scoped, nicht function-scoped"
        elif "is not defined" in message:
            return f"**Undeclared Variable/Function:**\n- {message}\n- Variable/Funktion wurde nicht definiert oder ist außerhalb des Scopes"
        
        return causes.get(error_type, f"**Unbekannter Fehler:**\n- {message}")
    
    def _generate_fix(self, error_type: str, message: str, file_path: Optional[str], line_number: Optional[int]) -> str:
        """Generiert automatisch Fix-Vorschlag basierend auf Fehlertyp."""
        fixes = {
            "SyntaxError": "**Syntax-Fehler beheben:**\n- Prüfe Klammern, Anführungszeichen, Semikolons\n- Browser-Konsole für Details prüfen\n- Linter (ESLint) nutzen",
            "ReferenceError": "**Variable/Function definieren:**\n- Prüfe ob Variable/Funktion existiert\n- Prüfe Scope (block-scoped vs. function-scoped)\n- Import-Statements prüfen",
            "TypeError": "**Datentyp prüfen:**\n- Type-Checks hinzufügen\n- Null-Checks vor Verwendung\n- Defensive Programmierung"
        }
        
        # Spezifische Fixes für bekannte Fehler
        if "already been declared" in message:
            return "**Doppelte Deklaration entfernen:**\n- Entferne eine der Deklarationen\n- Verwende bereits deklarierte Variable\n- Prüfe Block-Scope"
        elif "is not defined" in message:
            return "**Variable/Function definieren:**\n- Deklariere Variable/Funktion\n- Prüfe ob Import fehlt\n- Prüfe Scope"
        
        return fixes.get(error_type, f"**Fehler analysieren und beheben:**\n- Browser-Konsole für Details prüfen\n- Stack-Trace analysieren\n- Code-Review durchführen")
    
    def _generate_lessons(self, error_type: str, message: str) -> list:
        """Generiert automatisch Lessons basierend auf Fehlertyp."""
        lessons = {
            "SyntaxError": [
                "Syntax-Fehler sofort beheben (blockieren Code-Ausführung)",
                "Browser-Konsole nach jeder Änderung prüfen",
                "Linter (ESLint) vor jedem Commit nutzen",
                "Keine 'ich probiere mal' - Änderungen ohne Syntax-Check"
            ],
            "ReferenceError": [
                "Immer prüfen ob Variable/Funktion existiert",
                "Scope-Bewusstsein (block-scoped vs. function-scoped)",
                "Defensive Programmierung (Null-Checks, Type-Checks)",
                "Import-Statements prüfen"
            ],
            "TypeError": [
                "Type-Checks vor Verwendung",
                "Null-Checks hinzufügen",
                "Defensive Programmierung erzwingen",
                "API-Kontrakt zwischen Backend und Frontend prüfen"
            ]
        }
        
        # Spezifische Lessons für bekannte Fehler
        if "already been declared" in message:
            return [
                "Immer auf doppelte Deklarationen prüfen",
                "Scope-Bewusstsein (const/let sind block-scoped)",
                "Code-Review vor Änderungen",
                "Linter nutzen (ESLint für JavaScript)"
            ]
        elif "is not defined" in message:
            return [
                "Immer prüfen ob Variable/Funktion existiert",
                "Scope-Bewusstsein",
                "Import-Statements prüfen",
                "Defensive Programmierung"
            ]
        
        return lessons.get(error_type, [
            "Fehler sofort analysieren und beheben",
            "Browser-Konsole für Details prüfen",
            "Code-Review durchführen",
            "Defensive Programmierung"
        ])


# Singleton-Instanz
_error_auto_logger = None

def get_error_auto_logger() -> ErrorAutoLogger:
    """Gibt Singleton-Instanz zurück."""
    global _error_auto_logger
    if _error_auto_logger is None:
        _error_auto_logger = ErrorAutoLogger()
    return _error_auto_logger

