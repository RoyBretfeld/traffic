"""
Benachrichtigungssystem für KI-Code-Verbesserungen.
Informiert Entwickler über alle Code-Änderungen.
"""
import os
import json
import smtplib
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from backend.config import cfg

class NotificationService:
    """Service für Benachrichtigungen über KI-Code-Verbesserungen."""
    
    def __init__(self):
        self.log_dir = Path("data/code_fixes_log")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # E-Mail-Konfiguration
        # Standard-E-Mail-Adresse: code@rh-automation-dresden.de
        self.smtp_server = cfg("notifications:email:smtp_server", "smtp.gmail.com")
        self.smtp_port = int(cfg("notifications:email:smtp_port", "587"))
        self.email_from = cfg("notifications:email:from", os.getenv("NOTIFICATION_EMAIL_FROM", "code@rh-automation-dresden.de"))
        self.email_to = cfg("notifications:email:to", os.getenv("NOTIFICATION_EMAIL_TO", "code@rh-automation-dresden.de"))
        self.email_password = cfg("notifications:email:password", os.getenv("NOTIFICATION_EMAIL_PASSWORD", ""))
        self.email_enabled = cfg("notifications:email:enabled", True)  # Standardmäßig aktiviert
        
        # WebSocket-Clients (wird von WebSocket-Handler verwaltet)
        self.websocket_clients = []
    
    def notify_improvement(self, improvement_result: Dict):
        """
        Benachrichtigt über Code-Verbesserung über alle Kanäle.
        
        Args:
            improvement_result: Dict mit file, timestamp, issues_fixed, diff, backup, etc.
        """
        # Timestamp hinzufügen
        improvement_result["timestamp"] = datetime.now().isoformat()
        
        # 1. Log-Datei
        self._log_improvement(improvement_result)
        
        # 2. E-Mail (wenn enabled)
        if self.email_enabled and improvement_result.get("action") in ["improved", "rollback"]:
            self._send_email(improvement_result)
        
        # 3. WebSocket (Live-Updates)
        self._broadcast_websocket(improvement_result)
        
        return improvement_result
    
    def _log_improvement(self, improvement_result: Dict):
        """Schreibt Verbesserung in Log-Datei (JSONL-Format)."""
        date_str = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{date_str}.jsonl"
        
        # Erstelle kompakte Log-Entry
        log_entry = {
            "timestamp": improvement_result.get("timestamp", datetime.now().isoformat()),
            "file": improvement_result.get("file", ""),
            "action": improvement_result.get("action", "unknown"),
            "issues_fixed": improvement_result.get("issues_fixed", 0),
            "tests_passed": improvement_result.get("tests_passed", False),
            "backup": improvement_result.get("backup", ""),
            "improvement_score": improvement_result.get("improvement_score", 0),
            "reason": improvement_result.get("reason", "")
        }
        
        # Schreibe in Log-Datei
        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')
    
    def _send_email(self, improvement_result: Dict):
        """Sendet E-Mail-Benachrichtigung."""
        if not self.email_from or not self.email_to:
            return
        
        try:
            if improvement_result.get("action") == "rollback":
                subject, body = self._create_rollback_email(improvement_result)
            else:
                subject, body = self._create_success_email(improvement_result)
            
            msg = MIMEMultipart()
            msg['From'] = self.email_from
            msg['To'] = self.email_to
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain', 'utf-8'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            if self.email_password:
                server.login(self.email_from, self.email_password)
            server.send_message(msg)
            server.quit()
            
            print(f"[NOTIFICATION] E-Mail gesendet: {subject}")
        except Exception as e:
            print(f"[NOTIFICATION] E-Mail-Versand fehlgeschlagen: {e}")
    
    def _create_success_email(self, improvement_result: Dict) -> tuple:
        """Erstellt E-Mail für erfolgreiche Verbesserung."""
        file_path = Path(improvement_result.get("file", ""))
        file_name = file_path.name if file_path else "Unbekannt"
        
        subject = f"[KI-CodeChecker] ✅ Code-Verbesserung: {file_name}"
        
        body = f"""Hallo Entwickler,

die KI hat erfolgreich eine Code-Verbesserung vorgenommen:

📁 Datei: {improvement_result.get('file', 'Unbekannt')}
🕐 Zeit: {improvement_result.get('timestamp', 'Unbekannt')}
🔧 Issues behoben: {improvement_result.get('issues_fixed', 0)}
✅ Status: Erfolgreich
📊 Tests: {'Alle bestanden' if improvement_result.get('tests_passed', False) else 'Nicht ausgeführt'}

"""
        
        # Diff hinzufügen (gekürzt)
        if improvement_result.get("diff"):
            diff_preview = improvement_result["diff"][:1000]  # Erste 1000 Zeichen
            body += f"""Diff-Vorschau:
{diff_preview}
{'...' if len(improvement_result.get('diff', '')) > 1000 else ''}

"""
        
        if improvement_result.get("backup"):
            body += f"""💾 Backup: {improvement_result['backup']}
"""
        
        body += """
🔗 Dashboard: http://localhost:8111/admin/ki-improvements

---
KI-CodeChecker System
"""
        
        return subject, body
    
    def _create_rollback_email(self, improvement_result: Dict) -> tuple:
        """Erstellt E-Mail für Rollback."""
        file_path = Path(improvement_result.get("file", ""))
        file_name = file_path.name if file_path else "Unbekannt"
        
        subject = f"[KI-CodeChecker] ⚠️ Rollback: {file_name}"
        
        body = f"""Hallo Entwickler,

die KI hat versucht eine Code-Verbesserung vorzunehmen, 
aber die Tests nach der Änderung sind fehlgeschlagen.
Die Änderung wurde automatisch rückgängig gemacht.

📁 Datei: {improvement_result.get('file', 'Unbekannt')}
🕐 Zeit: {improvement_result.get('timestamp', 'Unbekannt')}
❌ Status: Rollback (Tests fehlgeschlagen)
🔧 Issues (nicht behoben): {improvement_result.get('issues_fixed', 0)}

Grund:
{improvement_result.get('reason', 'Unbekannt')}

"""
        
        if improvement_result.get("backup"):
            body += f"""💾 Backup: {improvement_result['backup']}
"""
        
        body += """
🔗 Dashboard: http://localhost:8111/admin/ki-improvements

---
KI-CodeChecker System
"""
        
        return subject, body
    
    def _broadcast_websocket(self, improvement_result: Dict):
        """Sendet Update an alle WebSocket-Clients."""
        # Import hier um Zirkel-Import zu vermeiden
        try:
            from backend.routes.ki_improvements_api import broadcast_improvement_to_websockets
            import asyncio
            
            # Führe async-Funktion aus
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Loop läuft bereits, erstelle Task
                    asyncio.create_task(broadcast_improvement_to_websockets(improvement_result))
                else:
                    # Loop läuft nicht, führe direkt aus
                    loop.run_until_complete(broadcast_improvement_to_websockets(improvement_result))
            except RuntimeError:
                # Kein Event-Loop, erstelle neuen
                asyncio.run(broadcast_improvement_to_websockets(improvement_result))
        except Exception as e:
            print(f"[NOTIFICATION] WebSocket-Broadcast fehlgeschlagen: {e}")
    
    def get_recent_improvements(self, limit: int = 10) -> List[Dict]:
        """Gibt letzte Verbesserungen zurück."""
        improvements = []
        
        # Lese Log-Dateien (neueste zuerst)
        log_files = sorted(self.log_dir.glob("*.jsonl"), reverse=True)
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                # Neueste zuerst
                for line in reversed(lines):
                    if len(improvements) >= limit:
                        break
                    try:
                        improvements.append(json.loads(line.strip()))
                    except json.JSONDecodeError:
                        continue
            
            if len(improvements) >= limit:
                break
        
        return improvements[:limit]
    
    def get_improvement_stats(self) -> Dict:
        """Gibt Statistiken zurück."""
        today = datetime.now().strftime("%Y-%m-%d")
        log_file = self.log_dir / f"{today}.jsonl"
        
        improvements_today = 0
        successful_count = 0
        failed_count = 0
        
        if log_file.exists():
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        entry = json.loads(line.strip())
                        improvements_today += 1
                        if entry.get("action") == "improved":
                            successful_count += 1
                        elif entry.get("action") == "rollback":
                            failed_count += 1
                    except json.JSONDecodeError:
                        continue
        
        return {
            "improvements_today": improvements_today,
            "successful_count": successful_count,
            "failed_count": failed_count,
            "last_improvement": self._get_last_improvement_time()
        }
    
    def _get_last_improvement_time(self) -> Optional[str]:
        """Gibt Zeitpunkt der letzten Verbesserung zurück."""
        improvements = self.get_recent_improvements(limit=1)
        if improvements:
            return improvements[0].get("timestamp")
        return None

# Singleton-Instanz
_notification_service = None

def get_notification_service() -> NotificationService:
    """Gibt Singleton-Instanz zurück."""
    global _notification_service
    if _notification_service is None:
        _notification_service = NotificationService()
    return _notification_service

