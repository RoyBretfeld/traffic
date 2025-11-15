#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importiert Kunden-Synonyme basierend auf KdNr (Tourplan) → Echte Kundennummer/Adresse

Verwendung:
    python scripts/import_customer_synonyms.py
"""

import sys
from pathlib import Path

# Projekt-Root finden
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from backend.services.synonyms import SynonymStore, Synonym

# Synonym-Daten aus der E-Mail/Liste
SYNONYM_DATA = [
    # Format: (Tourplan-KdNr, Alias-Name, Echte_KdNr_oder_Adresse, Zusatzinfo)
    
    # Einzelne Einträge
    {"tourplan_kdnr": "4993", "alias": "Sven PF", "real_customer_id": "5287", "address": "Str. des 17. Juni 11, 01257 Dresden", "note": "Auto Werft Dresden"},
    {"tourplan_kdnr": "4993", "alias": "Jochen PF", "real_customer_id": "5000", "address": "Bärensteiner Str. 27-29, 01277 Dresden", "note": "MotorMafia"},
    {"tourplan_kdnr": "6000", "alias": "Büttner", "real_customer_id": "4318", "address": "Steigerstr. 1, 01705 Freital", "lat": 50.998357, "lon": 13.6879985, "note": None},
    
    # Mehrfach (2-4 Vorkommen)
    {"tourplan_kdnr": "44993", "alias": "AG", "real_customer_id": "40589", "address": "Dresdner Straße 46, 01796 Pirna", "note": "Werk A KfZ Werkstatt"},
    {"tourplan_kdnr": "4993", "alias": "Schrage/Johne PF", "real_customer_id": "4169", "address": "Friedrich-List-Platz 2, 01069 Dresden", "note": "SachsenNetze GmbH"},
    {"tourplan_kdnr": "4727", "alias": "MSM", "real_customer_id": "5236", "address": "Fröbelstraße 20, 01159 Dresden", "lat": 51.05216577633894, "lon": 13.714659672419806, "note": None},
    {"tourplan_kdnr": "6000", "alias": "MSM", "real_customer_id": "5236", "address": "Fröbelstraße 20, 01159 Dresden", "lat": 51.05216577633894, "lon": 13.714659672419806, "note": None},  # MSM hat 2 KdNr
    {"tourplan_kdnr": "40721", "alias": "Motor Mafia", "real_customer_id": "5000", "address": "Bärensteiner Str. 27-29, 01277 Dresden", "lat": 51.03523132671772, "lon": 13.803029497635833, "note": None},
    {"tourplan_kdnr": None, "alias": "MFH PF", "real_customer_id": "5236", "address": "Fröbelstraße 20, 01159 Dresden", "lat": 51.05216577633894, "lon": 13.714659672419806, "note": "PF"},  # KdNr fehlt
    
    # Einzeln
    {"tourplan_kdnr": "4993", "alias": "36 Nici zu RP", "real_customer_id": "4601", "address": "Mügelner Str. 29, 01237 Dresden", "lat": 51.013179, "lon": 13.804567, "note": "Automatikgetriebeservice"},
    {"tourplan_kdnr": "4727", "alias": "Hubraum", "real_customer_id": "5236", "address": "Fröbelstraße 20, 01159 Dresden", "lat": 51.05216577633894, "lon": 13.714659672419806, "note": None},
    {"tourplan_kdnr": "4916", "alias": "Astral UG", "real_customer_id": "5525", "address": "Löbtauer Straße 80, 01159 Dresden", "lat": 51.0470144, "lon": 13.7081843, "note": None},
    {"tourplan_kdnr": "4993", "alias": "Peter Söllner", "real_customer_id": "4426", "address": "August Bebel Strasse 82, 01728 Bannewitz", "note": "Kfz-Meisterbetrieb Söllner"},
    {"tourplan_kdnr": "4993", "alias": "Jens Spahn PF", "real_customer_id": "4043", "address": "Burgker Straße 145, 01705 Freital", "note": "autoBURGK Lohse"},
    {"tourplan_kdnr": "4993", "alias": "Jens Spahn - PF", "real_customer_id": "4043", "address": "Burgker Straße 145, 01705 Freital", "note": "autoBURGK Lohse"},
    {"tourplan_kdnr": "4993", "alias": "Jens Spahn-PF", "real_customer_id": "4043", "address": "Burgker Straße 145, 01705 Freital", "note": "autoBURGK Lohse"},
    {"tourplan_kdnr": "44993", "alias": "Schleich", "real_customer_id": None, "address": "Liebstädter Str. 45, 01796 Pirna", "lat": 50.93723, "lon": 13.9206719, "note": None},
    {"tourplan_kdnr": "5461", "alias": "Blumentritt", "real_customer_id": "2118", "address": "Straße des 17. Juni 16, 01257 Dresden", "note": "Blumentritt Diesel-Einspritztechnik"},
]


def parse_address(address_str):
    """Parst Adresse aus String wie 'Liebstädter Str. 45, 01796 Pirna'"""
    if not address_str:
        return None, None, None
    
    parts = address_str.split(',')
    if len(parts) >= 2:
        street = parts[0].strip()
        city_part = parts[1].strip()
        
        # Extrahiere PLZ und Stadt
        plz_match = city_part.split()
        if plz_match and plz_match[0].isdigit():
            postal_code = plz_match[0]
            city = ' '.join(plz_match[1:]) if len(plz_match) > 1 else ''
            return street, postal_code, city
    
    return address_str, None, None


def import_synonyms():
    """Importiert alle Synonyme in die Datenbank"""
    # Datenbank-Pfad finden
    db_path = PROJECT_ROOT / "data" / "traffic.db"
    if not db_path.exists():
        # Fallback: Versuche andere mögliche Pfade
        possible_paths = [
            PROJECT_ROOT / "data" / "traffic.db",
            PROJECT_ROOT / "data" / "address_corrections.sqlite3",
            Path("./data/traffic.db"),
            Path("data/traffic.db")
        ]
        for path in possible_paths:
            if path.exists():
                db_path = path
                break
    
    if not db_path.exists():
        print(f"[FEHLER] Datenbank nicht gefunden. Versuche: {db_path}")
        print(f"[FEHLER] Erstelle Datenbank-Verzeichnis...")
        db_path.parent.mkdir(parents=True, exist_ok=True)
    
    # SynonymStore initialisieren
    store = SynonymStore(db_path)
    
    print(f"[SYNONYM IMPORT] Öffne Datenbank: {db_path}")
    print(f"[SYNONYM IMPORT] Importiere {len(SYNONYM_DATA)} Synonyme...\n")
    
    imported = 0
    updated = 0
    errors = 0
    
    for entry in SYNONYM_DATA:
        tourplan_kdnr = entry.get("tourplan_kdnr")
        alias = entry.get("alias", "").strip()
        real_customer_id = entry.get("real_customer_id")
        address = entry.get("address")
        note = entry.get("note")
        
        if not alias:
            print(f"[WARN] Überspringe Eintrag ohne Alias: {entry}")
            errors += 1
            continue
        
        # Erstelle Synonym-Eintrag
        # Alias kann sowohl Name als auch KdNr sein
        lat = entry.get("lat")
        lon = entry.get("lon")
        
        synonym = Synonym(
            alias=alias,
            customer_id=str(real_customer_id) if real_customer_id else None,
            customer_name=alias,
            street=None,
            postal_code=None,
            city=None,
            country="DE",
            lat=float(lat) if lat is not None else None,
            lon=float(lon) if lon is not None else None,
            priority=1 if tourplan_kdnr else 0,  # Höhere Priorität wenn KdNr vorhanden
            active=1,
            note=f"Tourplan-KdNr: {tourplan_kdnr} | Echte KdNr: {real_customer_id} | {note or ''}".strip(" | ")
        )
        
        # Wenn Adresse vorhanden, parsen
        if address:
            street, postal_code, city = parse_address(address)
            synonym.street = street
            synonym.postal_code = postal_code
            synonym.city = city
        
        # Wenn KdNr vorhanden, erstelle zusätzlich Eintrag für KdNr → Echte KdNr/Adresse
        if tourplan_kdnr:
            kdnr_synonym = Synonym(
                alias=f"KdNr:{tourplan_kdnr}",
                customer_id=str(real_customer_id) if real_customer_id else None,
                customer_name=alias,
                street=synonym.street,
                postal_code=synonym.postal_code,
                city=synonym.city,
                country="DE",
                lat=synonym.lat,
                lon=synonym.lon,
                priority=2,  # Höchste Priorität für KdNr-Lookups
                active=1,
                note=f"Alias: {alias} | Echte KdNr: {real_customer_id} | {note or ''}".strip(" | ")
            )
            
            try:
                store.upsert(kdnr_synonym)
                print(f"[OK] KdNr:{tourplan_kdnr} -> {real_customer_id or address or 'Keine Adresse'}")
                imported += 1
            except Exception as e:
                print(f"[FEHLER] KdNr:{tourplan_kdnr}: {e}")
                errors += 1
        
        # Name-Alias eintragen (wenn Name vorhanden)
        if alias:
            try:
                existing = store.resolve(alias)
                if existing:
                    updated += 1
                    print(f"[UPDATE] {alias}")
                else:
                    imported += 1
                    print(f"[NEU] {alias}")
                store.upsert(synonym)
            except Exception as e:
                print(f"[FEHLER] {alias}: {e}")
                errors += 1
    
    print(f"\n[SYNONYM IMPORT] Fertig!")
    print(f"   Importiert: {imported}")
    print(f"   Aktualisiert: {updated}")
    print(f"   Fehler: {errors}")


if __name__ == "__main__":
    import_synonyms()

