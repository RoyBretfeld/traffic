#!/usr/bin/env python3
"""
Teste Cache-Lookup mit verbesserter Normalisierung
"""

import repositories.geo_repo as repo
from common.normalize import normalize_address

def test_improved_normalization():
    """Teste Cache-Lookup mit verbesserter Normalisierung."""
    
    test_cases = [
        'Am S??gewerk 36, 01328, Dresden OT Sch??nfeld',
        'Altnossener Stra??e 7, 01156, Dresden / Gompitz',
        'Dorfstra??e 37, 01768, Glash??tte OT Luchau',
        'Stolpener Strasse 39, 01477, Arnsdorf / Sachsen'
    ]

    print('=== Cache-Lookup mit verbesserter Normalisierung ===')
    for test in test_cases:
        normalized = normalize_address(test)
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
    test_improved_normalization()
