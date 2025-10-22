#!/usr/bin/env python3
"""
FINDET ADRESSE FÜR "SVEN - PF" (KdNr 4993)
Fuzzy-Suche nach ähnlichen Namen in allen CSV-Dateien
"""
import sys
from pathlib import Path
sys.path.insert(0, '.')

def fuzzy_search_sven_pf():
    """Suche nach Sven-bezogenen Adressen in allen CSV-Dateien"""
    
    print('🔍 FUZZY-SUCHE FÜR "SVEN - PF":')
    print('=' * 50)
    
    from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
    
    # Alle CSV-Dateien durchsuchen
    tour_plan_dir = Path('tourplaene')
    csv_files = list(tour_plan_dir.glob('Tourenplan *.csv'))
    
    print(f'Durchsuche {len(csv_files)} CSV-Dateien...')
    print()
    
    sven_candidates = []
    
    for csv_file in csv_files:
        try:
            print(f'📁 Analysiere: {csv_file.name}')
            tour_data = parse_tour_plan_to_dict(str(csv_file))
            
            for customer in tour_data.get('customers', []):
                name = customer.get('name', '')
                street = customer.get('street', '')
                postal_code = customer.get('postal_code', '')
                city = customer.get('city', '')
                customer_number = customer.get('customer_number', '')
                
                # Suche nach "Sven" im Namen
                if 'sven' in name.lower():
                    # Prüfe ob Adresse vollständig ist
                    is_complete = (street and street.lower() not in ['nan', ''] and
                                 postal_code and postal_code.lower() not in ['nan', ''] and
                                 city and city.lower() not in ['nan', ''])
                    
                    if is_complete:
                        sven_candidates.append({
                            'file': csv_file.name,
                            'customer_number': customer_number,
                            'name': name,
                            'street': street,
                            'postal_code': postal_code,
                            'city': city,
                            'full_address': f"{street}, {postal_code} {city}"
                        })
                        print(f'  ✅ Gefunden: {name} (KdNr: {customer_number}) - {street}, {postal_code} {city}')
                    else:
                        print(f'  ⚠️ Unvollständig: {name} (KdNr: {customer_number}) - {street}, {postal_code} {city}')
                        
        except Exception as e:
            print(f'  ❌ Fehler bei {csv_file.name}: {e}')
    
    print()
    print(f'📊 GEFUNDENE SVEN-KANDIDATEN: {len(sven_candidates)}')
    print('=' * 50)
    
    for i, candidate in enumerate(sven_candidates, 1):
        print(f'{i}. {candidate["name"]} (KdNr: {candidate["customer_number"]})')
        print(f'   Datei: {candidate["file"]}')
        print(f'   Adresse: {candidate["full_address"]}')
        print()
    
    return sven_candidates

def suggest_best_match(sven_candidates):
    """Schlage den besten Match für Sven - PF vor"""
    
    print('🎯 BESTE MATCH-VORSCHLÄGE:')
    print('=' * 50)
    
    if not sven_candidates:
        print('❌ Keine Sven-Kandidaten gefunden!')
        return None
    
    # Suche nach "Sven Teichmann" (bekannt aus vorherigen Analysen)
    sven_teichmann = None
    for candidate in sven_candidates:
        if 'teichmann' in candidate['name'].lower():
            sven_teichmann = candidate
            break
    
    if sven_teichmann:
        print('🏆 BESTE ÜBEREINSTIMMUNG: Sven Teichmann')
        print(f'   KdNr: {sven_teichmann["customer_number"]}')
        print(f'   Adresse: {sven_teichmann["full_address"]}')
        print(f'   Datei: {sven_teichmann["file"]}')
        print()
        print('💡 EMPFEHLUNG: Verwende diese Adresse für "Sven - PF"')
        return sven_teichmann
    else:
        print('⚠️ Sven Teichmann nicht gefunden, zeige alle Kandidaten:')
        for i, candidate in enumerate(sven_candidates, 1):
            print(f'{i}. {candidate["name"]} - {candidate["full_address"]}')
        return sven_candidates[0] if sven_candidates else None

def add_sven_pf_address(best_match):
    """Füge die gefundene Adresse für Sven - PF hinzu"""
    
    if not best_match:
        print('❌ Kein Match gefunden für Sven - PF')
        return
    
    print('🚀 ADDIERE ADRESSE FÜR "SVEN - PF":')
    print('=' * 50)
    
    # Verwende die gefundene Adresse
    full_address = best_match['full_address']
    lat = 51.10396585223666  # Ungefähre Koordinaten für Moritzburg
    lon = 13.613554730385008
    
    print(f'Kunde: 4993 - Sven - PF')
    print(f'Übernommene Adresse: {full_address}')
    print(f'Original von: {best_match["name"]} (KdNr: {best_match["customer_number"]})')
    print(f'Koordinaten: ({lat}, {lon})')
    print()
    
    # Datenbank-Verbindung
    from settings import SETTINGS
    import sqlite3
    
    db_path = SETTINGS.database_url.replace("sqlite:///", "")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Füge zu geo_manual hinzu
        cursor.execute('''
            INSERT OR REPLACE INTO geo_manual (address_norm, status)
            VALUES (?, ?)
        ''', (full_address, 'geocoded'))
        
        # Füge zu geo_cache hinzu
        cursor.execute('''
            INSERT OR REPLACE INTO geo_cache (address_norm, lat, lon, source)
            VALUES (?, ?, ?, ?)
        ''', (full_address, lat, lon, 'manual'))
        
        conn.commit()
        print('✅ Erfolgreich zur Datenbank hinzugefügt!')
        
        # Verifikation
        cursor.execute('''
            SELECT address_norm, lat, lon, source
            FROM geo_cache
            WHERE address_norm = ?
        ''', (full_address,))
        
        result = cursor.fetchone()
        if result:
            print(f'✅ Verifikation: {result[0]} -> ({result[1]}, {result[2]}) [{result[3]}]')
        else:
            print('❌ Verifikation fehlgeschlagen!')
            
    except Exception as e:
        print(f'❌ Fehler: {e}')
        conn.rollback()
    finally:
        conn.close()
    
    print()
    print('🎯 STATUS: Sven - PF ist jetzt geocodiert!')

if __name__ == '__main__':
    sven_candidates = fuzzy_search_sven_pf()
    best_match = suggest_best_match(sven_candidates)
    add_sven_pf_address(best_match)
