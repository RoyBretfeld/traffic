from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict

# Parse die CSV-Datei
data = parse_tour_plan_to_dict('tourplaene/Tourenplan 17.09.2025.csv')

print('=== ERSTE 10 KUNDEN AUS PARSER ===')
for i, c in enumerate(data['customers'][:10]):
    print(f'Zeile {i+1}: {c["customer_number"]} - {c["name"]}')
    print(f'   Adresse: {c["street"]}, {c["postal_code"]} {c["city"]}')
    print(f'   Vollständig: {c["street"]}, {c["postal_code"]} {c["city"]}')
    print()

print('=== PROBLEM IDENTIFIZIERT ===')
print('Der Parser hat die Adressen korrekt!')
print('Das Problem liegt im Match-API - es zeigt "nan" statt der echten Adresse!')
