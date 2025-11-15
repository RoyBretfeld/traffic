"""
Helper-Funktionen für Kunden-Datenbank-Operationen.
Extrahiert aus app.py für bessere Wartbarkeit.
"""
import sqlite3
import os
from typing import Optional


def _normalize_string(s: str) -> str:
    """Normalisiert String für Datenbank-Suche."""
    if not s:
        return ""
    return s.lower().strip()


def _search_in_customers_db(name: str, street: str, city: str) -> Optional[int]:
    """
    Sucht Kunde in customers.db.
    
    Args:
        name: Kundenname
        street: Straße
        city: Stadt
        
    Returns:
        Kunden-ID oder None
    """
    if not os.path.exists('data/customers.db'):
        return None
    
    try:
        conn = sqlite3.connect('data/customers.db')
        cursor = conn.cursor()
        
        normalized_name = _normalize_string(name)
        normalized_street = _normalize_string(street)
        normalized_city = _normalize_string(city)
        
        # Verschiedene Suchstrategien
        queries = [
            ("SELECT id FROM customers WHERE LOWER(name) LIKE ? AND "
             "LOWER(street) LIKE ? AND LOWER(city) LIKE ?",
             (f'%{normalized_name}%', f'%{normalized_street}%', f'%{normalized_city}%')),
            ("SELECT id FROM customers WHERE LOWER(name) LIKE ? AND LOWER(street) LIKE ?",
             (f'%{normalized_name}%', f'%{normalized_street}%')),
            ("SELECT id FROM customers WHERE LOWER(name) LIKE ? AND LOWER(city) LIKE ?",
             (f'%{normalized_name}%', f'%{normalized_city}%'))
        ]
        
        for query, params in queries:
            try:
                cursor.execute(query, params)
                result = cursor.fetchone()
                if result:
                    conn.close()
                    print(f"[DB-SUCCESS] Kunde gefunden in customers.db: ID {result[0]}")
                    return result[0]
            except sqlite3.OperationalError:
                continue
        
        conn.close()
        return None
    except Exception as e:
        print(f"[DB-ERROR] Fehler bei customers.db-Suche: {e}")
        return None


def _search_in_traffic_db(name: str, street: str, city: str) -> Optional[int]:
    """
    Sucht Kunde in traffic.db.
    
    Args:
        name: Kundenname
        street: Straße
        city: Stadt (wird nicht verwendet, aber für Konsistenz)
        
    Returns:
        Kunden-ID oder None
    """
    if not os.path.exists('data/traffic.db'):
        return None
    
    try:
        conn = sqlite3.connect('data/traffic.db')
        cursor = conn.cursor()
        
        normalized_name = _normalize_string(name)
        normalized_street = _normalize_string(street)
        
        # Suche nach Name und Adresse
        cursor.execute(
            "SELECT id FROM kunden WHERE LOWER(name) LIKE ? AND LOWER(adresse) LIKE ?",
            (f'%{normalized_name}%', f'%{normalized_street}%')
        )
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            print(f"[DB-SUCCESS] Kunde gefunden in traffic.db: ID {result[0]}")
            return result[0]
        
        return None
    except Exception as e:
        print(f"[DB-ERROR] Fehler bei traffic.db-Suche: {e}")
        return None


def get_kunde_id_by_name_adresse(name: str, street: str, city: str) -> Optional[int]:
    """
    Sucht Kunde-ID nach Name und Adresse in der Datenbank.
    Prüft zuerst customers.db, dann traffic.db als Fallback.
    
    Args:
        name: Kundenname
        street: Straße
        city: Stadt
        
    Returns:
        Kunden-ID oder None wenn nicht gefunden
    """
    # Prüfe customers.db zuerst
    result = _search_in_customers_db(name, street, city)
    if result:
        return result
    
    # Prüfe traffic.db als Fallback
    result = _search_in_traffic_db(name, street, city)
    if result:
        return result
    
    print(f"[DB-INFO] Kein Kunde gefunden für: {name}, {street}, {city}")
    return None

