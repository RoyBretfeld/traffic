#!/usr/bin/env python3
"""
Identifiziert alle Kunden ohne Geocoding aus einer CSV-Datei
"""
import sys
sys.path.insert(0, '.')

from pathlib import Path
from backend.parsers.tour_plan_parser import parse_tour_plan
from backend.services.geocode import geocode_address

# CSV-Datei parsen
csv_file = Path("tourplaene/Tourenplan 18.08.2025.csv")
print(f"[1/3] Parse CSV-Datei: {csv_file.name}")
plan = parse_tour_plan(str(csv_file))

print(f"[2/3] Gefunden: {plan.total_tours} Touren mit {plan.total_customers} Kunden")
print(f"[3/3] Pruefe Geocoding...\n")

failed_customers = []
success_count = 0
failed_count = 0

for tour in plan.tours:
    for customer in tour.customers:
        # Adresse zusammenbauen
        full_address = f"{customer.street}, {customer.postal_code} {customer.city}"
        
        # Geocoding testen (mit Fehlerbehandlung)
        try:
            result = geocode_address(full_address)
            
            if result and result.get('lat') and result.get('lon'):
                success_count += 1
            else:
                failed_count += 1
                failed_customers.append({
                    'tour': tour.name,
                    'customer_number': customer.customer_number,
                    'name': customer.name,
                    'street': customer.street,
                    'postal_code': customer.postal_code,
                    'city': customer.city,
                    'full_address': full_address
                })
        except Exception as e:
            print(f"[FEHLER] {customer.name}: {e}")
            failed_count += 1
            failed_customers.append({
                'tour': tour.name,
                'customer_number': customer.customer_number,
                'name': customer.name,
                'street': customer.street,
                'postal_code': customer.postal_code,
                'city': customer.city,
                'full_address': full_address
            })

print(f"\n{'='*80}")
print(f"ERGEBNIS:")
print(f"{'='*80}")
print(f"Erfolgreich geocodiert: {success_count}")
print(f"Fehlgeschlagen:         {failed_count}")
print(f"Erfolgsrate:            {(success_count/(success_count+failed_count)*100):.1f}%")
print(f"{'='*80}\n")

if failed_customers:
    print(f"\n{'='*80}")
    print(f"KUNDEN OHNE GEOCODING ({len(failed_customers)}):")
    print(f"{'='*80}\n")
    
    for i, cust in enumerate(failed_customers, 1):
        print(f"{i}. {cust['name']} (KdNr: {cust['customer_number']})")
        print(f"   Tour: {cust['tour']}")
        print(f"   Adresse: {cust['full_address']}")
        print()
    
    # Exportiere als Text-Datei
    output_file = Path("failed_geocoding_18_08_2025.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("KUNDEN OHNE GEOCODING - Tourenplan 18.08.2025\n")
        f.write("="*80 + "\n\n")
        for i, cust in enumerate(failed_customers, 1):
            f.write(f"{i}. {cust['name']} (KdNr: {cust['customer_number']})\n")
            f.write(f"   Tour: {cust['tour']}\n")
            f.write(f"   Original: {cust['full_address']}\n")
            f.write(f"   Korrektur: \n")
            f.write("\n")
    
    print(f"[EXPORT] Liste exportiert nach: {output_file}")
else:
    print("[OK] Alle Kunden erfolgreich geocodiert!")

