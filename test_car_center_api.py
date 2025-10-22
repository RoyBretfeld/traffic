#!/usr/bin/env python3
"""
TESTE API-ENDPOINT FÜR CAR - CENTER PROBLEM
"""
import sys
import asyncio
sys.path.insert(0, '.')

async def test_car_center_api():
    """Teste den API-Endpoint für CAR - Center Problem"""
    
    try:
        from routes.tourplan_match import api_tourplan_match
        
        print('🔍 TESTE API-ENDPOINT:')
        print('=' * 50)
        
        result = await api_tourplan_match('Tourenplan 01.09.2025.csv')
        
        print(f'Gesamt Zeilen: {result["rows"]}')
        print(f'OK: {result["ok"]}')
        print(f'WARN: {result["warn"]}')
        print(f'BAD: {result["bad"]}')
        print()
        
        # Suche nach CAR - Center
        car_items = [item for item in result['items'] 
                    if 'CAR' in item.get('customer_name', '') or 'Center' in item.get('customer_name', '')]
        
        print('🔍 CAR - CENTER ITEMS:')
        for item in car_items:
            print(f'  Kunde: {item["customer_name"]}')
            print(f'  Adresse: {item["address"]}')
            print(f'  Status: {item["status"]}')
            print(f'  Has Geo: {item["has_geo"]}')
            print(f'  Geo: {item["geo"]}')
            print()
        
        # Prüfe alle Items mit Status "warn" oder "bad"
        problem_items = [item for item in result['items'] 
                        if item['status'] in ['warn', 'bad']]
        
        print(f'🚨 PROBLEMATISCHE ITEMS ({len(problem_items)}):')
        for item in problem_items[:5]:  # Nur erste 5 anzeigen
            print(f'  {item["customer_name"]}: {item["status"]} - {item["address"][:50]}...')
        
        return result
        
    except Exception as e:
        print(f'❌ Fehler: {e}')
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    asyncio.run(test_car_center_api())
