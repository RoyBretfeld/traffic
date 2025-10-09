#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbank-Struktur-Check
"""

import sqlite3

def check_db_structure(db_path, db_name):
    """Prüft die Struktur einer Datenbank"""
    print(f'\n=== {db_name} ===')
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Tabellen auflisten
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        print(f'\nTabelle: {table_name}')
        
        # Spalten-Info
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        print('  Spalten:')
        for col in columns:
            print(f'    {col[1]} ({col[2]})')
        
        # Erste 2 Zeilen
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 2")
        rows = cursor.fetchall()
        print('  Erste 2 Zeilen:')
        for i, row in enumerate(rows):
            print(f'    Zeile {i+1}: {row}')
    
    conn.close()

if __name__ == "__main__":
    check_db_structure('data/customers.db', 'customers.db')
    check_db_structure('data/traffic.db', 'traffic.db')
