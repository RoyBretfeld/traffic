#!/usr/bin/env python3
"""
Address Management Dashboard
Zentrales Management für alle Address-Mapping-Funktionen
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.address_mapper import address_mapper
from backend.services.address_analyzer import address_analyzer
from backend.parsers.tour_plan_parser import parse_tour_plan_to_dict
import json
from datetime import datetime

def show_dashboard():
    """Zeige Dashboard mit aktuellen Statistiken"""
    print("ADDRESS MANAGEMENT DASHBOARD")
    print("=" * 50)
    print(f"Zeitstempel: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print()
    
    # Lade aktuelle Konfiguration
    print("AKTUELLE KONFIGURATION:")
    print(f"  BAR-Sondernamen: {len(address_mapper.bar_sondernamen)}")
    print(f"  Address-Mappings: {len(address_mapper.mappings)}")
    print(f"  Regeln: {len(address_mapper.rules)}")
    print()
    
    # Zeige BAR-Sondernamen
    print("BAR-SONDERNAMEN:")
    for i, entry in enumerate(address_mapper.bar_sondernamen, 1):
        print(f"  {i}. {entry['sondername']}")
        print(f"     -> {entry['echte_adresse']}")
        if entry['lat'] and entry['lon']:
            print(f"     Koordinaten: {entry['lat']}, {entry['lon']}")
        print(f"     Kategorie: {entry['kategorie']}")
        print()
    
    # Zeige Top Address-Mappings
    print("TOP ADDRESS-MAPPINGS:")
    for i, mapping in enumerate(address_mapper.mappings[:5], 1):
        print(f"  {i}. {mapping['pattern']}")
        print(f"     -> {mapping['corrected_address']}")
        if mapping.get('lat') and mapping.get('lon'):
            print(f"     Koordinaten: {mapping['lat']}, {mapping['lon']}")
        print(f"     Priorität: {mapping['priority']}")
        print()
    
    if len(address_mapper.mappings) > 5:
        print(f"     ... und {len(address_mapper.mappings) - 5} weitere")

def analyze_new_tourplan(csv_file):
    """Analysiere neuen Tourplan"""
    print(f"ANALYSE NEUER TOURPLAN: {csv_file}")
    print("=" * 50)
    
    if not os.path.exists(csv_file):
        print(f"FEHLER: Datei nicht gefunden: {csv_file}")
        return
    
    try:
        result = parse_tour_plan_to_dict(csv_file)
        if not result or 'tours' not in result:
            print("FEHLER: CSV-Parsing fehlgeschlagen")
            return
        
        print(f"OK: CSV geparst: {len(result['tours'])} Touren gefunden")
        
        # Analysiere mit Address-Analyzer
        analysis = address_analyzer.analyze_tour_plan(result)
        
        # Zeige Zusammenfassung
        address_analyzer.print_summary(analysis)
        
        # Speichere Bericht
        report_file = address_analyzer.save_analysis_report()
        suggestions_file = address_analyzer.generate_mapping_suggestions_file()
        
        print(f"\nBerichte gespeichert:")
        print(f"  Analyse-Bericht: {report_file}")
        print(f"  Mapping-Vorschläge: {suggestions_file}")
        
        return analysis
        
    except Exception as e:
        print(f"FEHLER beim Analysieren: {e}")
        import traceback
        traceback.print_exc()
        return None

def add_bar_sondername_interactive():
    """Interaktives Hinzufügen von BAR-Sondernamen"""
    print("BAR-SONDERNAME HINZUFÜGEN")
    print("=" * 40)
    
    sondername = input("Sondername: ").strip()
    if not sondername:
        print("Fehler: Sondername darf nicht leer sein")
        return
    
    echte_adresse = input("Echte Adresse: ").strip()
    if not echte_adresse:
        print("Fehler: Echte Adresse darf nicht leer sein")
        return
    
    lat_input = input("Latitude (optional): ").strip()
    lon_input = input("Longitude (optional): ").strip()
    
    lat = None
    lon = None
    if lat_input and lon_input:
        try:
            lat = float(lat_input)
            lon = float(lon_input)
        except ValueError:
            print("Warnung: Ungültige Koordinaten, verwende None")
    
    beschreibung = input("Beschreibung (optional): ").strip()
    kategorie = input("Kategorie (autohaus/autoservice/werkstatt/teilehandel): ").strip()
    
    # Prüfe ob bereits vorhanden
    existing = address_mapper.find_bar_sondername(sondername)
    if existing:
        print(f"Warnung: BAR-Sondername '{sondername}' bereits vorhanden")
        print(f"  Echte Adresse: {existing['echte_adresse']}")
        print(f"  Koordinaten: {existing['lat']}, {existing['lon']}")
        
        overwrite = input("Überschreiben? (j/n): ").strip().lower()
        if overwrite != 'j':
            print("Abgebrochen")
            return
    
    # Füge hinzu
    new_entry = {
        "sondername": sondername,
        "echte_adresse": echte_adresse,
        "lat": lat,
        "lon": lon,
        "beschreibung": beschreibung or f"BAR-Sondername für {sondername}",
        "kategorie": kategorie or "unknown"
    }
    
    address_mapper.bar_sondernamen.append(new_entry)
    
    if address_mapper.save_config():
        print(f"[OK] BAR-Sondername '{sondername}' erfolgreich hinzugefügt")
    else:
        print("[FEHLER] Fehler beim Speichern der Konfiguration")

def test_address(address):
    """Teste eine Adresse"""
    print(f"TESTE ADRESSE: '{address}'")
    print("=" * 40)
    
    result = address_mapper.map_address(address)
    print(f"Ergebnis:")
    print(f"  Korrigierte Adresse: {result['corrected_address']}")
    print(f"  Methode: {result['method']}")
    print(f"  Confidence: {result['confidence']}")
    if result['lat'] and result['lon']:
        print(f"  Koordinaten: {result['lat']}, {result['lon']}")
    if 'kategorie' in result:
        print(f"  Kategorie: {result['kategorie']}")

def main():
    """Hauptmenü"""
    while True:
        print("\nADDRESS MANAGEMENT DASHBOARD")
        print("=" * 50)
        print("1. Dashboard anzeigen")
        print("2. Neuen Tourplan analysieren")
        print("3. BAR-Sondername hinzufügen")
        print("4. Adresse testen")
        print("5. Beenden")
        
        choice = input("\nWahl (1-5): ").strip()
        
        if choice == '1':
            show_dashboard()
        elif choice == '2':
            csv_file = input("CSV-Datei: ").strip()
            if csv_file:
                analyze_new_tourplan(csv_file)
        elif choice == '3':
            add_bar_sondername_interactive()
        elif choice == '4':
            address = input("Adresse zum Testen: ").strip()
            if address:
                test_address(address)
        elif choice == '5':
            print("Auf Wiedersehen!")
            break
        else:
            print("Ungültige Wahl, bitte 1-5 eingeben")

if __name__ == "__main__":
    main()
