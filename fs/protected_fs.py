"""
Geschützte Filesystem-Operationen für Original-Tourenpläne
Verhindert Schreibzugriffe auf Original-Verzeichnisse
"""

from pathlib import Path
import os
from typing import Optional
import warnings

# Read-Only Verzeichnisse (Original-Tourenpläne)
PROTECTED_DIRS = [
    Path("./tourplaene"),
    Path("./Tourenpläne"),
    Path("./Tourplaene"),
]

# Schreibbare Verzeichnisse für Verarbeitung
WRITABLE_DIRS = [
    Path("./data/staging"),
    Path("./data/temp"),
    Path("./data/tmp"),
]

def is_protected_path(path: Path) -> bool:
    """Prüft ob ein Pfad in einem geschützten Verzeichnis liegt"""
    path = path.resolve()
    
    for protected in PROTECTED_DIRS:
        protected_abs = protected.resolve()
        try:
            if path.is_relative_to(protected_abs):
                return True
        except (AttributeError, ValueError):
            # Python < 3.9 Kompatibilität
            try:
                path.relative_to(protected_abs)
                return True
            except ValueError:
                pass
    
    return False

def ensure_writable_dir(path: Path) -> Path:
    """Stellt sicher, dass ein Pfad in einem schreibbaren Verzeichnis liegt"""
    path = path.resolve()
    
    # Prüfe ob bereits in schreibbarem Verzeichnis
    for writable in WRITABLE_DIRS:
        writable_abs = writable.resolve()
        try:
            if path.is_relative_to(writable_abs):
                return path
        except (AttributeError, ValueError):
            try:
                path.relative_to(writable_abs)
                return path
            except ValueError:
                pass
    
    # Falls nicht, verwende staging als Fallback
    staging = Path("./data/staging").resolve()
    staging.mkdir(parents=True, exist_ok=True)
    return staging / path.name

def protected_write(path: Path, content: bytes, *, 
                   mode: str = 'wb', 
                   allow_staging: bool = True) -> Path:
    """
    Geschützte Schreib-Operation. Verhindert Schreiben in Original-Verzeichnisse.
    
    Args:
        path: Ziel-Pfad
        content: Zu schreibende Daten
        mode: Datei-Modus ('wb', 'w', etc.)
        allow_staging: Wenn True, wird staging-Verzeichnis verwendet als Fallback
        
    Returns:
        Tatsächlicher geschriebener Pfad
        
    Raises:
        PermissionError: Wenn versucht wird, in geschütztes Verzeichnis zu schreiben
    """
    path = Path(path)
    
    if is_protected_path(path):
        if allow_staging:
            warnings.warn(
                f"Schreibversuch in geschütztes Verzeichnis blockiert: {path}\n"
                f"Verwende staging-Verzeichnis stattdessen.",
                UserWarning
            )
            safe_path = ensure_writable_dir(path)
            safe_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            raise PermissionError(
                f"Schreibzugriff auf geschütztes Verzeichnis verweigert: {path}\n"
                f"Original-Tourenpläne dürfen nicht verändert werden!\n"
                f"Verwende data/staging/ oder data/temp/ für Änderungen."
            )
    else:
        safe_path = path
        safe_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Schreiben
    if 'b' in mode:
        safe_path.write_bytes(content)
    else:
        safe_path.write_text(content if isinstance(content, str) else content.decode('utf-8'))
    
    return safe_path

def protected_save_csv(path: Path, df, **kwargs) -> Path:
    """
    Geschützte CSV-Speicherung. Verhindert Überschreiben von Original-CSVs.
    
    Args:
        path: Ziel-Pfad für CSV
        df: pandas DataFrame
        **kwargs: Weitere Argumente für to_csv()
        
    Returns:
        Tatsächlicher gespeicherter Pfad
    """
    import pandas as pd
    
    path = Path(path)
    
    if is_protected_path(path):
        warnings.warn(
            f"CSV-Speicherung in geschütztes Verzeichnis blockiert: {path}\n"
            f"Speichere stattdessen in staging-Verzeichnis.",
            UserWarning
        )
        safe_path = ensure_writable_dir(path)
        safe_path.parent.mkdir(parents=True, exist_ok=True)
    else:
        safe_path = path
        safe_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Speichere CSV
    df.to_csv(safe_path, **kwargs)
    
    return safe_path

def verify_readonly(path: Path) -> bool:
    """Prüft ob eine Datei/Ordner Read-Only ist"""
    if not path.exists():
        return False
    
    mode = path.stat().st_mode
    
    # Windows: Prüfe ob Write-Bit fehlt
    if os.name == 'nt':
        return not (mode & stat.S_IWRITE)
    else:
        # Unix: Prüfe ob Owner-Write fehlt
        import stat
        return not (mode & stat.S_IWUSR)

# Stat-Modul bereits oben importiert

