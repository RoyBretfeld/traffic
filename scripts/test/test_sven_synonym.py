import sys
sys.path.insert(0, '.')
from common.synonyms import resolve_synonym

print('🔍 DEBUG: Synonym-Auflösung für Sven - PF testen')
print('=' * 50)

customer_name = "Sven - PF"
hit = resolve_synonym(customer_name)
if hit:
    print(f'✅ "{customer_name}" -> {hit.resolved_address}')
    print(f'   Lat: {hit.lat}, Lon: {hit.lon}')
else:
    print(f'❌ "{customer_name}" -> KEIN TREFFER')
