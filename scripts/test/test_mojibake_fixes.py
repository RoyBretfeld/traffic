#!/usr/bin/env python3
"""
Test Mojibake-Fixes und Cache-Lookup
"""

import repositories.geo_repo as repo
from common.normalize import normalize_address

def test_mojibake_fixes():
    """Teste Mojibake-Fixes und Cache-Lookup."""
    
    test_cases = [
        'Burgker Stra??e 145, 01705, Freital',
        'Cosch??tzer Stra??e 46, 01705, Freital', 
        'Wilsdruffer Stra??e 7, 01705, Freital',
        'L??btauer Stra??e 80, 01159, Dresden',
        'Fr??belstra??e 20, 01159, Dresden'
    ]

    print('=== Cache-Lookup mit Mojibake-Fixes ===')
    for test in test_cases:
        # 1) Normalisiere (mit Mojibake-Fix)
        normalized = normalize_address(test)
        
        # 2) Cache-Lookup
        cache_result = repo.bulk_get([normalized])
        
        print(f'Original:  {test}')
        print(f'Fixed:     {normalized}')
        
        if cache_result:
            geo = cache_result[normalized]
            print(f'✅ Cache:   ({geo["lat"]}, {geo["lon"]}) [{geo["src"]}]')
        else:
            print(f'❌ Nicht im Cache')
        print()

if __name__ == "__main__":
    test_mojibake_fixes()
