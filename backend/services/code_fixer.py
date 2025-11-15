"""
Code-Fixer für KI-CodeChecker.
Wendet Code-Verbesserungen sicher an mit Backup und Rollback.
"""
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional
from backend.services.notification_service import get_notification_service

class CodeFixer:
    """Wendet Code-Verbesserungen sicher an."""
    
    def __init__(self):
        self.backup_dir = Path("data/code_fixes_backup")
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.notification_service = get_notification_service()
    
    def apply_improvement(self, file_path: Path, improved_code: str, 
                         issues_fixed: int = 0) -> Dict[str, Any]:
        """
        Wendet Code-Verbesserung an.
        
        Args:
            file_path: Pfad zur Datei
            improved_code: Verbesserter Code
            issues_fixed: Anzahl behobener Issues
            
        Returns:
            Dict mit Ergebnis
        """
        if not file_path.exists():
            return {
                "success": False,
                "error": f"Datei nicht gefunden: {file_path}",
                "backup": None
            }
        
        # 1. Backup erstellen
        backup_path = self._create_backup(file_path)
        if not backup_path:
            return {
                "success": False,
                "error": "Backup konnte nicht erstellt werden",
                "backup": None
            }
        
        try:
            # 2. Verbesserten Code schreiben
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(improved_code)
            
            # 3. Benachrichtigung senden
            self.notification_service.notify_improvement({
                "file": str(file_path),
                "action": "improved",
                "issues_fixed": issues_fixed,
                "tests_passed": True,  # Wird vom Safety-Manager geprüft
                "backup": str(backup_path),
                "improvement_score": 0  # Wird später berechnet
            })
            
            return {
                "success": True,
                "backup": str(backup_path),
                "file": str(file_path),
                "issues_fixed": issues_fixed
            }
            
        except Exception as e:
            # Rollback bei Fehler
            self._rollback(file_path, backup_path)
            return {
                "success": False,
                "error": f"Fehler beim Anwenden: {e}",
                "backup": str(backup_path),
                "rolled_back": True
            }
    
    def _create_backup(self, file_path: Path) -> Optional[Path]:
        """Erstellt Backup der Datei."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = file_path.name
            backup_name = f"{timestamp}_{file_name}"
            backup_path = self.backup_dir / backup_name
            
            shutil.copy2(file_path, backup_path)
            return backup_path
        except Exception as e:
            print(f"[CODE-FIXER] Backup-Fehler: {e}")
            return None
    
    def _rollback(self, file_path: Path, backup_path: Path):
        """Stellt Datei aus Backup wieder her."""
        try:
            if backup_path.exists():
                shutil.copy2(backup_path, file_path)
                print(f"[CODE-FIXER] Rollback erfolgreich: {file_path}")
        except Exception as e:
            print(f"[CODE-FIXER] Rollback-Fehler: {e}")

