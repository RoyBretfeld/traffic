"""
Code-Analyzer für KI-CodeChecker.
Analysiert Python-Dateien auf Fehler, Probleme und Verbesserungspotenziale.
"""
import ast
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum

class IssueSeverity(Enum):
    """Schweregrad von Problemen."""
    ERROR = "error"      # Kritischer Fehler
    WARNING = "warning"  # Warnung
    SUGGESTION = "suggestion"  # Verbesserungsvorschlag

@dataclass
class CodeIssue:
    """Ein gefundenes Problem im Code."""
    severity: IssueSeverity
    type: str  # z.B. "syntax_error", "missing_error_handling", "hardcoded_path"
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    file_path: Optional[str] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None

class CodeAnalyzer:
    """Analysiert Code-Dateien auf Probleme."""
    
    def __init__(self):
        self.issues: List[CodeIssue] = []
    
    def analyze_file(self, file_path: Path) -> List[CodeIssue]:
        """
        Analysiert eine Python-Datei.
        
        Args:
            file_path: Pfad zur Python-Datei
            
        Returns:
            Liste von gefundenen Problemen
        """
        self.issues = []
        
        if not file_path.exists():
            self.issues.append(CodeIssue(
                severity=IssueSeverity.ERROR,
                type="file_not_found",
                message=f"Datei nicht gefunden: {file_path}",
                file_path=str(file_path)
            ))
            return self.issues
        
        if file_path.suffix != '.py':
            # Nur Python-Dateien analysieren
            return self.issues
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            self.issues.append(CodeIssue(
                severity=IssueSeverity.ERROR,
                type="read_error",
                message=f"Fehler beim Lesen der Datei: {e}",
                file_path=str(file_path)
            ))
            return self.issues
        
        # Syntax-Check
        self._check_syntax(file_path, content)
        
        # Struktur-Analyse
        self._check_structure(file_path, content, lines)
        
        # Code-Qualität
        self._check_code_quality(file_path, content, lines)
        
        # Best Practices
        self._check_best_practices(file_path, content, lines)
        
        return self.issues
    
    def _check_syntax(self, file_path: Path, content: str):
        """Prüft Syntax-Fehler."""
        try:
            ast.parse(content)
        except SyntaxError as e:
            self.issues.append(CodeIssue(
                severity=IssueSeverity.ERROR,
                type="syntax_error",
                message=f"Syntax-Fehler: {e.msg}",
                line=e.lineno,
                column=e.offset,
                file_path=str(file_path),
                code_snippet=e.text
            ))
        except Exception as e:
            self.issues.append(CodeIssue(
                severity=IssueSeverity.ERROR,
                type="parse_error",
                message=f"Fehler beim Parsen: {e}",
                file_path=str(file_path)
            ))
    
    def _check_structure(self, file_path: Path, content: str, lines: List[str]):
        """Prüft Code-Struktur."""
        try:
            tree = ast.parse(content)
            
            # Prüfe auf fehlende Docstrings
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.Module)):
                    if not ast.get_docstring(node):
                        if isinstance(node, ast.FunctionDef):
                            # Überspringe private Methoden (__xxx__)
                            if not node.name.startswith('__') or node.name.endswith('__'):
                                self.issues.append(CodeIssue(
                                    severity=IssueSeverity.SUGGESTION,
                                    type="missing_docstring",
                                    message=f"Funktion '{node.name}' hat keinen Docstring",
                                    line=node.lineno,
                                    file_path=str(file_path)
                                ))
        except Exception:
            pass  # Syntax-Fehler wurden bereits erkannt
    
    def _check_code_quality(self, file_path: Path, content: str, lines: List[str]):
        """Prüft Code-Qualität."""
        # Prüfe auf zu lange Zeilen
        for i, line in enumerate(lines, 1):
            if len(line) > 120:
                self.issues.append(CodeIssue(
                    severity=IssueSeverity.SUGGESTION,
                    type="line_too_long",
                    message=f"Zeile {i} ist zu lang ({len(line)} Zeichen, max. 120)",
                    line=i,
                    file_path=str(file_path),
                    code_snippet=line[:100] + "..."
                ))
        
        # Prüfe auf fehlendes Error-Handling
        self._check_error_handling(file_path, content, lines)
        
        # Prüfe auf Hardcoded-Pfade
        self._check_hardcoded_paths(file_path, content, lines)
    
    def _check_error_handling(self, file_path: Path, content: str, lines: List[str]):
        """Prüft auf fehlendes Error-Handling."""
        # Suche nach gefährlichen Operationen ohne try-except
        dangerous_patterns = [
            (r'open\([^)]+\)', "Datei-Operation ohne Error-Handling"),
            (r'\.read\(\)', "Datei-Lesen ohne Error-Handling"),
            (r'\.write\([^)]+\)', "Datei-Schreiben ohne Error-Handling"),
            (r'requests\.(get|post|put|delete)', "HTTP-Request ohne Error-Handling"),
            (r'fetch\([^)]+\)', "Fetch-Request ohne Error-Handling"),
        ]
        
        for pattern, message in dangerous_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                # Prüfe ob try-except in der Nähe ist
                context_start = max(0, line_num - 10)
                context_end = min(len(lines), line_num + 10)
                context = '\n'.join(lines[context_start:context_end])
                
                if 'try:' not in context or 'except' not in context:
                    self.issues.append(CodeIssue(
                        severity=IssueSeverity.WARNING,
                        type="missing_error_handling",
                        message=message,
                        line=line_num,
                        file_path=str(file_path),
                        code_snippet=line_content.strip(),
                        suggestion="Verwende try-except für Fehlerbehandlung"
                    ))
    
    def _check_hardcoded_paths(self, file_path: Path, content: str, lines: List[str]):
        """Prüft auf Hardcoded-Pfade."""
        # Suche nach hardcoded Pfaden
        path_patterns = [
            (r'["\'](/[^"\']+|C:\\[^"\']+|[A-Z]:\\[^"\']+)["\']', "Hardcoded-Pfad gefunden"),
            (r'path\s*=\s*["\'](/[^"\']+|C:\\[^"\']+)["\']', "Hardcoded-Pfad in Variable"),
        ]
        
        for pattern, message in path_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                # Überspringe Test-Dateien und Config-Dateien
                if 'test' in str(file_path).lower() or 'config' in str(file_path).lower():
                    continue
                
                self.issues.append(CodeIssue(
                    severity=IssueSeverity.WARNING,
                    type="hardcoded_path",
                    message=message,
                    line=line_num,
                    file_path=str(file_path),
                    code_snippet=line_content.strip(),
                    suggestion="Verwende konfigurierbare Pfade oder Path-Objekte"
                ))
    
    def _check_best_practices(self, file_path: Path, content: str, lines: List[str]):
        """Prüft Best Practices."""
        # Prüfe auf print() statt logging
        for i, line in enumerate(lines, 1):
            if re.search(r'\bprint\s*\(', line) and 'logging' not in content.lower():
                self.issues.append(CodeIssue(
                    severity=IssueSeverity.SUGGESTION,
                    type="use_logging",
                    message=f"Zeile {i} verwendet print() statt logging",
                    line=i,
                    file_path=str(file_path),
                    code_snippet=line.strip(),
                    suggestion="Verwende logging.getLogger() statt print()"
                ))
        
        # Prüfe auf Magic Numbers
        magic_number_pattern = r'\b\d{3,}\b'  # Zahlen mit 3+ Ziffern
        for i, line in enumerate(lines, 1):
            if re.search(magic_number_pattern, line) and '#' not in line:
                # Überspringe offensichtliche Zahlen (Jahre, Versionsnummern, etc.)
                if not re.search(r'(20\d{2}|version|v\d+)', line, re.IGNORECASE):
                    self.issues.append(CodeIssue(
                        severity=IssueSeverity.SUGGESTION,
                        type="magic_number",
                        message=f"Zeile {i} enthält möglicherweise eine Magic Number",
                        line=i,
                        file_path=str(file_path),
                        code_snippet=line.strip(),
                        suggestion="Definiere eine Konstante für diesen Wert"
                    ))

def analyze_code_file(file_path: Path) -> List[CodeIssue]:
    """
    Analysiert eine Code-Datei.
    
    Args:
        file_path: Pfad zur Datei
        
    Returns:
        Liste von gefundenen Problemen
    """
    analyzer = CodeAnalyzer()
    return analyzer.analyze_file(file_path)

