# common/normalize.py
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Optional

_PIPE_SEP = re.compile(r"\s*\|\s*")
_MULTI_SEP = re.compile(r"\s*[;,]+\s*")
_SPACES   = re.compile(r"\s+")

# Sehr konservative UTF‑8‑Mojibake-Fixes (klassische Fehldekodierungen)
_SAFE_FIXES = {
    "Ã¤":"ä","Ã¶":"ö","Ã¼":"ü","ÃŸ":"ß",
    "Ã„":"Ä","Ã–":"Ö","Ãœ":"Ü",
}

# Cache für vollständige Adressen (PLZ + Name -> vollständige Adresse)
_address_cache: Dict[str, str] = {}

def normalize_address(addr: str | None, customer_name: str | None = None, postal_code: str | None = None) -> str:
    """
    Zentrale Adress-Normalisierung.
    
    Wandelt Pipes zu Kommas, bereinigt Mehrfach-Trenner und Whitespace,
    und führt sichere Mojibake-Fixes durch.
    
    Bei unvollständigen Adressen (leere Straße) wird versucht, eine vollständige
    Adresse über PLZ + Firmenname zu finden.
    
    Args:
        addr: Rohe Adresse (kann None sein)
        customer_name: Firmenname (optional, für PLZ+Name-Regel)
        postal_code: Postleitzahl (optional, für PLZ+Name-Regel)
        
    Returns:
        Normalisierte Adresse als String
    """
    # Synonym-Check: Prüfe zuerst auf bekannte Synonyme
    if customer_name:
        synonym_address = _check_synonym(customer_name)
        if synonym_address:
            return synonym_address
    
    # PLZ + Name-Regel: Bei unvollständigen Adressen nach vollständiger Adresse suchen
    if (not addr or str(addr).strip().lower() in ['nan', '']) and customer_name:
        # Versuche zuerst mit gegebener PLZ
        if postal_code and postal_code.lower() not in ['nan', '']:
            full_address = _find_complete_address_by_plz_name(customer_name, postal_code)
            if full_address:
                return full_address
        
        # Falls keine PLZ oder keine Übereinstimmung, suche ohne PLZ-Beschränkung
        full_address = _find_complete_address_by_name_only(customer_name)
        if full_address:
            return full_address
    
    if not addr:
        return ""
    s = str(addr).strip()

    # 1) Pipes zu Komma-Blöcken verschmelzen
    if '|' in s:
        s = _PIPE_SEP.sub(', ', s)

    # 2) Halle-Erwähnungen entfernen (für bessere Geocoding-Erfolgsrate)
    s = re.sub(r',\s*Halle\s+\d+\w*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'/\s*Halle\s+\d+\w*', '', s, flags=re.IGNORECASE)
    
    # 3) OT-Erwähnungen entfernen (selektiv für bessere Geocoding-Erfolgsrate)
    s = re.sub(r'\(\s*OT\s+\w+\s*\)', '', s, flags=re.IGNORECASE)
    s = re.sub(r'/\s*OT\s+\w+', '', s, flags=re.IGNORECASE)
    # Nicht entfernen: , OT und OT ohne Klammern (zu aggressiv)

    # 4) Sekundäre Trenner vereinheitlichen und trimmen
    parts = [p.strip(" ,;/") for p in _MULTI_SEP.split(s) if p.strip(" ,;/")]
    s = ", ".join(parts)

    # 5) Whitespace normalisieren (doppelte Leerzeichen entfernen)
    s = _SPACES.sub(" ", s).strip(' ,')
    
    # 6) Spezielle Adress-Korrekturen für bekannte Problemfälle
    s = re.sub(r'\bAn der Triebe\s+25, 01468 Moritzburg\b', 'An der Triebe 25, 01468 Moritzburg', s)

    # 6) Schreibfehler-Korrekturen (häufige Tippfehler)
    s = re.sub(r'\bHaupstr\.?\b', 'Hauptstr.', s, flags=re.IGNORECASE)
    s = re.sub(r'\bHauptstrasse\b', 'Hauptstr.', s, flags=re.IGNORECASE)
    s = re.sub(r'\bHauptstraße\b', 'Hauptstr.', s, flags=re.IGNORECASE)
    s = re.sub(r'\bStrae\b', 'Straße', s, flags=re.IGNORECASE)  # Strae -> Straße
    s = re.sub(r'\.\.', '.', s)  # Doppelte Punkte entfernen
    
    # 7) Spezielle Adress-Korrekturen für bekannte Problemfälle
    s = re.sub(r'\bHauptstr\. 1, 01809 Heidenau\b', 'Hauptstraße 1, 01809 Heidenau', s)
    s = re.sub(r'\bHauptstr\. 9a, 01728 Bannewitz\b', 'Hauptstrasse 9a, 01728 Bannewitz/OT Possendorf', s)
    s = re.sub(r'\bHauptstr\. 70, 01705 Freital\b', 'Hauptstraße 70, 01705 Freital', s)
    
    # Weitere spezielle Korrekturen basierend auf CRM-Daten
    s = re.sub(r'\bHauptstr\. 122, 01816 Bad Gottleuba-Berggießhübel\b', 'Hauptstraße 122, 01816 Bad Gottleuba-Berggießhübel', s)
    s = re.sub(r'\bHauptstr\. 16, 01816 Bad Gottleuba-Berggießhübel\b', 'Hauptstraße 16, 01816 Bad Gottleuba-Berggießhübel', s)
    
    # OT-Suffixe nur hinzufügen wenn noch nicht vorhanden
    s = re.sub(r'\bGersdorf 43, 01819 Bahretal(?!\s+OT)', 'Gersdorf 43, 01819 Bahretal OT Gersdorf', s)
    s = re.sub(r'\bAlte Str\. 33, 01768 Glashütte(?!\s+OT)', 'Alte Str. 33, 01768 Glashütte OT Hirschbach', s)
    s = re.sub(r'\bHohensteiner Str\. 101, 09212 Limbach-O\.?(?!\s*/OT)', 'Hohensteiner Str. 101, 09212 Limbach-O./OT Pleißa', s)
    s = re.sub(r'\bReinberger Dorfstraße 6a, 01744 Dippoldiswalde(?!\s*/OT)', 'Reinberger Dorfstraße 6a, 01744 Dippoldiswalde/OT Reinberg', s)
    s = re.sub(r'\bJohnsbacher Hauptstr\. 55, 01768 Glashütte\b', 'Johnsbacher Hauptstraße 55, 01768 Glashütte', s)
    
    # Doppelte OT-Suffixe bereinigen
    s = re.sub(r'\bOT\s+(\w+)\s+OT\s+\1\b', r'OT \1', s)  # OT Gersdorf OT Gersdorf -> OT Gersdorf
    s = re.sub(r'\b/OT\s+(\w+)\s+/OT\s+\1\b', r'/OT \1', s)  # /OT Pleißa /OT Pleißa -> /OT Pleißa
    s = re.sub(r'\.+$', '', s)  # Trailing dots entfernen
    
    # 7) sichere Mojibake-Fixes (keine Fantasie-Mappings)
    for bad, good in _SAFE_FIXES.items():
        if bad in s:
            s = s.replace(bad, good)

    return s


def _find_complete_address_by_plz_name(customer_name: str, postal_code: str) -> Optional[str]:
    """
    Sucht nach einer vollständigen Adresse basierend auf PLZ + Firmenname.
    Erweiterte Fuzzy-Suche für ähnliche Namen (z.B. "Sven - PF" -> "Sven Teichmann").
    
    Args:
        customer_name: Firmenname
        postal_code: Postleitzahl
        
    Returns:
        Vollständige Adresse oder None
    """
    if not customer_name or not postal_code:
        return None
    
    # Cache-Key: PLZ + Name
    cache_key = f"{postal_code}|{customer_name.strip()}"
    
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
                    
                    # Prüfe ob Name und PLZ übereinstimmen (exakt oder fuzzy)
                    name_match = (csv_name.lower() == customer_name.lower().strip() or
                                _fuzzy_name_match(customer_name, csv_name))
                    
                    if (name_match and 
                        csv_postal_code == postal_code and 
                        csv_street and csv_street.lower() not in ['nan', '']):
                        
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


def _find_complete_address_by_name_only(customer_name: str) -> Optional[str]:
    """
    Sucht nach einer vollständigen Adresse basierend nur auf dem Firmennamen.
    Für Fälle wo PLZ fehlt (z.B. "Sven - PF" mit PLZ "nan").
    
    Args:
        customer_name: Firmenname
        
    Returns:
        Vollständige Adresse oder None
    """
    if not customer_name:
        return None
    
    # Cache-Key: nur Name
    cache_key = f"name_only|{customer_name.strip()}"
    
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
                    if (_fuzzy_name_match(customer_name, csv_name) and 
                        csv_street and csv_street.lower() not in ['nan', ''] and
                        csv_postal_code and csv_postal_code.lower() not in ['nan', '']):
                        
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


def _check_synonym(customer_name: str) -> Optional[str]:
    """
    Prüft auf bekannte Synonyme in der geo_cache Tabelle.
    
    Args:
        customer_name: Firmenname
        
    Returns:
        Vollständige Adresse oder None
    """
    if not customer_name:
        return None
    
    # Cache-Key: Synonym-Check
    cache_key = f"synonym|{customer_name.strip()}"
    
    # Erst im Cache suchen
    if cache_key in _address_cache:
        return _address_cache[cache_key]
    
    # Datenbank-Verbindung
    from settings import SETTINGS
    import sqlite3
    
    try:
        db_path = SETTINGS.database_url.replace("sqlite:///", "")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Suche nach Synonym in geo_cache
        cursor.execute('''
            SELECT address_norm, lat, lon
            FROM geo_cache
            WHERE address_norm LIKE ? AND source = 'synonym'
        ''', (f"%{customer_name}%",))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            # Vollständige Adresse extrahieren (ohne den Synonym-Namen)
            full_address = result[0]
            # Entferne den Synonym-Namen vom Anfang
            if ', ' in full_address:
                full_address = full_address.split(', ', 1)[1]
            
            # Im Cache speichern
            _address_cache[cache_key] = full_address
            return full_address
        
    except Exception:
        pass
    
    # Nichts gefunden
    _address_cache[cache_key] = None
    return None


def _fuzzy_name_match(name1: str, name2: str) -> bool:
    """
    Fuzzy-Name-Matching für ähnliche Kunden.
    
    Args:
        name1: Erster Name (z.B. "Sven - PF")
        name2: Zweiter Name (z.B. "Sven Teichmann")
        
    Returns:
        True wenn die Namen ähnlich genug sind
    """
    if not name1 or not name2:
        return False
    
    # Normalisiere Namen
    n1 = name1.lower().strip()
    n2 = name2.lower().strip()
    
    # Exakte Übereinstimmung
    if n1 == n2:
        return True
    
    # Spezielle Regeln für bekannte Fälle
    if 'sven' in n1 and 'sven' in n2:
        # "Sven - PF" matches "Sven Teichmann" - DEAKTIVIERT!
        # "Sven - PF" ist NICHT "Sven Teichmann"!
        return False
    
    # Weitere Fuzzy-Regeln können hier hinzugefügt werden
    # z.B. Levenshtein-Distanz, Soundex, etc.
    
    return False


def clear_address_cache():
    """Leert den Adress-Cache (für Tests)."""
    global _address_cache
    _address_cache.clear()
