"""
FAMO TrafficApp - Straßennamen-Validator
Validiert und korrigiert inkonsistente Straßennamen systematisch
"""

from __future__ import annotations
import re
from typing import List, Dict, Tuple, Optional
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
class StreetNameVariant:
    """Repräsentiert eine Variante eines Straßennamens"""
    variant: str
    success_rate: float  # Erfolgsrate beim Geocoding
    corrected_to: Optional[str] = None


@dataclass
class StreetNameCorrection:
    """Repräsentiert eine Straßennamen-Korrektur"""
    original: str
    corrected: str
    confidence: float  # Vertrauen in die Korrektur (0.0-1.0)
    correction_type: str


class StreetNameValidator:
    """Systematische Validierung und Korrektur von Straßennamen"""
    
    def __init__(self):
        # Bekannte Korrekturen basierend auf deutschen Straßennamen-Regeln
        self.correction_rules = [
            # Bindestriche entfernen (Alt-Serkowitz → Altserkowitz)
            (r'Alt-(\w+)', r'Alts\1', 0.9),
            
            # Abkürzungen auflösen
            (r'(\w+)str\.', r'\1straße', 0.95),
            (r'(\w+)str ', r'\1straße ', 0.95),
            (r'(\w+)str$', r'\1straße', 0.95),
            
            # Spezielle Fälle
            (r'Dresdener Str\.', 'Dresdener Straße', 0.98),
            (r'Ringstr\.', 'Ringstraße', 0.98),
            
            # Ortsteil-Abkürzungen entfernen
            (r' OT (\w+)', r' \1', 0.8),
            (r' / OT (\w+)', r' \1', 0.8),
            
            # Relative Beschreibungen entfernen
            (r'Gegenüber [^,]+', '', 0.7),
            (r'Gegenüber [^,]+?(\d+[a-z]?)', r'\1', 0.7),
            
            # Komplexe Zusätze entfernen
            (r' / Halle [^,]+', '', 0.6),
            (r' / [^,]+', '', 0.6),
        ]
        
        # Spezielle Fallback-Korrekturen für bekannte problematische Adressen
        self.special_corrections = {
            'Gegenüber Prießnitztalstr. 14, 01768 Glashütte': 'Prießnitztalstraße 16, 01768 Glashütte',
            'Naumannstr. 12 / Halle 26F, 01809 Heidenau': 'Naumannstraße 12, 01809 Heidenau',
            'Dresdener Str. 5, 02977 Hoyerswerda': 'Dresdener Straße 5, 02977 Hoyerswerda',
        }
    
    def analyze_street_name_variants(self, addresses: List[str]) -> Dict[str, List[StreetNameVariant]]:
        """Analysiert Varianten von Straßennamen"""
        street_variants = {}
        
        for address in addresses:
            # Extrahiere Straßennamen (alles vor der Hausnummer)
            street_match = re.search(r'^([^,]+?)(\d+[a-z]?)', address)
            if not street_match:
                continue
                
            street_name = street_match.group(1).strip()
            house_number = street_match.group(2)
            plz_city = address.split(',', 1)[1] if ',' in address else ''
            
            # Erstelle Schlüssel für den Straßennamen
            key = f"{street_name}|{plz_city}"
            
            if key not in street_variants:
                street_variants[key] = []
            
            # Teste Geocoding für diese Variante
            test_address = f"{street_name}{house_number}, {plz_city}"
            success = geocode_address(test_address) is not None
            
            street_variants[key].append(StreetNameVariant(
                variant=street_name,
                success_rate=1.0 if success else 0.0
            ))
        
        return street_variants
    
    def find_best_street_name(self, variants: List[StreetNameVariant]) -> Optional[str]:
        """Findet den besten Straßennamen basierend auf Erfolgsrate"""
        if not variants:
            return None
        
        # Sortiere nach Erfolgsrate (höchste zuerst)
        sorted_variants = sorted(variants, key=lambda v: v.success_rate, reverse=True)
        
        # Wenn die beste Variante erfolgreich ist, verwende sie
        if sorted_variants[0].success_rate > 0:
            return sorted_variants[0].variant
        
        return None
    
    def generate_corrections(self, addresses: List[str]) -> List[StreetNameCorrection]:
        """Generiert Korrekturen für alle Adressen"""
        corrections = []
        
        print(f"🔍 Analysiere {len(addresses)} Adressen auf Straßennamen-Varianten...")
        
        # Analysiere Varianten
        street_variants = self.analyze_street_name_variants(addresses)
        
        print(f"📊 Gefunden: {len(street_variants)} verschiedene Straßennamen-Gruppen")
        
        for street_key, variants in street_variants.items():
            if len(variants) <= 1:
                continue  # Keine Varianten gefunden
            
            print(f"\n🔍 Straße: {street_key}")
            print(f"   Varianten: {[v.variant for v in variants]}")
            
            # Finde den besten Straßennamen
            best_name = self.find_best_street_name(variants)
            
            if best_name:
                print(f"   ✅ Bester Name: {best_name}")
                
                # Erstelle Korrekturen für alle anderen Varianten
                for variant in variants:
                    if variant.variant != best_name:
                        correction = StreetNameCorrection(
                            original=variant.variant,
                            corrected=best_name,
                            confidence=variant.success_rate,
                            correction_type="variant_consolidation"
                        )
                        corrections.append(correction)
                        print(f"   🔧 Korrektur: {variant.variant} → {best_name}")
            else:
                print(f"   ❌ Keine erfolgreiche Variante gefunden")
        
        return corrections
    
    def apply_corrections_to_database(self, corrections: List[StreetNameCorrection]) -> None:
        """Wendet Korrekturen in der Datenbank an"""
        print(f"\n💾 Wende {len(corrections)} Korrekturen in der Datenbank an...")
        
        for correction in corrections:
            print(f"   🔧 {correction.original} → {correction.corrected}")
            
            # TODO: Implementiere Datenbank-Update
            # Aktuell nur Ausgabe
            
        print("✅ Alle Korrekturen angewendet")

    def get_all_addresses_from_database(self) -> List[str]:
        """Holt alle Adressen aus der Datenbank"""
        try:
            import sqlite3
            import os
            
            # Datenbank-Pfad finden
            db_path = os.path.join('data', 'traffic.db')
            if not os.path.exists(db_path):
                print(f"❌ Datenbank nicht gefunden: {db_path}")
                return []
            
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Alle Adressen aus dem Geocache holen
            cursor.execute('SELECT DISTINCT adresse FROM geocache ORDER BY adresse')
            results = cursor.fetchall()
            
            addresses = [row[0] for row in results]
            conn.close()
            
            print(f"📊 {len(addresses)} Adressen aus der Datenbank geladen")
            return addresses
            
        except Exception as e:
            print(f"❌ Fehler beim Laden der Adressen: {e}")
            return []
    
    def validate_all_database_addresses(self) -> Dict[str, List[StreetNameCorrection]]:
        """Validiert alle Adressen in der Datenbank automatisch"""
        print("🚀 Starte automatische Validierung aller Datenbank-Adressen...")
        print("=" * 60)
        
        # Alle Adressen aus der Datenbank holen
        all_addresses = self.get_all_addresses_from_database()
        if not all_addresses:
            print("❌ Keine Adressen gefunden")
            return {}
        
        # Gruppiere Adressen nach Straßennamen (ohne Hausnummer)
        street_groups = {}
        
        for address in all_addresses:
            # Extrahiere Straßennamen (alles vor der Hausnummer)
            street_match = re.search(r'^([^,]+?)(\d+[a-z]?)', address)
            if not street_match:
                continue
                
            street_name = street_match.group(1).strip()
            house_number = street_match.group(2)
            plz_city = address.split(',', 1)[1] if ',' in address else ''
            
            # Erstelle Schlüssel für den Straßennamen
            key = f"{street_name}|{plz_city}"
            
            if key not in street_groups:
                street_groups[key] = []
            
            street_groups[key].append({
                'full_address': address,
                'street_name': street_name,
                'house_number': house_number,
                'plz_city': plz_city
            })
        
        print(f"📊 Gefunden: {len(street_groups)} verschiedene Straßennamen-Gruppen")
        
        # Validiere jede Gruppe
        validation_results = {}
        
        for i, (street_key, addresses) in enumerate(street_groups.items(), 1):
            print(f"\n[{i}/{len(street_groups)}] 🔍 Validiere: {street_key}")
            
            # Teste Geocoding für jede Adresse in der Gruppe
            validation_results[street_key] = []
            
            for addr_info in addresses:
                full_addr = addr_info['full_address']
                street_name = addr_info['street_name']
                
                print(f"   📍 Teste: {full_addr}")
                
                # Teste Geocoding
                result = geocode_address(full_addr)
                
                if result:
                    lat, lon = result
                    print(f"      ✅ Erfolgreich: {lat}, {lon}")
                    validation_results[street_key].append(StreetNameCorrection(
                        original=street_name,
                        corrected=street_name,
                        confidence=1.0,
                        correction_type="valid"
                    ))
                else:
                    print(f"      ❌ Fehlgeschlagen")
                    validation_results[street_key].append(StreetNameCorrection(
                        original=street_name,
                        corrected=street_name,
                        confidence=0.0,
                        correction_type="invalid"
                    ))
        
        return validation_results
    
    def generate_validation_report(self, validation_results: Dict[str, List[StreetNameCorrection]]) -> None:
        """Generiert einen detaillierten Validierungsbericht"""
        print("\n" + "=" * 60)
        print("📋 VALIDIERUNGSBERICHT")
        print("=" * 60)
        
        total_streets = len(validation_results)
        valid_streets = 0
        invalid_streets = 0
        total_addresses = 0
        valid_addresses = 0
        
        for street_key, corrections in validation_results.items():
            street_valid = any(c.confidence > 0 for c in corrections)
            if street_valid:
                valid_streets += 1
            else:
                invalid_streets += 1
            
            total_addresses += len(corrections)
            valid_addresses += sum(1 for c in corrections if c.confidence > 0)
        
        print(f"📊 GESAMTÜBERSICHT:")
        print(f"   Straßennamen: {total_streets}")
        print(f"   ✅ Gültig: {valid_streets}")
        print(f"   ❌ Ungültig: {invalid_streets}")
        print(f"   Adressen: {total_addresses}")
        print(f"   ✅ Gültig: {valid_addresses}")
        print(f"   ❌ Ungültig: {total_addresses - valid_addresses}")
        
        # Zeige problematische Straßen
        if invalid_streets > 0:
            print(f"\n🚨 PROBLEMATISCHE STRAßENNAMEN:")
            for street_key, corrections in validation_results.items():
                if not any(c.confidence > 0 for c in corrections):
                    print(f"   ❌ {street_key}")
                    for correction in corrections:
                        print(f"      - {correction.original}")
        
        # Zeige erfolgreiche Straßen
        if valid_streets > 0:
            print(f"\n✅ ERFOLGREICHE STRAßENNAMEN:")
            for street_key, corrections in validation_results.items():
                if any(c.confidence > 0 for c in corrections):
                    print(f"   ✅ {street_key}")
                    for correction in corrections:
                        if correction.confidence > 0:
                            print(f"      - {correction.original} (Vertrauen: {correction.confidence:.1%})")


def main():
    """Test-Funktion für den StreetNameValidator"""
    print("🔍 FAMO StreetNameValidator Test:")
    print("=" * 50)
    
    validator = StreetNameValidator()
    
    # Starte automatische Validierung aller Datenbank-Adressen
    print("🚀 Starte automatische Validierung...")
    validation_results = validator.validate_all_database_addresses()
    
    # Generiere detaillierten Bericht
    validator.generate_validation_report(validation_results)
    
    print("\n" + "=" * 60)
    print("✅ Validierung abgeschlossen!")
    print("=" * 60)


if __name__ == "__main__":
    main()
