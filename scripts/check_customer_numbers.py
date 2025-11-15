#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Prüft vierstellige Kundennummern aus der Synonym-Tabelle gegen vorhandene Datenbanken.
"""

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import sqlite3
from backend.services.synonyms import SynonymStore

def check_customer_numbers():
    """Prüft Kundennummern in verschiedenen Tabellen"""
    
    # Datenbank-Pfad
    db_path = PROJECT_ROOT / "data" / "traffic.db"
    if not db_path.exists():
        print(f"[FEHLER] Datenbank nicht gefunden: {db_path}")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    # Hole alle Synonyme mit real_customer_id aus address_synonyms Tabelle
    cursor.execute("SELECT DISTINCT customer_id FROM address_synonyms WHERE customer_id IS NOT NULL AND customer_id != ''")
    customer_ids = set()
    for row in cursor.fetchall():
        cust_id = str(row[0]).strip()
        if cust_id.isdigit() and len(cust_id) >= 4:
            customer_ids.add(int(cust_id))
    
    # Sortiere
    customer_ids = sorted(customer_ids)
    
    print(f"[INFO] Gefundene Kundennummern aus Synonym-Tabelle: {len(customer_ids)}")
    print(f"[INFO] Nummern: {', '.join(map(str, customer_ids))}\n")
    
    # Prüfe verschiedene Tabellen
    tables_to_check = [
        ('kunden', 'id'),
        ('customers', 'id'),
        ('address_synonyms', 'customer_id'),
    ]
    
    found_in_db = {}
    missing_in_db = []
    
    for table_name, id_column in tables_to_check:
        try:
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if cursor.fetchone():
                # Tabelle existiert
                print(f"[CHECK] Prüfe Tabelle: {table_name}")
                
                # Versuche verschiedene Spaltennamen
                possible_id_columns = [id_column, 'kundennr', 'customer_number', 'customer_id']
                
                for col_name in possible_id_columns:
                    try:
                        cursor.execute(f"PRAGMA table_info({table_name})")
                        columns = [row[1] for row in cursor.fetchall()]
                        
                        if col_name in columns:
                            # Spalte existiert
                            for cust_id in customer_ids:
                                query = f"SELECT * FROM {table_name} WHERE {col_name} = ?"
                                cursor.execute(query, (str(cust_id),))
                                result = cursor.fetchone()
                                
                                if result:
                                    if cust_id not in found_in_db:
                                        found_in_db[cust_id] = []
                                    found_in_db[cust_id].append({
                                        'table': table_name,
                                        'column': col_name,
                                        'row': result
                                    })
                                    print(f"  [OK] KdNr {cust_id} gefunden in {table_name}.{col_name}")
                        else:
                            # Spalte nicht vorhanden
                            continue
                    except Exception as e:
                        continue
                
        except Exception as e:
            print(f"[WARN] Fehler bei Tabelle {table_name}: {e}")
            continue
    
    # Zusammenfassung
    print("\n" + "="*60)
    print("ZUSAMMENFASSUNG")
    print("="*60)
    
    for cust_id in customer_ids:
        if cust_id in found_in_db:
            locations = ', '.join([f"{loc['table']}.{loc['column']}" for loc in found_in_db[cust_id]])
            print(f"[OK] KdNr {cust_id}: Gefunden in {locations}")
        else:
            missing_in_db.append(cust_id)
            print(f"[FEHLT] KdNr {cust_id}: NICHT in Datenbank gefunden")
    
    print(f"\n[INFO] Gefunden: {len(found_in_db)} / {len(customer_ids)}")
    print(f"[INFO] Fehlend: {len(missing_in_db)}")
    
    if missing_in_db:
        print(f"\n[INFO] Fehlende Kundennummern: {', '.join(map(str, missing_in_db))}")
        print("[INFO] Diese Nummern könnten in einer externen Kundenstamm-Datenbank sein.")
    
    conn.close()

if __name__ == "__main__":
    check_customer_numbers()

