"""
Temporary File Cleanup Service für FAMO TrafficApp
Verwaltet temporäre Tourpläne und löscht sie nach 40 Tagen
"""

import os
import shutil
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

TEMP_DIR = Path("temp")
RETENTION_DAYS = 40

def ensure_temp_dir():
    """Erstellt das temp-Verzeichnis falls nicht vorhanden."""
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"[TEMP] Verzeichnis sichergestellt: {TEMP_DIR.resolve()}")
    return TEMP_DIR

def cleanup_old_temp_files():
    """
    Löscht temporäre Dateien älter als RETENTION_DAYS.
    Wird regelmäßig aufgerufen (z.B. beim Server-Start).
    """
    ensure_temp_dir()
    
    if not TEMP_DIR.exists():
        logger.warning(f"[TEMP] Verzeichnis existiert nicht: {TEMP_DIR}")
        return
    
    now = datetime.now()
    cutoff_time = now - timedelta(days=RETENTION_DAYS)
    deleted_count = 0
    deleted_size = 0
    
    try:
        for item in TEMP_DIR.iterdir():
            try:
                # Modifikationszeit prüfen
                mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                
                if mod_time < cutoff_time:
                    if item.is_file():
                        size = item.stat().st_size
                        item.unlink()
                        deleted_count += 1
                        deleted_size += size
                        logger.info(f"[TEMP] Datei gelöscht: {item.name} ({size} bytes, älter als {RETENTION_DAYS} Tage)")
                    elif item.is_dir():
                        size = sum(f.stat().st_size for f in item.rglob('*') if f.is_file())
                        shutil.rmtree(item)
                        deleted_count += 1
                        deleted_size += size
                        logger.info(f"[TEMP] Verzeichnis gelöscht: {item.name} ({size} bytes, älter als {RETENTION_DAYS} Tage)")
            except Exception as e:
                logger.error(f"[TEMP] Fehler beim Löschen von {item.name}: {e}")
                continue
        
        if deleted_count > 0:
            logger.info(f"[TEMP] Bereinigung abgeschlossen: {deleted_count} Dateien, {deleted_size / 1024 / 1024:.2f} MB freigegeben")
        else:
            logger.info(f"[TEMP] Keine Dateien älter als {RETENTION_DAYS} Tage gefunden")
    
    except Exception as e:
        logger.error(f"[TEMP] Fehler bei Bereinigung: {e}")

def get_temp_file_path(filename: str) -> Path:
    """
    Gibt den Pfad für eine temporäre Datei zurück.
    
    Args:
        filename: Basis-Dateiname (z.B. "tour_20250101_001.json")
    
    Returns:
        Path zum temp-Verzeichnis
    """
    ensure_temp_dir()
    return TEMP_DIR / filename

def save_temp_file(filename: str, content: str) -> Path:
    """
    Speichert Inhalt in einer temporären Datei.
    
    Args:
        filename: Basis-Dateiname
        content: Dateicontent (String)
    
    Returns:
        Path zur gespeicherten Datei
    """
    file_path = get_temp_file_path(filename)
    file_path.write_text(content, encoding='utf-8')
    logger.info(f"[TEMP] Datei gespeichert: {file_path}")
    return file_path

def get_temp_file_size() -> dict:
    """
    Gibt Statistiken über das temp-Verzeichnis zurück.
    """
    ensure_temp_dir()
    
    file_count = 0
    total_size = 0
    oldest_file = None
    oldest_time = None
    
    try:
        for item in TEMP_DIR.rglob('*'):
            if item.is_file():
                file_count += 1
                size = item.stat().st_size
                total_size += size
                
                mod_time = datetime.fromtimestamp(item.stat().st_mtime)
                if oldest_time is None or mod_time < oldest_time:
                    oldest_time = mod_time
                    oldest_file = item.name
    except Exception as e:
        logger.error(f"[TEMP] Fehler bei Statistik: {e}")
    
    return {
        "temp_dir": str(TEMP_DIR.resolve()),
        "file_count": file_count,
        "total_size_mb": round(total_size / 1024 / 1024, 2),
        "oldest_file": oldest_file,
        "oldest_file_date": oldest_time.isoformat() if oldest_time else None,
        "retention_days": RETENTION_DAYS,
        "cleanup_threshold": (datetime.now() - timedelta(days=RETENTION_DAYS)).isoformat()
    }
