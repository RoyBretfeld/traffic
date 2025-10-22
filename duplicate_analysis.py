#!/usr/bin/env python3
"""
DETAILLIERTE DUPLIKAT-ANALYSE
"""
import sqlite3
from pathlib import Path

def detailed_duplicate_analysis():
    """Detaillierte Analyse aller Tabellen auf Duplikate."""
    db_path = Path('data/traffic.db')
    
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print('🔍 DETAILLIERTE DUPLIKAT-ANALYSE:')
    print('=' * 60)
    
    # Prüfe alle Tabellen auf Duplikate
    tables = ['geo_cache', 'geo_alias', 'geo_fail', 'geo_manual', 'kunden']
    
    for table in tables:
        try:
            cursor.execute(f'SELECT COUNT(*) FROM {table}')
            total = cursor.fetchone()[0]
            
            # Prüfe auf Duplikate basierend auf address_norm
            cursor.execute(f'''
                SELECT address_norm, COUNT(*) as count 
                FROM {table} 
                WHERE address_norm IS NOT NULL
                GROUP BY address_norm 
                HAVING COUNT(*) > 1
            ''')
            duplicates = cursor.fetchall()
            
            print(f'📊 {table}:')
            print(f'   Gesamt: {total} Einträge')
            print(f'   Duplikate: {len(duplicates)}')
            
            if duplicates:
                print('   Beispiele:')
                for addr, count in duplicates[:3]:
                    print(f'     - "{addr[:50]}...": {count}x')
            print()
            
        except sqlite3.OperationalError as e:
            print(f'❌ {table}: {e}')
            print()
    
    # Prüfe auf ähnliche Adressen (fuzzy duplicates)
    print('🔍 FUZZY DUPLIKATE (ähnliche Adressen):')
    print('-' * 40)
    
    cursor.execute('''
        SELECT address_norm, COUNT(*) as count
        FROM geo_cache 
        GROUP BY address_norm
        ORDER BY count DESC
        LIMIT 10
    ''')
    frequent_addresses = cursor.fetchall()
    
    print('Häufigste Adressen:')
    for addr, count in frequent_addresses:
        print(f'   {count}x: "{addr[:60]}..."')
    
    conn.close()

if __name__ == '__main__':
    detailed_duplicate_analysis()
