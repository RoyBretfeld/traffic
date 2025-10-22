#!/usr/bin/env python3
"""
Debug-Test für Tourplan-Analyse
"""

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
import unicodedata
import re

def _norm(s: str) -> str:
    """Normalisiert Adressen: Unicode NFC + Whitespace-Bereinigung."""
    s = unicodedata.normalize("NFC", (s or ""))
    s = re.sub(r"\s+", " ", s).strip()
    return s

def debug_tourplan(file_path: str):
    """Debuggt einen Tourplan."""
    print(f"🔍 Debug: {file_path}")
    
    # 1) Parser testen
    data = parse_tour_plan_to_dict(file_path)
    customers = data.get('customers', [])
    
    print(f"📊 Gefunden: {len(customers)} Kunden")
    
    # 2) Erste 5 Kunden analysieren
    print("\n📋 Erste 5 Kunden:")
    for i, customer in enumerate(customers[:5]):
        print(f"\nKunde {i+1}:")
        print(f"  Name: '{customer.get('name', '')}'")
        print(f"  Street: '{customer.get('street', '')}'")
        print(f"  Postal: '{customer.get('postal_code', '')}'")
        print(f"  City: '{customer.get('city', '')}'")
        print(f"  Address: '{customer.get('address', '')}'")
        
        # Adresse zusammenbauen
        if customer.get('address'):
            full_address = customer['address']
        else:
            full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
        
        normalized = _norm(full_address)
        print(f"  Full Address: '{full_address}'")
        print(f"  Normalized: '{normalized}'")
        
        # Synonym-Check
        customer_name = customer.get('name', '')
        if customer_name:
            from common.synonyms import resolve_synonym
            synonym_hit = resolve_synonym(customer_name)
            if synonym_hit:
                print(f"  ✅ Synonym gefunden: {synonym_hit.resolved_address}")
            else:
                print(f"  ❌ Kein Synonym für: {customer_name}")

if __name__ == "__main__":
    debug_tourplan("./tourplaene/Tourenplan 01.09.2025.csv")
