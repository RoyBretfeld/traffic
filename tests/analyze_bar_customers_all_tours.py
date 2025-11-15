#!/usr/bin/env python3
"""
BAR-Kunden Analyse aus allen Tourplänen

Dieses Skript analysiert alle verfügbaren Tourpläne und sammelt alle BAR-Kunden
mit ihren verschiedenen Namen, um ein umfassendes Mapping-System zu erstellen.
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
    
    for encoding in encodings:
        try:
            with open(csv_file, 'r', encoding=encoding) as f:
                reader = csv.reader(f)
                rows = list(reader)
            break
        except UnicodeDecodeError:
            continue
    else:
        print(f"  ⚠️ Konnte {csv_file.name} mit keinem Encoding lesen")
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
                
    except Exception as e:
        print(f"Fehler beim Parsen von {csv_file}: {e}")
    
    return customers

def analyze_bar_customers():
    """Analysiert alle BAR-Kunden aus allen Tourplänen."""
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
    
    return all_customers, bar_customers

def find_bar_name_variants(bar_customers):
    """Findet verschiedene Namen für dieselben BAR-Kunden."""
    name_groups = defaultdict(list)
    
    # Gruppiere nach ähnlichen Namen
    for customer in bar_customers:
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

def create_bar_mappings(name_groups):
    """Erstellt Mappings für BAR-Kunden-Varianten."""
    mappings = []
    
    for group_key, customers in name_groups.items():
        if len(customers) > 1:  # Nur Gruppen mit mehreren Varianten
            # Finde die häufigste Adresse
            addresses = [c['adresse'] for c in customers]
            address_counts = Counter(addresses)
            most_common_address = address_counts.most_common(1)[0][0]
            
            # Finde den häufigsten Namen
            names = [c['name'] for c in customers]
            name_counts = Counter(names)
            most_common_name = name_counts.most_common(1)[0][0]
            
            # Erstelle Mapping
            mapping = {
                'canonical_name': most_common_name,
                'canonical_address': most_common_address,
                'variants': []
            }
            
            for customer in customers:
                if customer['name'] != most_common_name or customer['adresse'] != most_common_address:
                    mapping['variants'].append({
                        'name': customer['name'],
                        'adresse': customer['adresse'],
                        'kdnr': customer['kdnr'],
                        'tour_file': customer['tour_file']
                    })
            
            if mapping['variants']:  # Nur wenn es Varianten gibt
                mappings.append(mapping)
    
    return mappings

def analyze_bar_patterns(bar_customers):
    """Analysiert Muster in BAR-Kunden-Namen."""
    patterns = {
        'common_prefixes': Counter(),
        'common_suffixes': Counter(),
        'common_words': Counter(),
        'name_lengths': Counter(),
        'special_chars': Counter()
    }
    
    for customer in bar_customers:
        name = customer['name']
        
        # Präfixe (erste 3 Zeichen)
        if len(name) >= 3:
            patterns['common_prefixes'][name[:3].lower()] += 1
        
        # Suffixe (letzte 3 Zeichen)
        if len(name) >= 3:
            patterns['common_suffixes'][name[-3:].lower()] += 1
        
        # Wörter
        words = re.findall(r'\w+', name.lower())
        for word in words:
            if len(word) > 2:  # Ignoriere kurze Wörter
                patterns['common_words'][word] += 1
        
        # Länge
        patterns['name_lengths'][len(name)] += 1
        
        # Sonderzeichen
        special_chars = re.findall(r'[^\w\s]', name)
        for char in special_chars:
            patterns['special_chars'][char] += 1
    
    return patterns

def main():
    """Hauptfunktion."""
    print("🚀 BAR-Kunden Analyse - Alle Tourpläne")
    print("=" * 50)
    
    # Analysiere alle Tourpläne
    all_customers, bar_customers = analyze_bar_customers()
    
    if not bar_customers:
        print("❌ Keine BAR-Kunden gefunden!")
        return
    
    print(f"\n📊 BAR-Kunden Statistiken:")
    print(f"  Gesamt BAR-Kunden: {len(bar_customers)}")
    print(f"  Aus {len(set(c['tour_file'] for c in bar_customers))} Tourplänen")
    
    # Finde Namens-Varianten
    print(f"\n🔍 Suche nach Namens-Varianten...")
    name_groups = find_bar_name_variants(bar_customers)
    
    print(f"  Gefundene Namens-Gruppen: {len(name_groups)}")
    
    # Erstelle Mappings
    mappings = create_bar_mappings(name_groups)
    
    print(f"  Mappings mit Varianten: {len(mappings)}")
    
    # Analysiere Muster
    patterns = analyze_bar_patterns(bar_customers)
    
    # Speichere Ergebnisse
    results = {
        'analysis_timestamp': datetime.now().isoformat(),
        'total_bar_customers': len(bar_customers),
        'name_groups_count': len(name_groups),
        'mappings_count': len(mappings),
        'mappings': mappings,
        'patterns': patterns,
        'all_bar_customers': bar_customers
    }
    
    # JSON-Export
    with open('bar_customers_analysis.json', 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    # Markdown-Report
    with open('bar_customers_report.md', 'w', encoding='utf-8') as f:
        f.write("# BAR-Kunden Analyse Report\n\n")
        f.write(f"**Analyse-Datum:** {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
        
        f.write(f"## 📊 Statistiken\n\n")
        f.write(f"- **Gesamt BAR-Kunden:** {len(bar_customers)}\n")
        f.write(f"- **Tourpläne analysiert:** {len(set(c['tour_file'] for c in bar_customers))}\n")
        f.write(f"- **Namens-Gruppen:** {len(name_groups)}\n")
        f.write(f"- **Mappings mit Varianten:** {len(mappings)}\n\n")
        
        f.write("## 🔍 Namens-Varianten\n\n")
        for i, mapping in enumerate(mappings, 1):
            f.write(f"### {i}. {mapping['canonical_name']}\n\n")
            f.write(f"**Kanonische Adresse:** {mapping['canonical_address']}\n\n")
            f.write("**Varianten:**\n")
            for variant in mapping['variants']:
                f.write(f"- `{variant['name']}` - {variant['adresse']} (Tour: {variant['tour_file']})\n")
            f.write("\n")
        
        f.write("## 📈 Häufigste Muster\n\n")
        f.write("### Häufigste Wörter:\n")
        for word, count in patterns['common_words'].most_common(10):
            f.write(f"- `{word}`: {count}x\n")
        
        f.write("\n### Häufigste Präfixe:\n")
        for prefix, count in patterns['common_prefixes'].most_common(10):
            f.write(f"- `{prefix}`: {count}x\n")
        
        f.write("\n### Häufigste Suffixe:\n")
        for suffix, count in patterns['common_suffixes'].most_common(10):
            f.write(f"- `{suffix}`: {count}x\n")
    
    print(f"\n✅ Analyse abgeschlossen!")
    print(f"📁 Ergebnisse gespeichert:")
    print(f"  - bar_customers_analysis.json")
    print(f"  - bar_customers_report.md")
    
    # Zeige Top-Mappings
    print(f"\n🔍 Top 5 BAR-Kunden mit Varianten:")
    for i, mapping in enumerate(mappings[:5], 1):
        print(f"  {i}. {mapping['canonical_name']}")
        print(f"     Varianten: {len(mapping['variants'])}")
        for variant in mapping['variants'][:2]:  # Zeige nur erste 2 Varianten
            print(f"       - {variant['name']} ({variant['tour_file']})")
        if len(mapping['variants']) > 2:
            print(f"       ... und {len(mapping['variants']) - 2} weitere")

if __name__ == "__main__":
    main()
