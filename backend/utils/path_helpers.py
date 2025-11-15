"""
Helper-Funktionen für Pfad-Operationen.
Vermeidet hardcoded Pfade und macht Code konfigurierbar.
"""
from pathlib import Path
import os
from typing import Optional


def get_frontend_path(relative_path: str) -> Path:
    """
    Gibt den vollständigen Pfad zu einer Frontend-Datei zurück.
    
    Args:
        relative_path: Relativer Pfad zur Datei (z.B. "index.html" oder "admin/login.html")
        
    Returns:
        Path-Objekt zum vollständigen Pfad
        
    Raises:
        FileNotFoundError: Wenn das Frontend-Verzeichnis nicht existiert
    """
    frontend_dir = os.getenv("FRONTEND_DIR", "frontend")
    frontend_path = Path(frontend_dir)
    
    if not frontend_path.exists():
        raise FileNotFoundError(f"Frontend-Verzeichnis nicht gefunden: {frontend_path}")
    
    full_path = frontend_path / relative_path
    return full_path


def read_frontend_file(relative_path: str, encoding: str = "utf-8") -> str:
    """
    Liest eine Frontend-Datei und gibt den Inhalt zurück.
    
    Args:
        relative_path: Relativer Pfad zur Datei (z.B. "index.html")
        encoding: Encoding der Datei (Standard: utf-8)
        
    Returns:
        Dateiinhalt als String
        
    Raises:
        FileNotFoundError: Wenn die Datei nicht gefunden wird
        IOError: Wenn die Datei nicht gelesen werden kann
    """
    file_path = get_frontend_path(relative_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Frontend-Datei nicht gefunden: {file_path}")
    
    with open(file_path, 'r', encoding=encoding) as f:
        return f.read()

