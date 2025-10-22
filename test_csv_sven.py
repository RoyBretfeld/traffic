import sys
sys.path.insert(0, '.')
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict

print('🔍 DEBUG: CSV-Parser testen')
print('=' * 50)

csv_path = 'tourplaene/Tourenplan 15.09.2025.csv'
tour_data = parse_tour_plan_to_dict(csv_path)

# Suche nach Sven - PF
for i, customer in enumerate(tour_data['customers']):
    name = customer.get('name', '')
    if 'sven' in name.lower() and 'pf' in name.lower():
        street = customer.get('street', '')
        postal_code = customer.get('postal_code', '')
        city = customer.get('city', '')
        address = customer.get('address', '')
        print(f'{i+1}. Name: "{name}"')
        print(f'   Street: "{street}"')
        print(f'   Postal: "{postal_code}"')
        print(f'   City: "{city}"')
        print(f'   Address: "{address}"')
        print(f'   Contains apostrophe: {"'" in str(street) or "'" in str(postal_code) or "'" in str(city)}')
        print()
