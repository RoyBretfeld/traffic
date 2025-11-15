#!/usr/bin/env python3
"""
DIREKTER TEST DER API-LOGIK OHNE HTTP
"""
import sys
import asyncio
from pathlib import Path
sys.path.insert(0, '.')

async def test_direct_api_logic():
    """Teste die API-Logik direkt ohne HTTP"""
    
    try:
        from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
        from repositories.geo_repo import bulk_get
        from repositories.geo_alias_repo import resolve_aliases
        from common.normalize import normalize_address
        import unicodedata
        import re
        
        print('🔍 DIREKTER TEST DER API-LOGIK:')
        print('=' * 50)
        
        # 1) CSV mit modernem Parser lesen
        csv_file = 'tourplaene/Tourenplan 01.09.2025.csv'
        tour_data = parse_tour_plan_to_dict(csv_file)
        
        print(f'Kunden gefunden: {len(tour_data["customers"])}')
        
        # 2) Adressen normalisieren
        def _norm(s: str) -> str:
            s = unicodedata.normalize("NFC", (s or ""))
            s = re.sub(r"\s+", " ", s).strip()
            return s
        
        addrs = []
        for customer in tour_data["customers"]:
            if 'address' in customer and customer['address']:
                full_address = customer['address']
            else:
                full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
            addrs.append(normalize_address(full_address))
        
        print(f'Adressen normalisiert: {len(addrs)}')
        
        # 3) Alias-Auflösung und DB-Lookup
        aliases = resolve_aliases(addrs)
        geo = bulk_get(addrs + list(aliases.values()))
        
        print(f'Geo-Cache Treffer: {len(geo)}')
        
        # 4) Suche nach CAR - Center
        car_customers = []
        for i, customer in enumerate(tour_data["customers"]):
            if 'CAR' in customer.get('name', '') or 'Center' in customer.get('name', ''):
                car_customers.append((i, customer))
        
        print(f'\\n🔍 CAR - CENTER KUNDEN GEFUNDEN: {len(car_customers)}')
        
        for i, customer in car_customers:
            if 'address' in customer and customer['address']:
                full_address = customer['address']
            else:
                full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
            
            addr_norm = _norm(full_address)
            canon = aliases.get(addr_norm)
            rec = geo.get(addr_norm) or (geo.get(canon) if canon else None)
            has_geo = rec is not None
            
            print(f'  Kunde: {customer.get("name", "Unbekannt")}')
            print(f'  Adresse: {addr_norm}')
            print(f'  Has Geo: {has_geo}')
            print(f'  Geo: {rec}')
            print(f'  Alias: {canon}')
            print()
        
        # 5. Prüfe alle problematischen Adressen
        problem_count = 0
        for i, customer in enumerate(tour_data["customers"]):
            if 'address' in customer and customer['address']:
                full_address = customer['address']
            else:
                full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
            
            addr_norm = _norm(full_address)
            canon = aliases.get(addr_norm)
            rec = geo.get(addr_norm) or (geo.get(canon) if canon else None)
            has_geo = rec is not None
            
            if not has_geo:
                problem_count += 1
                if problem_count <= 5:  # Nur erste 5 anzeigen
                    print(f'❌ {customer.get("name", "Unbekannt")}: {addr_norm[:50]}...')
        
        print(f'\\n📊 ZUSAMMENFASSUNG:')
        print(f'  Gesamt Kunden: {len(tour_data["customers"])}')
        print(f'  Mit Geo-Daten: {len([c for c in tour_data["customers"] if True]) - problem_count}')
        print(f'  Ohne Geo-Daten: {problem_count}')
        print(f'  Erkennungsrate: {((len(tour_data["customers"]) - problem_count) / len(tour_data["customers"]) * 100):.1f}%')
        
    except Exception as e:
        print(f'❌ Fehler: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    asyncio.run(test_direct_api_logic())
