# common/normalize.py
from __future__ import annotations
import re
from pathlib import Path
from typing import Dict, List, Optional
from repositories.address_lookup import _find_complete_address_by_plz_name, _find_complete_address_by_name_only, clear_address_cache
from common.text_cleaner import _fix_question_marks

_PIPE_SEP = re.compile(r"\s*\|\s*")
_MULTI_SEP = re.compile(r"\s*[;,]+\s*")
_SPACES   = re.compile(r"\s+")

# Sehr konservative UTF‑8‑Mojibake-Fixes (klassische Fehldekodierungen)
_SAFE_FIXES = {
    "Ã¤":"ä","Ã¶":"ö","Ã¼":"ü","ÃŸ":"ß",
    "Ã„":"Ä","Ã–":"Ö","Ãœ":"Ü",
}

# Intelligente ?? Zeichen-Korrektur basierend auf Kontext
def _fix_question_marks(text: str) -> str:
    """Korrigiert ?? Zeichen basierend auf Kontext."""
    if not text or "??" not in text:
        return text
    
    # Kontext-basierte Korrekturen für häufige Fälle
    context_fixes = {
        # Straße/Straße-Korrekturen
        "Stra??e": "Straße",
        "stra??e": "straße", 
        "Stra??": "Straße",
        "stra??": "straße",
        
        # Häufige Straßennamen mit ?? 
        "Burgker Stra??e": "Burgker Straße",
        "Cosch??tzer": "Coschützer",
        "Cosch??tzer Stra??e": "Coschützer Straße",
        "Wilsdruffer Stra??e": "Wilsdruffer Straße",
        "Dresdner Stra??e": "Dresdner Straße",
        "Tharandter Stra??e": "Tharandter Straße",
        "L??btauer": "Löbtauer",
        "L??btauer Stra??e": "Löbtauer Straße",
        "Fr??belstra??e": "Fröbelstraße",
        "Morgenr??the": "Morgenröthe",
        "Nieder m??hle": "Niedermühle",
        "B??renstein": "Bärenstein",
        "Gro??opitz": "Großopitz",
        "Berggie??h??bel": "Berggießhübel",
        "Gottleuba-Berggie??h??bel": "Gottleuba-Berggießhübel",
        "Bad Gottleuba-Berggie??h??bel": "Bad Gottleuba-Berggießhübel",
        
        # Allgemeine ?? Zeichen-Korrekturen (nach spezifischen Fällen)
        
        # Weitere häufige Fälle
        "H??se": "Häse",  # Häufig in Namen
        "H??hnel": "Höhnel",
        "M??ller": "Müller",
        "M??glitztalstra??e": "Müglitztalstraße",
        "Pratzschwitzer Stra??e": "Pratzschwitzer Straße",
        "Herbert-Liebsch- Str.": "Herbert-Liebsch-Straße",
        "Stra??e des Friedens": "Straße des Friedens",
        "Stra??e der MTS": "Straße der MTS",
        "Dresdner Landstrasse": "Dresdner Landstraße",
        "Kleine Basch??tzer": "Kleine Baschützer",
        "Kleine Basch??tzer Str.": "Kleine Baschützer Straße",
        
        # Zusätzliche Mojibake-Fälle aus den verbleibenden Warnungen
        "S??gewerk": "Sägewerk",
        "Sch??nfeld": "Schönfeld",
        "Glash??tte": "Glashütte",
        "haftungsbeschr??nkt": "haftungsbeschränkt",
        "Altnossener Stra??e": "Altnossener Straße",
        "Dorfstra??e": "Dorfstraße",
        "Stolpener Strasse": "Stolpener Straße",
        
        # Weitere spezifische Fälle
        "Am S??gewerk": "Am Sägewerk",
        "OT Sch??nfeld": "OT Schönfeld",
        "OT Luchau": "OT Luchau",  # Bereits korrekt
        "OT Sehma": "OT Sehma",    # Bereits korrekt
    }
    
    # Wende Kontext-Fixes an
    for corrupt, correct in context_fixes.items():
        text = text.replace(corrupt, correct)
    
    return text

# Cache für vollständige Adressen (PLZ + Name -> vollständige Adresse)
_address_cache: Dict[str, str] = {}

def normalize_address(addr: str | None, customer_name: str | None = None, postal_code: str | None = None) -> str:
    """
    Zentrale Adress-Normalisierung.
    
    Die Adress-Vervollständigung (PLZ + Name-Regel) wird beibehalten, da sie
    für unvollständige CSV-Einträge wichtig ist.
    
    Args:
        addr: Rohe Adresse (kann None sein)
        customer_name: Firmenname (optional, für PLZ+Name-Regel)
        postal_code: Postleitzahl (optional, für PLZ+Name-Regel)
        
    Returns:
        Normalisierte Adresse als String
    """
    
    # PLZ + Name-Regel: Bei unvollständigen Adressen nach vollständiger Adresse suchen
    if (not addr or str(addr).strip().lower() in ['nan', '']) and customer_name:
        # Versuche zuerst mit gegebener PLZ
        if postal_code and postal_code.lower() not in ['nan', '']:
            full_address = _find_complete_address_by_plz_name(customer_name, postal_code, normalize_address_func=normalize_address)
            if full_address:
                # WICHTIG: Die gefundene Adresse muss selbst normalisiert werden
                return normalize_address(full_address)
        
        # Falls keine PLZ oder keine Übereinstimmung, suche ohne PLZ-Beschränkung
        full_address = _find_complete_address_by_name_only(customer_name, normalize_address_func=normalize_address)
        if full_address:
            # WICHTIG: Die gefundene Adresse muss selbst normalisiert werden
            return normalize_address(full_address)
    if not addr:
        return ""
    s = str(addr).strip()

    # 1) Pipes zu Komma-Blöcken verschmelzen
    if '|' in s:
        s = _PIPE_SEP.sub(', ', s)

    # 2) Halle-Erwähnungen entfernen (für bessere Geocoding-Erfolgsrate)
    # Verbesserter Regex, um ", Halle 14" oder "/ Halle 14" zu entfernen
    s = re.sub(r',\\s*Halle\\s+\\d+\\w*', '', s, flags=re.IGNORECASE)
    s = re.sub(r'/\\s*Halle\\s+\\d+\\w*', '', s, flags=re.IGNORECASE)
    
    # 3) OT-Erwähnungen entfernen (präziser, um Duplikate zu vermeiden)
    # Entfernt: "(OT Ortsteil)", "/ OT Ortsteil", ", OT Ortsteil"
    s = re.sub(r'\s*\(\s*(?:OT|Ortsteil)\s+[\\w\\s.-]+\s*\)', '', s, flags=re.IGNORECASE)
    s = re.sub(r',\\s*(?:OT|Ortsteil)\\s+[\\w\\s.-]+', '', s, flags=re.IGNORECASE)
    s = re.sub(r'/\\s*(?:OT|Ortsteil)\\s+[\\w\\s.-]+', '', s, flags=re.IGNORECASE)
    
    # 4) Sekundäre Trenner vereinheitlichen und trimmen
    parts = [p.strip(" ,;/") for p in _MULTI_SEP.split(s) if p.strip(" ,;/")]
    s = ", ".join(parts)
    
    # 4.1) ?? Zeichen-Korrektur (intelligente Kontext-basierte Fixes)
    s = _fix_question_marks(s)
    
    # 4.2) Komma-Normalisierung für bessere Cache-Treffer
    s = re.sub(r',\\s*(\\d{5})\\s*,\\s*([A-Za-zäöüßÄÖÜ]+)\\s*$', r', \\1 \\2', s)
    s = re.sub(r',\\s*(\\d{5})\\s*,\\s*([A-Za-zäöüßÄÖÜ]+)\\s+OT\\s+', r', \\1 \\2 OT ', s)
    s = re.sub(r',\\s*(\\d{5})\\s*,\\s*([A-Za-zäöüßÄÖÜ]+)\\s+/', r', \\1 \\2 /', s)

    # 5) Whitespace normalisieren (doppelte Leerzeichen entfernen)
    s = _SPACES.sub(" ", s).strip(' ,')
    
    # 6) Schreibfehler- und Konsistenz-Korrekturen
    # KRITISCH: Konsequente Normalisierung auf Hauptstr.
    s = re.sub(r'\bHauptstr\\.?(?=\s|$)', 'Hauptstr.', s, flags=re.IGNORECASE) # Haupstr. -> Hauptstr.
    s = re.sub(r'\bHauptstrasse', 'Hauptstr.', s, flags=re.IGNORECASE) # Hauptstrasse -> Hauptstr.
    s = re.sub(r'\bHauptstraße', 'Hauptstr.', s, flags=re.IGNORECASE) # Hauptstraße -> Hauptstr.
    s = re.sub(r'\bHaupstr', 'Hauptstr.', s, flags=re.IGNORECASE) # Haupstr ohne Punkt -> Hauptstr.
    s = re.sub(r'\bStrae', 'Straße', s, flags=re.IGNORECASE)  # Strae -> Straße
    s = re.sub(r'\.\\.', '.', s)  # Doppelte Punkte entfernen
    
    # 7) Spezifische Adress-Korrekturen für bekannte Problemfälle (mit Hauptstr. Konsistenz)
    s = re.sub(r'\bHauptstr\\. 1, 01809 Heidenau', 'Hauptstr. 1, 01809 Heidenau', s)
    s = re.sub(r'\bHauptstr\\. 9a, 01728 Bannewitz', 'Hauptstr. 9a, 01728 Bannewitz/OT Possendorf', s)
    s = re.sub(r'\bHauptstr\\. 70, 01705 Freital', 'Hauptstr. 70, 01705 Freital', s)
    s = re.sub(r'\bHauptstr\\. 122, 01816 Bad Gottleuba-Berggießhübel', 'Hauptstr. 122, 01816 Bad Gottleuba-Berggießhübel', s)
    s = re.sub(r'\bHauptstr\\. 16, 01816 Bad Gottleuba-Berggießhübel', 'Hauptstr. 16, 01816 Bad Gottleuba-Berggießhübel', s)
    s = re.sub(r'\bJohnsbacher Hauptstr\\. 55, 01768 Glashütte', 'Johnsbacher Hauptstr. 55, 01768 Glashütte', s)
    s = re.sub(r'\bAn der Triebe\\s+25, 01468 Moritzburg', 'An der Triebe 25, 01468 Moritzburg', s)

    # 8) OT-Suffixe nur hinzufügen wenn nötig und nicht dupliziert (mit negativen Lookaheads)
    # Beispiel: Alte Str. 33, 01768 Glashütte (OT Hirschbach) -> Glashütte OT Hirschbach
    
    # Sicherstellen, dass der Ortsteil noch nicht am Ende der Adresse steht
    s = re.sub(r'\bGersdorf 43, 01819 Bahretal(?!\s*OT\s*Gersdorf)', 'Gersdorf 43, 01819 Bahretal OT Gersdorf', s)
    s = re.sub(r'\bAlte Str\\. 33, 01768 Glashütte(?!\s*OT\s*Hirschbach)', 'Alte Str. 33, 01768 Glashütte OT Hirschbach', s)
    s = re.sub(r'\bHohensteiner Str\\. 101, 09212 Limbach-O\\.?(?!\s*/OT\s*Pleißa)', 'Hohensteiner Str. 101, 09212 Limbach-O./OT Pleißa', s)
    s = re.sub(r'\bReinberger Dorfstraße 6a, 01744 Dippoldiswalde(?!\s*/OT\s*Reinberg)', 'Reinberger Dorfstraße 6a, 01744 Dippoldiswalde/OT Reinberg', s)
    
    # 9) Bereinigung von Duplikaten und trailing dots
    s = re.sub(r'\bOT\s+(\w+)\s+OT\s+\1\b', r'OT \1', s)  
    s = re.sub(r'\b/OT\s+(\w+)\s+/OT\s+\1\b', r'/OT \1', s)  
    s = re.sub(r'\.+$', '', s)  
    
    # 10) sichere Mojibake-Fixes (keine Fantasie-Mappings)
    for bad, good in _SAFE_FIXES.items():
        if bad in s:
            s = s.replace(bad, good)

    return s.strip() # Finaler Trim für den Fall, dass die End-Regex Leerzeichen hinterlässt



# Funktion entfernt: _check_synonym (wird in geocode_fill.py/synonyms.py gehandhabt)
# Funktion entfernt: _check_synonym (zweite DB-Version)
# Funktion entfernt: _fuzzy_name_match (fehlerhafte Fuzzy-Logik)


# def clear_address_cache(): # moved to address_lookup.py
#     """Leert den Adress-Cache (für Tests)."""
#     global _address_cache
#     _address_cache.clear()
