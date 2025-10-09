#!/usr/bin/env python3
"""
Management-Script für Address-Mappings
Ermöglicht einfaches Hinzufügen und Verwalten von BAR-Sondernamen und Adress-Mappings
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from backend.services.address_mapper import address_mapper
import json

def add_bar_sondername():
    """Füge neuen BAR-Sondernamen hinzu"""
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
        print(f"✅ BAR-Sondername '{sondername}' erfolgreich hinzugefügt")
    else:
        print("❌ Fehler beim Speichern der Konfiguration")

def add_address_mapping():
    """Füge neues Adress-Mapping hinzu"""
    print("ADDRESS-MAPPING HINZUFÜGEN")
    print("=" * 40)
    
    pattern = input("Pattern (zu suchende Adresse): ").strip()
    if not pattern:
        print("Fehler: Pattern darf nicht leer sein")
        return
    
    corrected_address = input("Korrigierte Adresse: ").strip()
    if not corrected_address:
        print("Fehler: Korrigierte Adresse darf nicht leer sein")
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
    
    reason = input("Grund (optional): ").strip()
    priority = input("Priorität (1-5, Standard: 1): ").strip()
    
    try:
        priority = int(priority) if priority else 1
    except ValueError:
        priority = 1
    
    # Prüfe ob bereits vorhanden
    existing = address_mapper.find_exact_mapping(pattern)
    if existing:
        print(f"Warnung: Mapping für '{pattern}' bereits vorhanden")
        print(f"  Korrigierte Adresse: {existing['corrected_address']}")
        
        overwrite = input("Überschreiben? (j/n): ").strip().lower()
        if overwrite != 'j':
            print("Abgebrochen")
            return
    
    # Füge hinzu
    if address_mapper.add_mapping(pattern, corrected_address, lat, lon, reason, priority):
        if address_mapper.save_config():
            print(f"✅ Address-Mapping für '{pattern}' erfolgreich hinzugefügt")
        else:
            print("❌ Fehler beim Speichern der Konfiguration")
    else:
        print("❌ Fehler beim Hinzufügen des Mappings")

def list_mappings():
    """Zeige alle Mappings an"""
    print("ALLE MAPPINGS")
    print("=" * 40)
    
    print(f"\nBAR-Sondernamen ({len(address_mapper.bar_sondernamen)}):")
    for i, entry in enumerate(address_mapper.bar_sondernamen, 1):
        print(f"  {i}. {entry['sondername']}")
        print(f"     -> {entry['echte_adresse']}")
        if entry['lat'] and entry['lon']:
            print(f"     Koordinaten: {entry['lat']}, {entry['lon']}")
        print(f"     Kategorie: {entry['kategorie']}")
        print()
    
    print(f"\nAddress-Mappings ({len(address_mapper.mappings)}):")
    for i, mapping in enumerate(address_mapper.mappings, 1):
        print(f"  {i}. {mapping['pattern']}")
        print(f"     -> {mapping['corrected_address']}")
        if mapping.get('lat') and mapping.get('lon'):
            print(f"     Koordinaten: {mapping['lat']}, {mapping['lon']}")
        print(f"     Priorität: {mapping['priority']}")
        print()

def test_mapping():
    """Teste ein Mapping"""
    print("MAPPING TESTEN")
    print("=" * 40)
    
    address = input("Adresse zum Testen: ").strip()
    if not address:
        print("Fehler: Adresse darf nicht leer sein")
        return
    
    print(f"\nTeste Adresse: '{address}'")
    print("-" * 40)
    
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
        print("\nADDRESS-MAPPING MANAGEMENT")
        print("=" * 40)
        print("1. BAR-Sondername hinzufügen")
        print("2. Address-Mapping hinzufügen")
        print("3. Alle Mappings anzeigen")
        print("4. Mapping testen")
        print("5. Beenden")
        
        choice = input("\nWahl (1-5): ").strip()
        
        if choice == '1':
            add_bar_sondername()
        elif choice == '2':
            add_address_mapping()
        elif choice == '3':
            list_mappings()
        elif choice == '4':
            test_mapping()
        elif choice == '5':
            print("Auf Wiedersehen!")
            break
        else:
            print("Ungültige Wahl, bitte 1-5 eingeben")

if __name__ == "__main__":
    main()
