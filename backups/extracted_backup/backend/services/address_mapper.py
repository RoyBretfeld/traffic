#!/usr/bin/env python3
"""
Intelligenter Address-Mapper Service
Verwendet Konfigurationsdatei für spezielle Adress-Mappings und Korrekturen
"""

import json
import re
import os
from typing import Dict, List, Optional, Tuple, Any
from difflib import SequenceMatcher

class AddressMapper:
    def __init__(self, config_file: str = "address_mappings.json"):
        """Initialisiere den Address-Mapper mit Konfigurationsdatei"""
        self.config_file = config_file
        self.mappings = []
        self.rules = []
        self.fallback_strategies = []
        self.load_config()
    
    def load_config(self):
        """Lade Konfiguration aus JSON-Datei"""
        # Initialisiere alle Attribute mit Standardwerten
        self.mappings = []
        self.rules = []
        self.fallback_strategies = []
        self.bar_sondernamen = []
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.mappings = config.get('mappings', [])
                    self.rules = config.get('rules', [])
                    self.fallback_strategies = config.get('fallback_strategies', [])
                    self.bar_sondernamen = config.get('bar_sondernamen', [])
                print(f"[AddressMapper] Konfiguration geladen: {len(self.mappings)} Mappings, {len(self.rules)} Regeln, {len(self.bar_sondernamen)} BAR-Sondernamen")
            else:
                print(f"[AddressMapper] WARNUNG: Konfigurationsdatei {self.config_file} nicht gefunden - verwende Standardwerte")
        except Exception as e:
            print(f"[AddressMapper] FEHLER beim Laden der Konfiguration: {e} - verwende Standardwerte")
    
    def find_exact_mapping(self, address: str) -> Optional[Dict]:
        """Suche exakte Adress-Übereinstimmung in Mappings"""
        for mapping in self.mappings:
            if mapping['pattern'] == address:
                return mapping
        return None
    
    def find_fuzzy_mapping(self, address: str, threshold: float = 0.8) -> Optional[Dict]:
        """Suche ähnliche Adressen in Mappings"""
        best_match = None
        best_similarity = 0.0
        
        for mapping in self.mappings:
            similarity = SequenceMatcher(None, address.lower(), mapping['pattern'].lower()).ratio()
            if similarity >= threshold and similarity > best_similarity:
                best_match = mapping
                best_similarity = similarity
        
        return best_match
    
    def find_bar_sondername(self, address: str) -> Optional[Dict]:
        """Suche BAR-Sondername zu echter Adresse"""
        # Exakte Übereinstimmung
        for bar_entry in self.bar_sondernamen:
            if bar_entry['sondername'].lower() == address.lower():
                return bar_entry
        
        # Fuzzy-Matching für ähnliche Namen
        best_match = None
        best_similarity = 0.0
        
        for bar_entry in self.bar_sondernamen:
            similarity = SequenceMatcher(None, address.lower(), bar_entry['sondername'].lower()).ratio()
            if similarity >= 0.7 and similarity > best_similarity:  # Niedrigere Schwelle für BAR-Namen
                best_match = bar_entry
                best_similarity = similarity
        
        return best_match
    
    def apply_rules(self, address: str) -> str:
        """Wende Regeln auf Adresse an"""
        corrected_address = address
        
        # Sortiere Regeln nach Priorität (niedrigere Zahl = höhere Priorität)
        sorted_rules = sorted(self.rules, key=lambda x: x.get('priority', 999))
        
        for rule in sorted_rules:
            try:
                pattern = rule['pattern']
                replacement = rule['replacement']
                
                # Verwende Regex für Pattern-Matching
                if re.search(pattern, corrected_address):
                    if replacement == ".*":
                        # Spezielle Behandlung für OT-Entfernung
                        if "OT " in corrected_address:
                            corrected_address = re.sub(r'\s*\([^)]*OT[^)]*\)', '', corrected_address)
                            corrected_address = re.sub(r'\s*OT\s+[^,]+', '', corrected_address)
                        elif "| Halle" in corrected_address:
                            corrected_address = re.sub(r'\s*\|\s*Halle\s+\d+', '', corrected_address)
                        elif "(" in corrected_address and ")" in corrected_address:
                            corrected_address = re.sub(r'\s*\([^)]+\)', '', corrected_address)
                    else:
                        corrected_address = re.sub(pattern, replacement, corrected_address)
                    
                    print(f"[AddressMapper] Regel '{rule['name']}' angewendet: '{address}' -> '{corrected_address}'")
                    
            except Exception as e:
                print(f"[AddressMapper] FEHLER bei Regel '{rule['name']}': {e}")
        
        return corrected_address.strip()
    
    def map_address(self, address: str) -> Dict[str, Any]:
        """
        Mappe eine Adresse zu korrigierten Koordinaten
        
        Returns:
            Dict mit 'corrected_address', 'lat', 'lon', 'provider', 'method'
        """
        print(f"[AddressMapper] Mappe Adresse: '{address}'")
        
        # 1. BAR-Sondername-Suche (höchste Priorität)
        bar_match = self.find_bar_sondername(address)
        if bar_match:
            print(f"[AddressMapper] BAR-Sondername gefunden: {bar_match['beschreibung']}")
            return {
                'corrected_address': bar_match['echte_adresse'],
                'lat': bar_match['lat'],
                'lon': bar_match['lon'],
                'provider': 'address_mapper_bar',
                'method': 'bar_sondername',
                'confidence': 1.0,
                'kategorie': bar_match.get('kategorie', 'unknown')
            }
        
        # 2. Exakte Mapping-Suche
        exact_mapping = self.find_exact_mapping(address)
        if exact_mapping:
            print(f"[AddressMapper] Exakte Übereinstimmung gefunden: {exact_mapping['reason']}")
            return {
                'corrected_address': exact_mapping['corrected_address'],
                'lat': exact_mapping['lat'],
                'lon': exact_mapping['lon'],
                'provider': 'address_mapper_exact',
                'method': 'exact_mapping',
                'confidence': 1.0
            }
        
        # 3. Fuzzy Mapping-Suche
        fuzzy_mapping = self.find_fuzzy_mapping(address)
        if fuzzy_mapping:
            print(f"[AddressMapper] Ähnliche Übereinstimmung gefunden: {fuzzy_mapping['reason']}")
            return {
                'corrected_address': fuzzy_mapping['corrected_address'],
                'lat': fuzzy_mapping['lat'],
                'lon': fuzzy_mapping['lon'],
                'provider': 'address_mapper_fuzzy',
                'method': 'fuzzy_mapping',
                'confidence': 0.8
            }
        
        # 4. Regel-basierte Korrektur
        corrected_address = self.apply_rules(address)
        if corrected_address != address:
            print(f"[AddressMapper] Adresse korrigiert: '{address}' -> '{corrected_address}'")
            return {
                'corrected_address': corrected_address,
                'lat': None,
                'lon': None,
                'provider': 'address_mapper_rules',
                'method': 'rule_correction',
                'confidence': 0.6
            }
        
        # 5. Keine Korrektur möglich
        print(f"[AddressMapper] Keine Korrektur für Adresse gefunden: '{address}'")
        return {
            'corrected_address': address,
            'lat': None,
            'lon': None,
            'provider': None,
            'method': 'no_correction',
            'confidence': 0.0
        }
    
    def add_mapping(self, pattern: str, corrected_address: str, lat: float = None, lon: float = None, reason: str = "", priority: int = 1):
        """Füge neues Mapping zur Konfiguration hinzu"""
        new_mapping = {
            "pattern": pattern,
            "corrected_address": corrected_address,
            "lat": lat,
            "lon": lon,
            "reason": reason,
            "priority": priority
        }
        
        # Prüfe ob Mapping bereits existiert
        existing = self.find_exact_mapping(pattern)
        if existing:
            print(f"[AddressMapper] Mapping bereits vorhanden: {pattern}")
            return False
        
        self.mappings.append(new_mapping)
        print(f"[AddressMapper] Neues Mapping hinzugefügt: {pattern} -> {corrected_address}")
        return True
    
    def add_bar_sondername(self, sondername: str, echte_adresse: str, lat: float, lon: float, beschreibung: str, kategorie: str):
        """Füge neuen BAR-Sondernamen zur Konfiguration hinzu"""
        new_bar_entry = {
            "sondername": sondername,
            "echte_adresse": echte_adresse,
            "lat": lat,
            "lon": lon,
            "beschreibung": beschreibung,
            "kategorie": kategorie
        }
        self.bar_sondernamen.append(new_bar_entry)
        print(f"[AddressMapper] Neuer BAR-Sondername hinzugefügt: {sondername} -> {echte_adresse}")
        return True
    
    def save_config(self):
        """Speichere aktualisierte Konfiguration"""
        try:
            config = {
                "description": "Spezielle Adress-Mappings und Korrekturen für problematische CSV-Einträge",
                "version": "1.0",
                "mappings": self.mappings,
                "rules": self.rules,
                "bar_sondernamen": self.bar_sondernamen,
                "fallback_strategies": self.fallback_strategies
            }
            
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            
            print(f"[AddressMapper] Konfiguration gespeichert: {self.config_file}")
            return True
        except Exception as e:
            print(f"[AddressMapper] FEHLER beim Speichern: {e}")
            return False

# Globale Instanz
address_mapper = AddressMapper()
