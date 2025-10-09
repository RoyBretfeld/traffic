#!/usr/bin/env python3
"""
Address-Analyzer Service
Sammelt und analysiert nicht erkannte Adressen aus Tourplänen
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Set, Optional, Any
from backend.services.address_mapper import address_mapper
from backend.services.geocode import geocode_address
from backend.db.dao import get_kunde_id_by_name_adresse, get_kunde_by_id
import json
from datetime import datetime

class AddressAnalyzer:
    def __init__(self):
        self.unrecognized_addresses = set()
        self.analysis_results = []
        self.suggestions = []
    
    def analyze_tour_plan(self, tour_plan_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analysiere einen Tourplan auf nicht erkannte Adressen
        
        Args:
            tour_plan_data: Geparster Tourplan-Daten
            
        Returns:
            Analyse-Ergebnisse mit nicht erkannten Adressen und Vorschlägen
        """
        print(f"[AddressAnalyzer] Analysiere Tourplan...")
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_customers": 0,
            "recognized_addresses": 0,
            "unrecognized_addresses": [],
            "suggestions": [],
            "database_matches": [],
            "mapping_suggestions": []
        }
        
        for tour in tour_plan_data.get('tours', []):
            tour_name = tour.get('name', 'Unbekannt')
            customers = tour.get('customers', [])
            
            print(f"[AddressAnalyzer] Tour: {tour_name} ({len(customers)} Kunden)")
            
            for customer in customers:
                analysis["total_customers"] += 1
                
                name = customer.get("name", "").strip()
                street = customer.get("street", "").strip()
                postal_code = customer.get("postal_code", "").strip()
                city = customer.get("city", "").strip()
                
                # Prüfe ob Adresse vollständig ist
                if not street or not postal_code or not city:
                    analysis["unrecognized_addresses"].append({
                        "type": "incomplete_address",
                        "customer_name": name,
                        "address_parts": {
                            "street": street,
                            "postal_code": postal_code,
                            "city": city
                        },
                        "tour": tour_name,
                        "suggestion": "Adresse vervollständigen"
                    })
                    continue
                
                full_address = f"{street}, {postal_code} {city}"
                
                # 1. Prüfe Address-Mapper (BAR-Sondernamen, etc.)
                mapping_result = address_mapper.map_address(name)
                if mapping_result['confidence'] > 0:
                    analysis["recognized_addresses"] += 1
                    continue
                
                # 2. Prüfe Datenbank
                kunde_id = get_kunde_id_by_name_adresse(name, full_address)
                if kunde_id:
                    kunde_obj = get_kunde_by_id(kunde_id)
                    if kunde_obj and kunde_obj.lat and kunde_obj.lon:
                        analysis["recognized_addresses"] += 1
                        analysis["database_matches"].append({
                            "customer_name": name,
                            "address": full_address,
                            "tour": tour_name,
                            "kunde_id": kunde_id,
                            "coordinates": f"{kunde_obj.lat}, {kunde_obj.lon}"
                        })
                        continue
                
                # 3. Prüfe Geocoding
                geo_result = geocode_address(full_address)
                if geo_result and geo_result.get('lat') and geo_result.get('lon'):
                    analysis["recognized_addresses"] += 1
                    continue
                
                # 4. Nicht erkannt - sammle für Analyse
                unrecognized = {
                    "type": "unrecognized",
                    "customer_name": name,
                    "address": full_address,
                    "tour": tour_name,
                    "suggestions": self._generate_suggestions(name, full_address)
                }
                
                analysis["unrecognized_addresses"].append(unrecognized)
                
                # Generiere Mapping-Vorschläge
                mapping_suggestion = self._generate_mapping_suggestion(name, full_address)
                if mapping_suggestion:
                    analysis["mapping_suggestions"].append(mapping_suggestion)
        
        # Berechne Statistiken
        analysis["recognition_rate"] = (
            analysis["recognized_addresses"] / analysis["total_customers"] * 100 
            if analysis["total_customers"] > 0 else 0
        )
        
        self.analysis_results.append(analysis)
        return analysis
    
    def _generate_suggestions(self, name: str, address: str) -> List[str]:
        """Generiere Vorschläge für nicht erkannte Adressen"""
        suggestions = []
        
        # Prüfe ob es ein BAR-Sondername sein könnte
        if any(keyword in name.lower() for keyword in ['autohaus', 'autoservice', 'werkstatt', 'garage', 'halle']):
            suggestions.append(f"Möglicher BAR-Sondername: '{name}' -> echte Adresse hinzufügen")
        
        # Prüfe Adress-Pattern
        if 'OT ' in address:
            suggestions.append(f"OT-Angabe entfernen: '{address}' -> '{address.replace(' OT ', ' ')}'")
        
        if '| Halle' in address:
            suggestions.append(f"Halle-Angabe entfernen: '{address}' -> '{address.split(' | Halle')[0]}'")
        
        if '(' in address and ')' in address:
            suggestions.append(f"Klammer-Angaben entfernen: '{address}' -> '{address.split('(')[0].strip()}'")
        
        # Prüfe ähnliche Namen in Datenbank
        similar_names = self._find_similar_names_in_db(name)
        if similar_names:
            suggestions.append(f"Ähnliche Namen in DB gefunden: {', '.join(similar_names[:3])}")
        
        return suggestions
    
    def _generate_mapping_suggestion(self, name: str, address: str) -> Optional[Dict]:
        """Generiere Mapping-Vorschlag für Konfiguration"""
        # Prüfe ob es ein BAR-Sondername ist
        if any(keyword in name.lower() for keyword in ['autohaus', 'autoservice', 'werkstatt', 'garage', 'halle']):
            return {
                "type": "bar_sondername",
                "sondername": name,
                "echte_adresse": address,
                "suggested_lat": None,
                "suggested_lon": None,
                "kategorie": self._guess_category(name),
                "confidence": 0.8
            }
        
        # Prüfe ob Adress-Korrektur nötig ist
        if 'OT ' in address or '| Halle' in address or '(' in address:
            corrected = address
            if 'OT ' in corrected:
                corrected = corrected.replace(' OT ', ' ')
            if '| Halle' in corrected:
                corrected = corrected.split(' | Halle')[0]
            if '(' in corrected and ')' in corrected:
                corrected = corrected.split('(')[0].strip()
            
            if corrected != address:
                return {
                    "type": "address_mapping",
                    "pattern": address,
                    "corrected_address": corrected,
                    "suggested_lat": None,
                    "suggested_lon": None,
                    "reason": "Adress-Korrektur",
                    "priority": 2
                }
        
        return None
    
    def _find_similar_names_in_db(self, name: str) -> List[str]:
        """Finde ähnliche Namen in der Datenbank"""
        # TODO: Implementiere ähnliche Namenssuche in der Datenbank
        return []
    
    def _guess_category(self, name: str) -> str:
        """Errate Kategorie basierend auf Namen"""
        name_lower = name.lower()
        
        if 'autohaus' in name_lower:
            return 'autohaus'
        elif 'autoservice' in name_lower or 'werkstatt' in name_lower:
            return 'autoservice'
        elif 'halle' in name_lower or 'teile' in name_lower:
            return 'teilehandel'
        else:
            return 'unknown'
    
    def save_analysis_report(self, filename: str = None) -> str:
        """Speichere Analyse-Bericht"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"address_analysis_{timestamp}.json"
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "total_analyses": len(self.analysis_results),
            "analyses": self.analysis_results
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"[AddressAnalyzer] Analyse-Bericht gespeichert: {filename}")
        return filename
    
    def generate_mapping_suggestions_file(self, filename: str = None) -> str:
        """Generiere Datei mit Mapping-Vorschlägen"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"mapping_suggestions_{timestamp}.json"
        
        all_suggestions = []
        for analysis in self.analysis_results:
            all_suggestions.extend(analysis.get("mapping_suggestions", []))
        
        suggestions_file = {
            "timestamp": datetime.now().isoformat(),
            "description": "Vorgeschlagene Mappings für address_mappings.json",
            "suggestions": all_suggestions
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(suggestions_file, f, indent=2, ensure_ascii=False)
        
        print(f"[AddressAnalyzer] Mapping-Vorschläge gespeichert: {filename}")
        return filename
    
    def print_summary(self, analysis: Dict[str, Any]):
        """Drucke Zusammenfassung der Analyse"""
        print(f"\nADDRESS-ANALYSE ZUSAMMENFASSUNG")
        print("=" * 50)
        print(f"Gesamt Kunden: {analysis['total_customers']}")
        print(f"Erkannt: {analysis['recognized_addresses']} ({analysis['recognition_rate']:.1f}%)")
        print(f"Nicht erkannt: {len(analysis['unrecognized_addresses'])}")
        print(f"Datenbank-Matches: {len(analysis['database_matches'])}")
        print(f"Mapping-Vorschläge: {len(analysis['mapping_suggestions'])}")
        
        if analysis['unrecognized_addresses']:
            print(f"\nNICHT ERKANNTE ADRESSEN:")
            print("-" * 30)
            for i, addr in enumerate(analysis['unrecognized_addresses'][:10], 1):  # Zeige nur erste 10
                print(f"{i}. {addr['customer_name']} - {addr.get('address', 'Unvollständig')}")
                if addr.get('suggestions'):
                    for suggestion in addr['suggestions'][:2]:  # Zeige nur erste 2 Vorschläge
                        print(f"   -> {suggestion}")
                print()
            
            if len(analysis['unrecognized_addresses']) > 10:
                print(f"   ... und {len(analysis['unrecognized_addresses']) - 10} weitere")

# Globale Instanz
address_analyzer = AddressAnalyzer()
