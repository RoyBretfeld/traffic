"""
FAMO TrafficApp - Intelligente Adress-Korrektur
Korrigiert problematische Adressen automatisch und speichert sie in der Datenbank
"""

from __future__ import annotations
import re
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
try:
    from .geocode import geocode_address
    from ..db.dao import geocache_get, geocache_set
except ImportError:
    # Für direkten Test
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
    from backend.services.geocode import geocode_address
    from backend.db.dao import geocache_get, geocache_set


@dataclass
class AddressCorrection:
    """Repräsentiert eine Adress-Korrektur"""
    original_address: str
    corrected_address: str
    lat: float
    lon: float
    postal_code: Optional[str]
    city: Optional[str]
    correction_type: str
    success: bool


class AddressCorrector:
    """Intelligente Adress-Korrektur für problematische Geocoding-Fälle"""
    
    def __init__(self):
        # Firmenumzüge-Mapping für dauerhafte Adress-Korrekturen
        # CAR-ART GmbH hat ZWEI Filialen - beide sind korrekt!
        self.company_moves = {
            # Keine automatischen Umleitungen mehr - beide Adressen sind gültig
        }
        
        # Intelligente Adress-Abgleichung zwischen CSV und Datenbank
        self.database_address_mappings = {
            # Bekannte Adress-Varianten die automatisch erkannt werden sollen
            "Gewerbegebiet Kaltes Feld 36, 08468 Heinsdorfergrund": "Kaltes Feld 36, 08468 Heinsdorfergrund",
            "Hohensteiner Str. 101, 09212 Limbach-O./OT Pleißa": "Hohensteiner Str. 101, 09212 Limbach-Oberfrohna",
            "Enno-Heidebroeck-Str. 11, 01237 Dresden": "Enno-Heidebroeck-Str. 11, 01237 Dresden",
            "Dresdner Str. 5, 02977 Hoyerswerda": "Dresdner Straße 5, 02977 Hoyerswerda",
        }
        
        # Bekannte Korrekturen basierend auf unseren Tests
        self.correction_patterns = [
            # Bindestriche entfernen
            (r'Alt-Serkowitz', 'Altserkowitz'),
            (r'Alt-(\w+)', r'Alts\1'),
            
            # Abkürzungen auflösen - spezifische Fälle
            (r'Dresdener Str\.', 'Dresdener Straße'),
            (r'Dresdner Str\.', 'Dresdner Straße'),
            (r'Straae', 'Straße'),
            (r'Strasse', 'Straße'),
            (r'Straáe', 'Straße'),
            (r'Strasze', 'Straße'),
            (r'Stráe', 'Straße'),
            (r'Stalstraße', 'Stalstraße'),
            (r'Strasse', 'Straße'),
            (r'\bStr\s*aa\s*e\b', 'Straße'),
            (r'Ringstr\.', 'Ringstraße'),
            (r'(\w+)str\.', r'\1straße'),
            (r'(\w+)str ', r'\1straße '),
            
            # Ortsteil-Abkürzungen entfernen - intelligente Lösung
            (r'([^,]+) OT [^,]+', r'\1'),           # "Kreischa OT Wittgensdorf" -> "Kreischa"
            (r'([^,]+) / OT [^,]+', r'\1'),         # "Moritzburg / OT Boxdorf" -> "Moritzburg"
            (r'([^,]+)-OT [^,]+', r'\1'),           # "Sehmatal-OT Sehma" -> "Sehmatal"
            (r'([^,]+)/OT [^,]+', r'\1'),           # "Bannewitz/OT Possendorf" -> "Bannewitz"
            
            # Relative Beschreibungen entfernen
            (r'Gegenüber [^,]+', ''),
            (r'Gegenüber [^,]+?(\d+[a-z]?)', r'\1'),
            
            # Komplexe Zusätze entfernen
            (r' / Halle [^,]+', ''),
            (r' / [^,]+', ''),
            
            # Mehrfache Leerzeichen bereinigen
            (r'\s+', ' '),
            (r'^\s+|\s+$', ''),
        ]
        
        # Spezielle Fallback-Korrekturen für bekannte problematische Adressen
        self.special_corrections = {
            'Gegenüber Prießnitztalstr. 14, 01768 Glashütte': 'Prießnitztalstraße 16, 01768 Glashütte',
            'Naumannstr. 12 / Halle 26F, 01809 Heidenau': 'Naumannstraße 12, 01809 Heidenau',
            'Dresdener Str. 5, 02977 Hoyerswerda': 'Dresdener Straße 5, 02977 Hoyerswerda',
            'Straae des Friedens 37, 01723 Kesselsdorf, Deutschland': 'Straße des Friedens 37, 01723 Kesselsdorf, Deutschland',
            'Nikolaus-Otto-Straae 3, 55129 Mainz, Deutschland': 'Nikolaus-Otto-Straße 3, 55129 Mainz, Deutschland',
        }
    
    def correct_address(self, address: str) -> AddressCorrection:
        """Korrigiert eine problematische Adresse und versucht Geocoding"""
        
        print(f"[ADDR] Korrigiere Adresse: {address}")
        
        # 0. Intelligente Datenbank-Abgleichung prüfen
        if address in self.database_address_mappings:
            corrected_address = self.database_address_mappings[address]
            print(f"   -> Datenbank-Mapping: {corrected_address}")
            
            # Prüfe ob die korrigierte Adresse bereits in der Datenbank existiert
            from ..db.dao import get_kunde_id_by_name_adresse, get_kunde_by_id
            import sqlite3
            from ..db.config import get_database_path
            
            # Suche direkt nach der korrigierten Adresse in der Datenbank
            with sqlite3.connect(get_database_path()) as conn:
                cur = conn.execute('SELECT id, name, adresse, lat, lon FROM kunden WHERE adresse = ?', (corrected_address,))
                kunde_row = cur.fetchone()
            
            if kunde_row and kunde_row[3] and kunde_row[4] and kunde_row[3] != 0 and kunde_row[4] != 0:
                print(f"   -> [CACHE HIT] Gefunden in Datenbank: {kunde_row[3]}, {kunde_row[4]}")
                geocache_set(address, kunde_row[3], kunde_row[4], "database_mapping")
                return AddressCorrection(
                    original_address=address,
                    corrected_address=corrected_address,
                    lat=kunde_row[3],
                    lon=kunde_row[4],
                    postal_code=None,
                    city=None,
                    correction_type="database_mapping",
                    success=True
                )
        
        # 1. Firmenumzüge prüfen
        for company, moves in self.company_moves.items():
            for old_addr, new_addr in moves.items():
                if old_addr in address:
                    # Ersetze nur die Adresse, behalte Firmenname
                    corrected = address.replace(old_addr, new_addr)
                    print(f"   -> Firmenumzug: {old_addr} -> {new_addr}")
                    # Geocode nur die neue Adresse (ohne Firmenname)
                    geo_info = geocode_address(new_addr)
                    if geo_info:
                        lat = geo_info.get('lat')
                        lon = geo_info.get('lon')
                        provider = geo_info.get('provider')
                        geocache_set(address, lat, lon, "company_move")
                        return AddressCorrection(
                            original_address=address,
                            corrected_address=corrected,
                            lat=lat,
                            lon=lon,
                            postal_code=geo_info.get("postal_code"),
                            city=geo_info.get("city"),
                            correction_type="company_move",
                            success=True
                        )
        
        # 2. Spezielle Korrektur probieren
        if address in self.special_corrections:
            corrected = self.special_corrections[address]
            print(f"   -> Spezielle Korrektur: {corrected}")
            geo_info = geocode_address(corrected)
            if geo_info:
                lat = geo_info.get('lat')
                lon = geo_info.get('lon')
                provider = geo_info.get('provider')
                geocache_set(address, lat, lon, "address_corrector")
                return AddressCorrection(
                    original_address=address,
                    corrected_address=corrected,
                    lat=lat,
                    lon=lon,
                    postal_code=geo_info.get("postal_code"),
                    city=geo_info.get("city"),
                    correction_type="special_correction",
                    success=True
                )
        
        # 2. Pattern-basierte Korrekturen probieren
        for pattern, replacement in self.correction_patterns:
            corrected = re.sub(pattern, replacement, address)
            if corrected != address:
                print(f"   -> Pattern-Korrektur: {corrected}")
                result = geocode_address(corrected)
                if result:
                    lat = result.get('lat')
                    lon = result.get('lon')
                    provider = result.get('provider')
                    geocache_set(address, lat, lon, "address_corrector")
                    postal_code = result.get("postal_code")
                    city = result.get("city")
                    return AddressCorrection(
                        original_address=address,
                        corrected_address=corrected,
                        lat=lat,
                        lon=lon,
                        postal_code=postal_code,
                        city=city,
                        correction_type="pattern_correction",
                        success=True
                    )
        
        # 3. Vereinfachte Adresse probieren (nur Straße + Hausnummer + PLZ + Stadt)
        simplified = self._simplify_address(address)
        if simplified != address:
            print(f"   -> Vereinfachung: {simplified}")
            result = geocode_address(simplified)
            if result:
                lat = result["lat"]
                lon = result["lon"]
                geocache_set(address, lat, lon, "address_corrector")
                return AddressCorrection(
                    original_address=address,
                    corrected_address=simplified,
                    lat=lat,
                    lon=lon,
                    postal_code=result.get("postal_code"),
                    city=result.get("city"),
                    correction_type="simplification",
                    success=True
                )
        
        # 4. Alle Versuche fehlgeschlagen
        print(f"   [X] Alle Korrekturen fehlgeschlagen")
        return AddressCorrection(
            original_address=address,
            corrected_address=address,
            lat=0.0,
            lon=0.0,
            postal_code=None,
            city=None,
            correction_type="failed",
            success=False
        )
    
    def _simplify_address(self, address: str) -> str:
        """Vereinfacht eine Adresse auf das Wesentliche"""
        # Extrahiere PLZ und Stadt
        plz_city_match = re.search(r'(\d{5}),\s*([^,]+)$', address)
        if not plz_city_match:
            return address
        
        plz, city = plz_city_match.groups()
        
        # Extrahiere Straße und Hausnummer
        street_match = re.search(r'^([^,]+?)(\d+[a-z]?)', address)
        if not street_match:
            return address
        
        street, house_number = street_match.groups()
        
        # Bereinige Straßennamen
        street = re.sub(r'[^\w\s]', '', street).strip()
        
        return f"{street} {house_number}, {plz} {city}"
    
    def batch_correct_addresses(self, addresses: List[str]) -> List[AddressCorrection]:
        """Korrigiert mehrere Adressen in einem Batch"""
        results = []
        
        print(f"[BATCH] Starte Batch-Korrektur fuer {len(addresses)} Adressen...")
        
        for i, address in enumerate(addresses, 1):
            print(f"\n[{i}/{len(addresses)}] Bearbeite: {address}")
            
            # Prüfe zuerst Cache
            cached = geocache_get(address)
            if cached:
                print(f"   [CACHE] Aus Cache: {cached}")
                results.append(AddressCorrection(
                    original_address=address,
                    corrected_address=address,
                    lat=cached[0],
                    lon=cached[1],
                    correction_type="cached",
                    success=True
                ))
                continue
            
            # Versuche Korrektur
            correction = self.correct_address(address)
            results.append(correction)
            
            if correction.success:
                print(f"   [OK] Korrigiert: {correction.corrected_address}")
            else:
                print(f"   [X] Fehlgeschlagen")
        
        # Statistiken
        successful = sum(1 for r in results if r.success)
        print(f"\n[BATCH] Batch-Korrektur abgeschlossen:")
        print(f"   [OK] Erfolgreich: {successful}/{len(addresses)}")
        print(f"   [X] Fehlgeschlagen: {len(addresses) - successful}")
        
        return results


# Globale Instanz
address_corrector = AddressCorrector()


async def main():
    """Test-Funktion für den AddressCorrector"""
    print("[ADDR] FAMO AddressCorrector Test:")
    print("=" * 50)
    
    # Test-Adressen
    test_addresses = [
        "Alt-Serkowitz 1, 01445 Radebeul",
        "Ringstr. 43, 01468 Moritzburg OT Boxdorf",
        "Gegenüber Prießnitztalstr. 14, 01768 Glashütte",
        "Naumannstr. 12 / Halle 26F, 01809 Heidenau",
        "Dresdener Str. 5, 02977 Hoyerswerda"
    ]
    
    print(f"Teste {len(test_addresses)} problematische Adressen...\n")
    
    # Batch-Korrektur durchführen
    results = address_corrector.batch_correct_addresses(test_addresses)
    
    print("\n" + "=" * 50)
    print("[DETAIL] Detaillierte Ergebnisse:")
    
    for result in results:
        status = "[OK]" if result.success else "[X]"
        print(f"{status} {result.original_address}")
        if result.success:
            print(f"   -> {result.corrected_address}")
            print(f"   -> {result.lat}, {result.lon}")
            print(f"   -> Typ: {result.correction_type}")
        print()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
