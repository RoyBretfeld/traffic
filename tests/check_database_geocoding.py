#!/usr/bin/env python3
"""
Prüft die Datenbank auf Kunden ohne Geokoordinaten
"""
import sys
import sqlite3
sys.path.insert(0, '.')

from pathlib import Path
from backend.db.config import get_database_path

db_path = get_database_path()

if not Path(db_path).exists():
    print(f"[FEHLER] Datenbank nicht gefunden: {db_path}")
    sys.exit(1)

print(f"\n{'='*80}")
print(f"DATENBANK GEOCODING-ANALYSE")
print(f"{'='*80}\n")
print(f"Datenbank: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Prüfe welche Tabellen existieren
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"Gefundene Tabellen: {', '.join(tables)}\n")

results = {}

# Prüfe kunden-Tabelle
if 'kunden' in tables:
    print(f"{'='*80}")
    print(f"TABELLE: kunden")
    print(f"{'='*80}\n")
    
    # Gesamtanzahl
    cursor.execute("SELECT COUNT(*) FROM kunden")
    total = cursor.fetchone()[0]
    
    # Mit Koordinaten (nicht NULL und nicht 0)
    cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NOT NULL AND lon IS NOT NULL AND lat != 0 AND lon != 0")
    with_coords = cursor.fetchone()[0]
    
    # Ohne Koordinaten
    cursor.execute("SELECT COUNT(*) FROM kunden WHERE lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0")
    without_coords = cursor.fetchone()[0]
    
    print(f"Gesamt: {total} Kunden")
    print(f"  [OK] Mit Koordinaten: {with_coords} ({with_coords/total*100:.1f}%)")
    print(f"  [X] Ohne Koordinaten: {without_coords} ({without_coords/total*100:.1f}%)")
    
    results['kunden'] = {
        'total': total,
        'with_coords': with_coords,
        'without_coords': without_coords
    }
    
    # Details zu Kunden ohne Koordinaten
    if without_coords > 0:
        print(f"\n{'='*80}")
        print(f"KUNDEN OHNE KOORDINATEN ({without_coords}):")
        print(f"{'='*80}\n")
        
        cursor.execute("""
            SELECT id, name, adresse, lat, lon 
            FROM kunden 
            WHERE lat IS NULL OR lon IS NULL OR lat = 0 OR lon = 0
            ORDER BY name
            LIMIT 100
        """)
        
        no_coords_customers = cursor.fetchall()
        
        output_file = Path("database_missing_geocoding.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("DATENBANK - KUNDEN OHNE GEOKOORDINATEN\n")
            f.write("="*80 + "\n\n")
            
            for i, (cid, name, adresse, lat, lon) in enumerate(no_coords_customers, 1):
                # Schreibe in Datei (unterstützt UTF-8)
                f.write(f"{i}. {name} (ID: {cid})\n")
                f.write(f"   Adresse: {adresse}\n")
                f.write(f"   Koordinaten: lat={lat}, lon={lon}\n")
                f.write(f"   Korrektur: _________________________\n\n")
            
            print(f"[INFO] {len(no_coords_customers)} Kunden ohne Koordinaten gefunden")
        
        if without_coords > 100:
            print(f"... und {without_coords - 100} weitere")
            print(f"\n[INFO] Nur die ersten 100 angezeigt. Gesamt: {without_coords}")
        
        print(f"\n[EXPORT] Liste exportiert nach: {output_file}")

# Prüfe customers-Tabelle (falls vorhanden)
if 'customers' in tables:
    print(f"\n{'='*80}")
    print(f"TABELLE: customers")
    print(f"{'='*80}\n")
    
    cursor.execute("SELECT COUNT(*) FROM customers")
    total = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customers WHERE latitude IS NOT NULL AND longitude IS NOT NULL AND latitude != 0 AND longitude != 0")
    with_coords = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM customers WHERE latitude IS NULL OR longitude IS NULL OR latitude = 0 OR longitude = 0")
    without_coords = cursor.fetchone()[0]
    
    print(f"Gesamt: {total} Eintraege")
    print(f"  [OK] Mit Koordinaten: {with_coords} ({with_coords/total*100:.1f}%)")
    print(f"  [X] Ohne Koordinaten: {without_coords} ({without_coords/total*100:.1f}%)")
    
    results['customers'] = {
        'total': total,
        'with_coords': with_coords,
        'without_coords': without_coords
    }

conn.close()

# Zusammenfassung
print(f"\n\n{'='*80}")
print(f"ZUSAMMENFASSUNG")
print(f"{'='*80}\n")

for table_name, data in results.items():
    print(f"{table_name.upper()}:")
    print(f"  Erfolgsrate: {data['with_coords']/data['total']*100:.1f}%")
    print(f"  {data['with_coords']} von {data['total']} mit Koordinaten")
    if data['without_coords'] > 0:
        print(f"  -> {data['without_coords']} benoetigen Geocoding")
    print()

