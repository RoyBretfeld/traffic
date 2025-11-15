#!/usr/bin/env python3
"""
BAR-Kunden Analyse - Angepasst für CSV-Format

Analysiert alle Tourpläne und findet BAR-Kunden mit verschiedenen Namen.
"""

import os
import csv
import json
from pathlib import Path
from collections import defaultdict, Counter
from datetime import datetime
import re

def parse_tour_plan(csv_file):
    """Parst einen Tourplan und extrahiert alle Kunden."""
    customers = []
    
    # Teste verschiedene Encodings - UTF-8 zuerst für deutsche Umlaute
    encodings = ['utf-8', 'cp1252', 'latin-1', 'iso-8859-1']
    rows = []
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.reader(f, delimiter=';')
                rows = list(reader)
            
            # Prüfe ob deutsche Umlaute korrekt gelesen wurden
            content = ' '.join([' '.join(row) for row in rows[:10]])
            if 'ß' in content or 'ü' in content or 'ä' in content or 'ö' in content:
                print(f"  ✅ {csv_file.name} mit {encoding} gelesen (deutsche Umlaute erkannt)")
            else:
                print(f"  ✅ {csv_file.name} mit {encoding} gelesen")
            break
        except UnicodeDecodeError:
            continue
    else:
        print(f"  ❌ Konnte {csv_file.name} mit keinem Encoding lesen")
        return customers
    
    if len(rows) < 5:
        return customers
    
    # Finde die Header-Zeile (enthält "Kdnr")
    header_row = None
    for i, row in enumerate(rows):
        if 'Kdnr' in row or 'kdnr' in row:
            header_row = i
            break
    
    if header_row is None:
        print(f"  ⚠️ Keine Header-Zeile in {csv_file.name} gefunden")
        return customers
    
    # Spalten-Indizes finden
    kdnr_idx = None
    name_idx = None
    strasse_idx = None
    plz_idx = None
    ort_idx = None
    
    headers = rows[header_row]
    for i, header in enumerate(headers):
        header_lower = header.lower().strip()
        if 'kdnr' in header_lower:
            kdnr_idx = i
        elif 'name' in header_lower:
            name_idx = i
        elif 'straße' in header_lower or 'strasse' in header_lower or 'stra' in header_lower:
            strasse_idx = i
        elif 'plz' in header_lower:
            plz_idx = i
        elif 'ort' in header_lower:
            ort_idx = i
    
    print(f"    Spalten: Kdnr={kdnr_idx}, Name={name_idx}, Straße={strasse_idx}, PLZ={plz_idx}, Ort={ort_idx}")
    
    # Kunden extrahieren
    for row in rows[header_row + 1:]:
        if len(row) <= max(filter(None, [kdnr_idx, name_idx, strasse_idx, plz_idx, ort_idx])):
            continue
        
        # Prüfe ob es eine Tour-Zeile ist (enthält "W-", "PIR-", etc.)
        if any(tour_type in row[0] for tour_type in ['W-', 'PIR-', 'T-']):
            continue
            
        kdnr = row[kdnr_idx].strip() if kdnr_idx and kdnr_idx < len(row) else ""
        name = row[name_idx].strip() if name_idx and name_idx < len(row) else ""
        strasse = row[strasse_idx].strip() if strasse_idx and strasse_idx < len(row) else ""
        plz = row[plz_idx].strip() if plz_idx and plz_idx < len(row) else ""
        ort = row[ort_idx].strip() if ort_idx and ort_idx < len(row) else ""
        
        # Prüfe ob es ein BAR-Kunde ist
        is_bar = False
        if name and ('BAR' in name.upper() or 'bar' in name.lower()):
            is_bar = True
        
        if name and strasse and plz and ort:
            adresse = f"{strasse}, {plz} {ort}"
            customer = {
                'kdnr': kdnr,
                'name': name,
                'adresse': adresse,
                'strasse': strasse,
                'plz': plz,
                'ort': ort,
                'is_bar': is_bar,
                'tour_file': os.path.basename(csv_file)
            }
            customers.append(customer)
    
    return customers

def find_similar_names(customers):
    """Findet ähnliche Namen."""
    name_groups = defaultdict(list)
    
    for customer in customers:
        name = customer['name'].lower().strip()
        
        # Normalisiere den Namen
        normalized = re.sub(r'[^\w\s]', '', name)
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Finde ähnliche Namen
        found_group = None
        for group_key, group_customers in name_groups.items():
            if is_similar_name(normalized, group_key):
                found_group = group_key
                break
        
        if found_group:
            name_groups[found_group].append(customer)
        else:
            name_groups[normalized].append(customer)
    
    return name_groups

def is_similar_name(name1, name2):
    """Prüft ob zwei Namen ähnlich sind."""
    # Entferne häufige Wörter
    common_words = {'gmbh', 'kg', 'ohg', 'ag', 'e.k.', 'e.k', 'autohaus', 'autoservice', 'werkstatt', 'garage', 'bar'}
    
    words1 = set(name1.split()) - common_words
    words2 = set(name2.split()) - common_words
    
    # Prüfe Überschneidungen
    intersection = words1.intersection(words2)
    union = words1.union(words2)
    
    if len(union) == 0:
        return False
    
    similarity = len(intersection) / len(union)
    return similarity > 0.3  # 30% Ähnlichkeit

def main():
    """Hauptfunktion."""
    print("🚀 BAR-Kunden Analyse - Alle Tourpläne")
    print("=" * 50)
    
    tourplaene_dir = Path("tourplaene")
    all_customers = []
    bar_customers = []
    
    print("🔍 Analysiere alle Tourpläne...")
    
    # Alle CSV-Dateien verarbeiten
    for csv_file in tourplaene_dir.glob("*.csv"):
        print(f"  📄 Verarbeite: {csv_file.name}")
        customers = parse_tour_plan(csv_file)
        all_customers.extend(customers)
        
        # BAR-Kunden extrahieren
        for customer in customers:
            if customer['is_bar']:
                bar_customers.append(customer)
    
    print(f"✅ Gesamt: {len(all_customers)} Kunden, {len(bar_customers)} BAR-Kunden")
    
    if not bar_customers:
        print("❌ Keine BAR-Kunden gefunden!")
        # Zeige alle Kunden zur Debugging
        print("\n🔍 Alle gefundenen Kunden:")
        for customer in all_customers[:10]:  # Erste 10
            print(f"  - {customer['name']} ({customer['adresse']})")
        return
    
    # Finde ähnliche Namen
    print(f"\n🔍 Suche nach ähnlichen Namen...")
    name_groups = find_similar_names(bar_customers)
    
    print(f"  Gefundene Namens-Gruppen: {len(name_groups)}")
    
    # Zeige Ergebnisse
    print(f"\n📊 BAR-Kunden nach Tourplänen:")
    tour_counts = Counter(c['tour_file'] for c in bar_customers)
    for tour, count in tour_counts.most_common():
        print(f"  {tour}: {count} BAR-Kunden")
    
    print(f"\n🔍 Top 10 BAR-Kunden mit verschiedenen Namen:")
    for i, (group_key, customers) in enumerate(list(name_groups.items())[:10], 1):
        if len(customers) > 1:
            print(f"  {i}. {group_key}")
            for customer in customers:
                print(f"       - {customer['name']} ({customer['tour_file']})")
    
    # Speichere Ergebnisse
    results = {
        'analysis_timestamp': datetime.now().isoformat(),
        'total_customers': len(all_customers),
        'total_bar_customers': len(bar_customers),
        'name_groups_count': len(name_groups),
        'bar_customers': bar_customers,
        'name_groups': dict(name_groups)
    }
    
    with open('bar_customers_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Analyse abgeschlossen!")
    print(f"📁 Ergebnisse gespeichert: bar_customers_analysis.json")

if __name__ == "__main__":
    main()
