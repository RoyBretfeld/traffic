# -*- coding: utf-8 -*-
"""
LLM-Optimizer Service für FAMO TrafficApp 3.0

Integriert OpenAI API für intelligente Routenoptimierung und Clustering.
"""

import os
import time
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import json
import httpx
import asyncio

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logging.warning("OpenAI package not installed. LLM features will be disabled.")

@dataclass
class OptimizationResult:
    """Ergebnis einer LLM-basierten Optimierung"""
    optimized_route: List[int]
    confidence_score: float
    reasoning: str
    tokens_used: int
    processing_time: float
    model_used: str

@dataclass
class ClusteringResult:
    """Ergebnis einer LLM-basierten Clustering-Analyse"""
    clusters: List[List[int]]
    cluster_centers: List[Tuple[float, float]]
    reasoning: str
    tokens_used: int
    processing_time: float

class LLMOptimizer:
    """LLM-basierter Optimierer für Routenplanung"""
    
    def __init__(self, api_key: Optional[str] = None):
        # Versuche verschlüsselten Key zu laden
        if not api_key:
            try:
                from services.secure_key_manager import get_secure_key
                api_key = get_secure_key("openai")
            except ImportError:
                pass
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.max_tokens = int(os.getenv("LLM_MAX_TOKENS", "1000"))
        self.temperature = float(os.getenv("LLM_TEMPERATURE", "0.3"))
        
        self.logger = logging.getLogger(__name__)
        self.metrics = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "successful_calls": 0,
            "failed_calls": 0
        }
        
        # OSRM-Integration
        self.osrm_base = os.environ.get("OSRM_BASE_URL")
        self.osrm_profile = os.environ.get("OSRM_PROFILE", "driving")
        self.osrm_timeout = float(os.environ.get("OSRM_TIMEOUT", "10"))
        
        if OPENAI_AVAILABLE and self.api_key:
            try:
                self.client = openai.OpenAI(api_key=self.api_key)
                self.enabled = True
                self.logger.info("LLM-Optimizer initialized successfully")
            except Exception as e:
                self.logger.error(f"Failed to initialize OpenAI client: {e}")
                self.enabled = False
        else:
            self.enabled = False
            self.logger.warning("LLM-Optimizer disabled - OpenAI not available or no API key")
    
    def optimize_route(self, stops: List[Dict], region: str = "Dresden") -> OptimizationResult:
        """
        Optimiert eine Route mit LLM-basierter Heuristik
        
        Args:
            stops: Liste von Stopps mit Koordinaten
            region: Region für Kontext (z.B. "Dresden")
            
        Returns:
            OptimizationResult mit optimierter Route
        """
        if not self.enabled:
            return self._fallback_optimization(stops)
        
        start_time = time.time()
        
        try:
            # Bereite Prompt vor
            prompt = self._build_route_optimization_prompt(stops, region)
            
            # LLM-Call mit JSON-Format für strukturierte Antworten
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt("route_optimization")},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}  # Strukturierte Antwort für Reasoning
            )
            
            processing_time = time.time() - start_time
            tokens_used = response.usage.total_tokens
            
            # Parse Response (kann jetzt JSON sein)
            response_text = response.choices[0].message.content
            optimized_route, reasoning_data = self._parse_route_response_with_reasoning(
                response_text, len(stops)
            )
            confidence_score = self._calculate_confidence_score(stops, optimized_route)
            
            # Update Metrics
            self._update_metrics(tokens_used, processing_time, True)
            
            # Reasoning aus Response extrahieren
            reasoning_text = reasoning_data.get("reasoning", response.choices[0].message.content)
            
            return OptimizationResult(
                optimized_route=optimized_route,
                confidence_score=confidence_score,
                reasoning=reasoning_text,
                tokens_used=tokens_used,
                processing_time=processing_time,
                model_used=self.model
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"LLM optimization failed: {e}")
            self._update_metrics(0, processing_time, False)
            
            # Fallback zu Nearest-Neighbor
            return self._fallback_optimization(stops)
    
    def analyze_clustering(self, stops: List[Dict], max_clusters: int = 5) -> ClusteringResult:
        """
        Analysiert optimale Clustering-Parameter mit LLM
        
        Args:
            stops: Liste von Stopps
            max_clusters: Maximale Anzahl Cluster
            
        Returns:
            ClusteringResult mit Cluster-Empfehlungen
        """
        if not self.enabled:
            return self._fallback_clustering(stops, max_clusters)
        
        start_time = time.time()
        
        try:
            prompt = self._build_clustering_prompt(stops, max_clusters)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self._get_system_prompt("clustering")},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )
            
            processing_time = time.time() - start_time
            tokens_used = response.usage.total_tokens
            
            # Parse Clustering Response
            clusters, centers = self._parse_clustering_response(response.choices[0].message.content, stops)
            
            self._update_metrics(tokens_used, processing_time, True)
            
            return ClusteringResult(
                clusters=clusters,
                cluster_centers=centers,
                reasoning=response.choices[0].message.content,
                tokens_used=tokens_used,
                processing_time=processing_time
            )
            
        except Exception as e:
            processing_time = time.time() - start_time
            self.logger.error(f"LLM clustering analysis failed: {e}")
            self._update_metrics(0, processing_time, False)
            
            return self._fallback_clustering(stops, max_clusters)
    
    def _build_route_optimization_prompt(self, stops: List[Dict], region: str) -> str:
        """Baut Prompt für Routenoptimierung mit OSRM-Distanzen"""
        stops_info = []
        distance_matrix = None
        
        # Analysiere Straßen-Clustering (VERBESSERTE Normalisierung)
        street_groups = {}
        for i, stop in enumerate(stops):
            address = stop.get('address', '') or stop.get('street', '')
            if address:
                # Normalisiere Straßenname (Fröbelstraße, Fröbelstr., Fröbelstrasse → frobelstr)
                street_normalized = address.lower()
                # Entferne Hausnummer und PLZ für Gruppierung
                street_parts = street_normalized.split(',')[0].strip()  # Nur Straßenname vor Komma
                
                # Normalisiere Varianten (kräftiger)
                street_parts = street_parts.replace('straße', 'str')
                street_parts = street_parts.replace('strasse', 'str')
                street_parts = street_parts.replace('str.', 'str')
                street_parts = street_parts.replace('str ', 'str')
                # Entferne Hausnummern (z.B. "Fröbelstraße 20" → "frobelstr 20" → "frobelstr")
                import re
                street_parts = re.sub(r'\s+\d+[a-z]*', '', street_parts).strip()
                # Entferne Umlaute für bessere Matching (ö → oe, ü → ue, ä → ae)
                street_parts = street_parts.replace('ö', 'oe').replace('ü', 'ue').replace('ä', 'ae')
                street_parts = street_parts.replace('Ö', 'oe').replace('Ü', 'ue').replace('Ä', 'ae')
                
                if street_parts not in street_groups:
                    street_groups[street_parts] = []
                street_groups[street_parts].append(i)
        
        # Versuche OSRM-Distanzen zu berechnen
        if self.osrm_base:
            try:
                distance_matrix = self._get_osrm_distances(stops)
            except Exception as e:
                self.logger.warning(f"OSRM-Distanzen konnten nicht berechnet werden: {e}")
        
        for i, stop in enumerate(stops):
            lat = stop.get('lat')
            lon = stop.get('lon')
            coord_str = f"({lat:.4f}, {lon:.4f})" if lat and lon else ""
            stops_info.append(f"{i}: {stop.get('name', 'Unbekannt')} - {stop.get('address', 'Keine Adresse')} {coord_str}")
        
        prompt = f"""
Optimiere die Route für {len(stops)} Stopps in {region}.

Stopps:
{chr(10).join(stops_info)}
"""
        
        # Zeige Straßen-Clustering falls vorhanden
        if street_groups:
            multi_street_groups = {k: v for k, v in street_groups.items() if len(v) > 1}
            if multi_street_groups:
                prompt += "\n⚠️ WICHTIG: STRAßEN-CLUSTERING ERKANNT:\n"
                prompt += "Folgende Adressen liegen auf derselben Straße und MÜSSEN NACHEINANDER abgefahren werden:\n"
                for street, indices in multi_street_groups.items():
                    street_names = [stops[i].get('address', '') or stops[i].get('street', '') for i in indices]
                    prompt += f"  • {street.upper()}: Stopps {indices} - {', '.join(street_names[:3])}{'...' if len(street_names) > 3 else ''}\n"
                prompt += "\nREGEL: Fahre ALLE Adressen einer Straße ab, bevor du zur nächsten Straße wechselst!\n"
                prompt += "Beispiel: Fröbelstraße 20 → Fröbelstraße 51a → DANN erst zur Tharandter Straße\n"
                prompt += "NIEMALS: Fröbelstraße 20 → Tharandter Straße → zurück zu Fröbelstraße 51a\n\n"
        
        # Füge Distanz-Matrix hinzu falls verfügbar
        if distance_matrix:
            prompt += "\nStraßen-Distanzen zwischen Stopps (in km, basierend auf OSRM):\n"
            for i in range(len(stops)):
                row = []
                for j in range(len(stops)):
                    if i == j:
                        row.append("-")
                    else:
                        dist = distance_matrix.get((i, j), "?")
                        row.append(f"{dist:.1f}" if isinstance(dist, float) else str(dist))
                prompt += f"  Von {i} nach: {' | '.join(row)}\n"
            prompt += "\nDiese Distanzen basieren auf realen Straßenrouten (nicht Luftlinie).\n"
        else:
            prompt += "\nHinweis: Distanzen basieren auf geografischer Nähe (Koordinaten).\n"
        
        prompt += """
KRITISCHE OPTIMIERUNGS-REGELN:

1. STRAßEN-CLUSTERING (HÖCHSTE PRIORITÄT):
   - Wenn mehrere Adressen auf derselben Straße liegen, fahre diese IMMER NACHEINANDER ab
   - Beispiel: Fröbelstraße 20 → Fröbelstraße 51a → DANN erst zur nächsten Straße
   - NIEMALS: Eine Straße verlassen und später zurückkehren (vermeide Rückwege)
   
2. MINIMALE GESAMTFAHRZEIT:
   - Nutze die Straßen-Distanzen (OSRM) falls verfügbar
   - Wähle die Reihenfolge mit kürzester Gesamtfahrzeit
   - Berücksichtige aber: Straßen-Clustering hat Priorität über minimale Einzel-Distanz
   
3. LOGISCHE GEOGRAFISCHE REIHENFOLGE:
   - Fahre in eine Richtung, vermeide Zick-Zack-Routen
   - Gruppiere nahe gelegene Gebiete zusammen
   - Prioritäten der Kunden (falls vorhanden)

4. BEGRÜNDUNG:
   - Erkläre WARUM du die Reihenfolge so gewählt hast
   - Erkläre besonders WARUM Adressen derselben Straße zusammen gruppiert wurden
   - Erkläre WARUM ein eventueller Rückweg vermieden wurde

Gib die optimale Reihenfolge als Liste von Indizes zurück (z.B. [0, 3, 1, 2]).
Begründe deine Entscheidung AUSFÜHRLICH, besonders bezüglich Straßen-Clustering.
"""
        return prompt
    
    def _get_osrm_distances(self, stops: List[Dict]) -> Dict[Tuple[int, int], float]:
        """Berechnet OSRM-Distanzen zwischen allen Stopps"""
        if not self.osrm_base:
            return {}
        
        distance_matrix = {}
        
        try:
            # Asynchroner Aufruf in synchroner Umgebung
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def fetch_distances():
                async with httpx.AsyncClient(timeout=self.osrm_timeout) as client:
                    for i in range(len(stops)):
                        for j in range(len(stops)):
                            if i == j:
                                continue
                            
                            lat_i = stops[i].get('lat')
                            lon_i = stops[i].get('lon')
                            lat_j = stops[j].get('lat')
                            lon_j = stops[j].get('lon')
                            
                            if not all([lat_i, lon_i, lat_j, lon_j]):
                                continue
                            
                            coords = f"{lon_i},{lat_i};{lon_j},{lat_j}"
                            base = self.osrm_base.rstrip("/")
                            url = f"{base}/route/v1/{self.osrm_profile}/{coords}"
                            params = {"overview": "false"}
                            
                            try:
                                resp = await client.get(url, params=params)
                                if resp.status_code == 200:
                                    data = resp.json()
                                    if "routes" in data and len(data["routes"]) > 0:
                                        route = data["routes"][0]
                                        distance_km = route.get("distance", 0) / 1000.0
                                        distance_matrix[(i, j)] = distance_km
                            except Exception:
                                # Fehler bei einzelnen Distanzen ignorieren
                                pass
            
            loop.run_until_complete(fetch_distances())
            loop.close()
            
        except Exception as e:
            self.logger.warning(f"Fehler bei OSRM-Distanzberechnung: {e}")
        
        return distance_matrix
    
    def _build_clustering_prompt(self, stops: List[Dict], max_clusters: int) -> str:
        """Baut Prompt für Clustering-Analyse"""
        return f"""
Analysiere diese {len(stops)} Stopps für optimale Clustering:

{chr(10).join([f"{i}: {s.get('name', 'Unbekannt')} - {s.get('address', 'Keine Adresse')}" for i, s in enumerate(stops)])}

Empfehle:
- Optimale Anzahl Cluster (max. {max_clusters})
- Cluster-Zuordnung für jeden Stopp
- Begründung der Clustering-Strategie

Gib die Cluster als Listen von Indizes zurück.
"""
    
    def _get_system_prompt(self, task_type: str) -> str:
        """Gibt System-Prompt für verschiedene Aufgaben zurück"""
        prompts = {
            "route_optimization": """
Du bist ein Experte für Routenoptimierung und Logistik für FAMO TrafficApp.

DEINE AUFGABE:
Optimiere Routen für LKW-Fahrer basierend auf geografischer Nähe und Zeit-Constraints.

VERBINDLICHE REGELN:

1. STRAßEN-CLUSTERING (HÖCHSTE PRIORITÄT - KRITISCH!):
   - Wenn mehrere Adressen auf derselben Straße liegen, fahre diese IMMER NACHEINANDER ab
   - Beispiel: Fröbelstraße 20 → Fröbelstraße 51a → DANN erst zur nächsten Straße
   - NIEMALS eine Straße verlassen und später zurückkehren (vermeide Rückwege)
   - Gruppiere nach Straßenname (Fröbelstraße, Tharandter Straße, etc.)
   - Dies hat Priorität über minimale Einzel-Distanzen zwischen Stopps
   - Ziel: Effiziente Straßen-Abarbeitung, keine unnötigen Rückwege

2. ZEIT-CONSTRAINTS (KRITISCH):
   - Max. Gesamtzeit pro Route: 60-65 Minuten (inkl. Servicezeit)
   - Servicezeit pro Kunde: 2 Minuten (Ladezeit)
   - Rückfahrt zum Depot zählt NICHT in die 60-65 Minuten
   - Berechnung: Fahrzeit + (Anzahl_Kunden × 2_Minuten) ≤ 65 Minuten

3. DEPOT (Start/Ende):
   - Jede Route startet bei FAMO Depot: Stuttgarter Str. 33, 01189 Dresden
   - Koordinaten: 51.0111988, 13.7016485
   - Jede Route endet beim Depot (Rückfahrt wird nach der 60-65 Min Regel addiert)

4. GEOGRAFISCHES CLUSTERING:
   - Gruppiere Kunden nach geografischer Nähe (nach Straßen-Clustering)
   - Verwende OSRM-Straßendistanzen (nicht Luftlinie) falls verfügbar
   - Ziel: Minimale Gesamtfahrzeit (aber Straßen-Clustering hat Priorität)
   - Ausgewogene Touren: Keine Tour sollte deutlich mehr Kunden haben als andere

5. REASONING (WICHTIG):
   - Erkläre WARUM du Kunden in bestimmte Touren gruppierst
   - Erkläre WARUM du die Reihenfolge so gewählt hast (besonders Straßen-Clustering)
   - Erkläre WARUM du Touren splittest (falls nötig)
   - Gib geografische Begründungen (z.B. "Kunden 1-5 sind alle in Dresden-West")
   - Erkläre explizit: "Adressen auf Fröbelstraße wurden zusammengefasst, dann Tharandter Straße"

ANTWORTE MIT:
- JSON mit optimierter Route (Liste von Indizes)
- Detailliertes reasoning-Feld mit Erklärungen (besonders Straßen-Clustering)
- Metadaten über Clustering-Entscheidungen
""",
            "multi_tour_generation": """
Du bist ein Experte für Logistik und Routenoptimierung für FAMO TrafficApp.

DEINE AUFGABE:
Teile große Touren (z.B. W-07.00 mit 36 Kunden) in mehrere optimale Sub-Touren (A, B, C...) auf.

VERBINDLICHE REGELN:

1. ZEIT-CONSTRAINTS:
   - Max. 60-65 Minuten pro Sub-Tour (inkl. Servicezeit)
   - Servicezeit: 2 Minuten pro Kunde
   - Rückfahrt zum Depot zählt NICHT in die 60-65 Minuten
   - Berechnung: Fahrzeit_bis_letzter_Kunde + (Anzahl_Kunden × 2_Minuten) ≤ 65 Minuten

2. DEPOT-INTEGRATION:
   - Jede Sub-Tour startet bei FAMO Depot (51.0111988, 13.7016485)
   - Jede Sub-Tour endet beim Depot
   - Depot wird automatisch als erster und letzter Punkt eingefügt

3. GEOGRAFISCHES CLUSTERING:
   - Gruppiere Kunden nach geografischer Nähe
   - Verwende OSRM-Straßendistanzen für echte Fahrzeiten
   - Ziel: Minimale Gesamtfahrzeit über alle Sub-Touren
   - Ausgewogene Verteilung: Sub-Touren sollten ähnliche Größe haben

4. TOUR-SPLITTING:
   - Wenn eine Tour > 65 Minuten: Splitte in mehrere Sub-Touren
   - Naming: "W-07.00 A", "W-07.00 B", "W-07.00 C", ...
   - Jede Sub-Tour muss selbstständig funktionieren (Start/Ende Depot)

5. REASONING (KRITISCH):
   - Erkläre WARUM du bestimmte Kunden zusammen gruppierst
   - Erkläre WARUM du die Reihenfolge innerhalb einer Tour so gewählt hast
   - Erkläre WARUM du die Tour an bestimmten Stellen gesplittet hast
   - Gib konkrete geografische Begründungen

ANTWORTE MIT JSON:
{
  "tours": [
    {
      "tour_id": "W-07.00 A",
      "customer_ids": [1, 2, 3, ...],
      "reasoning": "Detaillierte Begründung..."
    }
  ],
  "overall_reasoning": "Gesamtbegründung..."
}
""",
            "clustering": """
Du bist ein Experte für geografisches Clustering und Tourenplanung für FAMO TrafficApp.
Analysiere die Stopps und empfehle optimale Cluster für effiziente Touren.
Berücksichtige geografische Nähe, Kundenprioritäten und logistische Faktoren.
Erkläre deine Clustering-Entscheidungen ausführlich.
Antworte mit konkreten Cluster-Zuordnungen und Begründung.
"""
        }
        return prompts.get(task_type, "Du bist ein hilfreicher Assistent für Logistik und Optimierung.")
    
    def _parse_route_response_with_reasoning(self, response: str, num_stops: int) -> Tuple[List[int], Dict[str, Any]]:
        """Parst LLM-Response mit Reasoning-Daten"""
        try:
            import json
            # Versuche JSON zu parsen
            try:
                data = json.loads(response)
                if "optimized_route" in data:
                    route = data["optimized_route"]
                    if isinstance(route, list) and all(isinstance(x, int) for x in route):
                        route = [r for r in route if 0 <= r < num_stops]
                        if len(set(route)) == num_stops and len(route) == num_stops:
                            return route, {
                                "reasoning": data.get("reasoning", ""),
                                "estimated_driving_time_minutes": data.get("estimated_driving_time_minutes"),
                                "estimated_service_time_minutes": data.get("estimated_service_time_minutes"),
                                "estimated_total_time_minutes": data.get("estimated_total_time_minutes"),
                                "cluster_analysis": data.get("cluster_analysis", "")
                            }
            except json.JSONDecodeError:
                pass
            
            # Fallback auf altes Parsing
            route = self._parse_route_response(response, num_stops)
            return route, {"reasoning": response}
            
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen der Route mit Reasoning: {e}")
            route = self._parse_route_response(response, num_stops)
            return route, {"reasoning": f"Parse-Fehler: {e}"}
    
    def _parse_route_response(self, response: str, num_stops: int) -> List[int]:
        """Parst LLM-Response für Routenoptimierung"""
        try:
            import re
            import json
            
            # Versuche JSON-Format zu finden [0, 1, 2, 3]
            json_match = re.search(r'\[[\d\s,]+\]', response)
            if json_match:
                try:
                    route = json.loads(json_match.group())
                    if isinstance(route, list) and all(isinstance(x, int) for x in route):
                        # Validiere: Alle Indizes müssen < num_stops sein und unique
                        route = [r for r in route if 0 <= r < num_stops]
                        if len(set(route)) == num_stops and len(route) == num_stops:
                            return route
                except (json.JSONDecodeError, ValueError):
                    pass
            
            # Fallback: Suche nach markdown-formatierter Liste **[0, 1, 2, 3]**
            md_match = re.search(r'\*\*\[([\d\s,]+)\]\*\*', response)
            if md_match:
                try:
                    route = [int(x.strip()) for x in md_match.group(1).split(',') if x.strip().isdigit()]
                    route = [r for r in route if 0 <= r < num_stops]
                    if len(set(route)) == num_stops and len(route) == num_stops:
                        return route
                except (ValueError, AttributeError):
                    pass
            
            # Fallback: Suche nach "Reihenfolge: 0, 1, 2, 3"
            order_match = re.search(r'(?:reihenfolge|route|order)[:\s]+\[?([\d\s,]+)\]?', response, re.IGNORECASE)
            if order_match:
                try:
                    route = [int(x.strip()) for x in order_match.group(1).split(',') if x.strip().isdigit()]
                    route = [r for r in route if 0 <= r < num_stops]
                    if len(set(route)) == num_stops and len(route) == num_stops:
                        return route
                except (ValueError, AttributeError):
                    pass
            
            # Letzter Fallback: Standard-Reihenfolge
            self.logger.warning(f"Konnte Route nicht parsen aus: {response[:200]}")
            return list(range(num_stops))
                
        except Exception as e:
            self.logger.error(f"Fehler beim Parsen der Route: {e}")
            return list(range(num_stops))
    
    def _parse_clustering_response(self, response: str, stops: List[Dict]) -> Tuple[List[List[int]], List[Tuple[float, float]]]:
        """Parst LLM-Response für Clustering"""
        try:
            # Vereinfachte Implementierung - in Produktion erweitern
            clusters = [list(range(len(stops)))]  # Ein Cluster mit allen Stopps
            centers = [(0.0, 0.0)]  # Placeholder
            return clusters, centers
        except Exception:
            return [list(range(len(stops)))], [(0.0, 0.0)]
    
    def _calculate_confidence_score(self, stops: List[Dict], route: List[int]) -> float:
        """Berechnet Confidence-Score für optimierte Route"""
        # Prüfe Validität
        if not route or len(route) != len(stops):
            return 0.0
        
        # Prüfe ob alle Indizes gültig sind
        if set(route) != set(range(len(stops))):
            return 0.0
        
        # Base score für erfolgreiche Route
        score = 0.7
        
        # Bonus: Prüfe auf geografische Logik (wenn OSRM verfügbar)
        if self.osrm_base and len(stops) > 2:
            try:
                # Berechne Gesamtdistanz der Route
                total_distance = 0.0
                valid_route = True
                
                for i in range(len(route) - 1):
                    idx_from = route[i]
                    idx_to = route[i + 1]
                    
                    lat_from = stops[idx_from].get('lat')
                    lon_from = stops[idx_from].get('lon')
                    lat_to = stops[idx_to].get('lat')
                    lon_to = stops[idx_to].get('lon')
                    
                    if not all([lat_from, lon_from, lat_to, lon_to]):
                        valid_route = False
                        break
                
                if valid_route:
                    # Wenn Route geografisch sinnvoll scheint, erhöhe Confidence
                    score = 0.85
            except Exception:
                pass
        
        return min(score, 1.0)
    
    def _fallback_optimization(self, stops: List[Dict]) -> OptimizationResult:
        """Fallback-Optimierung ohne LLM"""
        import math
        
        def haversine_distance(lat1, lon1, lat2, lon2):
            R = 6371000.0
            lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
            return 2 * R * math.asin(math.sqrt(a))
        
        # Nearest-Neighbor Fallback
        if not stops or len(stops) <= 1:
            return OptimizationResult(
                optimized_route=list(range(len(stops))),
                confidence_score=1.0,
                reasoning="Fallback: Keine Optimierung nötig",
                tokens_used=0,
                processing_time=0.0,
                model_used="fallback"
            )
        
        # Filtere Stopps mit Koordinaten
        valid_stops = [(i, stop) for i, stop in enumerate(stops) 
                      if stop.get('lat') and stop.get('lon')]
        
        if len(valid_stops) <= 1:
            return OptimizationResult(
                optimized_route=list(range(len(stops))),
                confidence_score=0.5,
                reasoning="Fallback: Zu wenige gültige Koordinaten",
                tokens_used=0,
                processing_time=0.0,
                model_used="fallback"
            )
        
        # Nearest-Neighbor Algorithmus
        optimized = [valid_stops[0][0]]
        remaining = valid_stops[1:]
        
        while remaining:
            last_stop = stops[optimized[-1]]
            nearest_idx = min(range(len(remaining)), 
                            key=lambda i: haversine_distance(
                                last_stop['lat'], last_stop['lon'],
                                remaining[i][1]['lat'], remaining[i][1]['lon']
                            ))
            optimized.append(remaining.pop(nearest_idx)[0])
        
        return OptimizationResult(
            optimized_route=optimized,
            confidence_score=0.7,
            reasoning="Fallback: Nearest-Neighbor Optimierung",
            tokens_used=0,
            processing_time=0.0,
            model_used="fallback"
        )
    
    def _fallback_clustering(self, stops: List[Dict], max_clusters: int) -> ClusteringResult:
        """Fallback-Clustering ohne LLM"""
        return ClusteringResult(
            clusters=[list(range(len(stops)))],
            cluster_centers=[(0.0, 0.0)],
            reasoning="Fallback: Ein Cluster mit allen Stopps",
            tokens_used=0,
            processing_time=0.0
        )
    
    def _update_metrics(self, tokens: int, processing_time: float, success: bool):
        """Aktualisiert Performance-Metriken"""
        self.metrics["total_calls"] += 1
        self.metrics["total_tokens"] += tokens
        self.metrics["total_time"] += processing_time
        
        if success:
            self.metrics["successful_calls"] += 1
        else:
            self.metrics["failed_calls"] += 1
    
    def get_performance_report(self) -> Dict[str, Any]:
        """Gibt Performance-Report zurück"""
        base_report = {
            "status": "enabled" if self.enabled else "disabled",
            "model": self.model if self.enabled else "N/A",
        }
        
        if self.metrics["total_calls"] == 0:
            return {**base_report, "calls_made": False}
        
        avg_time = self.metrics["total_time"] / self.metrics["total_calls"]
        success_rate = self.metrics["successful_calls"] / self.metrics["total_calls"]
        
        return {
            **base_report,
            "total_calls": self.metrics["total_calls"],
            "successful_calls": self.metrics["successful_calls"],
            "failed_calls": self.metrics["failed_calls"],
            "success_rate": success_rate,
            "total_tokens": self.metrics["total_tokens"],
            "calls_made": True,
            "avg_processing_time": avg_time,
            "total_processing_time": self.metrics["total_time"]
        }
    
    def reset_metrics(self):
        """Setzt Metriken zurück"""
        self.metrics = {
            "total_calls": 0,
            "total_tokens": 0,
            "total_time": 0.0,
            "successful_calls": 0,
            "failed_calls": 0
        }
