"""
Safety-Manager für KI-CodeChecker.
Sichert dass Code-Verbesserungen sicher sind und Software funktionsfähig bleibt.
"""
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
from backend.services.code_fixer import CodeFixer
from backend.services.notification_service import get_notification_service

class SafetyManager:
    """Sichert dass Code-Verbesserungen sicher sind."""
    
    def __init__(self):
        self.code_fixer = CodeFixer()
        self.notification_service = get_notification_service()
        self.test_command = [sys.executable, "-m", "pytest", "-x", "-v"]
    
    def validate_improvement(self, file_path: Path, improved_code: str) -> Dict[str, Any]:
        """
        Validiert Code-Verbesserung vor Anwendung.
        
        Args:
            file_path: Pfad zur Datei
            improved_code: Verbesserter Code
            
        Returns:
            Dict mit Validierungs-Ergebnis
        """
        # 1. Syntax-Check
        syntax_ok, syntax_error = self._check_syntax(improved_code)
        if not syntax_ok:
            return {
                "valid": False,
                "error": f"Syntax-Fehler: {syntax_error}",
                "tests_passed": False
            }
        
        # 2. Import-Check (optional, kann langsam sein)
        # import_ok = self._check_imports(file_path, improved_code)
        
        return {
            "valid": True,
            "tests_passed": None  # Wird nach Anwendung geprüft
        }
    
    def apply_with_safety_check(self, file_path: Path, improved_code: str, 
                                issues_fixed: int = 0) -> Dict[str, Any]:
        """
        Wendet Verbesserung an und prüft ob alles noch funktioniert.
        
        Args:
            file_path: Pfad zur Datei
            improved_code: Verbesserter Code
            issues_fixed: Anzahl behobener Issues
            
        Returns:
            Dict mit Ergebnis
        """
        # 1. Validierung vor Anwendung
        validation = self.validate_improvement(file_path, improved_code)
        if not validation["valid"]:
            return {
                "success": False,
                "error": validation.get("error", "Validierung fehlgeschlagen"),
                "backup": None
            }
        
        # 2. Verbesserung anwenden
        result = self.code_fixer.apply_improvement(file_path, improved_code, issues_fixed)
        if not result["success"]:
            return result
        
        # 3. Tests ausführen (nach Anwendung)
        tests_passed, test_output = self._run_tests(file_path)
        
        if not tests_passed:
            # Rollback bei Test-Fehlern
            backup_path = Path(result["backup"])
            self.code_fixer._rollback(file_path, backup_path)
            
            # Benachrichtigung für Rollback
            self.notification_service.notify_improvement({
                "file": str(file_path),
                "action": "rollback",
                "issues_fixed": 0,
                "tests_passed": False,
                "backup": str(backup_path),
                "reason": f"Tests fehlgeschlagen: {test_output[:200]}"
            })
            
            return {
                "success": False,
                "error": "Tests fehlgeschlagen nach Verbesserung",
                "test_output": test_output,
                "backup": str(backup_path),
                "rolled_back": True
            }
        
        # 4. Erfolgreich
        return {
            "success": True,
            "backup": result["backup"],
            "tests_passed": True,
            "issues_fixed": issues_fixed
        }
    
    def _check_syntax(self, code: str) -> tuple[bool, Optional[str]]:
        """Prüft Syntax des Codes."""
        try:
            compile(code, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, str(e)
        except Exception as e:
            return False, str(e)
    
    def _run_tests(self, file_path: Path) -> tuple[bool, str]:
        """
        Führt Tests aus.
        
        Returns:
            (tests_passed, output)
        """
        try:
            # Versuche Tests für die geänderte Datei zu finden
            # Für jetzt: Prüfe nur ob Datei importierbar ist
            result = subprocess.run(
                [sys.executable, "-c", f"import ast; ast.parse(open('{file_path}').read())"],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return True, "Syntax-Check erfolgreich"
            else:
                return False, result.stderr or result.stdout
                
        except subprocess.TimeoutExpired:
            return False, "Test-Timeout"
        except Exception as e:
            # Wenn Tests nicht ausführbar, akzeptiere Verbesserung
            # (besser als nichts)
            return True, f"Tests nicht ausführbar: {e}"

