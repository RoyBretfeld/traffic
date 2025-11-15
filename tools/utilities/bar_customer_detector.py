#!/usr/bin/env python3
"""
BAR-Kunden-Erkennung für Address-Corrector

Automatisch generiert basierend auf Tourplan-Analyse.
"""

BAR_CUSTOMER_MAPPINGS = {
    "Turboservice Ingo Barthel": {
        "canonical_name": "Turboservice Ingo Barthel",
        "canonical_address": "Bohnitzscher Str. 4, 01662 Meißen",
        "category": "autoservice",
        "is_bar": True
    },
    "Testa Baresi": {
        "canonical_name": "Testa Baresi", 
        "canonical_address": "Lausener Str. 4B, 04207 Leipzig",
        "category": "autoservice",
        "is_bar": True
    }
}

def is_bar_customer(name, address):
    """Prüft ob ein Kunde ein BAR-Kunde ist."""
    name_lower = name.lower().strip()
    
    for bar_name, mapping in BAR_CUSTOMER_MAPPINGS.items():
        if bar_name.lower() in name_lower:
            return True, mapping
    
    return False, None

def get_bar_customer_mapping(name, address):
    """Gibt das Mapping für einen BAR-Kunden zurück."""
    is_bar, mapping = is_bar_customer(name, address)
    return mapping if is_bar else None
