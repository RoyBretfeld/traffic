#!/usr/bin/env python3
"""
Filter für private Kunden - ignoriert bestimmte Kunden beim Geocoding
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Any

def load_ignore_list() -> Dict[str, Any]:
    """Lädt die Ignor-Liste für private Kunden"""
    config_file = Path("config/private_customers_ignore.json")
    if config_file.exists():
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"⚠️ Fehler beim Laden der Ignor-Liste: {e}")
            return {"private_customers": [], "ignore_patterns": []}
    return {"private_customers": [], "ignore_patterns": []}

def is_private_customer(customer: Dict[str, Any]) -> bool:
    """
    Prüft ob ein Kunde ein privater Kunde ist, der ignoriert werden soll
    
    Args:
        customer: Kunden-Dictionary mit name, address, etc.
        
    Returns:
        True wenn Kunde ignoriert werden soll, False sonst
    """
    ignore_config = load_ignore_list()
    
    # 1. Prüfe explizite Kunden-Namen
    customer_name = customer.get('name', '').strip()
    for private_customer in ignore_config.get('private_customers', []):
        if private_customer['name'].lower() in customer_name.lower():
            return True
    
    # 2. Prüfe Ignor-Patterns in der Adresse
    address = customer.get('address', '')
    for pattern in ignore_config.get('ignore_patterns', []):
        if pattern.lower() in address.lower():
            return True
    
    # 3. Prüfe auf unvollständige Daten (nan, None, leere Werte)
    # Nur ignorieren wenn ALLE Adresskomponenten fehlen
    street = customer.get('street', '').strip()
    postal_code = customer.get('postal_code', '').strip()
    city = customer.get('city', '').strip()
    
    # Ignoriere nur wenn alle Adresskomponenten unvollständig sind
    all_components_missing = (
        (not address or address.strip() in ['', 'nan', 'None']) and
        (not street or street in ['', 'nan', 'None']) and
        (not postal_code or postal_code in ['', 'nan', 'None']) and
        (not city or city in ['', 'nan', 'None'])
    )
    
    if all_components_missing:
        return True
    
    return False

def filter_private_customers(customers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filtert private Kunden aus der Kundenliste heraus
    
    Args:
        customers: Liste von Kunden-Dictionaries
        
    Returns:
        Gefilterte Liste ohne private Kunden
    """
    filtered_customers = []
    ignored_count = 0
    
    for customer in customers:
        if is_private_customer(customer):
            ignored_count += 1
            print(f"🚫 Ignoriert (Privatkunde): {customer.get('name', 'Unbekannt')} - {customer.get('address', 'Keine Adresse')}")
        else:
            filtered_customers.append(customer)
    
    if ignored_count > 0:
        print(f"📊 {ignored_count} private Kunden ignoriert, {len(filtered_customers)} verbleibend")
    
    return filtered_customers

def get_ignored_customers_summary() -> Dict[str, Any]:
    """Gibt eine Zusammenfassung der ignorierten Kunden zurück"""
    ignore_config = load_ignore_list()
    
    return {
        "total_ignored_patterns": len(ignore_config.get('ignore_patterns', [])),
        "total_ignored_customers": len(ignore_config.get('private_customers', [])),
        "ignored_customers": ignore_config.get('private_customers', []),
        "ignore_patterns": ignore_config.get('ignore_patterns', [])
    }
