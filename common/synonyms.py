# common/synonyms.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
from common.normalize import normalize_address

@dataclass(frozen=True)
class SynonymHit:
    key: str                 # kanonischer Key z.B. 'PF:JOCHEN'
    resolved_address: str    # menschenlesbar fürs UI
    lat: float
    lon: float
    source: str = "synonym"

# TODO: Diese Werte an eure realen Koordinaten anpassen.
# Keys immer in Uppercase, ohne Umlaute/Leerzeichen, z.B. 'PF:JOCHEN'
_SYNONYMS: Dict[str, SynonymHit] = {
    "PF:JOCHEN": SynonymHit("PF:JOCHEN", "Pf-Depot Jochen, Dresden", 51.0500, 13.7373),
    "PF:SVEN":   SynonymHit("PF:SVEN",   "Pf-Depot Sven, Dresden",   51.0600, 13.7300),
}

# mögliche Schreibweisen, die auf die Kanonischen zeigen (linke Seite frei erweiterbar)
_ALIASES = {
    "JOCHEN - PF": "PF:JOCHEN",
    "PF JOCHEN":   "PF:JOCHEN",
    "SVEN - PF":   "PF:SVEN",
    "PF SVEN":     "PF:SVEN",
    # "PF BAR" kann auf einen der beiden mappen, wenn gewünscht – ansonsten bewusst offen lassen
}

def _canon(s: str) -> str:
    return normalize_address((s or "").strip()).upper()

def resolve_synonym(name_or_addr: str) -> Optional[SynonymHit]:
    if not name_or_addr:
        return None
    k = _canon(name_or_addr)
    # direkter Treffer
    if k in _SYNONYMS:
        return _SYNONYMS[k]
    # Aliase
    if k in (kk := { _canon(a):c for a,c in _ALIASES.items() }):
        canon = kk[k]
        return _SYNONYMS.get(canon)
    return None

def resolve_customer_number(name: str) -> Optional[int]:
    """
    Resolver für Synonyme um die echte ERP-Kundennummer verfügbar zu machen.
    Wird als separates Feld customer_number_resolved ausgegeben.
    """
    # TODO: Hier die echten Kundennummern für PF-Kunden eintragen
    synonym_numbers = {
        "PF:JOCHEN": 9999,  # Beispiel-Kundennummer für Jochen
        "PF:SVEN":   9998,  # Beispiel-Kundennummer für Sven
    }
    
    hit = resolve_synonym(name)
    if hit:
        return synonym_numbers.get(hit.key)
    return None