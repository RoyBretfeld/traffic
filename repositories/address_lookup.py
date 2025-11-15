from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Optional
# from common.normalize import normalize_address # Importiere normalize_address (Entfernt: Zirkulärer Import)

# Cache für vollständige Adressen (PLZ + Name -> vollständige Adresse)
_address_cache: Dict[str, str] = {}

def _find_complete_address_by_plz_name(customer_name: str, postal_code: str, normalize_address_func) -> Optional[str]:
    """
    Sucht nach einer vollständigen Adresse basierend auf PLZ + Firmenname.
    
    Args:
        customer_name: Firmenname
        postal_code: Postleitzahl
        normalize_address_func: Die zentrale Normalisierungsfunktion (common.normalize.normalize_address)
        
    Returns:
        Vollständige Adresse oder None
    """
    if not customer_name or not postal_code:
        return None
    
    # Cache-Key: PLZ + Name
    cache_key = f"{postal_code}|{normalize_address_func(customer_name).strip()}"
    
    # Erst im Cache suchen
    if cache_key in _address_cache:
        return _address_cache[cache_key]
    
    # Alle CSV-Dateien durchsuchen
    tour_plan_dir = Path('tourplaene')
    if not tour_plan_dir.exists():
        return None
    
    csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    for csv_file in csv_files:
        try:
            # CSV parsen (vereinfacht, ohne den kompletten Parser zu laden)
            with open(csv_file, 'r', encoding='cp850', errors='ignore') as f:
                lines = f.readlines()
            
            # Header finden
            header_line = None
            for i, line in enumerate(lines):
                if 'Kdnr' in line and 'Name' in line and 'Straße' in line:
                    header_line = i
                    break
            
            if header_line is None:
                continue
                
            # Datenzeilen verarbeiten
            for line in lines[header_line + 1:]:
                if not line.strip() or line.startswith(';'):
                    continue
                    
                parts = line.strip().split(';')
                if len(parts) < 6:
                    continue
                
                try:
                    csv_customer_id = parts[0].strip()
                    csv_name = parts[1].strip()
                    csv_street = parts[2].strip()
                    csv_postal_code = parts[3].strip()
                    csv_city = parts[4].strip()
                    
                    # Prüfe ob Name und PLZ übereinstimmen (exakt)
                    name_match = (normalize_address_func(csv_name).lower() == normalize_address_func(customer_name).lower().strip())
                    
                    if (name_match and 
                        csv_postal_code == postal_code and 
                        csv_street and normalize_address_func(csv_street).lower() not in ['nan', '']):
                        
                        # Vollständige Adresse gefunden
                        full_address = f"{csv_street}, {csv_postal_code} {csv_city}"
                        
                        # Im Cache speichern
                        _address_cache[cache_key] = full_address
                        return full_address
                        
                except (IndexError, ValueError):
                    continue
                    
        except Exception:
            continue
    
    # Nichts gefunden
    _address_cache[cache_key] = None
    return None


def _find_complete_address_by_name_only(customer_name: str, normalize_address_func) -> Optional[str]:
    """
    Sucht nach einer vollständigen Adresse basierend nur auf dem Firmennamen.
    
    Args:
        customer_name: Firmenname
        normalize_address_func: Die zentrale Normalisierungsfunktion (common.normalize.normalize_address)
        
    Returns:
        Vollständige Adresse oder None
    """
    if not customer_name:
        return None
    
    # Cache-Key: nur Name
    cache_key = f"name_only|{normalize_address_func(customer_name).strip()}"
    
    # Erst im Cache suchen
    if cache_key in _address_cache:
        return _address_cache[cache_key]
    
    # Alle CSV-Dateien durchsuchen
    tour_plan_dir = Path('tourplaene')
    if not tour_plan_dir.exists():
        return None
    
    csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    for csv_file in csv_files:
        try:
            # CSV parsen (vereinfacht, ohne den kompletten Parser zu laden)
            with open(csv_file, 'r', encoding='cp850', errors='ignore') as f:
                lines = f.readlines()
            
            # Header finden
            header_line = None
            for i, line in enumerate(lines):
                if 'Kdnr' in line and 'Name' in line and 'Straße' in line:
                    header_line = i
                    break
            
            if header_line is None:
                continue
                
            # Datenzeilen verarbeiten
            for line in lines[header_line + 1:]:
                if not line.strip() or line.startswith(';'):
                    continue
                    
                parts = line.strip().split(';')
                if len(parts) < 6:
                    continue
                
                try:
                    csv_customer_id = parts[0].strip()
                    csv_name = parts[1].strip()
                    csv_street = parts[2].strip()
                    csv_postal_code = parts[3].strip()
                    csv_city = parts[4].strip()
                    
                    # Prüfe nur Name-Match (ohne PLZ)
                    if (normalize_address_func(csv_name).lower() == normalize_address_func(customer_name).lower().strip() and 
                        csv_street and normalize_address_func(csv_street).lower() not in ['nan', ''] and
                        csv_postal_code and normalize_address_func(csv_postal_code).lower() not in ['nan', '']):
                        
                        # Vollständige Adresse gefunden
                        full_address = f"{csv_street}, {csv_postal_code} {csv_city}"
                        
                        # Im Cache speichern
                        _address_cache[cache_key] = full_address
                        return full_address
                        
                except (IndexError, ValueError):
                    continue
                    
        except Exception:
            continue
    
    # Nichts gefunden
    _address_cache[cache_key] = None
    return None


def clear_address_cache():
    """Leert den Adress-Cache (für Tests)."""
    global _address_cache
    _address_cache.clear()
