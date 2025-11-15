#!/usr/bin/env python3
"""
ANALYSE DER FEHLGESCHLAGENEN GEOCODIERUNGEN
"""
import sqlite3
from pathlib import Path

def analyze_failed_geocoding():
    """Analysiere die fehlgeschlagenen Geocodierungen."""
    db_path = Path('data/traffic.db')
    
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print('🔍 ANALYSE DER FEHLGESCHLAGENEN GEOCODIERUNGEN:')
    print('=' * 60)
    
    # Alle fehlgeschlagenen Geocodierungen abrufen
    cursor.execute('''
        SELECT address_norm, reason, until, updated_at 
        FROM geo_fail 
        ORDER BY updated_at DESC
    ''')
    failed_addresses = cursor.fetchall()
    
    print(f'📊 Gesamt fehlgeschlagene Adressen: {len(failed_addresses)}')
    print()
    
    # Gruppiere nach Grund
    cursor.execute('''
        SELECT reason, COUNT(*) as count 
        FROM geo_fail 
        GROUP BY reason 
        ORDER BY count DESC
    ''')
    reasons = cursor.fetchall()
    
    print('📋 GRÜNDE FÜR FEHLGESCHLAGENE GEOCODIERUNGEN:')
    print('-' * 50)
    for reason, count in reasons:
        print(f'   {reason}: {count}x')
    
    print()
    
    # Detaillierte Liste aller fehlgeschlagenen Adressen
    print('📋 ALLE FEHLGESCHLAGENEN ADRESSEN:')
    print('-' * 50)
    
    for i, (address, reason, until, updated_at) in enumerate(failed_addresses, 1):
        print(f'{i:2d}. "{address}"')
        print(f'    Grund: {reason}')
        print(f'    Bis: {until}')
        print(f'    Aktualisiert: {updated_at}')
        print()
    
    # Prüfe ob diese Adressen jetzt erfolgreich geocodiert werden können
    print('🔍 PRÜFUNG: Können diese Adressen jetzt geocodiert werden?')
    print('-' * 50)
    
    successful_now = 0
    still_failed = 0
    
    for address, reason, until, updated_at in failed_addresses:
        # Prüfe ob Adresse jetzt in geo_cache existiert
        cursor.execute('SELECT lat, lon FROM geo_cache WHERE address_norm = ?', (address,))
        result = cursor.fetchone()
        
        if result:
            print(f'✅ "{address[:50]}..." - JETZT ERFOLGREICH')
            successful_now += 1
        else:
            print(f'❌ "{address[:50]}..." - IMMER NOCH FEHLGESCHLAGEN')
            still_failed += 1
    
    print()
    print(f'📊 ZUSAMMENFASSUNG:')
    print(f'   Jetzt erfolgreich: {successful_now}')
    print(f'   Immer noch fehlgeschlagen: {still_failed}')
    
    # Prüfe ob es ähnliche Adressen gibt, die erfolgreich geocodiert wurden
    print()
    print('🔍 ÄHNLICHE ADRESSEN IN GEO_CACHE:')
    print('-' * 50)
    
    for address, reason, until, updated_at in failed_addresses[:5]:  # Nur erste 5 prüfen
        # Suche nach ähnlichen Adressen
        cursor.execute('''
            SELECT address_norm, lat, lon 
            FROM geo_cache 
            WHERE address_norm LIKE ? 
            OR address_norm LIKE ?
            LIMIT 3
        ''', (f'%{address[:20]}%', f'%{address[-20:]}%'))
        
        similar = cursor.fetchall()
        if similar:
            print(f'Ähnlich zu "{address[:40]}...":')
            for sim_addr, lat, lon in similar:
                print(f'   ✅ "{sim_addr[:50]}..." ({lat:.6f}, {lon:.6f})')
            print()
    
    conn.close()

if __name__ == '__main__':
    analyze_failed_geocoding()
