#!/usr/bin/env python3
"""
Prüft ALLE Tourenpläne im tourplaene/ Ordner auf fehlende Geocoding
"""
import sys
sys.path.insert(0, '.')

from pathlib import Path
from backend.parsers.tour_plan_parser import parse_tour_plan
from backend.services.geocode import geocode_address

# Alle CSV-Dateien finden
tourplaene_dir = Path("tourplaene")
csv_files = sorted(tourplaene_dir.glob("*.csv"))

print(f"\n{'='*80}")
print(f"ANALYSE ALLER TOURENPLÄNE")
print(f"{'='*80}\n")
print(f"Gefundene CSV-Dateien: {len(csv_files)}\n")

all_failed = []
summary = []

for csv_file in csv_files:
    try:
        print(f"\n[DATEI] {csv_file.name}")
        print(f"{'='*80}")
        
        plan = parse_tour_plan(str(csv_file))
        
        failed_in_file = []
        success_count = 0
        failed_count = 0
        empty_count = 0
        
        for tour in plan.tours:
            for customer in tour.customers:
                # Prüfe auf leere Adresse
                if not customer.street or not customer.postal_code or not customer.city:
                    empty_count += 1
                    failed_in_file.append({
                        'name': customer.name,
                        'customer_number': customer.customer_number,
                        'tour': tour.name,
                        'reason': 'Keine Adressdaten',
                        'address': ''
                    })
                    continue
                
                # Teste Geocoding
                full_address = f"{customer.street}, {customer.postal_code} {customer.city}"
                try:
                    result = geocode_address(full_address)
                    if result and result.get('lat') and result.get('lon'):
                        success_count += 1
                    else:
                        failed_count += 1
                        failed_in_file.append({
                            'name': customer.name,
                            'customer_number': customer.customer_number,
                            'tour': tour.name,
                            'reason': 'Geocoding fehlgeschlagen',
                            'address': full_address
                        })
                except Exception as e:
                    failed_count += 1
                    failed_in_file.append({
                        'name': customer.name,
                        'customer_number': customer.customer_number,
                        'tour': tour.name,
                        'reason': f'Fehler: {str(e)[:50]}',
                        'address': full_address
                    })
        
        total = success_count + failed_count + empty_count
        success_rate = (success_count / total * 100) if total > 0 else 0
        
        print(f"Touren: {plan.total_tours}")
        print(f"Kunden gesamt: {total}")
        print(f"  [OK] Erfolgreich: {success_count} ({success_rate:.1f}%)")
        print(f"  [X] Fehlgeschlagen: {failed_count}")
        print(f"  [0] Ohne Adresse: {empty_count}")
        
        summary.append({
            'file': csv_file.name,
            'total': total,
            'success': success_count,
            'failed': failed_count,
            'empty': empty_count,
            'success_rate': success_rate,
            'failed_customers': failed_in_file
        })
        
        if failed_in_file:
            all_failed.extend([(csv_file.name, f) for f in failed_in_file])
    
    except Exception as e:
        print(f"[FEHLER] {csv_file.name}: {e}")
        summary.append({
            'file': csv_file.name,
            'error': str(e)
        })

# Zusammenfassung
print(f"\n\n{'='*80}")
print(f"GESAMTÜBERSICHT")
print(f"{'='*80}\n")

total_customers = sum(s.get('total', 0) for s in summary)
total_success = sum(s.get('success', 0) for s in summary)
total_failed = sum(s.get('failed', 0) for s in summary)
total_empty = sum(s.get('empty', 0) for s in summary)

print(f"Dateien analysiert: {len(csv_files)}")
print(f"Kunden gesamt: {total_customers}")
print(f"  [OK] Erfolgreich: {total_success} ({total_success/total_customers*100:.1f}%)")
print(f"  [X] Fehlgeschlagen: {total_failed}")
print(f"  [0] Ohne Adresse: {total_empty}")
print(f"\n{'='*80}\n")

# Details pro Datei
print(f"\nDETAILS PRO DATEI:")
print(f"{'='*80}")
for s in summary:
    if 'error' in s:
        print(f"\n{s['file']}: FEHLER - {s['error']}")
    else:
        status = "[OK]" if s['failed'] == 0 and s['empty'] == 0 else f"[X] {s['failed']+s['empty']} Probleme"
        print(f"\n{s['file']}: {status}")
        print(f"  Erfolgsrate: {s['success_rate']:.1f}% ({s['success']}/{s['total']})")
        if s['failed'] > 0 or s['empty'] > 0:
            print(f"  Fehlgeschlagen: {s['failed']}, Ohne Adresse: {s['empty']}")

# Exportiere alle Problemfälle
if all_failed:
    print(f"\n\n{'='*80}")
    print(f"ALLE PROBLEMFÄLLE ({len(all_failed)}):")
    print(f"{'='*80}\n")
    
    output_file = Path("all_tourplaene_problems.txt")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("ALLE TOURENPLÄNE - GEOCODING-PROBLEME\n")
        f.write("="*80 + "\n\n")
        
        current_file = None
        for file_name, fail in all_failed:
            if file_name != current_file:
                current_file = file_name
                f.write(f"\n{'='*80}\n")
                f.write(f"DATEI: {file_name}\n")
                f.write(f"{'='*80}\n\n")
                print(f"\n{file_name}:")
            
            f.write(f"Kunde: {fail['name']} (KdNr: {fail['customer_number']})\n")
            f.write(f"  Tour: {fail['tour']}\n")
            f.write(f"  Grund: {fail['reason']}\n")
            f.write(f"  Adresse: {fail['address']}\n")
            f.write(f"  Korrektur: _________________________\n\n")
            
            print(f"  - {fail['name']} ({fail['reason']})")
    
    print(f"\n[EXPORT] Alle Probleme exportiert nach: {output_file}")
else:
    print("\n[SUCCESS] Alle Tourenpläne zu 100% geocodiert!")

