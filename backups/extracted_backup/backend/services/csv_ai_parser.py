"""
CSV-AI-Parser für FAMO TrafficApp
Erweitert den bestehenden CSV-Parser mit KI-Intelligenz
"""

from __future__ import annotations
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path
import asyncio

from .ai_optimizer import AIOptimizer
from .ai_config import ai_config


class CSVAIParser:
    """KI-basierter CSV-Parser für Tourenpläne"""
    
    def __init__(self, use_local_ai: bool = True, api_key: Optional[str] = None):
        self.ai_optimizer = AIOptimizer(use_local=use_local_ai, api_key=api_key)
        self.config = ai_config
        
    async def parse_csv_with_ai(self, csv_content: str, filename: str = "") -> Dict[str, Any]:
        """
        Verwendet KI um CSV-Struktur zu verstehen und zu parsen
        
        Args:
            csv_content: Rohinhalt der CSV-Datei
            filename: Dateiname für bessere Kontext
            
        Returns:
            Geparste Daten mit KI-Analyse
        """
        try:
            print(f"🤖 KI-Parser startet für: {filename}")
            
            # 1. KI-Analyse der CSV-Struktur
            structure_analysis = await self._analyze_csv_structure(csv_content, filename)
            
            # 2. Tour-Header mit KI identifizieren
            tour_headers = await self._identify_tour_headers_with_ai(csv_content, structure_analysis)
            
            # 3. Kundenzeilen mit KI parsen
            customers = await self._parse_customers_with_ai(csv_content, structure_analysis)
            
            # 4. Touren mit KI gruppieren
            tours = await self._group_customers_into_tours_with_ai(customers, tour_headers)
            
            # 5. KI-basierte Optimierungsvorschläge
            optimization_suggestions = await self._generate_optimization_suggestions(tours)
            
            return {
                "success": True,
                "filename": filename,
                "ai_analysis": {
                    "structure_analysis": structure_analysis,
                    "tour_headers": tour_headers,
                    "optimization_suggestions": optimization_suggestions
                },
                "parsed_data": {
                    "tours": tours,
                    "customers": customers,
                    "metadata": {
                        "total_tours": len(tours),
                        "total_customers": len(customers),
                        "ai_enhanced": True
                    }
                }
            }
            
        except Exception as e:
            print(f"❌ Fehler im CSV-AI-Parser: {e}")
            return {
                "success": False,
                "error": str(e),
                "filename": filename
            }
    
    async def _analyze_csv_structure(self, csv_content: str, filename: str) -> Dict[str, Any]:
        """KI analysiert die CSV-Struktur"""
        prompt = f"""
        Analysiere diese CSV-Datei mit Tourenplänen:
        
        Dateiname: {filename}
        Inhalt (erste 1000 Zeichen):
        {csv_content[:1000]}
        
        Identifiziere:
        1. Dateistruktur (Spalten, Trennzeichen)
        2. Tour-Header-Format (z.B. "W-07.00 Uhr", "PIR Anlief. 7.45")
        3. Kundenzeilen-Format
        4. Besondere Markierungen (BAR, Tour, etc.)
        5. Zeitslot-Format
        
        Ausgabe als JSON:
        {{
            "structure": {{
                "separator": ";",
                "columns": ["Kdnr", "Name", "Straße", "PLZ", "Ort", "Gedruckt"],
                "tour_header_patterns": ["W-\\d{{2}}\\.\\d{{2}} Uhr", "PIR Anlief\\. \\d{{1,2}}\\.\\d{{2}} Uhr"],
                "customer_line_pattern": "\\d+;.+;.+;\\d{{5}};.+",
                "special_markers": ["BAR", "Tour"],
                "time_format": "HH.MM"
            }},
            "analysis": "Beschreibung der Struktur"
        }}
        """
        
        try:
            response = await self.ai_optimizer._call_ollama(prompt, require_json=True)
            # Versuche JSON zu parsen, auch wenn es unvollständig ist
            try:
                return json.loads(response)
            except json.JSONDecodeError as json_error:
                print(f"⚠️ JSON-Parsing fehlgeschlagen, versuche zu reparieren: {json_error}")
                # Versuche unvollständige JSON-Antwort zu reparieren
                repaired_response = self._repair_incomplete_json(response)
                if repaired_response:
                    return json.loads(repaired_response)
                else:
                    raise json_error
        except Exception as e:
            print(f"⚠️ KI-Strukturanalyse fehlgeschlagen, verwende Fallback: {e}")
            return self._fallback_structure_analysis(csv_content)
    
    async def _identify_tour_headers_with_ai(self, csv_content: str, structure_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """KI identifiziert Tour-Header"""
        prompt = f"""
        Identifiziere alle Tour-Header in dieser CSV-Datei:
        
        Struktur-Analyse: {json.dumps(structure_analysis, ensure_ascii=False)}
        
        CSV-Inhalt:
        {csv_content}
        
        Finde alle Zeilen, die Tour-Header sind (nicht Kundenzeilen).
        Tour-Header enthalten typischerweise:
        - Zeitangaben (z.B. "07.00 Uhr", "7.45 Uhr")
        - Tour-Typen (z.B. "W-", "PIR Anlief.", "CB Anlief.")
        - Keine Kundennummern
        
        Ausgabe als JSON-Liste:
        [
            {{
                "line_number": 1,
                "content": "W-07.00 Uhr BAR",
                "tour_type": "W-Tour",
                "time": "07:00",
                "bar_flag": true,
                "raw_line": "W-07.00 Uhr BAR"
            }},
            {{
                "line_number": 2,
                "content": "W-07.00 Uhr Tour", 
                "tour_type": "W-Tour",
                "time": "07:00",
                "bar_flag": false,
                "raw_line": "W-07.00 Uhr Tour"
            }}
        ]
        """
        
        try:
            response = await self.ai_optimizer._call_ollama(prompt, require_json=True)
            # Versuche JSON zu parsen, auch wenn es unvollständig ist
            try:
                return json.loads(response)
            except json.JSONDecodeError as json_error:
                print(f"⚠️ JSON-Parsing fehlgeschlagen, versuche zu reparieren: {json_error}")
                repaired_response = self._repair_incomplete_json(response)
                if repaired_response:
                    return json.loads(repaired_response)
                else:
                    raise json_error
        except Exception as e:
            print(f"⚠️ KI-Tour-Header-Identifikation fehlgeschlagen, verwende Fallback: {e}")
            return self._fallback_tour_headers(csv_content)
    
    async def _parse_customers_with_ai(self, csv_content: str, structure_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """KI parst Kundenzeilen"""
        prompt = f"""
        Parse alle Kundenzeilen aus dieser CSV-Datei:
        
        Struktur-Analyse: {json.dumps(structure_analysis, ensure_ascii=False)}
        
        CSV-Inhalt:
        {csv_content}
        
        Kundenzeilen enthalten:
        - Kundennummer (erste Spalte, numerisch)
        - Name, Straße, PLZ, Ort
        - Keine Tour-Header
        
        Ausgabe als JSON-Liste:
        [
            {{
                "line_number": 3,
                "customer_number": "5023",
                "name": "Stockmann KFZ-Service",
                "street": "Cowaplast 28",
                "postal_code": "01640",
                "city": "Coswig",
                "printed": "1",
                "bar_flag": false,
                "tour_assignment": "W-07.00 Uhr BAR"
            }}
        ]
        
        Wichtig: Ordne jeden Kunden der passenden Tour zu (basierend auf der Position im CSV).
        """
        
        try:
            response = await self.ai_optimizer._call_ollama(prompt, require_json=True)
            # Versuche JSON zu parsen, auch wenn es unvollständig ist
            try:
                return json.loads(response)
            except json.JSONDecodeError as json_error:
                print(f"⚠️ JSON-Parsing fehlgeschlagen, versuche zu reparieren: {json_error}")
                repaired_response = self._repair_incomplete_json(response)
                if repaired_response:
                    return json.loads(repaired_response)
                else:
                    raise json_error
        except Exception as e:
            print(f"⚠️ KI-Kundenparsing fehlgeschlagen, verwende Fallback: {e}")
            return self._fallback_customer_parsing(csv_content)
    
    async def _group_customers_into_tours_with_ai(self, customers: List[Dict[str, Any]], tour_headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """KI gruppiert Kunden in Touren"""
        prompt = f"""
        Gruppiere diese Kunden in die entsprechenden Touren:
        
        Tour-Header: {json.dumps(tour_headers, ensure_ascii=False)}
        Kunden: {json.dumps(customers, ensure_ascii=False)}
        
        Erstelle eine logische Gruppierung:
        - Kunden gehören zur Tour, die direkt über ihnen im CSV steht
        - Berücksichtige BAR-Flags
        - Ordne nach Zeitslots
        
        Ausgabe als JSON-Liste:
        [
            {{
                "tour_id": "w-07-00-bar",
                "tour_type": "W-Tour",
                "time": "07:00",
                "bar_flag": true,
                "raw_header": "W-07.00 Uhr BAR",
                "customers": [
                    {{
                        "customer_number": "5023",
                        "name": "Stockmann KFZ-Service",
                        "street": "Cowaplast 28",
                        "postal_code": "01640",
                        "city": "Coswig",
                        "bar_flag": false
                    }}
                ],
                "customer_count": 1,
                "bar_customer_count": 0
            }}
        ]
        """
        
        try:
            response = await self.ai_optimizer._call_ollama(prompt, require_json=True)
            # Versuche JSON zu parsen, auch wenn es unvollständig ist
            try:
                return json.loads(response)
            except json.JSONDecodeError as json_error:
                print(f"⚠️ JSON-Parsing fehlgeschlagen, versuche zu reparieren: {json_error}")
                repaired_response = self._repair_incomplete_json(response)
                if repaired_response:
                    return json.loads(repaired_response)
                else:
                    raise json_error
        except Exception as e:
            print(f"⚠️ KI-Tour-Gruppierung fehlgeschlagen, verwende Fallback: {e}")
            return self._fallback_tour_grouping(customers, tour_headers)
    
    async def _generate_optimization_suggestions(self, tours: List[Dict[str, Any]]) -> Dict[str, Any]:
        """KI generiert Optimierungsvorschläge"""
        prompt = f"""
        Analysiere diese Touren und schlage Optimierungen vor:
        
        Touren: {json.dumps(tours, ensure_ascii=False)}
        
        Berücksichtige:
        1. Zeitliche Überschneidungen
        2. Geografische Nähe
        3. Kapazitätsoptimierung
        4. BAR-Kunden-Verteilung
        5. Routenzusammenlegung (T-Routen)
        
        Ausgabe als JSON:
        {{
            "optimization_suggestions": [
                {{
                    "type": "route_consolidation",
                    "description": "T-Routen T2 und T3 können zusammengelegt werden",
                    "tours_involved": ["T2", "T3"],
                    "estimated_savings": {{
                        "distance_km": 15,
                        "time_minutes": 45,
                        "fuel_l": 1.2,
                        "cost_eur": 8.50
                    }}
                }}
            ],
            "route_analysis": {{
                "total_distance_km": 0,
                "total_time_minutes": 0,
                "efficiency_score": 0.0,
                "consolidation_potential": "high"
            }}
        }}
        """
        
        try:
            response = await self.ai_optimizer._call_ollama(prompt, require_json=True)
            # Versuche JSON zu parsen, auch wenn es unvollständig ist
            try:
                return json.loads(response)
            except json.JSONDecodeError as json_error:
                print(f"⚠️ JSON-Parsing fehlgeschlagen, versuche zu reparieren: {json_error}")
                repaired_response = self._repair_incomplete_json(response)
                if repaired_response:
                    return json.loads(repaired_response)
                else:
                    raise json_error
        except Exception as e:
            print(f"⚠️ KI-Optimierungsvorschläge fehlgeschlagen: {e}")
            return self._fallback_optimization_suggestions(tours)
    
    def _fallback_structure_analysis(self, csv_content: str) -> Dict[str, Any]:
        """Fallback-Strukturanalyse ohne KI"""
        lines = csv_content.split('\n')
        first_line = lines[0] if lines else ""
        
        return {
            "structure": {
                "separator": ";" if ";" in first_line else ",",
                "columns": first_line.split(";") if ";" in first_line else first_line.split(","),
                "tour_header_patterns": ["W-\\d{2}\\.\\d{2} Uhr", "PIR Anlief\\. \\d{1,2}\\.\\d{2} Uhr"],
                "customer_line_pattern": "\\d+;.+;.+;\\d{5};.+",
                "special_markers": ["BAR", "Tour"],
                "time_format": "HH.MM"
            },
            "analysis": "Fallback-Analyse ohne KI"
        }
    
    def _fallback_tour_headers(self, csv_content: str) -> List[Dict[str, Any]]:
        """Fallback-Tour-Header-Identifikation ohne KI"""
        tour_headers = []
        lines = csv_content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Einfache Regex-basierte Erkennung
            if re.match(r'^;.*\d{1,2}\.\d{2}\s*Uhr', line):
                tour_headers.append({
                    "line_number": i + 1,
                    "content": line.strip(';'),
                    "tour_type": "Unknown",
                    "time": "00:00",
                    "bar_flag": "BAR" in line.upper(),
                    "raw_line": line
                })
        
        return tour_headers
    
    def _fallback_customer_parsing(self, csv_content: str) -> List[Dict[str, Any]]:
        """Fallback-Kundenparsing ohne KI"""
        customers = []
        lines = csv_content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue
                
            # Einfache Regex-basierte Erkennung
            if re.match(r'^\d+;', line):
                parts = line.split(';')
                if len(parts) >= 5:
                    customers.append({
                        "line_number": i + 1,
                        "customer_number": parts[0],
                        "name": parts[1] if len(parts) > 1 else "",
                        "street": parts[2] if len(parts) > 2 else "",
                        "postal_code": parts[3] if len(parts) > 3 else "",
                        "city": parts[4] if len(parts) > 4 else "",
                        "printed": parts[5] if len(parts) > 5 else "",
                        "bar_flag": any("BAR" in part.upper() for part in parts),
                        "tour_assignment": "Unknown"
                    })
        
        return customers
    
    def _fallback_tour_grouping(self, customers: List[Dict[str, Any]], tour_headers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Fallback-Tour-Gruppierung ohne KI"""
        tours = []
        
        for header in tour_headers:
            tour = {
                "tour_id": f"tour-{header['line_number']}",
                "tour_type": header.get('tour_type', 'Unknown'),
                "time": header.get('time', '00:00'),
                "bar_flag": header.get('bar_flag', False),
                "raw_header": header.get('raw_line', ''),
                "customers": [],
                "customer_count": 0,
                "bar_customer_count": 0
            }
            
            # Einfache Gruppierung: Kunden nach diesem Header gehören zu dieser Tour
            for customer in customers:
                if customer.get('line_number', 0) > header.get('line_number', 0):
                    # Kunde kommt nach diesem Tour-Header
                    tour['customers'].append(customer)
                    tour['customer_count'] += 1
                    if customer.get('bar_flag', False):
                        tour['bar_customer_count'] += 1
            
            tours.append(tour)
        
        return tours
    
    def _fallback_optimization_suggestions(self, tours: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fallback-Optimierungsvorschläge ohne KI"""
        return {
            "optimization_suggestions": [
                {
                    "type": "basic_analysis",
                    "description": "Fallback-Analyse ohne KI",
                    "tours_involved": [],
                    "estimated_savings": {
                        "distance_km": 0,
                        "time_minutes": 0,
                        "fuel_l": 0,
                        "cost_eur": 0
                    }
                }
            ],
            "route_analysis": {
                "total_distance_km": 0,
                "total_time_minutes": 0,
                "efficiency_score": 0.0,
                "consolidation_potential": "unknown"
            }
        }
    
    def _repair_incomplete_json(self, incomplete_json: str) -> Optional[str]:
        """Versucht unvollständige JSON-Antworten zu reparieren"""
        try:
            # Entferne unvollständige Zeilen am Ende
            lines = incomplete_json.strip().split('\n')
            repaired_lines = []
            
            for line in lines:
                line = line.strip()
                if line and not line.startswith('...') and not line.startswith('⚠️'):
                    repaired_lines.append(line)
            
            if not repaired_lines:
                return None
            
            # Versuche die letzte Zeile zu vervollständigen
            last_line = repaired_lines[-1]
            if last_line.endswith(','):
                # Entferne das letzte Komma
                repaired_lines[-1] = last_line.rstrip(',')
            elif not last_line.endswith('}') and not last_line.endswith(']'):
                # Füge fehlende Klammern hinzu
                if last_line.startswith('{'):
                    repaired_lines.append('}')
                elif last_line.startswith('['):
                    repaired_lines.append(']')
            
            repaired_json = '\n'.join(repaired_lines)
            
            # Teste ob es jetzt gültiges JSON ist
            json.loads(repaired_json)
            print(f"✅ JSON erfolgreich repariert")
            return repaired_json
            
        except Exception as e:
            print(f"❌ JSON-Reparatur fehlgeschlagen: {e}")
            return None


# Hilfsfunktion für einfache Verwendung
async def parse_csv_with_ai(csv_content: str, filename: str = "", use_local_ai: bool = True) -> Dict[str, Any]:
    """Einfache Funktion zum Parsen von CSV mit AI"""
    parser = CSVAIParser(use_local_ai=use_local_ai)
    return await parser.parse_csv_with_ai(csv_content, filename)


if __name__ == "__main__":
    # Test-Funktion
    async def test():
        test_csv = """Tourenübersicht;;;;;
Lieferdatum: 14.08.25;;;;;
;;;;;
Kdnr;Name;Straße;PLZ;Ort;Gedruckt
;W-07.00 Uhr BAR;;;;
5023;Stockmann KFZ-Service;Cowaplast 28;01640;Coswig;1
;W-07.00 Uhr Tour;;;;
4772;Dresdner Klassiker Handel GmbH;Königsbrücker Straße 96;01099;Dresden;1"""
        
        result = await parse_csv_with_ai(test_csv, "test.csv")
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    asyncio.run(test())
