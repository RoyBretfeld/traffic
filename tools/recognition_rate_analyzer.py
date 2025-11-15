#!/usr/bin/env python3
"""
Erkennungsrate-Analyzer für alle Tourpläne
Analysiert die Geocoding-Erfolgsrate für alle verfügbaren CSV-Pläne
"""

import sys
from pathlib import Path
import pandas as pd
from datetime import datetime
import json

# Projekt-Root zum Python-Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent))

from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
from repositories.geo_repo import bulk_get, normalize_addr
from repositories.geo_alias_repo import resolve_aliases

def analyze_recognition_rate(csv_file: Path) -> dict:
    """
    Analysiert die Erkennungsrate für eine einzelne CSV-Datei
    """
    print(f"🔍 Analysiere: {csv_file.name}")
    
    try:
        # CSV parsen
        tour_data = parse_tour_plan_to_dict(str(csv_file))
        if not tour_data or not tour_data.get('customers'):
            return {
                'file': csv_file.name,
                'error': 'Keine Kunden-Daten gefunden',
                'total_customers': 0,
                'geocoded': 0,
                'missing': 0,
                'rate': 0.0
            }
        
        customers = tour_data['customers']
        total_customers = len(customers)
        
        # Alle Adressen sammeln und normalisieren
        addresses = []
        for customer in customers:
            full_address = f"{customer['street']}, {customer['postal_code']} {customer['city']}"
            addresses.append(normalize_addr(full_address))
        
        # Alias-Auflösung
        aliases = resolve_aliases(addresses)
        
        # Cache-Lookup (inkl. Aliases)
        all_addresses = addresses + list(aliases.values())
        geo_results = bulk_get(all_addresses)
        
        # Erfolgsrate berechnen
        geocoded_count = 0
        missing_addresses = []
        
        for addr in addresses:
            # Prüfe direkten Cache-Treffer
            if addr in geo_results:
                geocoded_count += 1
            else:
                # Prüfe Alias-Treffer
                alias = aliases.get(addr)
                if alias and alias in geo_results:
                    geocoded_count += 1
                else:
                    missing_addresses.append(addr)
        
        success_rate = (geocoded_count / total_customers * 100) if total_customers > 0 else 0
        
        return {
            'file': csv_file.name,
            'total_customers': total_customers,
            'geocoded': geocoded_count,
            'missing': len(missing_addresses),
            'rate': round(success_rate, 1),
            'missing_addresses': missing_addresses[:5],  # Nur erste 5 für Übersicht
            'tours': len(tour_data.get('tours', [])),
            'file_size_kb': round(csv_file.stat().st_size / 1024, 1)
        }
        
    except Exception as e:
        return {
            'file': csv_file.name,
            'error': str(e),
            'total_customers': 0,
            'geocoded': 0,
            'missing': 0,
            'rate': 0.0
        }

def main():
    """
    Hauptfunktion: Analysiert alle CSV-Pläne
    """
    print("🚀 Erkennungsrate-Analyzer für alle Tourpläne")
    print("=" * 60)
    
    # Tourplaene-Verzeichnis finden
    tourplaene_dir = Path("./tourplaene")
    if not tourplaene_dir.exists():
        print("❌ tourplaene Verzeichnis nicht gefunden")
        return
    
    # Alle CSV-Dateien auflisten
    csv_files = sorted(tourplaene_dir.glob("*.csv"))
    if not csv_files:
        print("❌ Keine CSV-Dateien gefunden")
        return
    
    print(f"📋 Gefundene Pläne: {len(csv_files)}")
    print()
    
    # Analyse durchführen
    results = []
    total_customers = 0
    total_geocoded = 0
    
    for csv_file in csv_files:
        result = analyze_recognition_rate(csv_file)
        results.append(result)
        
        if 'error' not in result:
            total_customers += result['total_customers']
            total_geocoded += result['geocoded']
    
    # Ergebnisse anzeigen
    print("\n📊 ERKENNUNGSRATE-ÜBERSICHT")
    print("=" * 60)
    print(f"{'Datei':<25} {'Kunden':<8} {'Geocodiert':<12} {'Rate':<8} {'Status'}")
    print("-" * 60)
    
    for result in results:
        if 'error' in result:
            print(f"{result['file']:<25} {'ERROR':<8} {'ERROR':<12} {'ERROR':<8} {result['error']}")
        else:
            status = "✅" if result['rate'] >= 90 else "⚠️" if result['rate'] >= 70 else "❌"
            print(f"{result['file']:<25} {result['total_customers']:<8} {result['geocoded']:<12} {result['rate']}%{'':<3} {status}")
    
    # Gesamtstatistik
    overall_rate = (total_geocoded / total_customers * 100) if total_customers > 0 else 0
    print("-" * 60)
    print(f"{'GESAMT':<25} {total_customers:<8} {total_geocoded:<12} {overall_rate:.1f}%{'':<3}")
    
    # Top-Probleme identifizieren
    print("\n🔍 TOP-PROBLEME (niedrigste Erkennungsraten):")
    print("-" * 60)
    
    problem_files = [r for r in results if 'error' not in r and r['rate'] < 90]
    problem_files.sort(key=lambda x: x['rate'])
    
    for result in problem_files[:5]:  # Top 5 Probleme
        print(f"\n📁 {result['file']} ({result['rate']}% Erfolgsrate)")
        print(f"   Kunden: {result['total_customers']}, Geocodiert: {result['geocoded']}, Fehlend: {result['missing']}")
        if result['missing_addresses']:
            print("   Fehlende Adressen (Beispiele):")
            for addr in result['missing_addresses']:
                print(f"     - {addr}")
    
    # Erfolgreiche Pläne
    print("\n✅ ERFOLGREICHE PLÄNE (≥90% Erkennungsrate):")
    print("-" * 60)
    
    successful_files = [r for r in results if 'error' not in r and r['rate'] >= 90]
    print(f"Anzahl: {len(successful_files)} von {len(results)} Plänen")
    
    if successful_files:
        for result in successful_files:
            print(f"  ✅ {result['file']} - {result['rate']}% ({result['geocoded']}/{result['total_customers']})")
    
    # Empfehlungen
    print("\n💡 EMPFEHLUNGEN:")
    print("-" * 60)
    
    if overall_rate >= 95:
        print("🎉 Exzellent! Erkennungsrate über 95% - System läuft optimal")
    elif overall_rate >= 90:
        print("✅ Sehr gut! Erkennungsrate über 90% - nur wenige Verbesserungen nötig")
    elif overall_rate >= 80:
        print("⚠️ Gut, aber verbesserbar. Erkennungsrate über 80% - einige Adressen brauchen Aufmerksamkeit")
    else:
        print("❌ Verbesserung nötig. Erkennungsrate unter 80% - systematische Geocoding-Ergänzung empfohlen")
    
    if problem_files:
        print(f"\n🔧 Nächste Schritte:")
        print(f"   1. Problem-Pläne einzeln analysieren")
        print(f"   2. Fehlende Adressen manuell geocodieren")
        print(f"   3. OT-Fallback für OT-Adressen prüfen")
        print(f"   4. Mojibake-Korrektur für Umlaute testen")
    
    # JSON-Export für detaillierte Analyse
    export_data = {
        'timestamp': datetime.now().isoformat(),
        'overall_stats': {
            'total_files': len(results),
            'total_customers': total_customers,
            'total_geocoded': total_geocoded,
            'overall_rate': round(overall_rate, 1)
        },
        'results': results
    }
    
    export_file = Path("./config/recognition_rate_analysis.json")
    export_file.parent.mkdir(exist_ok=True)
    export_file.write_text(json.dumps(export_data, indent=2, ensure_ascii=False))
    
    print(f"\n💾 Detaillierte Analyse gespeichert: {export_file}")
    print("\n🎯 Analyse abgeschlossen!")

if __name__ == "__main__":
    main()
