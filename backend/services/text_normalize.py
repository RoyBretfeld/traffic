"""Text-Normalisierung für deterministisches CSV-Parsing"""

from __future__ import annotations
import re
import unicodedata

_WS = re.compile(r"\s+")
_CTRL = re.compile(r"[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F]")


def normalize_token(s: str) -> str:
    """
    Unicode NFC + Whitespace vereinheitlichen + Steuerzeichen entfernen.
    
    Args:
        s: Input-String (kann None sein)
        
    Returns:
        Normalisierter String (leer wenn None)
    """
    if s is None:
        return ""
    s = unicodedata.normalize("NFC", s)
    s = _CTRL.sub("", s)
    s = _WS.sub(" ", s.strip())
    return s


def normalize_key(*parts: str) -> str:
    """
    Erstellt einen normalisierten Schlüssel aus mehreren Teilen.
    
    Args:
        *parts: Text-Teile die kombiniert werden
        
    Returns:
        Normalisierter, casefold-key (z.B. "street|plz|city|DE")
    """
    parts_norm = [normalize_token(p).casefold() for p in parts if p]
    return "|".join(parts_norm)

