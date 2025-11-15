#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Datenbank-Check Script
"""

import sqlite3
import os

def check_database(db_path, db_name):
    """Prüft eine SQLite-Datenbank"""
    if os.path.exists(db_path):
        print(f'TABELLEN in {db_name}:')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Tabellen auflisten
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        
        if tables:
            for table in tables:
                table_name = table[0]
                cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
                count = cursor.fetchone()[0]
                print(f'  {table_name}: {count} Einträge')
        else:
            print('  Keine Tabellen gefunden')
        
        conn.close()
    else:
        print(f'{db_name} nicht gefunden')

if __name__ == "__main__":
    print("=== DATENBANK-CHECK ===")
    print()
    
    check_database('data/customers.db', 'customers.db')
    print()
    check_database('data/traffic.db', 'traffic.db')
