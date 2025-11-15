#!/usr/bin/env python3
"""
DATENBANK-OPTIMIERUNG: Vorschläge und Implementierung
"""
import sqlite3
from pathlib import Path

def database_optimization_analysis():
    """Analysiere Optimierungsmöglichkeiten für die Datenbank."""
    db_path = Path('data/traffic.db')
    
    if not db_path.exists():
        print("❌ Datenbank nicht gefunden!")
        return
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    
    print('🚀 DATENBANK-OPTIMIERUNG:')
    print('=' * 60)
    
    # 1. Aktuelle Struktur analysieren
    print('📋 AKTUELLE STRUKTUR:')
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = cursor.fetchall()
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        
        print(f'   {table_name}: {count} Einträge, {len(columns)} Spalten')
        for col in columns:
            print(f'     - {col[1]} ({col[2]})')
    
    print()
    
    # 2. Index-Analyse
    print('📈 INDEX-ANALYSE:')
    cursor.execute("SELECT name, tbl_name FROM sqlite_master WHERE type='index'")
    indexes = cursor.fetchall()
    
    for idx_name, tbl_name in indexes:
        if not idx_name.startswith('sqlite_autoindex'):
            print(f'   ✅ {idx_name} auf {tbl_name}')
        else:
            print(f'   🔄 Auto-Index: {idx_name} auf {tbl_name}')
    
    print()
    
    # 3. Performance-Tests
    print('⚡ PERFORMANCE-TESTS:')
    
    # Test 1: Geo-Cache Lookup
    import time
    start_time = time.time()
    cursor.execute('SELECT * FROM geo_cache WHERE address_norm = ?', ('Test',))
    result = cursor.fetchone()
    lookup_time = time.time() - start_time
    print(f'   Geo-Cache Lookup: {lookup_time*1000:.2f}ms')
    
    # Test 2: Alle Adressen durchsuchen
    start_time = time.time()
    cursor.execute('SELECT COUNT(*) FROM geo_cache')
    count = cursor.fetchone()[0]
    scan_time = time.time() - start_time
    print(f'   Full Table Scan: {scan_time*1000:.2f}ms ({count} Einträge)')
    
    print()
    
    # 4. Optimierungsvorschläge
    print('💡 OPTIMIERUNGSVORSCHLÄGE:')
    print('-' * 30)
    
    # Vorschlag 1: Zusätzliche Indizes
    print('1. 📈 ZUSÄTZLICHE INDIZES:')
    print('   - Index auf lat/lon für räumliche Abfragen')
    print('   - Index auf source für Filterung')
    print('   - Index auf updated_at für Zeit-basierte Abfragen')
    
    # Vorschlag 2: Tabellen-Konsolidierung
    print('\n2. 🔄 TABELLEN-KONSOLIDIERUNG:')
    print('   - geo_cache, geo_alias, geo_fail, geo_manual → geo_unified')
    print('   - Einheitliche Struktur mit Status-Feld')
    print('   - Reduzierte Komplexität')
    
    # Vorschlag 3: Datenbereinigung
    print('\n3. 🧹 DATENBEREINIGUNG:')
    print('   - Leere Adressen entfernen')
    print('   - Ähnliche Adressen zusammenführen')
    print('   - Veraltete Einträge archivieren')
    
    # Vorschlag 4: Partitionierung
    print('\n4. 📦 PARTITIONIERUNG:')
    print('   - Nach Regionen (Sachsen vs. außerhalb)')
    print('   - Nach Zeit (aktuelle vs. historische)')
    print('   - Nach Quelle (geocoded vs. manual)')
    
    print()
    
    # 5. Konkrete Implementierung
    print('🛠️ KONKRETE IMPLEMENTIERUNG:')
    print('-' * 30)
    
    print('SQL für zusätzliche Indizes:')
    print('''
    -- Räumlicher Index
    CREATE INDEX IF NOT EXISTS idx_geo_cache_spatial 
    ON geo_cache (lat, lon);
    
    -- Source-Index
    CREATE INDEX IF NOT EXISTS idx_geo_cache_source 
    ON geo_cache (source);
    
    -- Zeit-Index
    CREATE INDEX IF NOT EXISTS idx_geo_cache_updated 
    ON geo_cache (updated_at);
    ''')
    
    print('SQL für Tabellen-Konsolidierung:')
    print('''
    CREATE TABLE geo_unified (
        address_norm TEXT PRIMARY KEY,
        lat DOUBLE PRECISION NOT NULL,
        lon DOUBLE PRECISION NOT NULL,
        source TEXT DEFAULT 'geocoded',
        status TEXT DEFAULT 'active',  -- active, failed, manual, alias
        by_user TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        original_address TEXT,  -- ursprüngliche Adresse vor Normalisierung
        confidence REAL DEFAULT 1.0  -- Vertrauen in die Geocodierung
    );
    ''')
    
    conn.close()

if __name__ == '__main__':
    database_optimization_analysis()
