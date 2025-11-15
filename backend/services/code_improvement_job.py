"""
Background-Job für kontinuierliche Code-Verbesserungen.
Arbeitet kontinuierlich am Code weiter, mit Rate-Limiting und Priorisierung.
"""
import asyncio
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from backend.services.ai_code_checker import get_ai_code_checker
from backend.services.safety_manager import SafetyManager
from backend.services.cost_tracker import get_cost_tracker
from backend.services.performance_tracker import get_performance_tracker
from backend.services.notification_service import get_notification_service
from backend.services.code_analyzer import analyze_code_file
from backend.config import cfg

class CodeImprovementJob:
    """Background-Job für kontinuierliche Code-Verbesserungen."""
    
    def __init__(self):
        self.ai_checker = get_ai_code_checker()
        self.safety_manager = SafetyManager()
        self.cost_tracker = get_cost_tracker()
        self.performance_tracker = get_performance_tracker()
        self.notification_service = get_notification_service()
        
        # Konfiguration
        self.enabled = cfg("ki_codechecker:background_job:enabled", True)
        self.interval_seconds = int(cfg("ki_codechecker:background_job:interval_seconds", 3600))  # Standard: 1 Stunde
        self.max_improvements_per_run = int(cfg("ki_codechecker:background_job:max_improvements_per_run", 3))
        self.priority_files = cfg("ki_codechecker:background_job:priority_files", [])
        self.exclude_patterns = cfg("ki_codechecker:background_job:exclude_patterns", [
            "**/__pycache__/**",
            "**/node_modules/**",
            "**/.git/**",
            "**/venv/**",
            "**/env/**",
            "**/tests/**",
            "**/backups/**",
        ])
        
        # State
        self.is_running = False
        self.last_run = None
        self.total_improvements = 0
        self.total_failures = 0
    
    async def run_once(self) -> Dict[str, any]:
        """
        Führt eine Verbesserungs-Runde aus.
        
        Returns:
            Dict mit Ergebnis-Statistiken
        """
        if not self.enabled:
            return {
                "success": False,
                "reason": "Background-Job ist deaktiviert",
                "improvements": 0
            }
        
        if not self.ai_checker:
            return {
                "success": False,
                "reason": "KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)",
                "improvements": 0
            }
        
        # Prüfe ob Verbesserung erlaubt ist
        can_improve, message = self.cost_tracker.can_improve_code()
        if not can_improve:
            return {
                "success": False,
                "reason": f"Limit erreicht: {message}",
                "improvements": 0
            }
        
        # Finde Dateien zum Verbessern
        files_to_improve = self._find_files_to_improve()
        
        if not files_to_improve:
            return {
                "success": True,
                "reason": "Keine Dateien zum Verbessern gefunden",
                "improvements": 0
            }
        
        # Verbessere Dateien (max. max_improvements_per_run)
        improvements = 0
        failures = 0
        improved_files = []
        failed_files = []
        
        for file_path in files_to_improve[:self.max_improvements_per_run]:
            try:
                # Sende Activity-Update: Datei wird analysiert
                await self._broadcast_activity(f"Analysiere: {file_path.name}", "info")
                
                result = await self._improve_file(file_path)
                if result["success"]:
                    improvements += 1
                    improved_files.append(str(file_path))
                    await self._broadcast_activity(f"✅ Verbessert: {file_path.name}", "success")
                else:
                    failures += 1
                    error_msg = result.get("error", "Unbekannter Fehler")
                    failed_files.append({
                        "file": str(file_path),
                        "error": error_msg
                    })
                    await self._broadcast_activity(f"⚠️ Fehler bei {file_path.name}: {error_msg}", "warning")
            except Exception as e:
                failures += 1
                failed_files.append({
                    "file": str(file_path),
                    "error": str(e)
                })
                await self._broadcast_activity(f"❌ Fehler bei {file_path.name}: {str(e)}", "error")
        
        # Update State
        self.last_run = datetime.now()
        self.total_improvements += improvements
        self.total_failures += failures
        
        return {
            "success": True,
            "improvements": improvements,
            "failures": failures,
            "improved_files": improved_files,
            "failed_files": failed_files,
            "timestamp": self.last_run.isoformat()
        }
    
    async def _improve_file(self, file_path: Path) -> Dict[str, any]:
        """
        Verbessert eine einzelne Datei.
        
        Args:
            file_path: Pfad zur Datei
            
        Returns:
            Dict mit Ergebnis
        """
        try:
            # 1. Analysiere Code
            analysis_result = self.ai_checker.analyze_and_improve(file_path)
            ai_analysis = analysis_result.get("ai_analysis", {})
            
            if "error" in ai_analysis:
                return {
                    "success": False,
                    "error": ai_analysis["error"]
                }
            
            issues = ai_analysis.get("issues", [])
            if not issues:
                return {
                    "success": True,
                    "message": "Keine Probleme gefunden",
                    "issues_fixed": 0
                }
            
            # 2. Generiere verbesserten Code
            improvement_result = self.ai_checker.generate_improved_code(file_path, issues)
            
            if "error" in improvement_result:
                return {
                    "success": False,
                    "error": improvement_result["error"]
                }
            
            improved_code = improvement_result.get("improved_code")
            if not improved_code:
                return {
                    "success": False,
                    "error": "Kein verbesserter Code generiert"
                }
            
            # 3. Wende Verbesserung sicher an
            apply_result = self.safety_manager.apply_with_safety_check(
                file_path,
                improved_code,
                issues_fixed=len(issues)
            )
            
            return apply_result
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    def _find_files_to_improve(self) -> List[Path]:
        """
        Findet Dateien die verbessert werden sollten.
        
        Returns:
            Liste von Datei-Pfaden (priorisiert)
        """
        files = []
        
        # 1. Priority-Dateien zuerst
        for priority_file in self.priority_files:
            path = Path(priority_file)
            if path.exists() and path.suffix == '.py':
                files.append(path)
        
        # 2. Suche Python-Dateien im Projekt
        project_root = Path(".")
        python_files = list(project_root.rglob("*.py"))
        
        # Filtere ausgeschlossene Patterns
        for pattern in self.exclude_patterns:
            # Einfache Pattern-Erkennung
            if "**/" in pattern:
                base_pattern = pattern.replace("**/", "")
                python_files = [f for f in python_files if base_pattern not in str(f)]
            elif pattern.endswith("/**"):
                base_pattern = pattern.replace("/**", "")
                python_files = [f for f in python_files if base_pattern not in str(f)]
            else:
                python_files = [f for f in python_files if pattern not in str(f)]
        
        # Entferne bereits behandelte Priority-Dateien
        python_files = [f for f in python_files if f not in files]
        
        # Priorisiere: Dateien mit mehr Issues zuerst
        files_with_issues = []
        for file_path in python_files[:50]:  # Max. 50 Dateien analysieren
            try:
                issues = analyze_code_file(file_path)
                if issues:
                    files_with_issues.append((file_path, len(issues)))
            except Exception:
                continue
        
        # Sortiere nach Anzahl Issues (absteigend)
        files_with_issues.sort(key=lambda x: x[1], reverse=True)
        
        # Füge priorisierte Dateien hinzu
        files.extend([f[0] for f in files_with_issues])
        
        return files
    
    async def run_continuously(self):
        """
        Führt kontinuierliche Verbesserungen aus (läuft in Endlosschleife).
        """
        if not self.enabled:
            print("[CODE-IMPROVEMENT-JOB] Background-Job ist deaktiviert")
            return
        
        if not self.ai_checker:
            print("[CODE-IMPROVEMENT-JOB] KI-Checker nicht verfügbar (OPENAI_API_KEY fehlt)")
            return
        
        self.is_running = True
        print(f"[CODE-IMPROVEMENT-JOB] Background-Job gestartet (Intervall: {self.interval_seconds}s)")
        
        while self.is_running:
            try:
                await self._broadcast_activity("🔄 Starte Verbesserungs-Runde...", "info")
                print(f"[CODE-IMPROVEMENT-JOB] Starte Verbesserungs-Runde...")
                result = await self.run_once()
                
                if result["success"]:
                    msg = f"Runde abgeschlossen: {result['improvements']} Verbesserungen, {result['failures']} Fehler"
                    print(f"[CODE-IMPROVEMENT-JOB] {msg}")
                    await self._broadcast_activity(f"✅ {msg}", "success")
                    
                    if result["improvements"] > 0:
                        files_msg = f"Verbesserte Dateien: {', '.join(result['improved_files'])}"
                        print(f"[CODE-IMPROVEMENT-JOB] {files_msg}")
                        await self._broadcast_activity(files_msg, "success")
                else:
                    reason = result.get('reason', 'Unbekannt')
                    print(f"[CODE-IMPROVEMENT-JOB] Runde fehlgeschlagen: {reason}")
                    await self._broadcast_activity(f"⚠️ Runde fehlgeschlagen: {reason}", "warning")
                
                # Warte bis zur nächsten Runde
                await self._broadcast_activity(f"⏸️ Warte {self.interval_seconds}s bis zur nächsten Runde...", "info")
                await asyncio.sleep(self.interval_seconds)
                
            except Exception as e:
                print(f"[CODE-IMPROVEMENT-JOB] Fehler in Verbesserungs-Runde: {e}")
                await asyncio.sleep(60)  # Kurze Pause bei Fehler
    
    def stop(self):
        """Stoppt den Background-Job."""
        self.is_running = False
        print("[CODE-IMPROVEMENT-JOB] Background-Job gestoppt")
    
    async def _broadcast_activity(self, message: str, level: str = "info"):
        """Sendet Activity-Update über WebSocket."""
        try:
            from backend.routes.ki_improvements_api import broadcast_activity_to_websockets
            await broadcast_activity_to_websockets(message, level)
        except Exception as e:
            # Fehler beim Broadcasting ist nicht kritisch
            pass
    
    def get_status(self) -> Dict[str, any]:
        """Gibt Status des Background-Jobs zurück."""
        return {
            "enabled": self.enabled,
            "is_running": self.is_running,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "total_improvements": self.total_improvements,
            "total_failures": self.total_failures,
            "interval_seconds": self.interval_seconds,
            "max_improvements_per_run": self.max_improvements_per_run,
            "ai_checker_available": self.ai_checker is not None
        }


# Singleton-Instanz
_background_job = None

def get_background_job() -> CodeImprovementJob:
    """Gibt Singleton-Instanz zurück."""
    global _background_job
    if _background_job is None:
        _background_job = CodeImprovementJob()
    return _background_job

