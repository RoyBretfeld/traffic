#!/usr/bin/env python3
"""
DATENBANK-ANALYSE: Duplikate und Optimierung
"""
import sqlite3
from pathlib import Path

def analyze_database():
    """Analysiere die Datenbank auf Duplikate und Optimierungsmöglichkeiten."""
    db_path = Path('data/traffic.db')
    
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print('🔍 DATENBANK-ANALYSE:')
    print('=' * 60)
    
    # Tabellen auflisten
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    print(f'📋 Tabellen: {len(tables)}')
    for table in tables:
        print(f'   - {table[0]}')
    
    print()
    
    # geo_cache analysieren
    cursor.execute('SELECT COUNT(*) FROM geo_cache')
    total_cache = cursor.fetchone()[0]
    print(f'📊 geo_cache: {total_cache} Einträge')
    
    # Duplikate prüfen
    cursor.execute('''
        SELECT address_norm, COUNT(*) as count 
        FROM geo_cache 
        GROUP BY address_norm 
        HAVING COUNT(*) > 1
    ''')
    duplicates = cursor.fetchall()
    print(f'🔍 Duplikate in geo_cache: {len(duplicates)}')
    
    if duplicates:
        print('   Top 5 Duplikate:')
        for addr, count in duplicates[:5]:
            print(f'   - "{addr}": {count}x')
    
    # Index-Status prüfen
    cursor.execute("SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='geo_cache'")
    indexes = cursor.fetchall()
    print(f'📈 Indizes auf geo_cache: {len(indexes)}')
    for idx in indexes:
        print(f'   - {idx[0]}')
    
    # Andere Tabellen analysieren
    for table_name in ['geo_alias', 'geo_fail', 'geo_manual', 'kunden']:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
            count = cursor.fetchone()[0]
            print(f'📊 {table_name}: {count} Einträge')
            
            # Duplikate in anderen Tabellen
            cursor.execute(f'''
                SELECT address_norm, COUNT(*) as count 
                FROM {table_name} 
                GROUP BY address_norm 
                HAVING COUNT(*) > 1
            ''')
            dupes = cursor.fetchall()
            if dupes:
                print(f'   ⚠️ Duplikate: {len(dupes)}')
                
        except sqlite3.OperationalError:
            print(f'📊 {table_name}: Tabelle existiert nicht')
    
    print()
    
    # Performance-Analyse
    print('⚡ PERFORMANCE-ANALYSE:')
    print('-' * 30)
    
    # Query-Plan für häufige Abfragen
    cursor.execute('EXPLAIN QUERY PLAN SELECT * FROM geo_cache WHERE address_norm = ?', ('Test Adresse',))
    plan = cursor.fetchall()
    print('Query-Plan für geo_cache Lookup:')
    for step in plan:
        print(f'   {step[3]}')
    
    conn.close()

if __name__ == '__main__':
    analyze_database()
