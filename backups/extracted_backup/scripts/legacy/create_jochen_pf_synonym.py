#!/usr/bin/env python3
"""
Erstellt Synonym für Jochen - PF mit leerer Adresse
"""
import sys
sys.path.append('.')

from backend.db.dao import _connect
from repositories.geo_repo import normalize_addr

def create_jochen_pf_synonym():
    """Erstellt Synonym für Jochen - PF mit leerer Adresse"""
    
    print("🔄 ERSTELLE JOCHEEN - PF SYNONYM:")
    print("=" * 50)
    
    # Synonym-Mapping
    synonym_address = ""  # Leere Adresse aus CSV
    canonical_address = "baerensteiner str. 27-29, 01277 dresden"  # Echte Adresse aus DB
    lat = 51.0353473
    lon = 13.8031489
    
    print(f'Synonym (leer): "{synonym_address}"')
    print(f'Kanonisch: "{canonical_address}"')
    print(f'Koordinaten: ({lat}, {lon})')
    print()
    
    conn = _connect()
    cursor = conn.cursor()
    
    try:
        # 1. Normalisiere Adressen
        synonym_norm = normalize_addr(synonym_address)
        canonical_norm = normalize_addr(canonical_address)
        
        print(f"Normalisiert:")
        print(f"  Synonym: '{synonym_norm}'")
        print(f"  Kanonisch: '{canonical_norm}'")
        
        # 2. Füge zu geo_alias hinzu
        cursor.execute("""
            INSERT OR REPLACE INTO geo_alias (address_norm, canonical_norm, created_at, created_by)
            VALUES (?, ?, datetime('now'), 'jochen_pf_fix')
        """, (synonym_norm, canonical_norm))
        
        print(f"✅ Synonym hinzugefügt: '{synonym_norm}' -> '{canonical_norm}'")
        
        # 3. Stelle sicher, dass kanonische Adresse in geo_cache ist
        cursor.execute("""
            INSERT OR REPLACE INTO geo_cache (address_norm, lat, lon, source, updated_at)
            VALUES (?, ?, ?, 'synonym_fix', datetime('now'))
        """, (canonical_norm, lat, lon))
        
        print(f"✅ Kanonische Adresse in Cache: '{canonical_norm}' -> ({lat}, {lon})")
        
        # 4. Commit
        conn.commit()
        
        print("\n🎯 STATUS: Jochen - PF Synonym erstellt!")
        print("🎯 Jetzt sollte 'Jochen - PF' mit leerer Adresse zur echten Adresse gemappt werden!")
        
    except Exception as e:
        print(f"❌ Fehler: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    create_jochen_pf_synonym()
