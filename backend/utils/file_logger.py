"""
Datei-Logger für Debug-Ausgaben
Schreibt alle Logs in eine Datei: logs/debug.log
"""
import os
from datetime import datetime
from pathlib import Path

# Log-Verzeichnis erstellen
LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)

LOG_FILE = LOG_DIR / "debug.log"

def log_to_file(*args, **kwargs):
    """
    Schreibt Log-Nachricht in Datei UND auf Console.
    ULTRA-ROBUST: Behandelt ALLE Unicode-Fehler.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
    
    # Formatiere Nachricht (mit Unicode-Schutz)
    try:
        message = " ".join(str(arg) for arg in args)
    except Exception as e:
        message = f"[LOG-FORMAT-ERROR] {e}"
    
    # Schreibe in Datei (UTF-8, append mode) - IMMER erfolgreich
    try:
        with open(LOG_FILE, "a", encoding="utf-8", errors="replace") as f:
            # Entferne problematische Unicode-Zeichen
            safe_message = message.encode('utf-8', errors='replace').decode('utf-8', errors='replace')
            f.write(f"[{timestamp}] {safe_message}\n")
            f.flush()  # Sofort schreiben
    except Exception as e:
        # Letzte Rettung: Schreibe Fehler in Datei
        try:
            with open(LOG_FILE, "a", encoding="utf-8", errors="ignore") as f:
                f.write(f"[{timestamp}] [LOG-ERROR] {str(e)[:200]}\n")
                f.flush()
        except Exception:
            pass  # Absolut ignorieren
    
    # Auch auf Console ausgeben (OPTIONAL - wenn es fehlschlägt, egal)
    try:
        # ASCII-Only für Console (sicher)
        safe_message_ascii = message.encode('ascii', errors='replace').decode('ascii')
        print(f"[{timestamp}] {safe_message_ascii}")
    except Exception:
        pass  # Console-Fehler ignorieren

def clear_log():
    """Löscht die Log-Datei (für neuen Test-Start)"""
    try:
        if LOG_FILE.exists():
            LOG_FILE.unlink()
    except Exception:
        pass

