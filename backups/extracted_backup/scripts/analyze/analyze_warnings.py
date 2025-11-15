#!/usr/bin/env python3
"""
Analysiere verbleibende Warnungen detailliert
"""

import repositories.geo_repo as repo
from common.normalize import normalize_address
import requests

def analyze_remaining_warnings():
    """Analysiere die verbleibenden Warnungen detailliert."""
    
    # Hole die Warnungen vom Match-Endpoint
    response = requests.get('http://localhost:8000/api/tourplan/match?file=./tourplaene/Tourenplan%2001.09.2025.csv')
    data = response.json()
    
    warnings = [item for item in data['items'] if item['status'] == 'warn']
    
    print(f"=== ANALYSE DER VERBLEIBENDEN WARNUNGEN ===")
    print(f"Anzahl Warnungen: {len(warnings)}")
    print()
    
    categories = {
        "mojibake": [],
        "incomplete": [],
        "out_of_region": [],
        "not_in_cache": [],
        "other": []
    }
    
    for i, warning in enumerate(warnings[:10]):  # Erste 10 analysieren
        address = warning['resolved_address']
        display_name = warning['display_name']
        
        print(f"{i+1}. {display_name}")
        print(f"   Adresse: {address}")
        
        # Normalisiere die Adresse
        normalized = normalize_address(address)
        
        # Cache-Lookup
        cache_result = repo.bulk_get([normalized])
        
        if cache_result:
            geo = cache_result[normalized]
            print(f"   ✅ Cache gefunden: ({geo['lat']}, {geo['lon']}) [{geo['src']}]")
            categories["not_in_cache"].append((address, "Cache gefunden aber trotzdem Warn"))
        else:
            print(f"   ❌ Nicht im Cache")
            
            # Kategorisiere das Problem
            if "??" in address:
                categories["mojibake"].append((address, "Mojibake nicht korrigiert"))
                print(f"   🔍 Problem: Mojibake-Zeichen")
            elif len(address.split(",")) < 2:
                categories["incomplete"].append((address, "Unvollständige Adresse"))
                print(f"   🔍 Problem: Unvollständige Adresse")
            elif any(city in address for city in ["Wetzlar", "Hamburg", "München", "Mainz"]):
                categories["out_of_region"].append((address, "Außerhalb der Region"))
                print(f"   🔍 Problem: Außerhalb der Region")
            else:
                categories["other"].append((address, "Unbekanntes Problem"))
                print(f"   🔍 Problem: Unbekannt")
        
        print()
    
    # Zusammenfassung
    print("=== ZUSAMMENFASSUNG ===")
    for category, items in categories.items():
        if items:
            print(f"{category.upper()}: {len(items)} Adressen")
            for addr, reason in items[:3]:  # Erste 3 Beispiele
                print(f"  - {addr} ({reason})")
            if len(items) > 3:
                print(f"  ... und {len(items) - 3} weitere")
            print()

if __name__ == "__main__":
    analyze_remaining_warnings()
