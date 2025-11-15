#!/usr/bin/env python3
"""
BAR-Kunden Analyse - Einfache Version

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
    
    # Teste verschiedene Encodings
    encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1']
    rows = []
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                rows = list(reader)
            print(f"  ✅ {csv_file.name} mit {encoding} gelesen")
            break
        except UnicodeDecodeError:
            continue
    else:
        print(f"  ❌ Konnte {csv_file.name} mit keinem Encoding lesen")
        return customers
    
    if len(rows) < 2:
        return customers
    
    # Header-Zeile finden
    header_row = None
    for i, row in enumerate(rows):
        if any('kunde' in cell.lower() for cell in row):
            header_row = i
            break
    
    if header_row is None:
        return customers
    
    headers = [cell.strip().lower() for cell in rows[header_row]]
    
    # Spalten-Indizes finden
    name_idx = None
    adresse_idx = None
    kdnr_idx = None
    bar_idx = None
    
    for i, header in enumerate(headers):
        if 'name' in header and 'kunde' in header:
            name_idx = i
        elif 'adresse' in header or 'straße' in header:
            adresse_idx = i
        elif 'kdnr' in header or 'kundennr' in header:
            kdnr_idx = i
        elif 'bar' in header:
            bar_idx = i
    
    # Kunden extrahieren
    for row in rows[header_row + 1:]:
        if len(row) <= max(filter(None, [name_idx, adresse_idx, kdnr_idx, bar_idx])):
            continue
            
        name = row[name_idx].strip() if name_idx and name_idx < len(row) else ""
        adresse = row[adresse_idx].strip() if adresse_idx and adresse_idx < len(row) else ""
        kdnr = row[kdnr_idx].strip() if kdnr_idx and kdnr_idx < len(row) else ""
        bar_flag = row[bar_idx].strip().lower() if bar_idx and bar_idx < len(row) else ""
        
        if name and adresse:
            customer = {
                'name': name,
                'adresse': adresse,
                'kdnr': kdnr,
                'bar_flag': bar_flag,
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
    common_words = {'gmbh', 'kg', 'ohg', 'ag', 'e.k.', 'e.k', 'autohaus', 'autoservice', 'werkstatt', 'garage'}
    
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
            if customer['bar_flag'] and customer['bar_flag'].lower() in ['ja', 'yes', '1', 'true', 'bar']:
                bar_customers.append(customer)
    
    print(f"✅ Gesamt: {len(all_customers)} Kunden, {len(bar_customers)} BAR-Kunden")
    
    if not bar_customers:
        print("❌ Keine BAR-Kunden gefunden!")
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
